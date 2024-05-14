import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty

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

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "use_shadow_catcher")
        layout.prop(self, "use_holdout")
