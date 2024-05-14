import bpy
from bpy.types import Panel, Operator

class OMNI_PT_ImportPanel(Panel):
    bl_label = "Omniscient"
    bl_idname = "OMNI_PT_import"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Omniscient'

    def draw(self, context):
        layout = self.layout

        # Add import button
        layout.operator("load.omni", text="Import .omni")


class OMNI_PT_ObjectsPanel(Panel):
    bl_label = "Imported Objects"
    bl_idname = "OMNI_PT_objects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Omniscient'
    bl_parent_id = "OMNI_PT_import"
    bl_options = {'DEFAULT_CLOSED'}  # This makes the panel collapsed by default

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.prop(context.scene, "Camera_Omni", text="Camera")
        
        row = layout.row()
        row.prop(context.scene, "Scan_Omni", text="Scan")


class OMNI_OT_ScanOmni(Operator):
    bl_idname = "scan.omni"
    bl_label = "Scan Omni"
    bl_description = "Perform a scan using the Omni"

    def execute(self, context):
        # Add the scan functionality here
        self.report({'INFO'}, "Scan Omni executed")
        return {'FINISHED'}

# Ensure you add the new property to the scene
def register():
    bpy.types.Scene.Camera_Omni = bpy.props.PointerProperty(
        name="Camera_Omni",
        type=bpy.types.Object
    )
    bpy.types.Scene.Scan_Omni = bpy.props.PointerProperty(
        name="Scan_Omni",
        type=bpy.types.Object
    )

def unregister():
    del bpy.types.Scene.Camera_Omni
    del bpy.types.Scene.Scan_Omni