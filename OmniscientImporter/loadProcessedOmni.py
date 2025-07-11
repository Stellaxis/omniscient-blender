import bpy
from .cameraProjection.cameraProjectionMaterial import create_projection_shader
from .setupCompositingNodes import setup_compositing_nodes
from .ui.utils import set_scene_fps, get_scene_fps
import os


def loadProcessedOmni(self, video_filepath, camera_filepath, geo_filepath, camera_fps=None, camera_settings=None):
    scene = bpy.context.scene
    scene.is_processing_shot = True

    def get_base_name(filepath):
        return os.path.splitext(os.path.basename(filepath))[0]

    base_name = get_base_name(geo_filepath).split('.')[0]

    def names_match(name1, name2):
        return name1.split('.')[0] == name2.split('.')[0]

    # Create or get the "Scene_Omni" collection in the current scene
    collection_name = "Scene_Omni"
    existing_omniscient_collection = None
    for coll in bpy.context.scene.collection.children:
        if coll.name.startswith(collection_name):
            for obj in coll.objects:
                if obj.type == 'MESH' and names_match(obj.name, base_name):
                    existing_omniscient_collection = coll
                    imported_mesh = obj
                    break
        if existing_omniscient_collection:
            break

    if existing_omniscient_collection is None:
        omniscient_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(omniscient_collection)
    else:
        omniscient_collection = existing_omniscient_collection

    def move_to_collection(obj, collection):
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        collection.objects.link(obj)

    def hide_omniscient_collections(scene):
        for omni_collection in scene.Omni_Collections:
            if omni_collection.collection:
                omni_collection.collection.hide_viewport = True
                omni_collection.collection.hide_render = True

    # If a matching mesh exists, skip importing the mesh and just import the camera
    if existing_omniscient_collection is None:
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
        elif geo_filepath.endswith(('.usd', '.usdc', '.usda')):
            bpy.ops.wm.usd_import(filepath=geo_filepath)
        # .ply
        elif geo_filepath.endswith('.ply'):
            bpy.ops.import_mesh.ply(filepath=geo_filepath)
        # .stl
        elif geo_filepath.endswith('.stl'):
            bpy.ops.import_mesh.stl(filepath=geo_filepath)

        # Find the newly imported mesh
        imported_mesh = find_new_mesh(initial_mesh_state)

        if imported_mesh:
            move_to_collection(imported_mesh, omniscient_collection)
            set_shade_smooth(imported_mesh)

    # Import the camera file into the blender scene
    initial_camera_state = capture_camera_state()
    import_camera(self, camera_filepath)
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
    clip = bpy.data.movieclips.load(video_filepath)  # Load only to get fps
    clip_fps = clip.fps
    width, height = img.size
    frame_duration = img.frame_duration
    bpy.context.scene.render.resolution_x = width
    bpy.context.scene.render.resolution_y = height
    set_scene_fps(bpy.context.scene, clip_fps)

    # Setting scene's start and end frames to match the video clip's duration
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = frame_duration

    # Adjust the timeline view to fit the entire range of frames
    for area in bpy.context.screen.areas:
        if area.type == 'DOPESHEET_EDITOR':
            override = bpy.context.copy()
            override["area"] = area
            override["region"] = area.regions[-1]
            with bpy.context.temp_override(**override):
                bpy.ops.action.view_all()
            break

    # Get preferences
    prefs = bpy.context.preferences.addons[__package__].preferences

    # Set renderer settings
    bpy.context.scene.render.engine = prefs.renderer
    if prefs.enable_motion_blur:
        bpy.context.scene.render.motion_blur_shutter = 0.5
        bpy.context.scene.render.use_motion_blur = True

    # Check if the collection already exists in Omni_Collections
    omni_collection = None
    for collection in bpy.context.scene.Omni_Collections:
        if collection.collection == omniscient_collection:
            omni_collection = collection
            break

    if omni_collection is None:
        omni_collection = bpy.context.scene.Omni_Collections.add()
        omni_collection.collection = omniscient_collection

    # Store the shot settings
    shot = omni_collection.shots.add()
    shot.camera = imported_cam
    shot.mesh = imported_mesh
    shot.video = img
    shot.fps = clip_fps
    shot.frame_start = 1
    shot.frame_end = frame_duration
    shot.resolution_x = width
    shot.resolution_y = height
    shot.shutter_speed = bpy.context.scene.render.motion_blur_shutter
    shot.collection = omniscient_collection
    shot.use_motion_blur = prefs.enable_motion_blur

    # Initialize material
    material = None

    if imported_cam:
        bpy.context.scene.Camera_Omni = imported_cam
        move_to_collection(imported_cam, omniscient_collection)
        if prefs.enable_dof:
            imported_cam.data.dof.use_dof = True
        imported_cam.data.show_background_images = True
        imported_cam.data.clip_start = 0.01
        imported_cam.data.clip_end = 10000
        bg = imported_cam.data.background_images.new()
        bg.image = img
        bg.image_user.frame_start = 1
        bg.image_user.frame_duration = frame_duration
        bg.alpha = 1.0
        # If vertical change sensor fit to vertical since auto mode isn't reliable
        if width < height:
            imported_cam.data.sensor_fit = 'VERTICAL'
        apply_camera_settings(imported_cam, camera_settings)

        # Create a unique material name
        material_name = f"Scan_Material_Omni_{base_name}"
        image_name = img.name
        # Check if the material already exists
        material = bpy.data.materials.get(material_name)
        if not material:
            material = create_projection_shader(material_name, image_name, imported_cam)
        else:
            # Update the existing material if it already exists
            create_projection_shader(material_name, image_name, imported_cam)

    if imported_mesh:
        bpy.context.scene.Scan_Omni = imported_mesh
        if prefs.use_shadow_catcher and prefs.renderer == 'CYCLES':
            imported_mesh.is_shadow_catcher = True
            imported_mesh.is_holdout = False  # Ensure holdout is disabled if shadow catcher is enabled
        elif prefs.use_holdout:
            imported_mesh.is_holdout = True

        # Assign the material to the imported mesh
        if material:
            if imported_mesh.data.materials:
                imported_mesh.data.materials[0] = material
            else:
                imported_mesh.data.materials.append(material)

    # Retime the abc to match the video FPS
    if camera_fps is not None:
        retime_alembic(clip_fps, camera_fps, frame_duration)

    # Enable shadow catcher pass
    bpy.context.view_layer.cycles.use_pass_shadow_catcher = True

    # Set up compositing nodes
    setup_compositing_nodes(img, prefs.renderer)

    # Save the shutter speed keyframes
    save_camera_settings(shot, camera_settings)

    # Assign a default name to the shot
    shot_index = len(omni_collection.shots) - 1
    shot.name = f"Shot {shot_index + 1:02d}"

    shot.assign_id()

    # Auto-select the imported shot
    bpy.context.scene.Selected_Shot_Index = shot_index
    if scene.Selected_Collection_Name != omniscient_collection.name:
        scene.Selected_Collection_Name = omniscient_collection.name

    hide_omniscient_collections(bpy.context.scene)
    omniscient_collection.hide_viewport = False
    omniscient_collection.hide_render = False

    # Trigger the shot switch
    if scene.camera != shot.camera:
        bpy.ops.object.switch_shot(index=shot_index)

    # Bake camera keyframes if the preference is enabled
    if prefs.bake_camera_keyframes and imported_cam:
        bpy.context.view_layer.objects.active = imported_cam
        bpy.ops.object.bake_camera_keyframes(
            frame_start=1,
            frame_end=frame_duration
        )

    scene.is_processing_shot = False


def capture_camera_state():
    # Capture the initial state of camera objects in the scene
    return set(obj.name for obj in bpy.context.scene.objects if obj.type == 'CAMERA')


def import_camera(self, camera_filepath):
    if camera_filepath.endswith('.abc'):
        bpy.ops.wm.alembic_import(filepath=camera_filepath)
    elif camera_filepath.endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=camera_filepath)
        self.report({'WARNING'}, "FBX format does not support importing the f-stop setting.")
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


def set_shade_smooth(mesh_obj):
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.shade_smooth()


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
        if 'film_offset' in frame_data:
            offset = frame_data['film_offset']
            if isinstance(offset, dict):
                camera.data.shift_x = offset.get('x', camera.data.shift_x)
                camera.data.shift_y = offset.get('y', camera.data.shift_y)
            elif isinstance(offset, (list, tuple)):
                if len(offset) > 0:
                    camera.data.shift_x = offset[0]
                if len(offset) > 1:
                    camera.data.shift_y = offset[1]
            else:
                camera.data.shift_y = offset
            camera.data.keyframe_insert(data_path="shift_x", frame=frame_index)
            camera.data.keyframe_insert(data_path="shift_y", frame=frame_index)
        if 'shutter_speed' in frame_data:
            scene_fps = get_scene_fps(scene)
            shutter_speed_fraction = frame_data['shutter_speed'] * scene_fps
            scene.render.motion_blur_shutter = shutter_speed_fraction
            scene.render.keyframe_insert(data_path="motion_blur_shutter", frame=frame_index)
        camera.data.keyframe_insert(data_path="lens", frame=frame_index)
        camera.data.dof.keyframe_insert(data_path="focus_distance", frame=frame_index)


def save_camera_settings(shot, settings):
    for frame_index, frame_data in enumerate(settings, start=1):
        if 'shutter_speed' in frame_data:
            new_keyframe = shot.shutter_speed_keyframes.add()
            new_keyframe.frame = frame_index
            new_keyframe.value = frame_data['shutter_speed']
            print(f"Added keyframe at frame {new_keyframe.frame} with value {new_keyframe.value}")


def calculate_frame_indices(camera_fps, clip_fps, frame_duration):
    first_frame_index = (1 / camera_fps) * clip_fps
    total_duration_seconds = (frame_duration - 1) / camera_fps
    new_total_frames_including_first = (total_duration_seconds * clip_fps) + first_frame_index
    return first_frame_index, new_total_frames_including_first
