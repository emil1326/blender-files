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

def get_overlimit_vertices(context, obj, limit):
    """Get vertices exceeding weight limit"""
    if not obj or obj.type != "MESH":
        return []
    
    result = []
    depsgraph = context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.to_mesh()
    
    for i, vert in enumerate(mesh_eval.vertices):
        total_weight = sum(g.weight for g in vert.groups)
        if total_weight > limit:
            co_world = obj.matrix_world @ vert.co
            result.append((co_world.x, co_world.y, co_world.z))
    
    obj_eval.to_mesh_clear()
    return result


def draw_weight_overlay():
    """Draw overlay for over-limit vertices"""
    context = bpy.context
    props = context.scene.emesh_toolkit
    
    if not props.overlay_weights or not props.weight_overlay_data:
        return
    
    try:
        coords = [(co[0], co[1], co[2]) for co in props.weight_overlay_data]
        
        if not coords:
            return
        
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        batch = batch_for_shader(shader, "POINTS", {"pos": coords})
        
        shader.bind()
        shader.uniform_float("color", (1.0, 0.0, 0.0, 1.0))
        
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
        
        overlimit = get_overlimit_vertices(context, obj, props.weight_limit)
        props.weight_overlay_data.clear()
        
        for co in overlimit:
            item = props.weight_overlay_data.add()
            item.x, item.y, item.z = co
        
        return self.report_info(f"Found {len(overlimit)} vertices over limit")


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
        
        box = layout.box()
        box.label(text="Weight Limit Checker:", icon="MOD_VERTEX_WEIGHT")
        box.prop(props, "overlay_weights", icon="OVERLAY")
        box.prop(props, "weight_limit", slider=True)
        box.operator("mesh.emesh_scan_weights", icon="VIEWZOOM")
        
        if props.weight_overlay_data:
            box.label(text=f"Over-Limit: {len(props.weight_overlay_data)}", icon="ERROR")
            box.operator("mesh.emesh_select_overlimit_weights", icon="RESTRICT_SELECT_OFF")


# ==================== REGISTRATION ====================

classes = (
    EMESH_OT_ScanWeights,
    EMESH_OT_SelectOverlimitWeights,
    EMESH_PT_Weights,
)

_draw_handler = None


def register():
    global _draw_handler
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
        draw_weight_overlay, (), "WINDOW", "POST_VIEW"
    )


def unregister():
    global _draw_handler
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    if _draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, "WINDOW")
        _draw_handler = None
