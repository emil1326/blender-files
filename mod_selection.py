"""
Emil's Mesh Toolkit - Selection Module
Tools for advanced object selection
"""

import bpy
from .toolkit_common import ToolkitUtils, ToolkitOperator, ToolkitPanel


# ==================== OPERATORS ====================

class EMESH_OT_SelectDeep(ToolkitOperator):
    """Select sibling objects that share the same bone parent"""
    bl_idname = "object.emesh_select_deep"
    bl_label = "Select Deep (Siblings)"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        active = context.active_object
        
        if not active:
            return self.report_warning("No active object")
        
        # Determine parent
        if active.parent_type == "BONE" and active.parent and active.parent_bone:
            parent_obj = active.parent
            parent_bone_name = active.parent_bone
            
            # Find all objects with the same bone parent
            count = 0
            for obj in bpy.data.objects:
                if (obj.parent == parent_obj and 
                    obj.parent_type == "BONE" and 
                    obj.parent_bone == parent_bone_name):
                    obj.select_set(True)
                    count += 1
            
            return self.report_info(f"Selected {count} siblings with bone parent '{parent_bone_name}'")
        
        elif active.parent and active.parent_type == "OBJECT":
            parent = active.parent
            
            # Find all objects with the same object parent
            count = 0
            for obj in bpy.data.objects:
                if obj.parent == parent and obj.parent_type == "OBJECT":
                    obj.select_set(True)
                    count += 1
            
            return self.report_info(f"Selected {count} siblings with object parent '{parent.name}'")
        
        else:
            return self.report_warning("Active object has no parent or unsupported parent type")


# ==================== UI ====================

class EMESH_PT_Selection(ToolkitPanel):
    """Selection tools panel"""
    bl_label = "Selection Tools"
    bl_idname = "EMESH_PT_Selection"
    bl_parent_id = "EMESH_PT_MainPanel"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        box = layout.box()
        box.label(text="Select Siblings:", icon="RESTRICT_SELECT_OFF")
        
        if obj:
            if obj.parent_type == "BONE" and obj.parent and obj.parent_bone:
                box.label(text=f"Parent: {obj.parent.name}", icon="ARMATURE_DATA")
                box.label(text=f"Bone: {obj.parent_bone}", icon="BONE_DATA")
            elif obj.parent and obj.parent_type == "OBJECT":
                box.label(text=f"Parent: {obj.parent.name}", icon="OBJECT_DATA")
            else:
                box.label(text="No parent", icon="INFO")
        else:
            box.label(text="No active object", icon="ERROR")
        
        box.operator("object.emesh_select_deep", icon="OUTLINER_OB_GROUP_INSTANCE")


# ==================== REGISTRATION ====================

classes = (
    EMESH_OT_SelectDeep,
    EMESH_PT_Selection,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
