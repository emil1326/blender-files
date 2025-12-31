"""
Emil's Mesh Toolkit - Common Utilities
Shared base classes and utility functions to avoid code duplication
"""

import bpy


class ToolkitUtils:
    """Static utility methods used across all modules"""
    
    @staticmethod
    def parse_vertex_indices(s):
        """Parse comma-separated vertex indices into a set"""
        if not s:
            return set()
        parts = [p.strip() for p in s.split(",") if p.strip()]
        try:
            return set(int(p) for p in parts)
        except Exception:
            return set()
    
    @staticmethod
    def join_vertex_indices(indices):
        """Convert set/list of indices to comma-separated string"""
        return ",".join(str(int(i)) for i in sorted(indices))
    
    @staticmethod
    def get_active_mesh_obj(context):
        """Get active mesh object or None"""
        obj = context.view_layer.objects.active
        if obj and obj.type == "MESH":
            return obj
        return None
    
    @staticmethod
    def set_mode(obj, mode):
        """Safely set object mode"""
        if bpy.context.view_layer.objects.active != obj:
            bpy.context.view_layer.objects.active = obj
        if obj.mode != mode.upper():
            bpy.ops.object.mode_set(mode=mode.upper())
    
    @staticmethod
    def select_vertex_in_edit_mode(obj, vertex_index):
        """Select a vertex in edit mode"""
        ToolkitUtils.set_mode(obj, "OBJECT")
        if vertex_index < len(obj.data.vertices):
            obj.data.vertices[vertex_index].select = True
        ToolkitUtils.set_mode(obj, "EDIT")


class ToolkitOperator(bpy.types.Operator):
    """Base operator class with common helper methods"""
    
    def report_info(self, message):
        """Report info message"""
        self.report({"INFO"}, message)
        return {"FINISHED"}
    
    def report_warning(self, message):
        """Report warning message"""
        self.report({"WARNING"}, message)
        return {"CANCELLED"}
    
    def report_error(self, message):
        """Report error message"""
        self.report({"ERROR"}, message)
        return {"CANCELLED"}


class ToolkitPanel(bpy.types.Panel):
    """Base panel class with common settings"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Emil"


def register():
    """Register common utilities (no classes to register)"""
    pass


def unregister():
    """Unregister common utilities (no classes to unregister)"""
    pass
