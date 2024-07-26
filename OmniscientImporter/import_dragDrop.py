import bpy

if bpy.app.version >= (4, 2, 0):
    from bpy.types import FileHandler

    class IMPORT_FH_omni(FileHandler):
        bl_idname = "IMPORT_FH_omni"
        bl_label = "Omni File Handler"
        bl_import_operator = "import_scene.omni"
        bl_file_extensions = ".omni"
        exclude_from_auto_register = True

        @classmethod
        def poll_drop(cls, context):
            return (context.area and context.area.type == 'VIEW_3D')

    def register():
        bpy.utils.register_class(IMPORT_FH_omni)

    def unregister():
        bpy.utils.unregister_class(IMPORT_FH_omni)
