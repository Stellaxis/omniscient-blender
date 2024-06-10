import bpy
from bpy.app.handlers import persistent
from bpy.types import Panel, Operator, PropertyGroup, UIList
from ..cameraProjection.cameraProjectionMaterial import delete_projection_nodes, reorder_projection_nodes
from ..setupCompositingNodes import setup_compositing_nodes
from ..loadCustomIcons import load_custom_icons, preview_collections

class ShutterSpeedKeyframe(PropertyGroup):
    frame: bpy.props.FloatProperty(name="Frame")
    value: bpy.props.FloatProperty(name="Value")

@persistent
def update_active_camera(scene, depsgraph):
    active_camera = scene.camera
    if active_camera:
        scene.Active_Camera_Name = active_camera.name
        current_index = scene.Selected_Shot_Index
        current_shot_camera = scene.Omni_Shots[current_index].camera if current_index < len(scene.Omni_Shots) else None

        if active_camera != current_shot_camera:
            for index, shot in enumerate(scene.Omni_Shots):
                if shot.camera == active_camera:
                    if scene.Selected_Shot_Index != index:
                        scene.Selected_Shot_Index = index
                        bpy.ops.object.switch_shot(index=index)
                    break
    else:
        scene.Active_Camera_Name = "None"

@persistent
def update_render_settings(self, context):
    scene = context.scene
    if scene.is_processing_shot:
        return
    current_index = scene.Selected_Shot_Index
    if current_index < len(scene.Omni_Shots):
        shot = scene.Omni_Shots[current_index]
        shot.use_motion_blur = scene.render.use_motion_blur
        shot.resolution_x = scene.render.resolution_x
        shot.resolution_y = scene.render.resolution_y
        shot.frame_start = scene.frame_start
        shot.frame_end = scene.frame_end
        shot.fps = scene.render.fps

class OmniShot(PropertyGroup):
    camera: bpy.props.PointerProperty(type=bpy.types.Object)
    mesh: bpy.props.PointerProperty(type=bpy.types.Object)
    video: bpy.props.PointerProperty(type=bpy.types.Image)
    fps: bpy.props.FloatProperty(name="FPS", default=24.0)
    frame_start: bpy.props.IntProperty(name="Start Frame", default=1)
    frame_end: bpy.props.IntProperty(name="End Frame", default=250)
    resolution_x: bpy.props.IntProperty(name="Resolution X", default=1920)
    resolution_y: bpy.props.IntProperty(name="Resolution Y", default=1080)
    shutter_speed_keyframes: bpy.props.CollectionProperty(type=ShutterSpeedKeyframe)
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)
    camera_projection_multiply: bpy.props.FloatProperty(name="Camera Projection Enabled", default=1.0)

    # Render settings properties
    use_motion_blur: bpy.props.BoolProperty(name="Use Motion Blur", default=False)

class OmniCollection(PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)

class OMNI_PT_ImportPanel(Panel):
    bl_label = "Omniscient"
    bl_idname = "OMNI_PT_import"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Omniscient'

    def draw(self, context):
        layout = self.layout
        layout.operator("load.omni", text="Import .omni")

class OMNI_PT_PreferencesPanel(Panel):
    bl_label = "Import Preferences"
    bl_idname = "OMNI_PT_import_preferences"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Omniscient'
    bl_parent_id = "OMNI_PT_import"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences.addons['OmniscientImporter'].preferences

        # Scene Options Panel
        box = layout.box()
        box.label(text="Scene", icon='SCENE_DATA')
        box.prop(prefs, "use_shadow_catcher")
        box.prop(prefs, "use_holdout")

        # Renderer Option
        box = layout.box()
        box.label(text="Renderer Settings", icon='RENDER_STILL')
        box.prop(prefs, "renderer", text="")

        # Motion Blur and Depth of Field Options
        box.prop(prefs, "enable_motion_blur")
        box.prop(prefs, "enable_dof")

        # Camera Keyframes Baking Option
        box = layout.box()
        box.label(text="Camera Settings", icon='CAMERA_DATA')
        box.prop(prefs, "bake_camera_keyframes")

class OMNI_PT_ShotsPanel(Panel):
    bl_label = "Shots"
    bl_idname = "OMNI_PT_shots"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Omniscient'
    bl_parent_id = "OMNI_PT_import"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Add the list UI
        layout.template_list("OMNI_UL_ShotList", "", scene, "Omni_Shots", scene, "Selected_Shot_Index")

class OMNI_UL_ShotList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        shot = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(shot, "name", text="", emboss=False)
            
            # Custom camera projector icons
            pcoll = preview_collections["main"]
            icon_on = pcoll["icon_cameraProjector_on"].icon_id
            icon_off = pcoll["icon_cameraProjector_off"].icon_id
            icon_value = icon_on if shot.camera_projection_multiply == 1.0 else icon_off
            row.operator("object.toggle_camera_projection", text="", icon_value=icon_value).index = index

            row.operator("object.delete_shot", text="", icon='X').index = index
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

    def draw_filter(self, context, layout):
        layout.label(text="Filter by Scene")

    def filter_items(self, context, data, property):
        flt_flags = []
        flt_neworder = []
        
        shots = getattr(data, property)
        scenes = sorted({shot.collection.name for shot in shots if shot.collection})
        
        for shot in shots:
            if shot.collection and shot.collection.name in scenes:
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0)

        return flt_flags, flt_neworder

    def invoke(self, context, event):
        bpy.ops.object.switch_shot()
        return super().invoke(context, event)

class OMNI_OT_SwitchShot(Operator):
    bl_idname = "object.switch_shot"
    bl_label = "Switch Shot"

    index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        shot_index = self.index if self.index is not None else scene.Selected_Shot_Index
        if shot_index < len(scene.Omni_Shots):
            shot = scene.Omni_Shots[shot_index]
            scene.camera = shot.camera
            scene.frame_start = shot.frame_start
            scene.frame_end = shot.frame_end
            scene.render.fps = int(shot.fps)  # Convert fps to int
            scene.render.resolution_x = shot.resolution_x
            scene.render.resolution_y = shot.resolution_y

            reorder_projection_nodes(shot.camera.name, shot.mesh)

            # Set scene's motion blur based on shot's settings 
            if scene.camera and scene.camera.data:
                clear_motion_blur_keyframes(scene)
                for keyframe in shot.shutter_speed_keyframes:
                    frame = keyframe.frame
                    value = keyframe.value * int(shot.fps)
                    scene.render.motion_blur_shutter = value
                    scene.render.keyframe_insert(data_path="motion_blur_shutter", frame=frame)

            # Update render settings based on the shot's stored values
            scene.render.use_motion_blur = shot.use_motion_blur

            adjust_timeline_view(context, shot.frame_start, shot.frame_end)
            if shot.collection:
                hide_omniscient_collections(scene)
                shot.collection.hide_viewport = False
                shot.collection.hide_render = False
            # Update compositing nodes with the correct image
            setup_compositing_nodes(shot.video)
        return {'FINISHED'}

class OMNI_OT_DeleteShot(Operator):
    bl_idname = "object.delete_shot"
    bl_label = "Delete Shot"

    index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        if 0 <= self.index < len(scene.Omni_Shots):
            shot = scene.Omni_Shots[self.index]

            delete_projection_nodes(shot.camera.name)

            # Unlink camera from scene and collection
            if shot.camera:
                for coll in shot.camera.users_collection:
                    coll.objects.unlink(shot.camera)
                bpy.data.objects.remove(shot.camera)

            # Remove the shot
            scene.Omni_Shots.remove(self.index)

            # Adjust the selected index
            if self.index == scene.Selected_Shot_Index:
                scene.Selected_Shot_Index = min(self.index, len(scene.Omni_Shots) - 1)

            return {'FINISHED'}
        return {'CANCELLED'}

class OMNI_OT_ToggleCameraProjection(Operator):
    bl_idname = "object.toggle_camera_projection"
    bl_label = "Toggle Camera Projection"

    index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        shot = scene.Omni_Shots[self.index]
        shot.camera_projection_multiply = 1.0 if shot.camera_projection_multiply == 0.0 else 0.0
        
        # Debug print to trace property update
        print(f"Toggled camera_projection_multiply for shot {shot.name} to {shot.camera_projection_multiply}")

        # Force update dependencies
        update_related_drivers(shot)
        return {'FINISHED'}

class OMNI_PT_VersionWarningPanel(Panel):
    bl_label = "Version Warning"
    bl_idname = "OMNI_PT_version_warning"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Omniscient'
    bl_order = 2

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        return bool(wm.popup_text)

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        if wm.popup_text:
            lines = wm.popup_text.split('\n')
            if lines:
                # First line with error icon
                row = layout.row()
                row.alert = True
                row.label(text=lines[0], icon='ERROR')
                
                # Center the remaining lines without error icon
                for line in lines[1:]:
                    row = layout.row()
                    row.alignment = 'CENTER'
                    row.label(text=line)
            
            row = layout.row()
            row.operator("wm.url_open", text="Update").url = "https://learn.omniscient-app.com/tutorial-thridParty/Blender"

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

def selected_shot_index_update(self, context):
    current_index = context.scene.Selected_Shot_Index
    current_shot = context.scene.Omni_Shots[current_index]
    
    if context.scene.camera != current_shot.camera:
        bpy.ops.object.switch_shot(index=current_index)

def add_driver_for_multiply(node, shot_index, data_path):
    driver = node.inputs[1].driver_add("default_value").driver
    driver.type = 'SCRIPTED'
    var = driver.variables.new()
    var.name = 'projection_multiply'
    var.targets[0].id_type = 'SCENE'
    var.targets[0].id = bpy.context.scene
    var.targets[0].data_path = f"Omni_Shots[{shot_index}].{data_path}"
    driver.expression = var.name

    # Force update dependencies
    bpy.context.scene.update_tag()
    bpy.context.view_layer.update()

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

def register():
    bpy.types.WindowManager.popup_text = bpy.props.StringProperty(
        name="Popup Text",
        default=""
    )
    bpy.types.Scene.Camera_Omni = bpy.props.PointerProperty(
        name="Camera_Omni",
        type=bpy.types.Object
    )
    bpy.types.Scene.Scan_Omni = bpy.props.PointerProperty(
        name="Scan_Omni",
        type=bpy.types.Object
    )
    
    bpy.types.Scene.Active_Camera_Name = bpy.props.StringProperty(name="Active Camera Name", default="None")
    bpy.types.Scene.Selected_Shot_Index = bpy.props.IntProperty(
        name="Selected Shot Index", 
        default=0,
        update=selected_shot_index_update
    )
    bpy.types.Scene.Omni_Shots = bpy.props.CollectionProperty(type=OmniShot)
    bpy.types.Scene.auto_switch_shot = bpy.props.BoolProperty(
        name="Auto Switch Shot",
        description="Automatically switch shot when selecting an OmniShot",
        default=True
    )
    bpy.types.Scene.Omni_Collections = bpy.props.CollectionProperty(type=OmniCollection)
    bpy.types.Scene.is_processing_shot = bpy.props.BoolProperty(
        name="Is Processing Shot",
        description="Flag to indicate if a shot is being processed",
        default=False
    )

    bpy.app.handlers.depsgraph_update_post.append(update_active_camera)
    bpy.app.handlers.depsgraph_update_post.append(update_render_settings)

def unregister():
    del bpy.types.WindowManager.popup_text
    del bpy.types.Scene.Camera_Omni
    del bpy.types.Scene.Scan_Omni
    del bpy.types.Scene.Active_Camera_Name
    del bpy.types.Scene.Omni_Shots
    del bpy.types.Scene.Selected_Shot_Index
    del bpy.types.Scene.auto_switch_shot
    del bpy.types.Scene.Omni_Collections

    bpy.app.handlers.depsgraph_update_post.remove(update_active_camera)
    bpy.app.handlers.depsgraph_update_post.remove(update_render_settings)
