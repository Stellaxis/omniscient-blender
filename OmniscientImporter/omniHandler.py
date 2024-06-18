import bpy
import json
import os
from . import bl_info
from .loadProcessedOmni import loadProcessedOmni


def loadOmni(self, omni_file):
    isVideoFileMissing = False
    isCameraFileMissing = False
    isGeoFileMissing = False
    video_filepath = ""
    camera_filepath = ""
    geo_filepath = ""
    camera_fps = None

    # Load the json file
    with open(omni_file, 'r') as f:
        data = json.load(f)

    # Check the minimum addon version specified in the .json file
    blender_data = data['blender']
    if blender_data:
        minimum_addon_version = blender_data['minimum_addon_version']
        ideal_addon_version = blender_data.get('ideal_addon_version')
        if minimum_addon_version:
            current_version = bl_info['version']
            current_version_str = ".".join(str(x) for x in current_version)
            if current_version_str < minimum_addon_version:
                bpy.ops.message.not_supported_omni('INVOKE_DEFAULT', minimum_addon_version=minimum_addon_version, current_version_str=current_version_str)
                return {'CANCELLED'}

        # Check if the current version is lower than the ideal version
        if ideal_addon_version and current_version_str < ideal_addon_version:
            bpy.context.window_manager.popup_text = f"Recommended version is:\n{ideal_addon_version}"

    # Get the filepaths from the json data
    video_relative_path = ""
    camera_relative_path = ""
    geo_relative_path = ""
    omni_file_version = data['version']

    # Check if the Omni file version is below 2.1.0
    if omni_file_version < "2.1.0":
        self.report({'ERROR'}, "Please re-export the shot using the Omniscient app version 1.16 or later.")
        return {'CANCELLED'}

    video_relative_path = data['data']['video']['relative_path']
    camera_relative_path = data['data']['camera']['relative_path']
    geo_relative_path = data['data']['geometry']['relative_path'][0]

    # Extract camera FPS value
    camera_data = data.get("data", {}).get("camera", {})
    camera_fps = camera_data.get("fps")

    camera_settings = data['data']['camera']['frames']

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
        loadProcessedOmni(self, video_filepath, camera_filepath, geo_filepath, camera_fps, camera_settings)

    else:
        bpy.ops.wm.missing_file_resolver('INVOKE_DEFAULT',
            isVideoFileMissing=isVideoFileMissing,
            isCameraFileMissing=isCameraFileMissing,
            isGeoFileMissing=isGeoFileMissing,
            CameraPath=camera_filepath,
            VideoPath=video_filepath,
            GeoPath=geo_filepath)
