bl_info = {
    "name": "Root Motion Transfer",
    "author": "Nguyễn Phúc Nguyễn",
    "version": (1, 0, 0),
    "blender": (4, 3, 2),
    "location": "View3D > Sidebar > Root Motion",
    "description": "This addon allows you to adjust the root controller position based on each action or fix it in world space. Supports batch processing for multiple actions, making it easier to calculate character positions in game engines.",
    "category": "Animation",
    "license": "Free to use for personal and commercial projects"
}

from . import Root_motion_transfer

def register():
    Root_motion_transfer.register()

def unregister():
    Root_motion_transfer.unregister()
