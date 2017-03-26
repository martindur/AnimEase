import bpy
import math

bl_info = {
    "name" : "Dur's AnimEase",
    "category" : "Animation",
}

class ToolsPanel(bpy.types.Panel):
    bl_label = "Dur's AnimEase"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "AnimEase"

    def draw(self, context):
        #self.layout.operator("spline.toggle", icon="OBJECT_DATAMODE")
        layout = self.layout

        col = layout.column(align=True)

        col.label(text="Toggle Spline/Constant:")
        row = col.row(align=True)
        row.operator("spline.toggle", icon="SMOOTHCURVE")
        row.operator("constant.toggle", icon="NOCURVE")

        col.label("Loopable:")
        row = col.row(align=True)
        row.operator("anim.endframe")
        col.label("Animation Mode:")
        row = col.row(align=True)
        row.operator("anim.splinemode")
    
    def execute(self, context):
        print("fixed item", self.spline_constant_toggle)
        return {'FINISHED'}

class ToggleSpline(bpy.types.Operator):
    """Toggles Spline solving for all existing keys"""
    bl_idname = "spline.toggle"
    bl_label = "Spline"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        interpType = 'BEZIER'
        rig = context.object
        if rig.type == 'ARMATURE':
            current_mode = rig.mode
            if current_mode != 'POSE':
                bpy.ops.object.mode_set(mode='POSE')
            fcurves = rig.animation_data.action.fcurves
            #initial_key_status = fcurves[0].keyframe_points[0].interpolation
            for fcurve in fcurves:
                for key in fcurve.keyframe_points:
                    key.interpolation = interpType
        else:
            print('Select an armature')
        return {'FINISHED'}

class ToggleConstant(bpy.types.Operator):
    """Toggles Constant solving for all existing keys"""
    bl_idname = "constant.toggle"
    bl_label = "Constant"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        interpType = 'CONSTANT'
        rig = context.object
        if rig.type == 'ARMATURE':
            current_mode = rig.mode
            if current_mode != 'POSE':
                bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='SELECT')
            fcurves = rig.animation_data.action.fcurves
            #initial_key_status = fcurves[0].keyframe_points[0].interpolation
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

    def execute(self, context):
        rig = context.object
        current_mode = rig.mode
        if rig.type =='ARMATURE':
            if current_mode != 'POSE':
                bpy.ops.object.mode_set(mode='POSE')
            
            current_selection = context.selected_pose_bones #Store current selection
            bpy.ops.pose.select_all(action='SELECT')
            
            fcurves = rig.animation_data.action.fcurves
            for f in fcurves:
                first_key_y = f.evaluate(0)
                end_frame = context.scene.frame_end + 1
                if f.keyframe_points[len(f.keyframe_points)-1].co.x != end_frame:
                    f.keyframe_points.add(1)
                end_keyframe = f.keyframe_points[len(f.keyframe_points)-1]
                end_keyframe.co = end_frame, first_key_y
                left_x = math.fabs(f.keyframe_points[0].handle_left.x - f.keyframe_points[0].co.x)
                right_x = math.fabs(f.keyframe_points[0].handle_right.x - f.keyframe_points[0].co.x)
                end_keyframe.handle_left = (end_keyframe.co.x - left_x), f.keyframe_points[0].handle_left.y
                end_keyframe.handle_right = (end_keyframe.co.x + right_x), f.keyframe_points[0].handle_right.y
                end_keyframe.handle_left_type="FREE"
                end_keyframe.handle_right_type="FREE"
                f.update()

            #bpy.ops.pose.select_all(action='DESELECT')
            #context.selected_pose_bones = current_selection
        else:
            print('Select an armature')
        return {'FINISHED'}

class NewSplineMode(bpy.types.Operator):
    bl_idname = "anim.splinemode"
    bl_label = "SplineMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rig = context.object
        cur_frame = context.scene.frame_current
        fcurves = rig.animation_data.action.fcurves
        for f in fcurves:
            ref_point = f.keyframe_points[1]
            left_point = f.keyframe_points[0]
            right_point = f.keyframe_points[2]
            left_point.handle_right = ref_point.co
            right_point.handle_left = ref_point.co
            f.update()
        for f in fcurves:
            f.keyframe_points.remove(ref_point)
            #else:
            #print("SplineMode requires key poses to work as intended")
        return {'FINISHED'}

class SplineMode(bpy.types.Operator):
    bl_idname = "anim.splinemode"
    bl_label = "SplineMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rig = context.object
        cur_frame = context.scene.frame_current
        fcurves = rig.animation_data.action.fcurves
        for f in fcurves:
            if len(f.keyframe_points) >= 2:
                for i in range(len(f.keyframe_points)-1):
                    if f.keyframe_points[i].co.x == cur_frame:
                        ref_point = f.keyframe_points[i]
                        if ref_point != f.keyframe_points[0]:
                            left_point = f.keyframe_points[i-1]
                            has_left_point = True
                        else:
                            del_single_point = f.keyframe_points
                            has_left_point = False
                        if ref_point != f.keyframe_points[len(f.keyframe_points)-1]:
                            right_point = f.keyframe_points[i+1]
                            has_right_point = True
                        else:
                            has_right_point = False
            if has_left_point == True and has_right_point == True:
                left_point.handle_right = ref_point.co
                right_point.handle_left = ref_point.co
            elif has_left_point == True and has_right_point == False:
                left_point.handle_right = ref_point.co
            elif has_left_point == False and has_right_point == True:
                right_point.handle_left = ref_point.co
            f.update()
        for f in fcurves:
            if len(f.keyframe_points) > 1:
                for point in f.keyframe_points:
                    if point.co.x == cur_frame:
                        f.keyframe_points.remove(point)
            f.update()
            #else:
            #print("SplineMode requires key poses to work as intended")
        return {'FINISHED'}
            

def register():
    bpy.utils.register_class(ToggleSpline)
    bpy.utils.register_class(ToggleConstant)
    bpy.utils.register_class(UpdateEndFrame)
    bpy.utils.register_class(SplineMode)
    bpy.utils.register_class(ToolsPanel)

def unregister():
    bpy.utils.unregister_class(ToggleSpline)
    bpy.utils.unregister_class(ToggleConstant)
    bpy.utils.unregister_class(UpdateEndFrame)
    bpy.utils.unregister_class(SplineMode)
    bpy.utils.unregister_class(ToolsPanel)

if __name__ == "__main__":
    register()
    