import bpy
from .ui.infoPopups import showTextPopup

def loadProcessedOmni(video_filepath, camera_filepath, geo_filepath, camera_fps=None, camera_settings=None):
    # Capture the initial state of mesh objects in the scene
    initial_mesh_state = capture_mesh_state()

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

    # Find the newly imported mesh
    imported_mesh = find_new_mesh(initial_mesh_state)
    
    # Import the camera file into the blender scene
    initial_camera_state = capture_camera_state()
    import_camera(camera_filepath)
    imported_cam = find_new_camera(initial_camera_state)

    # Ensure camera_fps is a float or None if not provided or conversion fails
    try:
        camera_fps = float(camera_fps) if camera_fps is not None else None
    except ValueError:
        print("Invalid camera FPS value; retiming will not be applied.")
        camera_fps = None

    # Import the .mov file into the blender scene
    # -- RENDER --
    bpy.context.scene.render.film_transparent = True
    img = bpy.data.images.load(video_filepath)
    clip = bpy.data.movieclips.load(video_filepath) # Load only to get fps
    clip_fps = clip.fps
    width, height = img.size
    frame_duration = img.frame_duration
    bpy.context.scene.render.resolution_x = width
    bpy.context.scene.render.resolution_y = height
    bpy.context.scene.render.fps = int(clip_fps)

    # Setting scene's start and end frames to match the video clip's duration
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = frame_duration 

    if imported_cam:
        bpy.context.scene.Camera_Omni = imported_cam
        imported_cam.data.show_background_images = True
        bg = imported_cam.data.background_images.new()
        bg.image = img
        bg.image_user.frame_start = 1
        bg.image_user.frame_duration = frame_duration
        # If vertical change sensor fit to vertical since auto mode isn't reliable
        if width < height:
            imported_cam.data.sensor_fit = 'VERTICAL'
        apply_camera_settings(imported_cam, camera_settings)

    if imported_mesh:
        bpy.context.scene.Scan_Omni = imported_mesh

    # Retime the abc to match the video FPS
    if camera_fps is not None:
        retime_alembic(clip_fps, camera_fps, frame_duration)

    showTextPopup("Success!")

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
        new_camera_name = next(iter(new_cameras))
        return bpy.context.scene.objects[new_camera_name]
    else:
        return None

def capture_mesh_state():
    # Capture the initial state of mesh objects in the scene
    return set(obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH')

def find_new_mesh(initial_state):
    # Find the newly imported mesh by comparing the current state to the initial state
    current_state = set(obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH')
    new_meshes = current_state - initial_state
    if new_meshes:
        new_mesh_name = next(iter(new_meshes))
        return bpy.context.scene.objects[new_mesh_name]
    else:
        return None

def retime_alembic(clip_fps, camera_fps, frame_duration):
    cache_files = bpy.data.cache_files
    if cache_files:
        last_cache_file = cache_files[-1]
        
        last_cache_file.override_frame = True
        
        # Calculate new first and last frame indices based on FPS changes
        first_time_value, new_total_time_including_first = calculate_frame_indices(camera_fps, clip_fps, frame_duration)
        
        # Insert the starting frame keyframe
        last_cache_file.frame = first_time_value
        last_cache_file.keyframe_insert(data_path="frame", frame=1)
        
        # Insert the keyframe for the new end frame
        last_cache_file.frame = new_total_time_including_first
        last_cache_file.keyframe_insert(data_path="frame", frame=frame_duration)
        
        # Ensure linear interpolation for all keyframes in the action's fcurves
        if last_cache_file.animation_data and last_cache_file.animation_data.action:
            for fcurve in last_cache_file.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'LINEAR'
    else:
        print("No cache files found.")

def apply_camera_settings(camera, settings):
    scene = bpy.context.scene
    for frame_index, frame_data in enumerate(settings, start=1):
        scene.frame_set(frame_index)  # Set the current frame
        camera.data.lens = frame_data['focal_length']
        camera.data.dof.focus_distance = frame_data['focus_distance']
        camera.data.keyframe_insert(data_path="lens", frame=frame_index)
        camera.data.dof.keyframe_insert(data_path="focus_distance", frame=frame_index)

def calculate_frame_indices(camera_fps, clip_fps, frame_duration):
    first_frame_index = (1 / camera_fps) * clip_fps
    total_duration_seconds = (frame_duration - 1) / camera_fps
    new_total_frames_including_first = (total_duration_seconds * clip_fps) + first_frame_index
    return first_frame_index, new_total_frames_including_first
