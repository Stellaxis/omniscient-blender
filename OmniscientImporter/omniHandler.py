import bpy
import json
import os
from . import bl_info
from .ui.info_popups import showTextPopup

isVideoFileMissing = False
isCameraFileMissing = False
isGeoFileMissing = False
video_filepath = ""
camera_filepath = ""
geo_filepath = ""

def loadOmni(self, omni_file):
    # Telling the function to consider as global
    global isVideoFileMissing
    global isCameraFileMissing
    global isGeoFileMissing
    global video_filepath
    global camera_filepath
    global geo_filepath

    # Load the json file
    with open(omni_file, 'r') as f:
        data = json.load(f)
        
    # Check the minimum plugin version specified in the .json file
    blender_data = data['blender']
    if blender_data:
        minimum_plugin_version = blender_data['minimum_plugin_version']
        if minimum_plugin_version:
            current_version = bl_info['version']
            current_version_str = ".".join(str(x) for x in current_version)
            if current_version_str < minimum_plugin_version:
                self.report({'ERROR'}, str(f"This .omni file requires at least version {minimum_plugin_version} of the Blender plugin, but the current version is {current_version_str}"))
                return {'CANCELLED'}

    # Get the filepaths from the json data
    video_relative_path = data['data']['video_relative_path']
    camera_relative_path = data['data']['camera_relative_path']
    geo_relative_path = data['data']['geo_relative_path'][0]

    # Make the filepaths absolute by combining them with the path of the .json file
    omni_dir = os.path.dirname(omni_file)
    video_filepath = os.path.join(omni_dir, video_relative_path)
    camera_filepath = os.path.join(omni_dir, camera_relative_path)
    geo_filepath = os.path.join(omni_dir, geo_relative_path)

    # Check if the video file exists
    if not os.path.exists(video_filepath):
        isVideoFileMissing = True
        # self.report({'ERROR'}, f"Video file not found at {video_filepath}")

    # Check if the camera file exists
    if not os.path.exists(camera_filepath):
        isCameraFileMissing = True
        # self.report({'ERROR'}, f"Camera file not found at {camera_filepath}")

    # Check if the geo file exists
    if not os.path.exists(geo_filepath):
        isGeoFileMissing = True
        # self.report({'ERROR'}, f"Geo file not found at {geo_filepath}")

    if (not isVideoFileMissing) and (not isCameraFileMissing) and (not isGeoFileMissing):
        loadProcessedOmni(video_filepath, camera_filepath, geo_filepath)
    else:
        bpy.ops.wm.missing_file_resolver('INVOKE_DEFAULT')

def loadProcessedOmni(self, video_filepath, camera_filepath, geo_filepath):
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
