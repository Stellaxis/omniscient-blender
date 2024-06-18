import bpy


def hide_omniscient_collections(scene):
    for omni_collection in scene.Omni_Collections:
        if omni_collection.collection:
            omni_collection.collection.hide_viewport = True
            omni_collection.collection.hide_render = True


def clear_motion_blur_keyframes(scene):
    # Ensure the scene's animation data exists
    if scene.animation_data:
        action = scene.animation_data.action
        if action:
            # Find the fcurve for motion_blur_shutter in scene.render and clear its keyframes
            for fcurve in action.fcurves:
                if fcurve.data_path == "render.motion_blur_shutter":
                    action.fcurves.remove(fcurve)
                    break


def adjust_timeline_view(context, frame_start, frame_end):
    # Set the preview range
    context.scene.use_preview_range = True
    context.scene.frame_preview_start = frame_start
    context.scene.frame_preview_end = frame_end

    # Adjust the timeline view to fit the entire preview range
    for area in context.screen.areas:
        if area.type == 'DOPESHEET_EDITOR':
            override = context.copy()
            override["area"] = area
            override["region"] = area.regions[-1]
            with context.temp_override(**override):
                bpy.ops.action.view_all()
            break


def update_related_drivers(shot):
    # Debug print to trace function call
    print(f"Updating drivers for shot {shot.name}")

    def update_driver(driver):
        if driver:
            driver.expression = driver.expression  # Or update to any new expression

    # Update drivers related to the shot's mesh
    if shot.mesh and shot.mesh.type == 'MESH':
        for mat in shot.mesh.data.materials:
            if mat and mat.node_tree and mat.node_tree.animation_data:
                for fcurve in mat.node_tree.animation_data.drivers:
                    # Check if the driver is for an input socket's default value
                    data_path = fcurve.data_path
                    if '.inputs[' in data_path and data_path.endswith('default_value'):
                        update_driver(fcurve.driver)


def update_driver(obj):
    if obj.animation_data:
        for fc in obj.animation_data.drivers:
            fc.driver.expression = fc.driver.expression


def get_selected_collection_and_shot(scene, collection_index=None, shot_index=None):
    collection_index = collection_index if collection_index is not None else scene.Selected_Collection_Index
    shot_index = shot_index if shot_index is not None else scene.Selected_Shot_Index

    if collection_index < len(scene.Omni_Collections):
        collection = scene.Omni_Collections[collection_index]
        if shot_index < len(collection.shots):
            return collection, collection.shots[shot_index]
    return None, None


def selected_shot_index_update(self, context):
    scene = context.scene
    collection, current_shot = get_selected_collection_and_shot(scene)

    if collection and current_shot:
        if scene.camera != current_shot.camera:
            bpy.ops.object.switch_shot(index=scene.Selected_Shot_Index, collection_index=scene.Selected_Collection_Index)


def find_collection_and_shot_index_by_camera(camera):
    scene = bpy.context.scene
    for collection_index, collection in enumerate(scene.Omni_Collections):
        for shot_index, shot in enumerate(collection.shots):
            if shot.camera == camera:
                return collection, shot, collection_index, shot_index
    return None, None, None, None
