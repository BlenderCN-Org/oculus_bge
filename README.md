# Blender Game Engine - Oculus

System to integrate the Oculus Rift into the BGE.

This is work in progress, use at your own risk.

Pre-Requisite
============
* Blender Decklink branch
  Windows 32: http://dalaifelinto.com/ftp/builds/decklink.zip

Oculus Legacy  (Linux, Mac, Windows)
* Oculus 0.5 runtime

Oculus (Windows)
* Oculus 0.7 runtime

Note
====
* Windows 64 builds are not working at the moment, use 32 bits instead

How to Use
==========

Append the 'Camera.VR' from the sample.blend into your `.blend` file. Your file needs to be able to access the `head_mounted_display` folder.

The `Camera.VR` object has a `backend` game property that you can pick between `oculus` or `oculus_legacy`, depending on the SDK you are ysing.


Easy Installation
=================
You can get the latest version of the system here:
http://www.dalaifelinto.com/ftp/builds/oculus_bge.zip

Advanced Installation
=====================
In a terminal paste the following commands:
```
$ git clone https://github.com/dfelinto/oculus_bge.git
$ cd oculus_bge
$ git submodule update --init --recursive --remote
```

Now follow the sample.blend to know how to integrate this in your file.

Update
======
In a terminal paste the following commands:
```
$ git pull origin
$ git submodule update --recursive --remote
```

Roadmap
=======
* Proper documentation

Credits
=======
* Oculus SDK 0.5 wrapper by https://github.com/jherico/python-ovrsdk
* Oculus SDK 0.7 bridge: Dalai Felinto and Djalma Lucio @ Visgraf / IMPA 
* Blender Addon - Dalai Felinto - http://www.dalaifelinto.com

Acknowledgements
================
* Benoit Bolsee - for the BGE offscreen drawing support
