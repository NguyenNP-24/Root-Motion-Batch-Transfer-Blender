import bpy
from . import compatibility

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

        selected_bones = compatibility.get_pose_bones_selected(context)
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected.")
            return {'CANCELLED'}

        added = 0
        for bone in selected_bones:
            if not any(item.name == bone.name for item in scene.controllers):
                new_ctrl = scene.controllers.add()
                new_ctrl.name = bone.name
                scene.controllers_index = len(scene.controllers) - 1
                added += 1

        self.report({'INFO'}, f"Added {added} controllers.")
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
            compatibility.safe_delete_collection(collection)

        self.report({'INFO'}, "Cleared all controllers.")
        return {'FINISHED'}

class RMT_OT_RemoveController(bpy.types.Operator):
    bl_idname = "rmt.remove_controller"
    bl_label = "Remove Controller"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        if 0 <= self.index < len(scene.controllers):
            scene.controllers.remove(self.index)
            self.report({'INFO'}, "Removed controller.")
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
            compatibility.safe_mode_set('POSE')

        bpy.ops.pose.select_all(action='DESELECT')

        selected_count = 0
        for name in controller_names:
            if name in rig.pose.edit_bones:
                rig.pose.bones[name].select = True
                selected_count += 1

        self.report({'INFO'}, f"Selected {selected_count} controllers.")
        return {'FINISHED'}

class RMT_OT_TransferRootMotion(bpy.types.Operator):
    bl_idname = "rmt.transfer_root_motion"
    bl_label = "Transfer Root Motion"
    bl_description = "Transfer selected axis motion from COG Controller to Root Controller, bake motion, and clean up."
    bl_options = {'REGISTER', 'UNDO'}

    action_name: bpy.props.StringProperty(name="Action Name", default="")

    def execute(self, context):
        scene = context.scene
        rig = scene.rmt_selected_rig

        if not rig:
            self.report({'WARNING'}, "No rig selected.")
            return {'CANCELLED'}

        # If running from batch then change action to active
        if self.action_name:
            action = bpy.data.actions.get(self.action_name)
            if action:
                anim_data = compatibility.ensure_animation_data(rig)
                anim_data.action = action
                print(f"[TransferRootMotion] Set action to: {action.name}")
            else:
                self.report({'ERROR'}, f"Action '{self.action_name}' not found.")
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
        try:
            self.create_reference(rig, controller_names, scene.axis_x, scene.axis_y, scene.axis_z)
            self.bake_reference(context)
            self.constraint_to_reference(rig)
            self.transfer_motion(context, rig)
            self.final_bake(context, rig)
            self.cleanup_reference_objects()
            
            self.report({'INFO'}, "Transfer Root Motion completed.")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error during transfer: {str(e)}")
            print(f"[Error] Transfer failed: {e}")
            return {'CANCELLED'}

    def create_reference(self, rig, controller_names, axis_x, axis_y, axis_z):
        scene = bpy.context.scene
        collection = bpy.data.collections.get("RootMotionRefs")

        if not collection:
            collection = bpy.data.collections.new("RootMotionRefs")
            bpy.context.scene.collection.children.link(collection)

        # Remove all previously created reference objects
        for obj in list(collection.objects):
            compatibility.safe_delete_object(obj)

        # Create reference objects
        created = 0
        for bone_name in controller_names:
            if bone_name not in rig.pose.bones:
                print(f"Warning: Bone '{bone_name}' not found in rig")
                continue
                
            ref_obj_name = f"{bone_name}-ref"
            if ref_obj_name in bpy.data.objects.keys():
                print(f"Warning: Reference object '{ref_obj_name}' already exists! Skipping.")
                continue

            empty_ref = bpy.data.objects.new(ref_obj_name, None)
            collection.objects.link(empty_ref)

            empty_ref.parent = rig
            empty_ref.matrix_world = rig.matrix_world @ rig.pose.bones[bone_name].matrix
            empty_ref.empty_display_size = 0.2
            empty_ref.empty_display_type = 'SPHERE'

            constraint = empty_ref.constraints.new('COPY_TRANSFORMS')
            constraint.target = rig
            constraint.subtarget = bone_name
            created += 1

        print(f"[Reference] Created {created} reference objects.")

    def bake_reference(self, context):
        scene = context.scene
        collection = bpy.data.collections.get("RootMotionRefs")

        if not collection or not collection.objects:
            raise RuntimeError("No reference objects found!")

        frame_start = scene.frame_start
        frame_end = scene.frame_end

        compatibility.safe_mode_set('OBJECT')

        bpy.ops.object.select_all(action='DESELECT')

        for obj in collection.objects:
            obj.select_set(True)

        context.view_layer.objects.active = collection.objects[0]

        # Use compatibility layer for baking
        success = compatibility.bake_animation_safe(
            context,
            frame_start=frame_start,
            frame_end=frame_end,
            bake_types={'OBJECT'},
            clear_parents=False
        )

        if not success:
            raise RuntimeError("Failed to bake reference objects")

        bpy.ops.object.select_all(action='DESELECT')

        # Add suffix "_refAction" to the actions of reference objects
        renamed_count = 0
        for obj in collection.objects:
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                
                if not action.name.endswith("_refAction"):
                    action.name = f"{action.name}_refAction"
                    renamed_count += 1

        print(f"[Bake] Baked and renamed {renamed_count} reference actions.")

    def constraint_to_reference(self, rig):
        scene = bpy.context.scene
        controller_names = [ctrl.name for ctrl in scene.controllers]

        collection = bpy.data.collections.get("RootMotionRefs")
        if not collection:
            raise RuntimeError("No reference objects found!")

        ref_objs = {obj.name: obj for obj in collection.objects}

        bpy.context.view_layer.objects.active = rig

        if rig.mode != 'POSE':
            compatibility.safe_mode_set('POSE')

        constrained = 0
        for bone_name in controller_names:
            ref_obj_name = f"{bone_name}-ref"
            ref_obj = ref_objs.get(ref_obj_name)

            if not ref_obj:
                print(f"Warning: Reference object '{ref_obj_name}' not found! Skipping.")
                continue

            pbone = rig.pose.bones.get(bone_name)
            if not pbone:
                print(f"Warning: Pose bone '{bone_name}' not found! Skipping.")
                continue

            # Clear old RMT constraints
            for con in list(pbone.constraints):
                if con.name.startswith("RMT_Constraint"):
                    compatibility.safe_constraint_remove(pbone, con)

            constraint = pbone.constraints.new(type='COPY_TRANSFORMS')
            constraint.name = "RMT_Constraint_CopyTransforms"
            constraint.target = ref_obj
            constrained += 1

        print(f"[Constraint] Applied constraints to {constrained} controllers.")

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
        collection.objects.link(empty_root)

        empty_root.location = (0, 0, 0)
        empty_root.empty_display_size = 0.2
        empty_root.empty_display_type = 'SPHERE'

        root_controller_name = scene.rmt_root_controller_name
        pb_root = rig.pose.bones.get(root_controller_name)

        if pb_root is None:
            raise RuntimeError(f"Root controller '{root_controller_name}' not found!")

        pb_root.location = (0, 0, 0)

        # Clear old COPY_LOCATION constraints
        for c in list(pb_root.constraints):
            if c.type == 'COPY_LOCATION':
                compatibility.safe_constraint_remove(pb_root, c)

        # Create new constraint
        constraint = pb_root.constraints.new('COPY_LOCATION')
        
        # Set axis usage based on scene properties
        if keep_in_world_origin:
            constraint.use_x = True
            constraint.use_y = True
            constraint.use_z = False
            constraint.target = empty_root
            print("[Transfer] Mode: Keep in World Origin (XY only)")
        else:
            # Apply user's axis selection
            constraint.use_x = scene.axis_x
            constraint.use_y = scene.axis_y  
            constraint.use_z = scene.axis_z

            # Get value from Enum dropdown torso
            torso_controller_name = scene.rmt_torso_controller_enum
            
            if torso_controller_name == 'NONE' or not torso_controller_name:
                raise RuntimeError("No torso controller selected!")
                
            torso_pbone = rig.pose.bones.get(torso_controller_name)

            if torso_pbone is None:
                raise RuntimeError(f"Torso controller '{torso_controller_name}' not found!")

            constraint.target = rig
            constraint.subtarget = torso_controller_name

            enabled_axes = []
            if scene.axis_x: enabled_axes.append("X")
            if scene.axis_y: enabled_axes.append("Y")
            if scene.axis_z: enabled_axes.append("Z")
            
            print(f"[Transfer] Mode: Follow {'+'.join(enabled_axes)} axes from '{torso_controller_name}'")

        constraint.use_offset = False
        constraint.target_space = 'WORLD'
        constraint.owner_space = 'WORLD'

    def cleanup_reference_objects(self):
        ref_action_suffix = "_refAction"

        # Delete "RootMotionRefs" collection and its objects
        collection = bpy.data.collections.get("RootMotionRefs")

        if collection:
            # Delete all objects in the collection
            for obj in list(collection.objects):
                if obj.animation_data and obj.animation_data.action:
                    action = obj.animation_data.action
                    action_name = action.name

                    if action_name.endswith(ref_action_suffix):
                        obj.animation_data.action = None
                        try:
                            bpy.data.actions.remove(action, do_unlink=True)
                            print(f"Removed action: {action_name}")
                        except Exception as e:
                            print(f"Warning: Could not remove action {action_name}: {e}")

                compatibility.safe_delete_object(obj)

            # Delete the collection
            try:
                bpy.data.collections.remove(collection)
                print("[Cleanup] Removed RootMotionRefs collection")
            except Exception as e:
                print(f"Warning: Could not remove collection: {e}")
        else:
            print("[Cleanup] No reference collection found")

        # Clean up any remaining actions with the suffix "_refAction"
        removed_action_names = []
        actions_to_remove = [a for a in bpy.data.actions if a.name.endswith(ref_action_suffix)]

        for action in actions_to_remove:
            action_name = action.name

            # Unlink from any object that still uses this action
            for obj in bpy.data.objects:
                if obj.animation_data and obj.animation_data.action == action:
                    obj.animation_data.action = None

            try:
                bpy.data.actions.remove(action, do_unlink=True)
                print(f"Removed leftover action: {action_name}")
                removed_action_names.append(action_name)
            except Exception as e:
                print(f"Warning: Could not remove action {action_name}: {e}")

        if removed_action_names:
            print(f"[Cleanup] Removed {len(removed_action_names)} reference actions")

    def final_bake(self, context, rig):
        scene = context.scene
        frame_start = scene.frame_start
        frame_end = scene.frame_end

        root_controller_name = scene.rmt_root_controller_name
        controller_names = [ctrl.name for ctrl in scene.controllers]

        if not root_controller_name:
            raise RuntimeError("No Root Controller selected for baking!")

        if rig.mode != 'POSE':
            compatibility.safe_mode_set('POSE')

        bpy.ops.pose.select_all(action='DESELECT')

        # Bake Root Controller
        pb_root = rig.pose.bones.get(root_controller_name)

        if pb_root:
            pb_root.select = True
            rig.data.bones.active = pb_root.bone

            success = compatibility.bake_animation_safe(
                context,
                frame_start=frame_start,
                frame_end=frame_end,
                bake_types={'POSE'},
                clear_parents=True
            )
            
            if success:
                print(f"[Bake] Baked Root Controller: {root_controller_name}")
            else:
                print(f"[Warning] Failed to bake Root Controller: {root_controller_name}")
        else:
            print(f"[Warning] Root Controller '{root_controller_name}' not found!")

        # Bake Other Controllers
        bpy.ops.pose.select_all(action='DESELECT')

        other_controllers = [name for name in controller_names if name != root_controller_name]

        for bone_name in other_controllers:
            pbone = rig.pose.bones.get(bone_name)
            if not pbone:
                print(f"Warning: Controller '{bone_name}' not found! Skipping.")
                continue

            pbone.select = True

        if other_controllers:
            rig.data.bones.active = rig.data.bones[other_controllers[0]]

            success = compatibility.bake_animation_safe(
                context,
                frame_start=frame_start,
                frame_end=frame_end,
                bake_types={'POSE'},
                clear_parents=False
            )
            
            if success:
                print(f"[Bake] Baked {len(other_controllers)} other controllers")
            else:
                print("[Warning] Failed to bake other controllers")
        else:
            print("[Bake] No other controllers to bake")

class RMT_OT_BatchTransferRootMotionContinue(bpy.types.Operator):
    bl_idname = "rmt.batch_transfer_root_motion_continue"
    bl_label = "Batch Transfer Root Motion"
    bl_description = "Apply Transfer Root Motion for all selected Actions"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        selected_actions = scene.rmt_batch_actions

        if not selected_actions:
            self.report({'WARNING'}, "No actions selected for batch processing.")
            return {'CANCELLED'}

        # Save current action to restore
        rig = scene.rmt_selected_rig
        current_action = rig.animation_data.action if rig.animation_data else None

        success_count = 0
        fail_count = 0

        for item in selected_actions:
            action_name = item.name
            print(f"\n[Batch] Processing Action: {action_name}")
            
            try:
                result = bpy.ops.rmt.transfer_root_motion('INVOKE_DEFAULT', action_name=action_name)
                if result == {'FINISHED'}:
                    success_count += 1
                else:
                    fail_count += 1
                    print(f"[Batch] Failed to process action: {action_name}")
            except Exception as e:
                fail_count += 1
                print(f"[Batch] Error processing action {action_name}: {e}")

        # Restore the original action (if any)
        if current_action:
            anim_data = compatibility.ensure_animation_data(rig)
            anim_data.action = current_action
            print("[Batch] Restored original action.")

        self.report({'INFO'}, f"Batch completed: {success_count} success, {fail_count} failed")
        return {'FINISHED'}

classes = [
    RMT_OT_AddController,
    RMT_OT_ClearControllers,
    RMT_OT_RemoveController,
    RMT_OT_SelectAllControllers,
    RMT_OT_TransferRootMotion,
    RMT_OT_BatchTransferRootMotionContinue,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"Warning: Could not unregister {cls.__name__}: {e}")