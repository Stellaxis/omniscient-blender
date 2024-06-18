import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator
from .omniHandler import loadOmni


class ImportOmniOperator(Operator, ImportHelper):
    """Import a .omni file"""
    bl_idname = "load.omni"
    bl_label = "Import .omni" # Import button text

    # ImportHelper mixin class uses this
    filename_ext = ".omni"

    filter_glob: StringProperty(
        default="*.omni",
        options={'HIDDEN'},
    )

    def execute(self, context):
        # Call the loadOmni function with the filepath specified in the operator
        loadOmni(self, self.filepath)
        return {'FINISHED'}


# To add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportOmniOperator.bl_idname, text="Omniscient (.omni)")


def register():
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)