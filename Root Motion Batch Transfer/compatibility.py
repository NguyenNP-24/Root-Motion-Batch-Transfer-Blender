"""
Compatibility layer for different Blender versions
"""
import bpy

def get_blender_version():
    """Get Blender version as tuple (major, minor, patch)"""
    return bpy.app.version

def is_blender_version_at_least(major, minor=0, patch=0):
    """Check if current Blender version is at least the specified version"""
    current = get_blender_version()
    target = (major, minor, patch)
    return current >= target

def safe_mode_set(mode='OBJECT'):
    """Safely set object mode, handling context differences"""
    try:
        if bpy.context.object and bpy.context.object.mode != mode:
            bpy.ops.object.mode_set(mode=mode)
    except RuntimeError:
        # Context may not allow mode change
        pass

def safe_delete_object(obj):
    """Safely delete object across Blender versions"""
    try:
        bpy.data.objects.remove(obj, do_unlink=True)
    except Exception as e:
        print(f"Warning: Could not delete object {obj.name}: {e}")

def safe_delete_collection(collection):
    """Safely delete collection across Blender versions"""
    try:
        # Remove all objects first
        for obj in list(collection.objects):
            safe_delete_object(obj)
        bpy.data.collections.remove(collection)
    except Exception as e:
        print(f"Warning: Could not delete collection {collection.name}: {e}")

def get_nla_bake_params():
    """
    Get NLA bake parameters compatible with current Blender version
    Returns dict of parameters for bpy.ops.nla.bake()
    """
    version = get_blender_version()
    
    # Base parameters that work across versions
    params = {
        'only_selected': True,
        'visual_keying': True,
        'clear_constraints': True,
        'use_current_action': True,
    }
    
    # Blender 4.0+ uses different parameter names
    if is_blender_version_at_least(4, 0):
        params['clear_parents'] = True
    
    return params

def bake_animation_safe(context, frame_start, frame_end, bake_types={'POSE'}, clear_parents=True):
    """
    Safely bake animation with version-compatible parameters
    """
    params = get_nla_bake_params()
    params['frame_start'] = frame_start
    params['frame_end'] = frame_end
    params['bake_types'] = bake_types
    
    if 'clear_parents' in params:
        params['clear_parents'] = clear_parents
    
    try:
        bpy.ops.nla.bake(**params)
        return True
    except Exception as e:
        print(f"Bake error: {e}")
        return False

def get_pose_bones_selected(context):
    """Get selected pose bones in a version-safe way"""
    if context.mode == 'POSE' and context.selected_pose_bones:
        return context.selected_pose_bones
    return []

def safe_constraint_remove(pbone, constraint):
    """Safely remove constraint from pose bone"""
    try:
        pbone.constraints.remove(constraint)
    except Exception as e:
        print(f"Warning: Could not remove constraint: {e}")

def ensure_animation_data(obj):
    """Ensure object has animation data"""
    if not obj.animation_data:
        obj.animation_data_create()
    return obj.animation_data