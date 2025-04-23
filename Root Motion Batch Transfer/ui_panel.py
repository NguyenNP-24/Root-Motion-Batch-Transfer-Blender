import bpy

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

        col = layout.column(align=True)
        col.scale_y = 1
        col.operator("rmt.transfer_root_motion", text="Transfer Root Motion", icon='PLAY')

        layout.operator("rmt.batch_transfer_root_motion", icon="ACTION")


def register():
    bpy.utils.register_class(RMT_PT_RootMotionPanel)

def unregister():
    bpy.utils.unregister_class(RMT_PT_RootMotionPanel)
