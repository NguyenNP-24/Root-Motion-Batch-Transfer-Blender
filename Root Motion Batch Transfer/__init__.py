bl_info = {
    "name": "Root Motion Batch Transfer",
    "author": "Nguyễn Phúc Nguyễn",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Root Motion",
    "description": (
        "This addon allows you to adjust the root controller position based on each action or set it in origin world space. "
        "Supports batch processing for multiple actions, making it easier to calculate character positions in game engines. "
        "Compatible with Blender 4.2, 4.3, 4.5, and 5.0+"
    ),
    "doc_url": "https://github.com/NguyenNP-24/Root-Motion-Batch-Transfer-Blender",
    "category": "Animation",
    "license": "SPDX:GPL-3.0-or-later"
}

import bpy
import sys

# Check Blender version and print info
print(f"[Root Motion Transfer] Loading on Blender {bpy.app.version_string}")

# Import modules
from . import compatibility
from . import properties
from . import operators
from . import ui_panel

def register():
    """Register addon classes and properties"""
    try:
        print("[Root Motion Transfer] Registering addon...")
        
        # Register in order: properties -> operators -> ui
        properties.register()
        operators.register()
        ui_panel.register()
        
        print(f"[Root Motion Transfer] Successfully registered on Blender {bpy.app.version_string}")
    except Exception as e:
        print(f"[Root Motion Transfer] Error during registration: {e}")
        import traceback
        traceback.print_exc()
        raise

def unregister():
    """Unregister addon classes and properties"""
    try:
        print("[Root Motion Transfer] Unregistering addon...")
        
        # Unregister in reverse order: ui -> operators -> properties
        ui_panel.unregister()
        operators.unregister()
        properties.unregister()
        
        print("[Root Motion Transfer] Successfully unregistered")
    except Exception as e:
        print(f"[Root Motion Transfer] Error during unregistration: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise here to allow Blender to continue cleanup

if __name__ == "__main__":
    register()