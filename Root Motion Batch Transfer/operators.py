import bpy

class RMT_OT_AddController(bpy.types.Operator):

    bl_idname = "rmt.add_controller"
    bl_label = "Add Controllers"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        rig = scene.rmt_selected_rig

        if not rig or rig.type != 'ARMATURE':
            self.report({'WARNING'}, "Please select a valid rig (Armature).")
            return {'CANCELLED'}

        if context.mode != 'POSE':
            self.report({'WARNING'}, "Please switch to Pose Mode and select bones.")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected.")
            return {'CANCELLED'}

        for bone in selected_bones:
            if not any(item.name == bone.name for item in scene.controllers):
                new_ctrl = scene.controllers.add()
                new_ctrl.name = bone.name
                scene.controllers_index = len(scene.controllers) - 1

        self.report({'INFO'}, f"Added {len(selected_bones)} controllers.")
        return {'FINISHED'}
class RMT_OT_ClearControllers(bpy.types.Operator):
    bl_idname = "rmt.clear_controllers"
    bl_label = "Clear All Controllers"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.controllers.clear()

        collection = bpy.data.collections.get("RootMotionRefs")
        if collection:
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)

        return {'FINISHED'}
class RMT_OT_RemoveController(bpy.types.Operator):
    bl_idname = "rmt.remove_controller"
    bl_label = "Remove Controller"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        scene.controllers.remove(self.index)
        return {'FINISHED'}
class RMT_OT_SelectAllControllers(bpy.types.Operator):
    bl_idname = "rmt.select_all_controllers"
    bl_label = "Select All Controllers"

    def execute(self, context):
        scene = context.scene
        rig = scene.rmt_selected_rig

        if not rig or rig.type != 'ARMATURE':
            self.report({'WARNING'}, "Please select a valid rig (Armature).")
            return {'CANCELLED'}

        controller_names = [ctrl.name for ctrl in scene.controllers]

        if not controller_names:
            self.report({'WARNING'}, "No controllers to select.")
            return {'CANCELLED'}

        bpy.context.view_layer.objects.active = rig

        if rig.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')

        bpy.ops.pose.select_all(action='DESELECT')

        for name in controller_names:
            if name in rig.pose.bones:
                rig.pose.bones[name].bone.select = True

        self.report({'INFO'}, "Selected all controllers.")
        return {'FINISHED'}
class RMT_OT_TransferRootMotion(bpy.types.Operator):
    bl_idname = "rmt.transfer_root_motion"
    bl_label = "Transfer Root Motion"
    bl_description = "Transfer selected axis motion from COG Controller to Root Controller, bake motion, and clean up."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        rig = scene.rmt_selected_rig

        if not rig:
            self.report({'WARNING'}, "No rig selected.")
            return {'CANCELLED'}

        controller_names = [ctrl.name for ctrl in scene.controllers]
        if not controller_names:
            self.report({'WARNING'}, "No controllers added.")
            return {'CANCELLED'}

        root_controller = scene.rmt_root_controller_name
        if not root_controller:
            self.report({'WARNING'}, "No Root Controller selected.")
            return {'CANCELLED'}

        print(f"Using Root Controller: {root_controller}")

        # Call processing functions
        #self.cleanup_reference_objects()
        self.create_reference(rig, controller_names, scene.axis_x, scene.axis_y, scene.axis_z)
        self.bake_reference(context)
        self.constraint_to_reference(rig)
        self.transfer_motion(context, rig)
        self.final_bake(context, rig)
        self.cleanup_reference_objects()

        self.report({'INFO'}, "Transfer Root Motion completed.")
        return {'FINISHED'}

    def create_reference(self, rig, controller_names, axis_x, axis_y, axis_z):
        scene = bpy.context.scene
        collection = bpy.data.collections.get("RootMotionRefs")

        if not collection:
            collection = bpy.data.collections.new("RootMotionRefs")
            bpy.context.scene.collection.children.link(collection)

        # Remove all previously created reference objects
        for obj in collection.objects:
            bpy.data.objects.remove(obj, do_unlink=True)

        # Create reference object
        for bone_name in controller_names:
            ref_obj_name = f"{bone_name}-ref"
            if ref_obj_name in bpy.data.objects.keys():
                self.report({'WARNING'}, f"Reference object '{ref_obj_name}' already exists! Skipping.")
                continue

            empty_ref = bpy.data.objects.new(ref_obj_name, None)
            collection.objects.link(empty_ref)

            empty_ref.parent = rig
            empty_ref.matrix_world = rig.matrix_world @ rig.pose.bones[bone_name].matrix
            empty_ref.empty_display_size = scene.empty_size if hasattr(scene, "empty_size") else 0.2
            empty_ref.empty_display_type = 'SPHERE'

            constraint = empty_ref.constraints.new('COPY_TRANSFORMS')
            constraint.target = rig
            constraint.subtarget = bone_name

        self.report({'INFO'}, "Created reference objects.")

    def bake_reference(self, context):
        scene = context.scene
        collection = bpy.data.collections.get("RootMotionRefs")

        if not collection or not collection.objects:
            self.report({'ERROR'}, "No reference objects found!")
            return

        frame_start = scene.frame_start
        frame_end = scene.frame_end

        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT')

        for obj in collection.objects:
            obj.select_set(True)

        context.view_layer.objects.active = collection.objects[0]

        bpy.ops.nla.bake(
            frame_start=frame_start,
            frame_end=frame_end,
            only_selected=True,
            visual_keying=True,
            clear_constraints=True,
            clear_parents=False,
            use_current_action=True,
            bake_types={'OBJECT'}
        )

        bpy.ops.object.select_all(action='DESELECT')

        #  Add suffix "_refAction" to the actions of reference objects
        renamed_count = 0
        for obj in collection.objects:
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                
                if not action.name.endswith("_refAction"):
                    action.name = f"{action.name}_refAction"
                    renamed_count += 1

        self.report({'INFO'}, f"Bake completed. Renamed {renamed_count} actions with '_refAction' suffix.")


    def constraint_to_reference(self, rig):
        scene = bpy.context.scene
        controller_names = [ctrl.name for ctrl in scene.controllers]

        collection = bpy.data.collections.get("RootMotionRefs")
        if not collection:
            self.report({'ERROR'}, "No reference objects found!")
            return

        ref_objs = {obj.name: obj for obj in collection.objects}

        bpy.context.view_layer.objects.active = rig

        if rig.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')

        for bone_name in controller_names:
            ref_obj_name = f"{bone_name}-ref"
            ref_obj = ref_objs.get(ref_obj_name)

            if not ref_obj:
                self.report({'WARNING'}, f"Reference object '{ref_obj_name}' not found! Skipping.")
                continue

            pbone = rig.pose.bones.get(bone_name)
            if not pbone:
                self.report({'WARNING'}, f"Pose bone '{bone_name}' not found! Skipping.")
                continue

            # Clear old constraints
            for con in pbone.constraints:
                if con.name.startswith("RMT_Constraint"):
                    pbone.constraints.remove(con)

            constraint = pbone.constraints.new(type='COPY_TRANSFORMS')
            constraint.name = "RMT_Constraint_CopyTransforms"
            constraint.target = ref_obj

    def transfer_motion(self, context, rig):
        scene = context.scene
        keep_in_world_origin = scene.keep_in_world_origin

        # Check and get collection "RootMotionRefs"
        collection = bpy.data.collections.get("RootMotionRefs")
        if not collection:
            collection = bpy.data.collections.new("RootMotionRefs")
            scene.collection.children.link(collection)

        # Create Empty-Root
        empty_root = bpy.data.objects.new("Empty-Root", None)
        collection.objects.link(empty_root)  # Link vào collection "RootMotionRefs" thay vì scene

        empty_root.location = (0, 0, 0)
        empty_root.empty_display_size = scene.empty_size if hasattr(scene, "empty_size") else 0.2
        empty_root.empty_display_type = 'SPHERE'

        root_controller_name = scene.rmt_root_controller_name
        pb_root = rig.pose.bones.get(root_controller_name)

        if pb_root is None:
            self.report({'ERROR'}, f"Root controller '{root_controller_name}' không tồn tại!")
            return {'CANCELLED'}

        pb_root.location = (0, 0, 0)

        # Clear old COPY_LOCATION constraints
        for c in pb_root.constraints:
            if c.type == 'COPY_LOCATION':
                pb_root.constraints.remove(c)

        # Create new constraint
        constraint = pb_root.constraints.new('COPY_LOCATION')
        constraint.use_x = True
        constraint.use_y = True
        constraint.use_offset = False
        constraint.target_space = 'WORLD'
        constraint.owner_space = 'WORLD'

        if keep_in_world_origin:
            constraint.use_z = False
            constraint.target = empty_root
            self.report({'INFO'}, "Keep in World Origin: XY only, Target is Empty-Root")
        else:
            constraint.use_z = False

            # Get value from Enum dropdown torso
            torso_controller_name = scene.rmt_torso_controller_enum
            torso_pbone = rig.pose.bones.get(torso_controller_name)

            if torso_pbone is None:
                self.report({'ERROR'}, f"Torso controller '{torso_controller_name}' không tồn tại!")
                return {'CANCELLED'}

            constraint.target = rig
            constraint.subtarget = torso_controller_name

            self.report({'INFO'}, f"Follow: XY only, Target is Torso Controller '{torso_controller_name}'")

        return {'FINISHED'}


    def cleanup_reference_objects(self):
        # The suffix name of the actions to be cleaned up
        ref_action_suffix = "_refAction"

        # Delete "RootMotionRefs" collection and its objects
        collection = bpy.data.collections.get("RootMotionRefs")

        if collection:
            # Delete all objects in the collection
            for obj in list(collection.objects):
                if obj.animation_data and obj.animation_data.action:
                    action = obj.animation_data.action
                    action_name = action.name  # Save name BEFORE deletion

                    if action_name.endswith(ref_action_suffix):
                        # Unlink action before removing it
                        obj.animation_data.action = None
                        bpy.data.actions.remove(action, do_unlink=True)
                        print(f"Removed action: {action_name}")

                # Remove the object itself
                bpy.data.objects.remove(obj, do_unlink=True)

            # Delete the collection
            bpy.data.collections.remove(collection)
            self.report({'INFO'}, "Cleaned up reference objects and collection.")
        else:
            self.report({'WARNING'}, "No reference collection found to clean.")

        # Clean up any remaining actions with the suffix "_refAction"
        removed_action_names = []  # Store names here

        # First, collect actions to remove
        actions_to_remove = [a for a in bpy.data.actions if a.name.endswith(ref_action_suffix)]

        for action in actions_to_remove:
            action_name = action.name  # Save BEFORE deletion

            # Unlink from any object that still uses this action
            for obj in bpy.data.objects:
                if obj.animation_data and obj.animation_data.action == action:
                    obj.animation_data.action = None

            bpy.data.actions.remove(action, do_unlink=True)
            print(f"Removed leftover action: {action_name}")
            removed_action_names.append(action_name)  # Save name for reporting

        # Report results
        if removed_action_names:
            self.report({'INFO'}, f"Removed actions: {', '.join(removed_action_names)}")
        else:
            self.report({'INFO'}, "No extra reference actions found to remove.")


    def final_bake(self, context, rig):
        scene = context.scene
        frame_start = scene.frame_start
        frame_end = scene.frame_end

        root_controller_name = scene.rmt_root_controller_name
        controller_names = [ctrl.name for ctrl in scene.controllers]

        if not root_controller_name:
            self.report({'ERROR'}, "No Root Controller selected for baking!")
            return {'CANCELLED'}

        if rig.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')

        bpy.ops.pose.select_all(action='DESELECT')

        # Bake Root Controller
        pb_root = rig.pose.bones.get(root_controller_name)

        if pb_root:
            pb_root.bone.select = True
            rig.data.bones.active = pb_root.bone

            bpy.ops.nla.bake(
                frame_start=frame_start,
                frame_end=frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                clear_parents=True,
                use_current_action=True,
                bake_types={'POSE'}
            )
            self.report({'INFO'}, f"Baked Root Controller: {root_controller_name}")
        else:
            self.report({'WARNING'}, f"Root Controller '{root_controller_name}' not found!")

        # Bake Other Controllers
        bpy.ops.pose.select_all(action='DESELECT')

        other_controllers = [name for name in controller_names if name != root_controller_name]

        for bone_name in other_controllers:
            pbone = rig.pose.bones.get(bone_name)
            if not pbone:
                self.report({'WARNING'}, f"Controller '{bone_name}' not found! Skipping.")
                continue

            pbone.bone.select = True

        if other_controllers:
            rig.data.bones.active = rig.data.bones[other_controllers[0]]

            bpy.ops.nla.bake(
                frame_start=frame_start,
                frame_end=frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                clear_parents=False,
                use_current_action=True,
                bake_types={'POSE'}
            )
            self.report({'INFO'}, f"Baked Controllers: {other_controllers}")
        else:
            self.report({'WARNING'}, "No other controllers to bake.")

        return {'FINISHED'}  
class RMT_OT_BatchTransferRootMotion(bpy.types.Operator):
    bl_idname = "rmt.batch_transfer_root_motion"
    bl_label = "Batch Transfer Root Motion"
    bl_description = "Transfer Root Motion for all actions in the rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        rig = scene.rmt_selected_rig

        if not rig:
            self.report({'WARNING'}, "No rig selected.")
            return {'CANCELLED'}

        original_action = rig.animation_data.action if rig.animation_data else None

        actions = [act for act in bpy.data.actions if act.users > 0]
        total = len(actions)

        if total == 0:
            self.report({'WARNING'}, "No actions found!")
            return {'CANCELLED'}

        for idx, action in enumerate(actions, 1):
            # Assign action to rig
            if rig.animation_data is None:
                rig.animation_data_create()

            rig.animation_data.action = action
            self.report({'INFO'}, f"Processing ({idx}/{total}): {action.name}")

            # Call the Transfer Root Motion process for each action
            result = self.transfer_for_action(context, rig)

            if result == {'CANCELLED'}:
                self.report({'ERROR'}, f"Failed on action: {action.name}")
                continue

        # Restore the original action
        if rig.animation_data:
            rig.animation_data.action = original_action

        self.report({'INFO'}, "Batch Transfer Root Motion completed.")
        return {'FINISHED'}

    def transfer_for_action(self, context, rig):
        # Copy the entire logic inside RMT_OT_TransferRootMotion.execute()
        return bpy.ops.rmt.transfer_root_motion('INVOKE_DEFAULT')

classes = [
    RMT_OT_AddController,
    RMT_OT_ClearControllers,
    RMT_OT_RemoveController,
    RMT_OT_SelectAllControllers,
    RMT_OT_TransferRootMotion,
    RMT_OT_BatchTransferRootMotion,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
