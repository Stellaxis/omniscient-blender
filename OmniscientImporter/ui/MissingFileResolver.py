import bpy
import os
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
from ..loadProcessedOmni import loadProcessedOmni

class SelectFileOperator(bpy.types.Operator, ImportHelper):
    """Operator to select a file"""
    bl_idname = "wm.select_file"
    bl_label = "Select File"

    filepath: StringProperty(name="File Path", description="Filepath used for setting the path", subtype='FILE_PATH')

    file_type: StringProperty() # Store the type of file being selected
    CameraPath: StringProperty()
    VideoPath: StringProperty()
    GeoPath: StringProperty()

    def execute(self, context):
        # Set the appropriate file path based on the file type
        if self.file_type == "CAMERA":
            self.CameraPath = self.filepath
        elif self.file_type == "VIDEO":
            self.VideoPath = self.filepath
        elif self.file_type == "GEO":
            self.GeoPath = self.filepath

        # Have to open again because of this issue : https://blender.stackexchange.com/questions/262627/prevent-properties-dialog-from-closing-during-file-path-selection
        bpy.ops.wm.missing_file_resolver('INVOKE_DEFAULT',
            isVideoFileMissing=not os.path.exists(self.VideoPath),
            isCameraFileMissing=not os.path.exists(self.CameraPath),
            isGeoFileMissing=not os.path.exists(self.GeoPath),
            CameraPath=self.CameraPath,
            VideoPath=self.VideoPath,
            GeoPath=self.GeoPath
        )
        return {'FINISHED'}

class MissingFileResolver(bpy.types.Operator):
    """Open the Missing File box"""
    bl_label = "Missing File"
    bl_idname = "wm.missing_file_resolver"

    isVideoFileMissing: BoolProperty(default=True)
    isCameraFileMissing: BoolProperty(default=True)
    isGeoFileMissing: BoolProperty(default=True)
    CameraPath: StringProperty(description="camera's absolute file path")
    VideoPath: StringProperty(description="video's absolute file path")
    GeoPath: StringProperty(description="gemoetry's absolute file path")

    def draw(self, context):
        lay = self.layout

        lay.label(text="Some files can't be located, locate them:")

        row = lay.row(align=True)
        if self.isCameraFileMissing:
            row.prop(self, "CameraPath", text="Camera", icon='ERROR')
            op = row.operator("wm.select_file", text="", icon='FILE_FOLDER')
            op.file_type = "CAMERA"
            op.CameraPath = self.CameraPath
            op.VideoPath = self.VideoPath
            op.GeoPath = self.GeoPath
        else:
            row.prop(self, "CameraPath", text="Camera", icon='CHECKBOX_HLT')

        row = lay.row(align=True)
        if self.isVideoFileMissing:
            row.prop(self, "VideoPath", text="Video", icon='ERROR',)
            op = row.operator("wm.select_file", text="", icon='FILE_FOLDER')
            op.file_type = "VIDEO"
            op.CameraPath = self.CameraPath
            op.VideoPath = self.VideoPath
            op.GeoPath = self.GeoPath
        else:
            row.prop(self, "VideoPath", text="Video", icon='CHECKBOX_HLT')

        row = lay.row(align=True) 
        if self.isGeoFileMissing:
            row.prop(self, "GeoPath", text="Geometry", icon='ERROR')
            op = row.operator("wm.select_file", text="", icon='FILE_FOLDER')
            op.file_type = "GEO"
            op.CameraPath = self.CameraPath
            op.VideoPath = self.VideoPath
            op.GeoPath = self.GeoPath
        else:
            row.prop(self, "GeoPath", text="Geometry", icon='CHECKBOX_HLT')

    def execute(self, context):
        loadProcessedOmni(self, self.VideoPath, self.CameraPath, self.GeoPath)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
