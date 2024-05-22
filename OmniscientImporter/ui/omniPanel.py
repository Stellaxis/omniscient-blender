import bpy
from bpy.types import Panel, Operator

bpy.types.Scene.Active_Camera_Name = bpy.props.StringProperty(name="Active Camera Name", default="None")

def update_active_camera(scene, depsgraph):
    active_camera = scene.camera
    if active_camera:
        scene.Active_Camera_Name = active_camera.name
    else:
        scene.Active_Camera_Name = "None"

# Panels for Omniscient add-on
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
    bl_options = {'DEFAULT_CLOSED'}
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

class OMNI_OT_UpdateActiveCamera(Operator):
    bl_idname = "object.update_active_camera"
    bl_label = "Update Active Camera"
    
    def execute(self, context):
        update_active_camera(context.scene, context.depsgraph)
        return {'FINISHED'}

def register():
    bpy.types.Scene.Camera_Omni = bpy.props.PointerProperty(
        name="Camera_Omni",
        type=bpy.types.Object
    )
    bpy.types.Scene.Scan_Omni = bpy.props.PointerProperty(
        name="Scan_Omni",
        type=bpy.types.Object
    )
    
    # Callback to run the update function when the active camera changes
    bpy.app.handlers.depsgraph_update_post.append(update_active_camera)
    
def unregister():
    del bpy.types.Scene.Camera_Omni
    del bpy.types.Scene.Scan_Omni
    del bpy.types.Scene.Active_Camera_Name
    
    bpy.app.handlers.depsgraph_update_post.remove(update_active_camera)
