import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator
from .omniHandler import loadOmni

class ImportOmniOperator(Operator, ImportHelper):
    """Import a .omni file"""
    bl_idname = "import_scene.omni"
    bl_label = "Import .omni"
    bl_options = {'UNDO'}
    exclude_from_auto_register = True

    filename_ext = ".omni"

    filter_glob: StringProperty(
        default="*.omni",
        options={'HIDDEN'},
    )

    filepath: StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})

    def execute(self, context):
        # Call the loadOmni function with the filepath specified in the operator
        loadOmni(self, self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.filepath:
            return self.execute(context)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_func_import(self, context):
    self.layout.operator(ImportOmniOperator.bl_idname, text="Omniscient (.omni)")

def register():
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.utils.register_class(ImportOmniOperator)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(ImportOmniOperator)
