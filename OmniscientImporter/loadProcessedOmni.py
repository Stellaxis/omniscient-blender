import bpy
import json
import os
from . import bl_info
from .ui.infoPopups import showTextPopup

def loadProcessedOmni(video_filepath, camera_filepath, geo_filepath):
    # Import the .abc file into the blender scene
    bpy.ops.wm.alembic_import(filepath=camera_filepath)

    # Import the .obj file into the blender scene
    bpy.ops.import_scene.obj(filepath=geo_filepath)

    # Import the .mov file into the blender scene
    # -- RENDER --
    cam = bpy.context.scene.objects['cameras']
    bpy.context.scene.render.film_transparent = True
    img = bpy.data.images.load(video_filepath)
    cam.data.show_background_images = True
    bg = cam.data.background_images.new()
    bg.image = img

    showTextPopup("Succes !")