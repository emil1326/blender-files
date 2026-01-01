"""
Emil's Mesh Toolkit - Modular Blender Add-on
Package initializer
"""

bl_info = {
    "name": "Emil's Mesh Toolkit",
    "author": "Emil",
    "version": (2, 5, 4),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Emil",
    "description": "Collection of tools for shapekeys, weights, rigging, and selection",
    "category": "Mesh",
}

# This makes the folder a Python package
# The main entry point is toolkit_main.py

from . import toolkit_main

def register():
    toolkit_main.register()

def unregister():
    toolkit_main.unregister()

if __name__ == "__main__":
    register()
