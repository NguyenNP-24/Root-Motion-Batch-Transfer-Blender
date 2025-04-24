import bpy

class RMT_ControllerItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
class RMT_ActionItem(bpy.types.PropertyGroup):
    action: bpy.props.PointerProperty(type=bpy.types.Action)
    is_selected: bpy.props.BoolProperty(name="Select", default=False)

def get_torso_items(self, context):
    scene = context.scene
    return [(ctrl.name, ctrl.name, "") for ctrl in scene.controllers]

def register():
    bpy.utils.register_class(RMT_ControllerItem)
    # bpy.types.Scene.rmt_selected_actions = bpy.props.CollectionProperty(type=bpy.types.Action)
    bpy.types.Scene.rmt_selected_rig = bpy.props.PointerProperty(
        name="Rig", type=bpy.types.Object,
        update=lambda self, ctx: ctx.area.tag_redraw()
    )
    bpy.types.Scene.controllers = bpy.props.CollectionProperty(type=RMT_ControllerItem)
    bpy.types.Scene.controllers_index = bpy.props.IntProperty()
    bpy.types.Scene.axis_x = bpy.props.BoolProperty(name="X", default=True)
    bpy.types.Scene.axis_y = bpy.props.BoolProperty(name="Y", default=True)
    bpy.types.Scene.axis_z = bpy.props.BoolProperty(name="Z", default=False)
    bpy.types.Scene.rmt_torso_controller_enum = bpy.props.EnumProperty(
        name="Torso Controller",
        description="Select Target from added controllers",
        items=get_torso_items
    )
    bpy.types.Scene.rmt_root_controller_name = bpy.props.StringProperty(
        name="Root Controller",
        description="Search for root controller bone"
    )
    bpy.types.Scene.keep_in_world_origin = bpy.props.BoolProperty(
        name="Keep in World Origin",
        description="Keep root controller at world origin",
        default=False
    )
    bpy.utils.register_class(RMT_ActionItem)
    bpy.types.Scene.rmt_action_items = bpy.props.CollectionProperty(type=RMT_ActionItem)
    bpy.types.Scene.rmt_batch_actions = bpy.props.CollectionProperty(type=RMT_ActionItem)


def unregister():
    del bpy.types.Scene.rmt_selected_rig
    del bpy.types.Scene.controllers
    del bpy.types.Scene.controllers_index
    del bpy.types.Scene.axis_x
    del bpy.types.Scene.axis_y
    del bpy.types.Scene.axis_z
    del bpy.types.Scene.rmt_torso_controller_enum
    del bpy.types.Scene.rmt_root_controller_name
    del bpy.types.Scene.keep_in_world_origin
    # del bpy.types.Scene.rmt_selected_actions
    del bpy.types.Scene.rmt_batch_actions
    del bpy.types.Scene.rmt_action_items
    bpy.utils.unregister_class(RMT_ActionItem)
    bpy.utils.unregister_class(RMT_ControllerItem)
