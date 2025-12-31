"""
Emil's Mesh Toolkit - Rigging Module
Tools for working with armatures and rigging
"""

import bpy
from mathutils import Vector
from .toolkit_common import ToolkitUtils, ToolkitOperator, ToolkitPanel


# ==================== OPERATORS ====================

class EMESH_OT_SetVertexToRoot(ToolkitOperator):
    """Snap selected vertices to their most influential bone's head position"""
    bl_idname = "mesh.emesh_set_vertex_to_root"
    bl_label = "Snap to Bone Root"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        obj = ToolkitUtils.get_active_mesh_obj(context)
        if not obj:
            return False
        
        for mod in obj.modifiers:
            if mod.type == "ARMATURE" and mod.object:
                return True
        return False
    
    def execute(self, context):
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        if not obj:
            return {"CANCELLED"}
        
        # Find armature modifier
        armature = None
        for mod in obj.modifiers:
            if mod.type == "ARMATURE" and mod.object:
                armature = mod.object
                break
        
        if not armature:
            return self.report_error("No armature modifier found")
        
        # Get vertex groups
        vgroups = obj.vertex_groups
        bones = armature.data.bones
        
        # Switch to object mode to read vertex selection
        original_mode = obj.mode
        ToolkitUtils.set_mode(obj, "OBJECT")
        
        selected_verts = [v for v in obj.data.vertices if v.select]
        
        if not selected_verts:
            ToolkitUtils.set_mode(obj, original_mode)
            return self.report_warning("No vertices selected")
        
        count = 0
        for vert in selected_verts:
            if not vert.groups:
                continue
            
            # Find bone with highest weight
            max_weight = -1
            max_bone = None
            
            for g in vert.groups:
                if g.group < len(vgroups):
                    vgroup_name = vgroups[g.group].name
                    if vgroup_name in bones and g.weight > max_weight:
                        max_weight = g.weight
                        max_bone = bones[vgroup_name]
            
            if max_bone:
                # Get bone head in world space
                bone_head_world = armature.matrix_world @ max_bone.head_local
                
                # Convert to object space
                bone_head_obj = obj.matrix_world.inverted() @ bone_head_world
                
                # Set vertex position
                vert.co = bone_head_obj
                count += 1
        
        ToolkitUtils.set_mode(obj, original_mode)
        return self.report_info(f"Snapped {count} vertices to bone roots")


# ==================== UI ====================

class EMESH_PT_Rigging(ToolkitPanel):
    """Rigging tools panel"""
    bl_label = "Rigging Tools"
    bl_idname = "EMESH_PT_Rigging"
    bl_parent_id = "EMESH_PT_MainPanel"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        box = layout.box()
        box.label(text="Vertex to Bone:", icon="BONE_DATA")
        
        # Check for armature
        has_armature = False
        if obj:
            for mod in obj.modifiers:
                if mod.type == "ARMATURE" and mod.object:
                    has_armature = True
                    box.label(text=f"Armature: {mod.object.name}", icon="ARMATURE_DATA")
                    break
        
        if not has_armature:
            box.label(text="No armature found", icon="ERROR")
        
        box.operator("mesh.emesh_set_vertex_to_root", icon="SNAP_ON")


# ==================== REGISTRATION ====================

classes = (
    EMESH_OT_SetVertexToRoot,
    EMESH_PT_Rigging,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
