import bpy
from bpy.props import StringProperty, BoolProperty
from ..omniHandler import loadProcessedOmni

class missingFileResolver(bpy.types.Operator):
    """Open the Missing File box"""
    bl_label = "Missing File"
    bl_idname = "wm.missing_file_resolver"
    
    isVideoFileMissing: BoolProperty(default=True)
    isCameraFileMissing: BoolProperty(default=True)
    isGeoFileMissing: BoolProperty(default=True)
    CameraPath: StringProperty(default="\wrong\path")
    VideoPath: StringProperty(default="\wrong\path")
    GeoPath: StringProperty(default="\wrong\path")

    def draw(self, context):
        row = self.layout

        row.label(text="Some files can't be located, locate them:")
        row.prop(self, "CameraPath", text="Camera")
        row.prop(self, "VideoPath", text="Video")
        row.prop(self, "GeoPath", text="Geometry")

    def execute(self, context):
        loadProcessedOmni(self, self.VideoPath, self.CameraPath, self.GeoPath)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
