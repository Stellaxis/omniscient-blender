import bpy

class missingFileResolver(bpy.types.Operator):
    """Open the Missing File box"""
    bl_label = "Missing File"
    bl_idname = "wm.missing_file_resolver"
    
    CameraPath: bpy.props.StringProperty(default="\wrong\path")
    VideoPath: bpy.props.StringProperty(default="\wrong\path")
    GeoPath: bpy.props.StringProperty(default="\wrong\path")

    def draw(self, context):
        row = self.layout

        row.label(text="Some files can't be located, locate them:")
        row.prop(self, "CameraPath", text="Camera")
        row.prop(self, "VideoPath", text="Video")
        row.prop(self, "GeoPath", text="Geometry")

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
