from bge import logic, render, texture
from mathutils import Matrix, Quaternion
from bgl import *


VERBOSE = True

def init():
    """
    called from logic brick
    """
    if not hasattr(logic, 'setRender'):
        print("ERROR: You require a patched Blender with bge.logic.setRender() method")
        return logic.endGame()

    scene = logic.getCurrentScene()
    camera = scene.objects.get('Camera.VR')

    if not camera:
        print("ERROR: Missing special Camera.VR object")
        return logic.endGame()

    backend = camera['backend']

    hmd = HMD(backend)

    if not hmd.start():
        return logic.endGame()

    """
    waiting for the following fix to use logic.globalDict instead of globals
    https://developer.blender.org/T46870

    (this is fixed, but it has not been merged in decklink yet)
    """
    logic.hmd = hmd


def loop():
    """
    called from logic brick
    """
    if hasattr(logic, 'hmd'):
        logic.hmd.loop()


def recenter(cont):
    """
    called from logic brick
    """
    if not cont.sensors[0].positive:
        return

    if hasattr(logic, 'hmd'):
        logic.hmd.reCenter()


def mirror(cont):
    """
    called from logic brick
    """
    if not cont.sensors[0].positive:
        return

    if hasattr(logic, 'hmd'):
        logic.hmd.mirror()


# #####################################
# Main Class
# #####################################

class Logger:
    def error(self, message, is_fatal):
        print(message)

        if is_fatal:
            logic.endGame()

    @staticmethod
    def log_traceback(err):
        raise err
        print(err)
        logic.endGame()


class HMD:
    def __init__(self, backend):
        self._hmd = None
        self._backend = backend
        self._mirror = False
        self.logger = Logger()
        self._checkLibraryPath()

    def __del__(self):
        self._hmd.quit()

    @property
    def use_mirror(self):
        return self._mirror and self._hmd.is_direct_mode

    def mirror(self):
        self._mirror = not self._mirror
        scene = logic.getCurrentScene()
        self._setupMirror(scene)

    def reCenter(self):
        return self._hmd.reCenter()

    def start(self):
        try:
            scene = logic.getCurrentScene()
            self._hmd = self._getHMDClass()(scene, self.logger.error)

            if not self._hmd.init():
                self.logger.error("Error initializing device", True)
                return False

        except Exception as E:
            self.logger.log_traceback(E)
            self._hmd = None
            return False

        else:
            self._setupGame()
            self._setupMirror(scene)
            return True

    def loop(self):
        self._hmd.loop()

        scene = logic.getCurrentScene()
        camera = scene.objects.get('Camera.VR')

        for i in range(2):
            self._hmd.setEye(i)

            offscreen = self._hmd.offscreen
            projection_matrix = self._hmd.projection_matrix
            modelview_matrix = self._hmd.modelview_matrix

            self._setMatrices(camera, projection_matrix, modelview_matrix)

            # drawing
            self._hmd.image_render.refresh()

        self._hmd.frameReady()

    def _setupGame(self):
        """
        general game settings
        """
        # required when logic takes most of the time
        logic.setMaxLogicFrame(1)

        # make sure we use the correct frame rate
        logic.setLogicTicRate(75)

        # redundant call since the SDK should also handle this
        render.setVsync(False)

    def _setupMirror(self, scene):
        if self.use_mirror:
            if self._drawMirror not in scene.post_draw:
                scene.post_draw.append(self._drawMirror)

            logic.setRender(True)
        else:
            logic.setRender(False)

    def _drawMirror(self):
        texture_a = self._hmd._color_texture[0]
        texture_b = self._hmd._color_texture[1]
        drawPreview(texture_a, texture_b)

    def _checkLibraryPath(self):
        """if library exists append it to sys.path"""
        import sys
        import os

        libs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'libs')
        oculus_path = os.path.join(libs_path, "hmd_sdk_bridge")

        if oculus_path not in sys.path:
            sys.path.append(oculus_path)

    def _getHMDClass(self):
        if self._backend == 'oculus':
            return BridgeOculus

        elif self._backend == 'oculus_legacy':
            return BridgeOculusLegacy

        else:
            self.logger.error('Oculus backend \"{0}\" not supported'.format(self._backend), True)
            return None

    def _checkOculus(self):
        """
        check if Oculus is connected
        """
        # TODO check is oculus is connected
        return True

    def _setMatrices(self, camera, projection_matrix, modelview_matrix):
        camera.projection_matrix = projection_matrix

        modelview_matrix.invert()
        camera.worldPosition = modelview_matrix.translation
        camera.worldOrientation = modelview_matrix.to_quaternion()


# #####################################
# OpenGL
# #####################################

def drawRectangle(eye):
    texco = [(1, 1), (0, 1), (0, 0), (1,0)]
    verco = [[(0.0, 1.0), (-1.0, 1.0), (-1.0, -1.0), ( 0.0, -1.0)],
             [(1.0, 1.0), ( 0.0, 1.0), ( 0.0, -1.0), ( 1.0, -1.0)]]

    glPolygonMode(GL_FRONT_AND_BACK , GL_FILL)

    glColor4f(1.0, 1.0, 1.0, 0.0)

    glBegin(GL_QUADS)
    for i in range(4):
        glTexCoord3f(texco[i][0], texco[i][1], 0.0)
        glVertex2f(verco[eye][i][0], verco[eye][i][1])
    glEnd()


def view_setup():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    glMatrixMode(GL_TEXTURE)
    glPushMatrix()
    glLoadIdentity()

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glOrtho(-1, 1, -1, 1, -20, 20)
    gluLookAt(0.0, 0.0, 1.0, 0.0,0.0,0.0, 0.0,1.0,0.0)


def view_reset():
    # Get texture info
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()

    glMatrixMode(GL_TEXTURE)
    glPopMatrix()

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def drawPreview(color_texture_left, color_texture_right):
    act_tex = Buffer(GL_INT, 1)
    glGetIntegerv(GL_TEXTURE_2D, act_tex)

    glDisable(GL_DEPTH_TEST)

    view_setup()

    glEnable(GL_TEXTURE_2D)
    glActiveTexture(GL_TEXTURE0)

    glBindTexture(GL_TEXTURE_2D, color_texture_left)
    drawRectangle(0)

    glBindTexture(GL_TEXTURE_2D, color_texture_right)
    drawRectangle(1)

    glBindTexture(GL_TEXTURE_2D, act_tex[0])

    glDisable(GL_TEXTURE_2D)

    view_reset()


# #####################################
# HMD BRIDGE SDK
# github.com/dfelinto/hmd_sdk_bridge
# #####################################

class HMD_Base:
    __slots__ = {
        "_name",
        "_current_eye",
        "_error_callback",
        "_width",
        "_height",
        "_projection_matrix",
        "_head_transformation",
        "_is_direct_mode",
        "_eye_pose",
        "_offscreen",
        "_image_render",
        "_color_texture",
        "_modelview_matrix",
        "_near",
        "_far",
        }

    def __init__(self, name, is_direct_mode, context, error_callback):
        self._name = name
        self._is_direct_mode = is_direct_mode
        self._error_callback = error_callback
        self._current_eye = 0
        self._width = [0, 0]
        self._height = [0, 0]
        self._projection_matrix = [Matrix.Identity(4), Matrix.Identity(4)]
        self._modelview_matrix = [Matrix.Identity(4), Matrix.Identity(4)]
        self._color_texture = [0, 0]
        self._offscreen = [None, None]
        self._image_render = [None, None]
        self._eye_orientation_raw = [[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]
        self._eye_position_raw = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        self._scale = self._calculateScale()

        self._updateViewClipping()

    @property
    def is_direct_mode(self):
        return self._is_direct_mode

    @property
    def width(self):
        return self._width[self._current_eye]

    @width.setter
    def width(self, value):
        self._width[self._current_eye] = value

    @property
    def height(self):
        return self._height[self._current_eye]

    @height.setter
    def height(self, value):
        self._height[self._current_eye] = value

    @property
    def offscreen(self):
        return self._offscreen[self._current_eye]

    @property
    def image_render(self):
        return self._image_render[self._current_eye]

    @property
    def color_texture(self):
        return self._color_texture[self._current_eye]

    @property
    def projection_matrix(self):
        return self._projection_matrix[self._current_eye]

    @property
    def modelview_matrix(self):
        return self._modelview_matrix[self._current_eye]

    def setEye(self, eye):
        self._current_eye = int(bool(eye))

    def init(self):
        """
        Initialize device

        :return: return True if the device was properly initialized
        :rtype: bool
        """
        try:
            scene = logic.getCurrentScene()
            camera = scene.objects.get('Camera.VR')

            if not camera:
                raise Exception('Camera.VR not found in scene')

            for i in range(2):
                offscreen = render.offScreenCreate(self._width[i], self._height[i], 0, render.RAS_OFS_RENDER_TEXTURE)
                image_render = texture.ImageRender(scene, camera, offscreen)
                image_render.alpha = True
                self._offscreen[i] = offscreen

                self._image_render[i] = image_render
                self._color_texture[i] = offscreen.color

                print(self._width[i], self._height[i], self._offscreen[i].color)

        except Exception as E:
            self.error('init', E, True)

            for i in range(2):
                self._offscreen[i] = None
                self._image_render[i] = None
                self._color_texture[i] = 0

            return False

        else:
            return True

    def loop(self):
        """
        Get fresh tracking data
        """
        self._updateViewClipping()
        self.updateMatrices()

    def frameReady(self):
        """
        The frame is ready to be sent to the device
        """
        assert False, "frameReady() not implemented for the \"{0}\" device".format(self._name)

    def reCenter(self):
        """
        Re-center the HMD device

        :return: return True if success
        :rtype: bool
        """
        assert False, "reCenter() not implemented for the \"{0}\" device".format(self._name)

    def quit(self):
        """
        Garbage collection
        """
        try:
            for i in range(2):
                self._offscreen[i] = None

        except Exception as E:
            print(E)

    def error(self, function, exception, is_fatal):
        """
        Handle error messages
        """
        if VERBOSE:
            print("HMD_SDK_BRIDGE :: {0}() : {1}".format(function, exception))
            import sys
            traceback = sys.exc_info()

            if traceback and traceback[0]:
                print(traceback[0])

        if hasattr(exception, "strerror"):
            message = exception.strerror
        else:
            message = str(exception)

        # send the error the interface
        self._error_callback(message, is_fatal)

    def updateMatrices(self):
        """
        Update OpenGL drawing matrices
        """
        view_matrix = self._getViewMatrix()

        for i in range(2):
            rotation_raw = self._eye_orientation_raw[i]
            rotation = Quaternion(rotation_raw).to_matrix().to_4x4()

            position_raw = self._eye_position_raw[i]

            # take scene units into consideration
            position_raw = self._scaleMovement(position_raw)
            position = Matrix.Translation(position_raw)

            transformation = position * rotation

            self._modelview_matrix[i] = transformation.inverted() * view_matrix

    def _getViewMatrix(self):
        from bge import logic

        scene = logic.getCurrentScene()
        camera = scene.active_camera

        return camera.worldTransform.inverted()

    def _updateViewClipping(self):
        from bge import logic

        scene = logic.getCurrentScene()
        camera = scene.active_camera

        self._near = camera.near
        self._far = camera.far

    def _calculateScale(self):
        """
        if BU != 1 meter, scale the transformations
        """
        # Scene unit system not supported in the BGE
        return None

    def _scaleMovement(self, position):
        """
        if BU != 1 meter, scale the transformations
        """
        if self._scale is None:
            return position

        return [position[0] * self._scale,
                position[1] * self._scale,
                position[2] * self._scale]

    def _convertMatrixTo4x4(self, value):
        matrix = Matrix()

        matrix[0] = value[0:4]
        matrix[1] = value[4:8]
        matrix[2] = value[8:12]
        matrix[3] = value[12:16]

        return matrix.transposed()


class BridgeOculus(HMD_Base):
    def __init__(self, context, error_callback):
        super(BridgeOculus, self).__init__('Oculus', True, context, error_callback)

    def _getHMDClass(self):
        from bridge.hmd.oculus import HMD
        return HMD

    @property
    def projection_matrix(self):
        if self._current_eye:
            matrix = self._hmd.getProjectionMatrixRight(self._near, self._far)
        else:
            matrix = self._hmd.getProjectionMatrixLeft(self._near, self._far)

        self.projection_matrix = matrix
        return super(BridgeOculus, self).projection_matrix

    @projection_matrix.setter
    def projection_matrix(self, value):
        self._projection_matrix[self._current_eye] = \
                self._convertMatrixTo4x4(value)

    def init(self):
        """
        Initialize device

        :return: return True if the device was properly initialized
        :rtype: bool
        """
        try:
            HMD = self._getHMDClass()
            self._hmd = HMD()

            # gather arguments from HMD

            self.setEye(0)
            self.width = self._hmd.width_left
            self.height = self._hmd.height_left

            self.setEye(1)
            self.width = self._hmd.width_right
            self.height = self._hmd.height_right

            # initialize FBO
            if not super(BridgeOculus, self).init():
                raise Exception("Failed to initialize HMD")

            # send it back to HMD
            if not self._setup():
                raise Exception("Failed to setup BridgeOculus")

        except Exception as E:
            self.error('init', E, True)
            self._hmd = None
            return False

        else:
            return True

    def _setup(self):
        return self._hmd.setup(self._color_texture[0], self._color_texture[1])

    def loop(self):
        """
        Get fresh tracking data
        """
        try:
            data = self._hmd.update()

            self._eye_orientation_raw[0] = data[0]
            self._eye_orientation_raw[1] = data[2]
            self._eye_position_raw[0] = data[1]
            self._eye_position_raw[1] = data[3]

            # update matrices
            super(BridgeOculus, self).loop()

        except Exception as E:
            self.error("loop", E, False)
            return False

        return True

    def frameReady(self):
        """
        The frame is ready to be sent to the device
        """
        try:
            self._hmd.frameReady()

        except Exception as E:
            self.error("frameReady", E, False)
            return False

        return True

    def reCenter(self):
        """
        Re-center the HMD device

        :return: return True if success
        :rtype: bool
        """
        return self._hmd.reCenter()

    def quit(self):
        """
        Garbage collection
        """
        self._hmd = None
        return super(BridgeOculus, self).quit()


class BridgeOculusLegacy(BridgeOculus):
    def __init__(self, context, error_callback):
        HMD_Base.__init__(self, 'BridgeOculus Legacy', False, context, error_callback)

    def _getHMDClass(self):
        from bridge.hmd.oculus_legacy import HMD
        return HMD
