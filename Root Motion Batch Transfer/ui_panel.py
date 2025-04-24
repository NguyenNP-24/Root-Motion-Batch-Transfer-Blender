import bpy

class RMT_ActionItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Action Name")
    action: bpy.props.PointerProperty(type=bpy.types.Action)
    is_selected: bpy.props.BoolProperty(name="Select", default=False)

# Main Panel
class RMT_PT_RootMotionPanel(bpy.types.Panel):
    bl_label = "Root Motion Transfer"
    bl_idname = "RMT_PT_root_motion_transfer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Root Motion"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column(align=True)
        col.prop(scene, "rmt_selected_rig", text="Rig Object")

        row = layout.row(align=True)
        row.operator("rmt.add_controller", text="Add Controllers", icon='PLUS')

        row = layout.row(align=True)
        row.operator("rmt.clear_controllers", text="Clear All", icon='TRASH')
        row.operator("rmt.select_all_controllers", text="Select All", icon='RESTRICT_SELECT_OFF')

        box = layout.box()
        for index, item in enumerate(scene.controllers):
            row = box.row(align=True)
            row.label(text=item.name, icon='BONE_DATA')
            op = row.operator("rmt.remove_controller", text="", icon='X')
            op.index = index

        col = layout.column(align=True)
        col.label(text="Target Controller (usually torso - COG):")
        col.prop(scene, "rmt_torso_controller_enum", text="")

        col.separator()
        col.label(text="Root Controller (master):")
        # Check if rmt_selected_rig is None
        if scene.rmt_selected_rig:
            col.prop_search(scene, "rmt_root_controller_name", scene.rmt_selected_rig.pose, "bones", text="", icon="OUTLINER_OB_EMPTY")
        else:
            # If no rig is selected, display message
            col.label(text="No rig selected!", icon='ERROR')

        row = layout.row(align=True)
        row.label(text="Keep in World Origin")
        row.prop(scene, "keep_in_world_origin", text="")

        # Only show axis selection when keep_in_world_origin is FALSE
        if not scene.keep_in_world_origin:
            row = layout.row(align=True)
            row.label(text="Transfer Axes:")
            subrow = row.row(align=True)
            subrow.scale_x = 0.5
            subrow.prop(scene, "axis_x", text="X")
            subrow.prop(scene, "axis_y", text="Y") 
            subrow.prop(scene, "axis_z", text="Z")

        col = layout.column(align=True)
        col.scale_y = 1
        col.operator("rmt.transfer_root_motion", text="Transfer Root Motion", icon='PLAY')

        layout.operator("rmt.batch_transfer_root_motion", icon="ACTION")

# Popup Panel for Batch transfer
class RMT_OT_SelectActionsPopup(bpy.types.Operator):
    bl_idname = "rmt.batch_transfer_root_motion"
    bl_label = "Batch Transfer"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Batch execute the following actions (list of actions with keys belonging to Rig)"

    def invoke(self, context, event):
        rig = context.scene.rmt_selected_rig
        scene = context.scene
        scene.rmt_action_items.clear()

        if not rig or rig.type != 'ARMATURE':
            self.report({'WARNING'}, "No rig selected.")
            return {'CANCELLED'}

        for act in bpy.data.actions:
            if act.users > 0 and action_contains_rig_animation(act, rig):
                item = scene.rmt_action_items.add()
                item.name = act.name
                item.action = act
                item.is_selected = False

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.label(text="Select actions to process:", icon='ACTION')

        for item in scene.rmt_action_items:
            layout.prop(item, "is_selected", text=item.name)

    def execute(self, context):
        selected = [item.action for item in context.scene.rmt_action_items if item.is_selected]
        
        # Check if no action is selected
        if not selected:
            self.report({'WARNING'}, "No actions selected for batch processing.")
            return {'CANCELLED'}
        
        # Clear previous selection
        context.scene.rmt_batch_actions.clear()  
        # Save selected actions to rmt_batch_actions
        for action in selected:
            item = context.scene.rmt_batch_actions.add()
            item.name = action.name
            item.action = action
        
        # Call the batch transfer operator
        bpy.ops.rmt.batch_transfer_root_motion_continue()
    
        self.report({'INFO'}, f"Transfered {len(selected)} actions: {', '.join([act.name for act in selected])}")     
        return {'FINISHED'}

# --- Helper function, only call in RMT_PT_SelectActionsPanel ---
def action_contains_rig_animation(action, rig):
    """
    Checks if the given action contains animation data for the specified rig's pose bones. We dont wanna bake not relate action.
    Returns: True if the action contains animation for the rig, False otherwise.
    """
    if not rig or rig.type != 'ARMATURE' or not action:
        return False

    # Check if action have Fcurve belong to select Rig's bone
    for fcurve in action.fcurves:
        if fcurve.data_path.startswith(f'pose.bones["') and fcurve.data_path.split('["')[1].split('"]')[0] in rig.data.bones:
            return True
    return False

def register():
    bpy.utils.register_class(RMT_ActionItem)
    bpy.utils.register_class(RMT_OT_SelectActionsPopup)
    bpy.utils.register_class(RMT_PT_RootMotionPanel)
    bpy.types.Scene.rmt_batch_actions = bpy.props.CollectionProperty(type=RMT_ActionItem)
    bpy.types.Scene.rmt_action_items = bpy.props.CollectionProperty(type=RMT_ActionItem)

def unregister():
    del bpy.types.Scene.rmt_batch_actions
    del bpy.types.Scene.rmt_action_items
    bpy.utils.unregister_class(RMT_PT_RootMotionPanel)
    bpy.utils.unregister_class(RMT_OT_SelectActionsPopup)
    bpy.utils.unregister_class(RMT_ActionItem)
