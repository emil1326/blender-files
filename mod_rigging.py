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
    
    interpolate_bones: bpy.props.IntProperty(
        name="Interpolate Bones",
        default=1,
        min=1,
        max=4,
        description="Number of most influential bones to average (1=single, 2+=interpolated)"
    )
    
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
        
        # Check if we're working with a shapekey
        shape_keys = obj.data.shape_keys
        is_shapekey_mode = (
            shape_keys and 
            shape_keys.active_index > 0 and 
            shape_keys.active_index < len(shape_keys.key_blocks)
        )
        
        shapekey = None
        if is_shapekey_mode:
            shapekey = shape_keys.key_blocks[shape_keys.active_index]
        
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
            
            # Collect bone weights (top N influential)
            bone_weights = []
            for g in vert.groups:
                if g.weight > 0 and g.group < len(vgroups):
                    vgroup_name = vgroups[g.group].name
                    if vgroup_name in bones:
                        bone_weights.append((vgroup_name, g.weight))
            
            if not bone_weights:
                continue
            
            # Sort by weight and take top N
            bone_weights.sort(key=lambda x: x[1], reverse=True)
            top_bones = bone_weights[:self.interpolate_bones]
            
            # Calculate interpolated position
            total_weight = sum(w for _, w in top_bones)
            final_pos = Vector((0, 0, 0))
            
            for bone_name, weight in top_bones:
                bone = bones[bone_name]
                bone_head_world = armature.matrix_world @ bone.head_local
                bone_head_obj = obj.matrix_world.inverted() @ bone_head_world
                final_pos += bone_head_obj * (weight / total_weight)
            
            # Set position (in shapekey or base mesh)
            if shapekey:
                shapekey.data[vert.index].co = final_pos
            else:
                vert.co = final_pos
            count += 1
        
        ToolkitUtils.set_mode(obj, original_mode)
        mode_text = f" in '{shapekey.name}'" if shapekey else ""
        return self.report_info(f"Snapped {count} vertices to bone roots{mode_text}")


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
        
        # ===== OBJECT INFO SECTION =====
        info_box = layout.box()
        info_box.label(text="Object Information", icon="INFO")
        
        has_armature = False
        if obj:
            for mod in obj.modifiers:
                if mod.type == "ARMATURE" and mod.object:
                    has_armature = True
                    info_box.label(text=f"Armature: {mod.object.name}", icon="ARMATURE_DATA")
                    
                    # Check shapekey mode - use obj.active_shape_key_index instead
                    if obj.data.shape_keys and obj.active_shape_key_index > 0:
                        try:
                            kb = obj.data.shape_keys.key_blocks[obj.active_shape_key_index]
                            info_box.label(text=f"Shapekey: {kb.name}", icon="SHAPEKEY_DATA")
                        except:
                            pass
                    break
        
        if not has_armature:
            info_box.label(text="No armature modifier found", icon="ERROR")
        else:
            # ===== SNAP TO ROOT SECTION =====
            snap_box = layout.box()
            snap_box.label(text="Snap Vertices to Bone Root", icon="SNAP_ON")
            
            # Settings
            settings_box = snap_box.box()
            settings_box.label(text="Settings", icon="PREFERENCES")
            settings_box.label(text="Bones to blend (1=single, 2+=avg)", icon="INFO")
            
            # Bone interpolation buttons - quick access
            button_box = snap_box.box()
            button_box.label(text="Interpolation Options", icon="AUTO")
            
            row1 = button_box.row(align=True)
            for i in range(1, 3):
                op = row1.operator("mesh.emesh_set_vertex_to_root", text=str(i), emboss=True)
                op.interpolate_bones = i
            
            row2 = button_box.row(align=True)
            for i in range(3, 5):
                op = row2.operator("mesh.emesh_set_vertex_to_root", text=str(i), emboss=True)
                op.interpolate_bones = i


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
