from bge import logic, render, texture
from bgl import *


def init():
    """
    setup render callback, create gpu offscreen
    """
    if not hasattr(logic, 'setRender'):
        print("You require a patched Blender with bge.logic.setRender() method")
        logic.endGame()

    scene = logic.getCurrentScene()
    scene.post_draw.append(draw)
    camera = scene.objects.get('Camera.VR')

    if not camera:
        print("You need a \"Camera.VR\" object")
        logic.endGame()

    offscreen = render.offScreenCreate(512, 512, 0, render.RAS_OFS_RENDER_TEXTURE)
    color_texture = offscreen.color
    image_render = texture.ImageRender(scene, camera, offscreen)
    image_render.alpha = True
    texture_buffer = bytearray(offscreen.width * offscreen.height * 4)

    logic.globalDict['offscreen'] = offscreen
    logic.globalDict['color_texture'] = color_texture
    logic.globalDict['image_render'] = image_render
    logic.globalDict['texture_buffer'] = texture_buffer


def loop():
    """
    update offscreen buffer
    """
    logic.globalDict['image_render'].refresh(logic.globalDict['texture_buffer'])


def draw():
    """
    draw overlay texture
    """
    color_texture = logic.globalDict['color_texture']
    drawPreview(color_texture, 50)


def drawRectangle():
    texco = [(1, 1), (0, 1), (0, 0), (1,0)]
    verco = [(1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0), ( 1.0, -1.0)]

    glPolygonMode(GL_FRONT_AND_BACK , GL_FILL)

    glColor4f(1.0, 1.0, 1.0, 0.0)

    glBegin(GL_QUADS)
    for i in range(4):
        glTexCoord3f(texco[i][0], texco[i][1], 0.0)
        glVertex2f(verco[i][0], verco[i][1])
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


def drawPreview(color_texture, scale):
    if not scale:
        return

    if scale != 100:
        viewport = Buffer(GL_INT, 4)
        glGetIntegerv(GL_VIEWPORT, viewport)

        width = int(scale * 0.01 * viewport[2])
        height = int(scale * 0.01 * viewport[3])

        glViewport(viewport[0], viewport[1], width, height)
        glScissor(viewport[0], viewport[1], width, height)

    glDisable(GL_DEPTH_TEST)

    view_setup()

    glEnable(GL_TEXTURE_2D)
    glActiveTexture(GL_TEXTURE0)

    glBindTexture(GL_TEXTURE_2D, color_texture)
    drawRectangle()
    glBindTexture(GL_TEXTURE_2D, 0)

    glDisable(GL_TEXTURE_2D)

    view_reset()

    if scale != 100:
        glViewport(viewport[0], viewport[1], viewport[2], viewport[3])
        glScissor(viewport[0], viewport[1], viewport[2], viewport[3])

