import bpy
from bpy.types import Panel, Operator, PropertyGroup, UIList

def update_active_camera(scene, depsgraph):
    active_camera = scene.camera
    if active_camera:
        scene.Active_Camera_Name = active_camera.name
    else:
        scene.Active_Camera_Name = "None"

class OmniShot(PropertyGroup):
    camera: bpy.props.PointerProperty(type=bpy.types.Object)
    mesh: bpy.props.PointerProperty(type=bpy.types.Object)
    video: bpy.props.PointerProperty(type=bpy.types.Image)
    fps: bpy.props.FloatProperty(name="FPS", default=24.0)
    frame_start: bpy.props.IntProperty(name="Start Frame", default=1)
    frame_end: bpy.props.IntProperty(name="End Frame", default=250)

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
        layout.prop(prefs, "use_shadow_catcher", text="Set Mesh as Shadow Catcher")
        layout.prop(prefs, "use_holdout", text="Set Mesh as Holdout")

class OMNI_PT_ObjectsPanel(Panel):
    bl_label = "Imported Objects"
    bl_idname = "OMNI_PT_objects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Omniscient'
    bl_parent_id = "OMNI_PT_import"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.prop(scene, "Camera_Omni", text="Camera")
        
        row = layout.row()
        row.prop(scene, "Scan_Omni", text="Scan")

        row = layout.row()
        row.label(text=f"Active Camera: {scene.Active_Camera_Name}")

        row = layout.row()
        row.operator("object.switch_shot", text="Switch Shot")

        row = layout.row()
        row.prop(scene, "auto_switch_shot", text="Auto Switch Shot")

        # Add the list UI
        layout.template_list("OMNI_UL_ShotList", "", scene, "Omni_Shots", scene, "Selected_Shot_Index")

class OMNI_UL_ShotList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        shot = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(shot, "name", text="", emboss=False)
            layout.label(text=f"Camera: {shot.camera.name if shot.camera else 'None'}")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

    def invoke(self, context, event):
        # Switch shot when an item is selected
        scene = context.scene
        if scene.auto_switch_shot:
            bpy.ops.object.switch_shot()
        return super().invoke(context, event)

class OMNI_OT_SwitchShot(Operator):
    bl_idname = "object.switch_shot"
    bl_label = "Switch Shot"

    def execute(self, context):
        scene = context.scene
        shot_index = scene.Selected_Shot_Index
        if shot_index < len(scene.Omni_Shots):
            shot = scene.Omni_Shots[shot_index]
            scene.camera = shot.camera
            scene.frame_start = shot.frame_start
            scene.frame_end = shot.frame_end
            scene.render.fps = int(shot.fps)  # Convert fps to int
            adjust_timeline_view(context, shot.frame_start, shot.frame_end)
        return {'FINISHED'}

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
    if context.scene.auto_switch_shot:
        bpy.ops.object.switch_shot()

def register():
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

    bpy.app.handlers.depsgraph_update_post.append(update_active_camera)

def unregister():
    del bpy.types.Scene.Camera_Omni
    del bpy.types.Scene.Scan_Omni
    del bpy.types.Scene.Active_Camera_Name
    del bpy.types.Scene.Omni_Shots
    del bpy.types.Scene.Selected_Shot_Index
    del bpy.types.Scene.auto_switch_shot

    bpy.app.handlers.depsgraph_update_post.remove(update_active_camera)