import bpy
from .ui.infoPopups import showTextPopup

def loadProcessedOmni(video_filepath, camera_filepath, geo_filepath):
    # Import the geo file into the blender scene
    # .obj
    if geo_filepath.endswith('.obj'):
        # Get Blender version
        major, minor, patch = bpy.app.version

        if major >= 4:
            # For Blender 4.0 and above
            bpy.ops.wm.obj_import(filepath=geo_filepath)
        else:
            # For Blender versions before 4.0
            bpy.ops.import_scene.obj(filepath=geo_filepath)

    # .usd / .usdc / .usda
    elif geo_filepath.endswith('.usd') or geo_filepath.endswith('.usdc') or geo_filepath.endswith('.usda'):
        bpy.ops.wm.usd_import(filepath=geo_filepath)
    # .ply
    elif geo_filepath.endswith('.ply'):
        bpy.ops.import_mesh.ply(filepath=geo_filepath)
    # .stl
    elif geo_filepath.endswith('.stl'):
        bpy.ops.import_mesh.stl(filepath=geo_filepath)

    # Import the camera file into the blender scene
    initial_camera_state = capture_camera_state()
    import_camera(camera_filepath)
    imported_cam = find_new_camera(initial_camera_state)

    # Import the .mov file into the blender scene
    # -- RENDER --
    bpy.context.scene.render.film_transparent = True
    img = bpy.data.images.load(video_filepath)
    clip = bpy.data.movieclips.load(video_filepath) # Load only to get fps
    fps = clip.fps
    width, height = img.size
    frame_duration = img.frame_duration
    bpy.context.scene.render.resolution_x = width
    bpy.context.scene.render.resolution_y = height
    bpy.context.scene.render.fps = int(fps)

    if imported_cam:
        imported_cam.data.show_background_images = True
        bg = imported_cam.data.background_images.new()
        bg.image = img
        bg.image_user.frame_start = 1
        bg.image_user.frame_duration = frame_duration
        # If vertical change sensor fit to vertical since auto mode isn't reliable
        if width < height:
            imported_cam.data.sensor_fit = 'VERTICAL'

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

def capture_camera_state():
    # Capture the initial state of camera objects in the scene
    return set(obj.name for obj in bpy.context.scene.objects if obj.type == 'CAMERA')

def import_camera(camera_filepath):
    if camera_filepath.endswith('.abc'):
        bpy.ops.wm.alembic_import(filepath=camera_filepath)
    elif camera_filepath.endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=camera_filepath)
    elif camera_filepath.endswith(('.usd', '.usdc', '.usda')):
        bpy.ops.wm.usd_import(filepath=camera_filepath)


def find_new_camera(initial_state):
    # Find the newly imported camera by comparing the current state to the initial state
    current_state = set(obj.name for obj in bpy.context.scene.objects if obj.type == 'CAMERA')
    new_cameras = current_state - initial_state
    if new_cameras:
        # Assuming the first new camera found is the one imported
        return bpy.context.scene.objects[next(iter(new_cameras))]
    else:
        return None