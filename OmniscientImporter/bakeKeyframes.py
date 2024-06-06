import bpy
from bpy.types import Operator

class OMNI_OT_BakeCameraKeyframes(Operator):
    bl_idname = "object.bake_camera_keyframes"
    bl_label = "Bake Camera Keyframes"

    frame_start: bpy.props.IntProperty()
    frame_end: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        camera = scene.camera

        # Ensure the camera is selected and active
        bpy.ops.object.select_all(action='DESELECT')
        camera.select_set(True)
        scene.view_layers[0].objects.active = camera

        # Bake the camera keyframes
        bpy.ops.nla.bake(
            frame_start=self.frame_start,
            frame_end=self.frame_end,
            only_selected=True,
            visual_keying=True,
            clear_constraints=True,
            clear_parents=True,
            use_current_action=True,
            bake_types={'OBJECT'}
        )
        return {'FINISHED'}
