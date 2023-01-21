import bpy
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
    clip = bpy.data.movieclips.load(video_filepath) # Load only to get fps
    fps = clip.fps
    width, height = img.size
    frame_duration = img.frame_duration
    bpy.context.scene.render.resolution_x = width
    bpy.context.scene.render.resolution_y = height
    bpy.context.scene.render.fps = int(fps)
    cam.data.show_background_images = True
    bg = cam.data.background_images.new()
    bg.image = img
    bg.image_user.frame_start = 1
    bg.image_user.frame_duration = frame_duration
    # If vertical change sensor fit to vertical since auto mode isn't reliable
    if width < height:
        cam.data.sensor_fit = 'VERTICAL'

    # Retime the abc to match the video FPS
    # The abc is read at 24 FPS by default and this value is hard-coded
    cache_files = bpy.data.cache_files
    if len(cache_files) > 0:
        last_cache_file = cache_files[len(cache_files) - 1]
        
        cache_file = bpy.data.cache_files[last_cache_file.name]
        
        cache_file.override_frame = True
        
        cache_file.frame = 1
        cache_file.keyframe_insert(data_path="frame", frame = 1)
        
        cache_file.frame = ( clip.frame_duration * (clip.fps/24))
        cache_file.keyframe_insert(data_path="frame", frame = clip.frame_duration)
        
        #Set the animation to linear
        for keyframes in cache_file.animation_data.action.fcurves[0].keyframe_points.values():
            keyframes.interpolation = 'LINEAR'
    else:
        print("No cache files found.")

    showTextPopup("Succes !")