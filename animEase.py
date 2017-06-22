import bpy
from bpy.props import EnumProperty
import math

bl_info = {
    "name": "Dur's AnimEase",
    "author": "Martin Durhuus",
    "version": (0, 1),
    "blender": (2, 78, 0),
    "location": "3d view",
    "description": "A set of tools that enables the user to easily manipulate f-curves, by moving/rotating/scaling objects(bones) in the 3d view. Avoid keyframe hell..",
    "warning": "For now, manually enable preferences > Editing > Keyframing: Only Insert Needed'",
    "category": "Animation",
}


def get_animation_mode(context):
    anim_mode = context.scene.anim_mode
    pref_edit = context.user_preferences.edit
    if anim_mode == 'block_mode':
        pref_edit.use_keyframe_insert_needed = False
    elif anim_mode == 'spline_mode':
        pref_edit.use_keyframe_insert_needed = True
    return (anim_mode)


def get_solve_mode(context):
    solve_mode = context.scene.solve_mode
    return (solve_mode)


def calculate_motionpath(context):
    bpy.ops.pose.paths_calculate(
        start_frame=context.scene.frame_start,
        end_frame=context.scene.frame_end + 1,
        bake_location='HEADS')


def get_handle_vector(point, left_handle=True):
    if left_handle:
        handle_vector = point.co - point.handle_left
    else:
        handle_vector = point.co - point.handle_right
    return (handle_vector)


def get_handle_pos(point, handle_vector):
    handle_pos = point.co + handle_vector
    return (handle_pos)


def set_handle_type(point_1, handle_type, point_2=None):
    point_1.handle_left_type = handle_type
    point_1.handle_right_type = handle_type
    if point_2 is not None:
        point_2.handle_left_type = handle_type
        point_2.handle_right_type = handle_type
        return (point_1, point_2)
    return (point_1)

def calc_bezier(p1, p2, p_ref):
    p = []
    #px = (p_ref.x * 2 - (p1.x + p2.x) / 2) * 0.75
    py = (p_ref.y * 2 - (p1.y + p2.y) / 2) * 0.75
    px = p_ref.x
    p.append(px)
    p.append(py)
    return p


#
#   UI panels in Tools bl_region_type
#
class ToolsPanel(bpy.types.Panel):
    bl_label = "Dur's AnimEase"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "AnimEase"

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
        col.label("Animation Pass:")
        row = col.row(align=True)
        layout.prop(scn, 'anim_mode', expand=True)
        layout.prop(scn, 'solve_mode', icon="RNDCURVE")

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
        return context.object.mode == 'POSE'

    def execute(self, context):
        interpType = 'BEZIER'
        rig = context.object
        pref_edit = context.user_preferences.edit
        pref_edit.keyframe_new_interpolation_type = interpType
        if rig.type == 'ARMATURE':
            current_mode = rig.mode
            if current_mode != 'POSE':
                bpy.ops.object.mode_set(mode='POSE')
            fcurves = rig.animation_data.action.fcurves
            for fcurve in fcurves:
                for key in fcurve.keyframe_points:
                    key.interpolation = interpType
        else:
            print('Select an armature')
        return {'FINISHED'}


class ToggleStepped(bpy.types.Operator):
    """Toggles Stepped solving for all existing keys"""
    bl_idname = "stepped.toggle"
    bl_label = "Stepped"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'POSE'

    def execute(self, context):
        interpType = 'CONSTANT'
        rig = context.object
        pref_edit = context.user_preferences.edit
        pref_edit.keyframe_new_interpolation_type = interpType
        if rig.type == 'ARMATURE':
            current_mode = rig.mode
            if current_mode != 'POSE':
                bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='SELECT')
            fcurves = rig.animation_data.action.fcurves
            for fcurve in fcurves:
                for key in fcurve.keyframe_points:
                    key.interpolation = interpType
        else:
            print('Select an armature')
        return {'FINISHED'}


class UpdateEndFrame(bpy.types.Operator):
    """Turn on to duplicate any changes from first key to last key"""
    bl_idname = "anim.endframe"
    bl_label = "Update Endframe"
    bl_options = {'REGISTER', 'UNDO'}

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
        if rig.type == 'ARMATURE':
            if current_mode != 'POSE':
                bpy.ops.object.mode_set(mode='POSE')

            current_selection = context.selected_pose_bones  # Store current selection
            bpy.ops.pose.select_all(action='SELECT')

            fcurves = rig.animation_data.action.fcurves
            for f in fcurves:
                self.calculate_end_keyframe(context, f)
                f.update()
            calculate_motionpath(context)
            # bpy.ops.pose.select_all(action='DESELECT')
            # context.selected_pose_bones = current_selection
        else:
            print('Select an armature')
        return {'FINISHED'}


class SplineMode(bpy.types.Operator):
    bl_idname = "anim.splinemode"
    bl_label = "SplineMode"
    bl_options = {'REGISTER', 'UNDO'}

    keyframes = []
    has_existing_key = False

    def __init__(self):
        print("Start")

    def __del__(self):
        print("End")

    def execute(self, context):
        solve_mode = get_solve_mode(context)
        rig = context.object
        cur_frame = context.scene.frame_current
        fcurves = rig.animation_data.action.fcurves
        for f in fcurves:
            if len(f.keyframe_points) >= 2:
                for i in range(len(f.keyframe_points) - 1):
                    if f.keyframe_points[i].co.x == cur_frame:
                        ref_point = f.keyframe_points[i]
                        if ref_point != f.keyframe_points[0]:
                            left_point = f.keyframe_points[i - 1]
                            has_left_point = True
                        else:
                            has_left_point = False
                        if ref_point != f.keyframe_points[len(f.keyframe_points) - 1]:
                            right_point = f.keyframe_points[i + 1]
                            has_right_point = True
                        else:
                            has_right_point = False
                        if has_left_point and has_right_point:
                            new_point = calc_bezier(left_point.co, right_point.co, ref_point.co)
                            left_point.handle_right = new_point
                            right_point.handle_left = new_point
                            if solve_mode == "auto_mode":
                                # Calculate the opposing handle to keep a 'proper' bezier curve.
                                left_point_vector = get_handle_vector(left_point, False)
                                right_point_vector = get_handle_vector(right_point, True)
                                left_point, right_point = set_handle_type(left_point,
                                                                          "FREE", right_point)
                                left_point.handle_left = get_handle_pos(left_point,
                                                                        left_point_vector)
                                right_point.handle_right = get_handle_pos(right_point,
                                                                          right_point_vector)
                        else:
                            self.report({'WARNING'}, "Cannot create a curve with one keyframe")
                        f.keyframe_points.remove(ref_point)
            else:
                f.keyframe_points.remove(f.keyframe_points[0])
            f.update()
        calculate_motionpath(context)
        return {'FINISHED'}


    def modal(self, context, event):
        anim_mode = get_animation_mode(context)
        cur_frame = context.scene.frame_current
        rig = context.object
        fcurves = rig.animation_data.action.fcurves
        if event.type == self.translate_key:
            if bpy.ops.transform.translate.poll():
                for f in fcurves:
                    for i in range(len(f.keyframe_points) - 1):
                        self.keyframes.append(f.keyframe_points[i].co.x)
                self.has_existing_key = any(key == cur_frame for key in self.keyframes)
                print("Translating..")
                bpy.ops.transform.translate('INVOKE_DEFAULT')
        elif event.type == self.rotate_key:
            if bpy.ops.transform.rotate.poll():
                print("Rotating..")
                bpy.ops.transform.rotate('INVOKE_DEFAULT')
        elif event.type == self.scale_key:
            if bpy.ops.transform.resize.poll():
                print("Scaling..")
                bpy.ops.transform.resize('INVOKE_DEFAULT')
        elif event.type == 'LEFTMOUSE':
            if anim_mode == 'spline_mode' and not self.has_existing_key:
                self.execute(context)
                return {'FINISHED'}
            else:
                return {'FINISHED'}

        elif event.type == 'ESC' or event.type == 'RIGHTMOUSE':
            print("Cancelled..")
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        kms = [bpy.context.window_manager.keyconfigs.active.keymaps['3D View'],
               bpy.context.window_manager.keyconfigs.active.keymaps['Object Mode']]
        kmis = []

        for km in kms:
            for kmi in km.keymap_items:
                if kmi.idname == "transform.translate" and \
                                kmi.map_type == 'KEYBOARD' and not \
                        kmi.properties.texture_space:
                    kmis.append(kmi)
                    self.translate_key = kmi.type
                elif kmi.idname == "transform.rotate" and \
                                kmi.map_type == 'KEYBOARD':
                    kmis.append(kmi)
                    self.rotate_key = kmi.type
                elif kmi.idname == "transform.resize" and \
                                kmi.map_type == 'KEYBOARD' and not \
                        kmi.properties.texture_space:
                    kmis.append(kmi)
                    self.scale_key = kmi.type
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


keymaps = []


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
    bpy.utils.register_class(ToggleSpline)
    bpy.utils.register_class(ToggleStepped)
    bpy.utils.register_class(UpdateEndFrame)
    bpy.utils.register_class(SplineMode)
    bpy.utils.register_class(ToolsPanel)
    # Keymap registration
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Pose', space_type='EMPTY')
    kmi = km.keymap_items.new(SplineMode.bl_idname, 'G', 'PRESS')
    keymaps.append(km)
    km = wm.keyconfigs.addon.keymaps.new(name='Pose', space_type='EMPTY')
    kmi = km.keymap_items.new(SplineMode.bl_idname, 'R', 'PRESS')
    keymaps.append(km)
    km = wm.keyconfigs.addon.keymaps.new(name='Pose', space_type='EMPTY')
    kmi = km.keymap_items.new(SplineMode.bl_idname, 'S', 'PRESS')
    keymaps.append(km)


def unregister():
    # Keymap unregistration(Not functioning at the moment)
    wm = bpy.context.window_manager
    for km in keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    # clear list
    keymaps.clear()
    # class unregistration
    bpy.utils.unregister_class(ToggleSpline)
    bpy.utils.unregister_class(ToggleStepped)
    bpy.utils.unregister_class(UpdateEndFrame)
    bpy.utils.unregister_class(SplineMode)
    bpy.utils.unregister_class(ToolsPanel)
    # Remove scene properties
    del bpy.types.Scene.anim_mode
    del bpy.types.Scene.solve_mode


if __name__ == "__main__":
    register()
