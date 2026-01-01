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
    
    mode: bpy.props.EnumProperty(
        name="Mode",
        items=[
            ("SIBLINGS", "Siblings", "Select objects with same parent"),
            ("CHILDREN", "Children", "Select all children recursively"),
            ("PARENTS", "Parents", "Select all parents up the chain"),
            ("HIERARCHY", "Full Hierarchy", "Select entire family tree"),
        ],
        default="SIBLINGS"
    )
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        active = context.active_object
        
        if not active:
            return self.report_warning("No active object")
        
        # Filter to only objects in current view layer
        view_layer_objs = set(obj.name for obj in context.view_layer.objects)
        selected_count = 0
        
        if self.mode == "SIBLINGS":
            # Select siblings with same parent
            if active.parent_type == "BONE" and active.parent and active.parent_bone:
                parent_obj = active.parent
                parent_bone_name = active.parent_bone
                
                for obj in bpy.data.objects:
                    if (obj.name in view_layer_objs and
                        obj.parent == parent_obj and 
                        obj.parent_type == "BONE" and 
                        obj.parent_bone == parent_bone_name):
                        obj.select_set(True)
                        selected_count += 1
                
                return self.report_info(f"Selected {selected_count} siblings with bone parent '{parent_bone_name}'")
            
            elif active.parent and active.parent_type == "OBJECT":
                parent = active.parent
                
                for obj in bpy.data.objects:
                    if obj.name in view_layer_objs and obj.parent == parent and obj.parent_type == "OBJECT":
                        obj.select_set(True)
                        selected_count += 1
                
                return self.report_info(f"Selected {selected_count} siblings with object parent '{parent.name}'")
        
        elif self.mode == "CHILDREN":
            # Recursively select all children
            def select_children(obj):
                count = 0
                for child in bpy.data.objects:
                    if child.name in view_layer_objs and child.parent == obj:
                        child.select_set(True)
                        count += 1
                        count += select_children(child)
                return count
            
            selected_count = select_children(active)
            return self.report_info(f"Selected {selected_count} children")
        
        elif self.mode == "PARENTS":
            # Select all parents up the chain
            current = active.parent
            while current:
                if current.name in view_layer_objs:
                    current.select_set(True)
                    selected_count += 1
                current = current.parent
            
            return self.report_info(f"Selected {selected_count} parents up the chain")
        
        elif self.mode == "HIERARCHY":
            # Select entire family tree (parents + children + siblings)
            def select_all_family(obj, visited=None):
                if visited is None:
                    visited = set()
                if obj.name in visited:
                    return 0
                visited.add(obj.name)
                count = 0
                
                # Select parents
                current = obj.parent
                while current and current.name not in visited:
                    current.select_set(True)
                    visited.add(current.name)
                    count += 1
                    current = current.parent
                
                # Select children
                for child in bpy.data.objects:
                    if child.parent == obj and child.name not in visited:
                        child.select_set(True)
                        visited.add(child.name)
                        count += 1
                        count += select_all_family(child, visited)
                
                # Select siblings
                if obj.parent:
                    for sibling in bpy.data.objects:
                        if (sibling.parent == obj.parent and 
                            sibling.name not in visited):
                            sibling.select_set(True)
                            visited.add(sibling.name)
                            count += 1
                
                return count
            
            selected_count = select_all_family(active)
            return self.report_info(f"Selected {selected_count} family members")
        
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
        
        # ===== PARENT INFO SECTION =====
        info_box = layout.box()
        info_box.label(text="Parent Information", icon="INFO")
        
        if obj:
            if obj.parent_type == "BONE" and obj.parent and obj.parent_bone:
                info_box.label(text=f"Armature: {obj.parent.name}", icon="ARMATURE_DATA")
                info_box.label(text=f"Bone: {obj.parent_bone}", icon="BONE_DATA")
            elif obj.parent and obj.parent_type == "OBJECT":
                info_box.label(text=f"Parent Object: {obj.parent.name}", icon="OBJECT_DATA")
            else:
                info_box.label(text="No parent assigned", icon="INFO")
        else:
            info_box.label(text="No active object", icon="ERROR")
        
        # ===== SELECTION MODES SECTION =====
        select_box = layout.box()
        select_box.label(text="Select Relatives", icon="RESTRICT_SELECT_OFF")
        
        # Row 1: Siblings
        row1 = select_box.row(align=True)
        op = row1.operator("object.emesh_select_deep", text="Siblings", icon="RESTRICT_SELECT_OFF")
        op.mode = "SIBLINGS"
        row1.label(text="Same parent", icon="INFO")
        
        # Row 2: Children and Parents
        row2 = select_box.row(align=True)
        op = row2.operator("object.emesh_select_deep", text="Children", icon="OUTLINER_OB_GROUP_INSTANCE")
        op.mode = "CHILDREN"
        op = row2.operator("object.emesh_select_deep", text="Parents", icon="OUTLINER_OB_ARMATURE")
        op.mode = "PARENTS"
        
        # Row 3: Full Hierarchy
        row3 = select_box.row(align=True)
        op = row3.operator("object.emesh_select_deep", text="Full Hierarchy", icon="OUTLINER")
        op.mode = "HIERARCHY"


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
