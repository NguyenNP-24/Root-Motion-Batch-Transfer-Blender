bl_info = {
    "name": "Root Motion Batch Transfer",
    "author": "Nguyễn Phúc Nguyễn",
    "version": (1, 0, 0),
    "blender": (4, 3, 2),
    "location": "View3D > Sidebar > RootMotion",
    "description": (
    "This addon allows you to adjust the root controller position based on each action "
    "or set it in world space. Supports batch processing for multiple actions, "
    "making it easier to calculate character positions in game engines."),
    "doc_url": "https://github.com/NguyenNP-24/Root-Motion-Batch-Transfer-Blender",
    "category": "RootMotion",
    "license": "SPDX:GPL-3.0-or-later"
}

import bpy
from . import operators
from . import ui_panel
from . import properties

def register():
    properties.register()
    operators.register()
    ui_panel.register()

def unregister():
    ui_panel.unregister()
    operators.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()
