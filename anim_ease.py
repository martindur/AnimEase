import bpy
from bpy.props import EnumProperty
import math

bl_info = {
    "name": "Arura AnimEase",
    "author": "Martin Durhuus",
    "version": (0, 1),
    "blender": (2, 78, 0),
    "location": "3d view",
    "description": "A set of tools to make the animator's life more happy!",
    "category": "Arura",
}


"""def calculate_motionpath(context):
    bpy.ops.pose.paths_calculate(
        start_frame=context.scene.frame_start,
        end_frame=context.scene.frame_end + 1,
        bake_location='HEADS')"""

#
#   UI panels in Tools bl_region_type
#
class ToolsPanel(bpy.types.Panel):
    bl_label = "Arura AnimEase"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Arura"

    def draw(self, context):
        # self.layout.operator("spline.toggle", icon="OBJECT_DATAMODE")
        layout = self.layout
        scn = context.scene
        col = layout.column(align=True)

        col.label(text="Toggle Spline/Stepped:")
        row = col.row(align=True)
        row.operator("spline.toggle", icon="IPO_BEZIER")
        row.operator("stepped.toggle", icon="IPO_CONSTANT")

        col.label("Loopable:")
        row = col.row(align=True)
        row.operator("anim.endframe")

    def execute(self, context):
        print("fixed item", self.spline_stepped_toggle)
        return {'FINISHED'}


class ToggleSpline(bpy.types.Operator):
    """Toggles Spline solving for all existing keys"""
    bl_idname = "spline.toggle"
    bl_label = "Spline"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            return context.object.animation_data.action.fcurves is not None
        except:
            return False

    def execute(self, context):
        interpType = 'BEZIER'
        rig = context.object
        pref_edit = context.user_preferences.edit
        pref_edit.keyframe_new_interpolation_type = interpType
        current_mode = rig.mode
        if current_mode == 'POSE':
            bpy.ops.pose.select_all(action='SELECT')
        fcurves = rig.animation_data.action.fcurves
        for fcurve in fcurves:
            for key in fcurve.keyframe_points:
                key.interpolation = interpType
        return {'FINISHED'}


class ToggleStepped(bpy.types.Operator):
    """Toggles Stepped solving for all existing keys"""
    bl_idname = "stepped.toggle"
    bl_label = "Stepped"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            return context.object.animation_data.action.fcurves is not None
        except:
            return False

    def execute(self, context):
        interpType = 'CONSTANT'
        rig = context.object
        pref_edit = context.user_preferences.edit
        pref_edit.keyframe_new_interpolation_type = interpType
        current_mode = rig.mode
        if current_mode == 'POSE':
            bpy.ops.pose.select_all(action='SELECT')
        fcurves = rig.animation_data.action.fcurves
        for fcurve in fcurves:
            for key in fcurve.keyframe_points:
                key.interpolation = interpType
        return {'FINISHED'}


class UpdateEndFrame(bpy.types.Operator):
    """Turn on to duplicate any changes from first key to last key"""
    bl_idname = "anim.endframe"
    bl_label = "Update Endframe"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            return context.object.animation_data.action.fcurves is not None
        except:
            return False

    def calculate_end_keyframe(self, context, fcurve):
        first_key_y = fcurve.evaluate(0)
        end_frame = context.scene.frame_end + 1
        last_key = len(fcurve.keyframe_points) - 1
        if fcurve.keyframe_points[last_key].co.x != end_frame:
            fcurve.keyframe_points.add(1)
        end_keyframe = fcurve.keyframe_points[len(fcurve.keyframe_points) - 1]
        end_keyframe.co = end_frame, first_key_y
        left_x = math.fabs(fcurve.keyframe_points[0].handle_left.x -
                           fcurve.keyframe_points[0].co.x)
        right_x = math.fabs(fcurve.keyframe_points[0].handle_right.x -
                            fcurve.keyframe_points[0].co.x)
        end_keyframe.handle_left = (end_keyframe.co.x - left_x), \
            fcurve.keyframe_points[0].handle_left.y
        end_keyframe.handle_right = (end_keyframe.co.x + right_x), \
            fcurve.keyframe_points[0].handle_right.y
        end_keyframe.handle_left_type = "FREE"
        end_keyframe.handle_right_type = "FREE"
        return

    def execute(self, context):
        rig = context.object
        current_mode = rig.mode
        if current_mode == 'POSE':
            #bpy.ops.object.mode_set(mode='POSE')

        #current_selection = context.selected_pose_bones  # Store current selection
            bpy.ops.pose.select_all(action='SELECT')

        fcurves = rig.animation_data.action.fcurves
        for f in fcurves:
            self.calculate_end_keyframe(context, f)
            f.update()
        #calculate_motionpath(context)
            # bpy.ops.pose.select_all(action='DESELECT')
            # context.selected_pose_bones = current_selection
        return {'FINISHED'}

classes = [
    ToggleSpline,
    ToggleStepped,
    UpdateEndFrame,
    ToolsPanel
]

def register():
    # Initialize scene properties
    bpy.types.Scene.anim_mode = EnumProperty(
        items=[('block_mode', 'Block', ''),
               ('spline_mode', 'Spline', '')])
    bpy.types.Scene.solve_mode = EnumProperty(
        items=[('free_mode', 'Free', ''),
               ('auto_mode', 'Auto', '')],
        name='Solver')
    # class registration
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    # class unregistration
    for cls in classes:
        bpy.utils.unregister_class(cls)
    # Remove scene properties
    del bpy.types.Scene.anim_mode
    del bpy.types.Scene.solve_mode


if __name__ == "__main__":
    register()
