import bpy
from bpy.app.handlers import persistent
from bpy.types import Panel, Operator, PropertyGroup, UIList
from ..cameraProjection.cameraProjectionMaterial import delete_projection_nodes, reorder_projection_nodes
from ..setupCompositingNodes import setup_compositing_nodes
from ..loadCustomIcons import load_custom_icons, preview_collections
from .utils import adjust_timeline_view, hide_omniscient_collections, clear_motion_blur_keyframes, update_related_drivers, selected_shot_index_update, get_selected_collection_and_shot, find_collection_and_shot_index_by_camera

# -------------------------------------------------------------------
# Property Groups
# -------------------------------------------------------------------

class ShutterSpeedKeyframe(PropertyGroup):
    frame: bpy.props.FloatProperty(name="Frame")
    value: bpy.props.FloatProperty(name="Value")

class OmniShot(PropertyGroup):
    id: bpy.props.IntProperty()
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
    camera_projection_multiply: bpy.props.FloatProperty(name="Camera Projection Enabled", default=0.0)
    use_motion_blur: bpy.props.BoolProperty(name="Use Motion Blur", default=False)

    def assign_id(self):
        self.id = OmniShot.get_next_id()

    @staticmethod
    def get_next_id():
        max_id = 0
        for collection in bpy.context.scene.Omni_Collections:
            for shot in collection.shots:
                if shot.id > max_id:
                    max_id = shot.id
        return max_id + 1

class OmniCollection(PropertyGroup):
    shots: bpy.props.CollectionProperty(type=OmniShot)
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)
    expanded: bpy.props.BoolProperty(name="Expanded", default=False)
    emission_value: bpy.props.FloatProperty(name="Emission Value", default=1.0, min=0.0, max=1000.0)
    color_scan: bpy.props.FloatVectorProperty(name="Color scan", subtype='COLOR', min=0.0, max=1.0, default=(0.18, 0.18, 0.18))

# -------------------------------------------------------------------
# Handlers
# -------------------------------------------------------------------

@persistent
def update_active_camera(scene, depsgraph):
    active_camera = scene.camera
    if active_camera:

        found_shot = None
        found_collection_index = -1
        found_shot_index = -1

        for collection_index, collection in enumerate(scene.Omni_Collections):
            for shot_index, shot in enumerate(collection.shots):
                if shot.camera == active_camera:
                    found_shot = shot
                    found_collection_index = collection_index
                    found_shot_index = shot_index
                    break
            if found_shot:
                break

        if found_shot:
            current_collection_index = scene.Selected_Collection_Index
            current_shot_index = scene.Selected_Shot_Index

            if (current_collection_index >= len(scene.Omni_Collections) or
                current_shot_index >= len(scene.Omni_Collections[current_collection_index].shots) or
                found_shot != scene.Omni_Collections[current_collection_index].shots[current_shot_index]):
                
                scene.Selected_Collection_Index = found_collection_index
                scene.Selected_Shot_Index = found_shot_index
                bpy.ops.object.switch_shot(index=found_shot_index, collection_index=found_collection_index)

@persistent
def update_render_settings(self, context):
    scene = context.scene
    if scene.is_processing_shot:
        return
    
    current_collection_index = scene.Selected_Collection_Index
    current_shot_index = scene.Selected_Shot_Index

    if current_collection_index < len(scene.Omni_Collections):
        collection = scene.Omni_Collections[current_collection_index]
        if current_shot_index < len(collection.shots):
            shot = collection.shots[current_shot_index]
            shot.use_motion_blur = scene.render.use_motion_blur
            shot.resolution_x = scene.render.resolution_x
            shot.resolution_y = scene.render.resolution_y
            shot.frame_start = scene.frame_start
            shot.frame_end = scene.frame_end
            shot.fps = scene.render.fps

# -------------------------------------------------------------------
# Panels
# -------------------------------------------------------------------

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

        if len(scene.Omni_Collections) > 1:
            layout.prop(scene, 'Selected_Collection_Name', text="")

        collection_index = scene.Selected_Collection_Index
        if collection_index < len(scene.Omni_Collections):
            collection = scene.Omni_Collections[collection_index]
            layout.template_list("OMNI_UL_ShotList", "", collection, "shots", scene, "Selected_Shot_Index")

            layout.prop(collection, "emission_value", text="Emission")
            layout.prop(collection, "color_scan", text="Color Scan")
        else:
            layout.label(text="No shots imported")

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

# -------------------------------------------------------------------
# UI Lists
# -------------------------------------------------------------------

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
            operator = row.operator("object.toggle_camera_projection", text="", icon_value=icon_value)
            operator.shot_id = shot.id

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

# -------------------------------------------------------------------
# Operators
# -------------------------------------------------------------------

class OMNI_OT_SwitchShot(Operator):
    bl_idname = "object.switch_shot"
    bl_label = "Switch Shot"

    index: bpy.props.IntProperty()
    collection_index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        collection_index = self.collection_index if self.collection_index is not None else scene.Selected_Collection_Index
        shot_index = self.index if self.index is not None else scene.Selected_Shot_Index

        collection, shot = get_selected_collection_and_shot(scene, collection_index, shot_index)

        if collection and shot:
            scene.camera = shot.camera
            scene.frame_start = shot.frame_start
            scene.frame_end = shot.frame_end
            scene.render.fps = int(shot.fps)
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

                if scene.Selected_Collection_Name != shot.collection.name:
                    scene.Selected_Collection_Name = shot.collection.name
                
            # Update compositing nodes with the correct image
            setup_compositing_nodes(shot.video)
        return {'FINISHED'}

class OMNI_OT_DeleteShot(Operator):
    bl_idname = "object.delete_shot"
    bl_label = "Delete Shot"

    index: bpy.props.IntProperty()
    collection_index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        collection_index = self.collection_index if self.collection_index is not None else scene.Selected_Collection_Index
        shot_index = self.index if self.index is not None else scene.Selected_Shot_Index

        if collection_index < len(scene.Omni_Collections):
            collection = scene.Omni_Collections[collection_index]
            if 0 <= shot_index < len(collection.shots):
                shot = collection.shots[shot_index]

                delete_projection_nodes(shot.camera.name)

                # Unlink camera from scene and collection
                if shot.camera:
                    for coll in shot.camera.users_collection:
                        coll.objects.unlink(shot.camera)
                    bpy.data.objects.remove(shot.camera)

                # Remove the shot
                collection.shots.remove(shot_index)

                # Adjust the selected index
                if shot_index == scene.Selected_Shot_Index:
                    scene.Selected_Shot_Index = min(shot_index, len(collection.shots) - 1)

                return {'FINISHED'}
        return {'CANCELLED'}

class OMNI_OT_ToggleCameraProjection(Operator):
    bl_idname = "object.toggle_camera_projection"
    bl_label = "Toggle Camera Projection"

    shot_id: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        for collection in scene.Omni_Collections:
            for shot in collection.shots:
                if shot.id == self.shot_id:
                    shot.camera_projection_multiply = 1.0 if shot.camera_projection_multiply == 0.0 else 0.0

                    # Force update dependencies
                    update_related_drivers(shot)
                    break

        return {'FINISHED'}


# -------------------------------------------------------------------
# Registration
# -------------------------------------------------------------------

# Function to get collection names
def get_collection_names(self, context):
    items = []
    if context is None:
        return items
    try:
        collections = context.scene.Omni_Collections
        items = [(col.collection.name, col.collection.name, "") for col in collections if col.collection]
    except AttributeError:
        pass  # Handle the case where the properties are not yet fully available
    return items

def selected_collection_name_update(self, context):
    scene = context.scene
    collection_name = scene.Selected_Collection_Name

    # Find the index of the collection with the selected name
    for index, collection in enumerate(scene.Omni_Collections):
        if collection.collection.name == collection_name:
            scene.Selected_Collection_Index = index

            if collection.shots:
                # Check if the active camera is already in the current collection
                current_camera = scene.camera
                _, _, current_collection_index, current_shot_index = find_collection_and_shot_index_by_camera(scene.camera)

                if current_collection_index != index:
                    # If the active shot is not in the current collection, change the shot index
                    scene.Selected_Shot_Index = 0
                    bpy.ops.object.switch_shot(index=0, collection_index=index)
                else:
                    scene.Selected_Shot_Index = current_shot_index
            else:
                scene.Selected_Shot_Index = -1
                
            break
    else:
        scene.Selected_Collection_Index = -1

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
    
    bpy.types.Scene.Selected_Shot_Index = bpy.props.IntProperty(
        name="Selected Shot Index", 
        default=0,
        update=selected_shot_index_update
    )
    bpy.types.Scene.Selected_Collection_Index = bpy.props.IntProperty(
        name="Selected Collection Index",
        default=0
    )
    bpy.types.Scene.Selected_Collection_Name = bpy.props.EnumProperty(
        name="",
        description="Choose a scene",
        items=get_collection_names,
        update=selected_collection_name_update
    )
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
    del bpy.types.Scene.Selected_Shot_Index
    del bpy.types.Scene.Selected_Collection_Index
    del bpy.types.Scene.Selected_Collection_Name
    del bpy.types.Scene.auto_switch_shot
    del bpy.types.Scene.Omni_Collections

    bpy.app.handlers.depsgraph_update_post.remove(update_active_camera)
    bpy.app.handlers.depsgraph_update_post.remove(update_render_settings)
