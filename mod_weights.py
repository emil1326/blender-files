"""
Emil's Mesh Toolkit - Weights Module
Tools for working with vertex weights
"""

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from .toolkit_common import ToolkitUtils, ToolkitOperator, ToolkitPanel


# ==================== DATA & DRAWING ====================

def get_deform_group_names(obj):
    """Get names of deform bones from armature modifier"""
    deform_group_names = set()
    for mod in obj.modifiers:
        if mod.type == "ARMATURE" and mod.object and mod.object.type == "ARMATURE":
            for bone in mod.object.data.bones:
                if bone.use_deform:
                    deform_group_names.add(bone.name)
    return deform_group_names


def get_overlimit_vertices(context, obj, limit, count_deform_only=True):
    """Get vertices exceeding weight limit (optionally counting deform groups only)"""
    if not obj or obj.type != "MESH":
        return []
    
    result = []
    deform_names = get_deform_group_names(obj) if count_deform_only else set()
    use_deform_filter = count_deform_only and len(deform_names) > 0
    
    depsgraph = context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.to_mesh()
    
    for i, vert in enumerate(mesh_eval.vertices):
        if use_deform_filter:
            # Count only deform groups
            total_weight = 0
            for g in vert.groups:
                if g.weight > 0 and g.group < len(obj.vertex_groups):
                    group_name = obj.vertex_groups[g.group].name
                    if group_name in deform_names:
                        total_weight += g.weight
        else:
            # Count all groups
            total_weight = sum(g.weight for g in vert.groups)
        
        if total_weight > limit:
            co_world = obj.matrix_world @ vert.co
            result.append((co_world.x, co_world.y, co_world.z))
    
    obj_eval.to_mesh_clear()
    return result


def get_overgroup_vertices(context, obj, max_groups, count_deform_only=True):
    """Get vertices with more than max_groups assigned"""
    if not obj or obj.type != "MESH" or not obj.vertex_groups:
        return []
    
    result = []
    deform_names = get_deform_group_names(obj) if count_deform_only else set()
    use_deform_filter = count_deform_only and len(deform_names) > 0
    
    for vert in obj.data.vertices:
        if use_deform_filter:
            # Count only deform groups
            count = 0
            for g in vert.groups:
                if g.weight > 0 and g.group < len(obj.vertex_groups):
                    group_name = obj.vertex_groups[g.group].name
                    if group_name in deform_names:
                        count += 1
        else:
            # Count all groups with nonzero weight
            count = sum(1 for g in vert.groups if g.weight > 0)
        
        if count > max_groups:
            co_world = obj.matrix_world @ vert.co
            result.append((co_world.x, co_world.y, co_world.z))
    
    return result


def draw_weight_overlay():
    """Draw overlay for over-limit and over-group vertices"""
    context = bpy.context
    props = context.scene.emesh_toolkit
    
    # Draw weight limit overlay
    if props.overlay_weights and props.weight_overlay_data:
        try:
            coords = [(item.x, item.y, item.z) for item in props.weight_overlay_data]
            
            if coords:
                shader = gpu.shader.from_builtin("UNIFORM_COLOR")
                batch = batch_for_shader(shader, "POINTS", {"pos": coords})
                shader.bind()
                shader.uniform_float("color", (1.0, 0.0, 0.0, 1.0))
                gpu.state.point_size_set(8.0)
                batch.draw(shader)
                gpu.state.point_size_set(1.0)
        except:
            pass
    
    # Draw vertex group overlay
    if props.overlay_vertex_groups and props.vertex_group_overlay_data:
        try:
            coords = [(item.x, item.y, item.z) for item in props.vertex_group_overlay_data]
            
            if coords:
                shader = gpu.shader.from_builtin("UNIFORM_COLOR")
                batch = batch_for_shader(shader, "POINTS", {"pos": coords})
                shader.bind()
                shader.uniform_float("color", (1.0, 0.5, 0.0, 1.0))
                gpu.state.point_size_set(8.0)
                batch.draw(shader)
                gpu.state.point_size_set(1.0)
        except:
            pass


# ==================== OPERATORS ====================

class EMESH_OT_ScanWeights(ToolkitOperator):
    """Scan for vertices over weight limit"""
    bl_idname = "mesh.emesh_scan_weights"
    bl_label = "Scan Weights"
    
    def execute(self, context):
        props = context.scene.emesh_toolkit
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        if not obj:
            return self.report_warning("No active mesh object")
        
        overlimit = get_overlimit_vertices(context, obj, props.weight_limit, count_deform_only=True)
        props.weight_overlay_data.clear()
        
        for co in overlimit:
            item = props.weight_overlay_data.add()
            item.x, item.y, item.z = co
        
        return self.report_info(f"Found {len(overlimit)} vertices over weight limit")


class EMESH_OT_ScanVertexGroups(ToolkitOperator):
    """Scan for vertices with too many group assignments"""
    bl_idname = "mesh.emesh_scan_vertex_groups"
    bl_label = "Scan Vertex Groups"
    
    def execute(self, context):
        props = context.scene.emesh_toolkit
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        if not obj:
            return self.report_warning("No active mesh object")
        
        overgroup = get_overgroup_vertices(context, obj, props.max_bone_groups, count_deform_only=True)
        props.vertex_group_overlay_data.clear()
        
        for co in overgroup:
            item = props.vertex_group_overlay_data.add()
            item.x, item.y, item.z = co
        
        return self.report_info(f"Found {len(overgroup)} vertices over {props.max_bone_groups} group limit")


class EMESH_OT_SelectOverlimitWeights(ToolkitOperator):
    """Select vertices over weight limit"""
    bl_idname = "mesh.emesh_select_overlimit_weights"
    bl_label = "Select Over-Limit"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        props = context.scene.emesh_toolkit
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        if not obj:
            return {"CANCELLED"}
        
        overlimit_coords = [(item.x, item.y, item.z) for item in props.weight_overlay_data]
        
        if not overlimit_coords:
            return self.report_warning("No over-limit vertices found. Scan first.")
        
        ToolkitUtils.set_mode(obj, "OBJECT")
        
        for v in obj.data.vertices:
            v.select = False
        
        count = 0
        for v in obj.data.vertices:
            co_world = obj.matrix_world @ v.co
            for oc in overlimit_coords:
                if (co_world - Vector(oc)).length < 0.0001:
                    v.select = True
                    count += 1
                    break
        
        ToolkitUtils.set_mode(obj, "EDIT")
        return self.report_info(f"Selected {count} vertices")


class EMESH_OT_SelectOvergroupVertices(ToolkitOperator):
    """Select vertices with too many group assignments"""
    bl_idname = "mesh.emesh_select_overgroup_vertices"
    bl_label = "Select Over-Group"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        props = context.scene.emesh_toolkit
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        if not obj:
            return {"CANCELLED"}
        
        overgroup_coords = [(item.x, item.y, item.z) for item in props.vertex_group_overlay_data]
        
        if not overgroup_coords:
            return self.report_warning("No over-group vertices found. Scan first.")
        
        ToolkitUtils.set_mode(obj, "OBJECT")
        
        for v in obj.data.vertices:
            v.select = False
        
        count = 0
        for v in obj.data.vertices:
            co_world = obj.matrix_world @ v.co
            for oc in overgroup_coords:
                if (co_world - Vector(oc)).length < 0.0001:
                    v.select = True
                    count += 1
                    break
        
        ToolkitUtils.set_mode(obj, "EDIT")
        return self.report_info(f"Selected {count} vertices")


class EMESH_OT_NormalizeWeights(ToolkitOperator):
    """Normalize weights for all vertices"""
    bl_idname = "mesh.emesh_normalize_weights"
    bl_label = "Normalize All Weights"
    bl_options = {"REGISTER", "UNDO"}
    
    selected_only: bpy.props.BoolProperty(
        name="Selected Only",
        default=False,
        description="Only normalize selected vertices"
    )
    
    @classmethod
    def poll(cls, context):
        obj = ToolkitUtils.get_active_mesh_obj(context)
        return obj and obj.data.vertices
    
    def execute(self, context):
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        if not obj:
            return {"CANCELLED"}
        
        deform_group_names = get_deform_group_names(obj)
        if not deform_group_names:
            return self.report_warning("No deform groups found")
        
        count = 0
        for vert in obj.data.vertices:
            # Skip if checking selected only and vertex not selected
            if self.selected_only and not vert.select:
                continue
            
            # Get total weight for deform groups only
            total_weight = 0.0
            deform_groups = []
            
            for g in vert.groups:
                if g.group < len(obj.vertex_groups):
                    group_name = obj.vertex_groups[g.group].name
                    if group_name in deform_group_names:
                        deform_groups.append(g)
                        total_weight += g.weight
            
            # Normalize deform groups
            if total_weight > 0.0001:
                scale = 1.0 / total_weight
                for g in deform_groups:
                    g.weight *= scale
                count += 1
        
        return self.report_info(f"Normalized {count} vertices")


# ==================== UI ====================

class EMESH_PT_Weights(ToolkitPanel):
    """Weight tools panel"""
    bl_label = "Weight Tools"
    bl_idname = "EMESH_PT_Weights"
    bl_parent_id = "EMESH_PT_MainPanel"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        props = context.scene.emesh_toolkit
        layout = self.layout
        
        # ===== WEIGHT LIMIT SECTION =====
        weight_box = layout.box()
        weight_box.label(text="Weight Limit Checker", icon="MOD_VERTEX_WEIGHT")
        
        settings_row = weight_box.row(align=True)
        settings_row.prop(props, "weight_limit", text="Limit", slider=True)
        settings_row.prop(props, "overlay_weights", text="", icon="OVERLAY")
        
        action_row = weight_box.row(align=True)
        action_row.operator("mesh.emesh_scan_weights", text="Scan", icon="VIEWZOOM")
        
        # Normalize buttons
        normalize_row = weight_box.row(align=True)
        op = normalize_row.operator("mesh.emesh_normalize_weights", text="Normalize All", icon="CHECKMARK")
        op.selected_only = False
        op = normalize_row.operator("mesh.emesh_normalize_weights", text="Selected", icon="RESTRICT_SELECT_OFF")
        op.selected_only = True
        
        if props.weight_overlay_data:
            result_box = weight_box.box()
            result_box.label(text=f"Over-Limit: {len(props.weight_overlay_data)}", icon="ERROR")
            result_box.operator("mesh.emesh_select_overlimit_weights", text="Select Over-Limit", icon="RESTRICT_SELECT_OFF")
        
        # ===== VERTEX GROUP SECTION =====
        group_box = layout.box()
        group_box.label(text="Vertex Group Counter", icon="GROUP_VERTEX")
        
        settings_row2 = group_box.row(align=True)
        settings_row2.prop(props, "max_bone_groups", text="Max Groups", slider=True)
        settings_row2.prop(props, "overlay_vertex_groups", text="", icon="OVERLAY")
        
        action_row2 = group_box.row(align=True)
        action_row2.operator("mesh.emesh_scan_vertex_groups", text="Scan", icon="VIEWZOOM")
        
        if props.vertex_group_overlay_data:
            result_box2 = group_box.box()
            result_box2.label(text=f"Over-Group: {len(props.vertex_group_overlay_data)}", icon="ERROR")
            result_box2.operator("mesh.emesh_select_overgroup_vertices", text="Select Over-Group", icon="RESTRICT_SELECT_OFF")


# ==================== REGISTRATION ====================

classes = (
    EMESH_OT_ScanWeights,
    EMESH_OT_ScanVertexGroups,
    EMESH_OT_SelectOverlimitWeights,
    EMESH_OT_SelectOvergroupVertices,
    EMESH_OT_NormalizeWeights,
    EMESH_PT_Weights,
)

_draw_handler = None


def register():
    global _draw_handler
    
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    global _draw_handler
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    if _draw_handler:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, "WINDOW")
        except:
            pass
        _draw_handler = None
