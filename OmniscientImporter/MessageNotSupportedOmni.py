import bpy


class MessageNotSupportedOmni(bpy.types.Operator):
    bl_idname = "message.not_supported_omni"
    bl_label = ""
    minimum_addon_version: bpy.props.StringProperty()
    current_version_str: bpy.props.StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text=str(f"Update needed: version {self.minimum_addon_version} or higher"))
        layout.label(text=str(f"Current version: {self.current_version_str}"))
        layout.operator("wm.url_open", text="Get the latest version", icon='URL').url = "https://github.com/Stellaxis/omniscient-blender/releases/latest"
