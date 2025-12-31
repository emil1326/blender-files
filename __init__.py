"""
Emil's Mesh Toolkit - Modular Blender Add-on
Package initializer
"""

# This makes the folder a Python package
# The main entry point is toolkit_main.py

from . import toolkit_main

bl_info = toolkit_main.bl_info

def register():
    toolkit_main.register()

def unregister():
    toolkit_main.unregister()

if __name__ == "__main__":
    register()
