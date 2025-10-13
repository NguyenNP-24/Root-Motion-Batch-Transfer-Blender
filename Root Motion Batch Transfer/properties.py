import bpy

class RMT_ControllerItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()

class RMT_ActionItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Action Name")
    action: bpy.props.PointerProperty(type=bpy.types.Action)
    is_selected: bpy.props.BoolProperty(name="Select", default=False)

def get_torso_items(self, context):
    """Get list of controllers for enum property"""
    scene = context.scene
    if not hasattr(scene, 'controllers'):
        return []
    items = [(ctrl.name, ctrl.name, "") for ctrl in scene.controllers]
    # Always return at least one item to prevent enum errors
    return items if items else [('NONE', 'No Controllers', '')]

def update_rig_selection(self, context):
    """Callback when rig selection changes"""
    if context.area:
        context.area.tag_redraw()

def register():
    # Register classes first
    bpy.utils.register_class(RMT_ControllerItem)
    bpy.utils.register_class(RMT_ActionItem)
    
    # Then register properties
    bpy.types.Scene.rmt_selected_rig = bpy.props.PointerProperty(
        name="Rig", 
        type=bpy.types.Object,
        update=update_rig_selection,
        description="Select the armature rig to process"
    )
    bpy.types.Scene.controllers = bpy.props.CollectionProperty(
        type=RMT_ControllerItem,
        description="List of controller bones"
    )
    bpy.types.Scene.controllers_index = bpy.props.IntProperty(
        name="Controller Index",
        default=0
    )
    bpy.types.Scene.axis_x = bpy.props.BoolProperty(
        name="X", 
        default=True,
        description="Transfer X axis motion"
    )
    bpy.types.Scene.axis_y = bpy.props.BoolProperty(
        name="Y", 
        default=True,
        description="Transfer Y axis motion"
    )
    bpy.types.Scene.axis_z = bpy.props.BoolProperty(
        name="Z", 
        default=False,
        description="Transfer Z axis motion"
    )
    bpy.types.Scene.rmt_torso_controller_enum = bpy.props.EnumProperty(
        name="Torso Controller",
        description="Select target controller (usually torso/COG)",
        items=get_torso_items
    )
    bpy.types.Scene.rmt_root_controller_name = bpy.props.StringProperty(
        name="Root Controller",
        description="Search for root controller bone (usually root/master bone)",
        default=""
    )
    bpy.types.Scene.keep_in_world_origin = bpy.props.BoolProperty(
        name="Keep in World Origin",
        description="Keep root controller at world origin (XY only)",
        default=False
    )
    bpy.types.Scene.rmt_action_items = bpy.props.CollectionProperty(
        type=RMT_ActionItem,
        description="Temporary list for action selection dialog"
    )
    bpy.types.Scene.rmt_batch_actions = bpy.props.CollectionProperty(
        type=RMT_ActionItem,
        description="Selected actions for batch processing"
    )


def unregister():
    # Delete properties first (in reverse order of registration)
    props_to_delete = [
        'rmt_batch_actions',
        'rmt_action_items',
        'keep_in_world_origin',
        'rmt_root_controller_name',
        'rmt_torso_controller_enum',
        'axis_z',
        'axis_y',
        'axis_x',
        'controllers_index',
        'controllers',
        'rmt_selected_rig'
    ]
    
    for prop_name in props_to_delete:
        try:
            if hasattr(bpy.types.Scene, prop_name):
                delattr(bpy.types.Scene, prop_name)
        except Exception as e:
            print(f"Warning: Could not delete property {prop_name}: {e}")
    
    # Then unregister classes (in reverse order)
    try:
        bpy.utils.unregister_class(RMT_ActionItem)
    except Exception as e:
        print(f"Warning: Could not unregister RMT_ActionItem: {e}")
    
    try:
        bpy.utils.unregister_class(RMT_ControllerItem)
    except Exception as e:
        print(f"Warning: Could not unregister RMT_ControllerItem: {e}")