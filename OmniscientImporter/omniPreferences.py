import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, EnumProperty

class OMNI_Preferences(AddonPreferences):
    bl_idname = "OmniscientImporter"
    
    use_shadow_catcher: BoolProperty(
        name="Use Shadow Catcher",
        description="Automatically set imported mesh as shadow catcher",
        default=True
    )

    use_holdout: BoolProperty(
        name="Use Holdout",
        description="Automatically set imported mesh as holdout",
        default=True
    )

    renderer: EnumProperty(
        name="Default Renderer",
        description="Choose the renderer to set at import",
        items=[
            ('CYCLES', "Cycles (recommended)", "Use Cycles renderer"),
            ('BLENDER_EEVEE', "Eevee", "Use Eevee renderer"),
            ('WORKBENCH', "Workbench", "Use Workbench renderer")
        ],
        default='CYCLES'
    )

    enable_motion_blur: BoolProperty(
        name="Enable Motion Blur",
        description="Activate motion blur for the renderer",
        default=True
    )

    enable_dof: BoolProperty(
        name="Enable Depth of Field",
        description="Activate depth of field for the renderer",
        default=True
    )

    def draw(self, context):
        layout = self.layout

        # Import Options Panel
        box = layout.box()
        box.label(text="Import Options", icon='IMPORT')
        box.prop(self, "use_shadow_catcher")
        box.prop(self, "use_holdout")

        # Renderer Option
        layout.separator()
        layout.label(text="Renderer Settings", icon='RENDER_STILL')
        layout.prop(self, "renderer")

        # Motion Blur and Depth of Field Options
        layout.prop(self, "enable_motion_blur")
        layout.prop(self, "enable_dof")
