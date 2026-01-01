"""
Emil's Mesh Toolkit - Shapekey Module
Tools for working with shapekeys
"""

import bpy
import numpy as np
from mathutils import Vector
from .toolkit_common import ToolkitUtils, ToolkitOperator, ToolkitPanel


# ==================== OVERLAY UPDATE OPERATORS ====================

class EMESH_OT_UpdateShapekeyOverlay(ToolkitOperator):
    """Update shapekey overlay (internal - triggered by scene changes)"""
    bl_idname = "mesh.emesh_update_shapekey_overlay"
    bl_label = "Update Overlay"
    
    def execute(self, context):
        # This just forces a redraw by the overlay handler
        return {"FINISHED"}


class EMESH_OT_AutoSelectShapekey(ToolkitOperator):
    """Automatically select shapekey by name or first available"""
    bl_idname = "mesh.emesh_auto_select_shapekey"
    bl_label = "Auto-Select Shapekey"
    
    def execute(self, context):
        props = context.scene.emesh_toolkit
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        # Don't auto-select if locked
        if props.lock_shapekey_selection:
            return {"FINISHED"}
        
        if not obj or not obj.data.shape_keys:
            return {"FINISHED"}
        
        current_name = props.shapekey_name
        key_blocks = obj.data.shape_keys.key_blocks
        available_names = [kb.name for kb in key_blocks]
        
        # Try to find shapekey with same name
        if current_name in available_names:
            return {"FINISHED"}
        
        # Try to find any non-Basis shapekey with same name
        for kb in key_blocks:
            if kb.name == current_name:
                props.shapekey_name = kb.name
                return {"FINISHED"}
        
        # If not found, select first non-Basis shapekey
        for kb in key_blocks:
            if kb.name != "Basis":
                props.shapekey_name = kb.name
                bpy.ops.mesh.emesh_scan_shapekey()
                return {"FINISHED"}
        
        return {"FINISHED"}


# ==================== OPERATORS ====================

class EMESH_OT_DeleteUselessShapekeys(ToolkitOperator):
    """Delete shapekeys that are identical to their basis"""
    bl_idname = "mesh.emesh_delete_useless_shapekeys"
    bl_label = "Delete Useless Shapekeys"
    bl_options = {"REGISTER", "UNDO"}
    
    tolerance: bpy.props.FloatProperty(
        name="Tolerance",
        default=0.001,
        min=0.0,
        max=1.0,
        precision=4
    )
    
    @classmethod
    def poll(cls, context):
        obj = ToolkitUtils.get_active_mesh_obj(context)
        return obj and obj.data.shape_keys
    
    def execute(self, context):
        deleted_count = 0
        
        # Get selected objects or active object
        objs = context.selected_objects if context.selected_objects else [ToolkitUtils.get_active_mesh_obj(context)]
        objs = [o for o in objs if o and o.type == "MESH"]
        
        if not objs:
            return self.report_warning("No mesh objects selected")
        
        for obj in objs:
            if not obj.data.shape_keys:
                continue
            if not obj.data.shape_keys.use_relative:
                continue
            
            kbs = obj.data.shape_keys.key_blocks
            nverts = len(obj.data.vertices)
            to_delete = []
            cache = {}
            locs = np.empty(3 * nverts, dtype=np.float32)
            
            for kb in kbs:
                if kb == kb.relative_key:
                    continue
                
                kb.data.foreach_get("co", locs)
                locs_copy = locs.copy()
                
                if kb.relative_key.name not in cache:
                    rel_locs = np.empty(3 * nverts, dtype=np.float32)
                    kb.relative_key.data.foreach_get("co", rel_locs)
                    cache[kb.relative_key.name] = rel_locs
                rel_locs = cache[kb.relative_key.name]
                
                locs_copy -= rel_locs
                if (np.abs(locs_copy) < self.tolerance).all():
                    to_delete.append(kb.name)
            
            for kb_name in to_delete:
                obj.shape_key_remove(obj.data.shape_keys.key_blocks[kb_name])
                deleted_count += 1
        
        return self.report_info(f"Deleted {deleted_count} useless shapekeys")


class EMESH_OT_ScanShapekey(ToolkitOperator):
    """Scan shapekey and populate vertex list (modified vertices only)"""
    bl_idname = "mesh.emesh_scan_shapekey"
    bl_label = "Scan Shapekey"
    
    def execute(self, context):
        props = context.scene.emesh_toolkit
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        if not obj:
            return self.report_warning("No active mesh object")
        
        if not props.shapekey_name:
            return self.report_warning("No shapekey selected")
        
        shape_keys = obj.data.shape_keys
        if not shape_keys or props.shapekey_name not in shape_keys.key_blocks:
            return self.report_warning("Shapekey not found")
        
        shapekey = shape_keys.key_blocks[props.shapekey_name]
        props.vertex_list.clear()
        
        for i, vert in enumerate(obj.data.vertices):
            if i < len(shapekey.data):
                co = shapekey.data[i].co
                base_co = vert.co.copy()
                distance = (co - base_co).length
                
                if distance >= 0.0001:
                    item = props.vertex_list.add()
                    item.index = i
                    item.x = co.x
                    item.y = co.y
                    item.z = co.z
                    item.distance = distance
        
        # Trigger overlay update for reactive display
        bpy.ops.mesh.emesh_update_shapekey_overlay()
        return self.report_info(f"Found {len(props.vertex_list)} modified vertices")


class EMESH_OT_ShapekeySelectVertex(ToolkitOperator):
    """Toggle vertex selection"""
    bl_idname = "mesh.emesh_shapekey_select_vertex"
    bl_label = "Select Vertex"
    
    vertex_index: bpy.props.IntProperty()
    
    def execute(self, context):
        props = context.scene.emesh_toolkit
        selected = ToolkitUtils.parse_vertex_indices(props.selected_vertices)
        
        if self.vertex_index in selected:
            selected.discard(self.vertex_index)
        else:
            selected.add(self.vertex_index)
        
        props.selected_vertices = ToolkitUtils.join_vertex_indices(selected)
        return {"FINISHED"}


class EMESH_OT_ShapekeyZeroOut(ToolkitOperator):
    """Zero out selected vertices in shapekey"""
    bl_idname = "mesh.emesh_shapekey_zero_out"
    bl_label = "Zero Out"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        props = context.scene.emesh_toolkit
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        if not obj:
            return {"CANCELLED"}
        
        shape_keys = obj.data.shape_keys
        if not shape_keys or props.shapekey_name not in shape_keys.key_blocks:
            return {"CANCELLED"}
        
        shapekey = shape_keys.key_blocks[props.shapekey_name]
        selected = ToolkitUtils.parse_vertex_indices(props.selected_vertices)
        
        if not selected:
            return self.report_warning("No vertices selected")
        
        for vid in selected:
            if vid < len(shapekey.data):
                shapekey.data[vid].co = obj.data.vertices[vid].co.copy()
        
        bpy.ops.mesh.emesh_scan_shapekey()
        # Trigger overlay update for reactive display
        bpy.ops.mesh.emesh_update_shapekey_overlay()
        return self.report_info(f"Zeroed out {len(selected)} vertices")


class EMESH_OT_ShapekeyApplyValues(ToolkitOperator):
    """Apply X, Y, Z values to selected vertices"""
    bl_idname = "mesh.emesh_shapekey_apply_values"
    bl_label = "Apply Values"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        props = context.scene.emesh_toolkit
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        if not obj:
            return {"CANCELLED"}
        
        shape_keys = obj.data.shape_keys
        if not shape_keys or props.shapekey_name not in shape_keys.key_blocks:
            return {"CANCELLED"}
        
        shapekey = shape_keys.key_blocks[props.shapekey_name]
        selected = ToolkitUtils.parse_vertex_indices(props.selected_vertices)
        
        if not selected:
            return self.report_warning("No vertices selected")
        
        if props.apply_mode == "OFFSET":
            offset = Vector((props.value_x, props.value_y, props.value_z))
            for vid in selected:
                if vid < len(shapekey.data):
                    shapekey.data[vid].co += offset
        else:
            value = Vector((props.value_x, props.value_y, props.value_z))
            for vid in selected:
                if vid < len(shapekey.data):
                    shapekey.data[vid].co = value
        
        bpy.ops.mesh.emesh_scan_shapekey()
        # Trigger overlay update for reactive display
        bpy.ops.mesh.emesh_update_shapekey_overlay()
        return self.report_info(f"Applied values to {len(selected)} vertices")


class EMESH_OT_ShapeKeyAddFromEditMode(ToolkitOperator):
    """Add selected vertices from Edit Mode to selection"""
    bl_idname = "mesh.emesh_shapekey_add_from_edit"
    bl_label = "Add from Edit Mode"
    
    def execute(self, context):
        props = context.scene.emesh_toolkit
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        if not obj:
            return {"CANCELLED"}
        
        current_mode = obj.mode
        ToolkitUtils.set_mode(obj, "OBJECT")
        
        selected_in_edit = [v.index for v in obj.data.vertices if v.select]
        
        if not selected_in_edit:
            ToolkitUtils.set_mode(obj, current_mode)
            return self.report_warning("No vertices selected in Edit Mode")
        
        current_selected = ToolkitUtils.parse_vertex_indices(props.selected_vertices)
        current_selected.update(selected_in_edit)
        props.selected_vertices = ToolkitUtils.join_vertex_indices(current_selected)
        
        ToolkitUtils.set_mode(obj, current_mode)
        return self.report_info(f"Added {len(selected_in_edit)} vertices")


class EMESH_OT_ShapeKeyClearSelection(ToolkitOperator):
    """Clear vertex selection"""
    bl_idname = "mesh.emesh_shapekey_clear_selection"
    bl_label = "Clear Selection"
    
    def execute(self, context):
        context.scene.emesh_toolkit.selected_vertices = ""
        return {"FINISHED"}


# ==================== UI ====================

class EMESH_UL_VertexList(bpy.types.UIList):
    """Vertex list for shapekey editing"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        props = context.scene.emesh_toolkit
        selected = ToolkitUtils.parse_vertex_indices(props.selected_vertices)
        
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            is_selected = item.index in selected
            row.label(text="✓" if is_selected else " ", icon="NONE")
            row.label(text=f"v{item.index}")
            row.label(text=f"Δ{item.distance:.4f}")
            row.label(text=f"({item.x:.3f}, {item.y:.3f}, {item.z:.3f})")
            op = row.operator("mesh.emesh_shapekey_select_vertex", text="", icon="RESTRICT_SELECT_OFF")
            op.vertex_index = item.index


class EMESH_PT_Shapekeys(ToolkitPanel):
    """Shapekey tools panel"""
    bl_label = "Shapekey Tools"
    bl_idname = "EMESH_PT_Shapekeys"
    bl_parent_id = "EMESH_PT_MainPanel"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        props = context.scene.emesh_toolkit
        layout = self.layout
        obj = ToolkitUtils.get_active_mesh_obj(context)
        
        # ===== CLEANUP SECTION =====
        cleanup_box = layout.box()
        cleanup_box.label(text="Cleanup", icon="BRUSH_DATA")
        cleanup_box.operator("mesh.emesh_delete_useless_shapekeys", icon="TRASH")
        
        # ===== VERTEX EDITOR SECTION =====
        if obj and obj.data.shape_keys:
            editor_box = layout.box()
            editor_box.label(text="Vertex Editor", icon="EDITMODE_HLT")
            
            # Shapekey selection
            select_box = editor_box.box()
            select_box.label(text="Select Shapekey", icon="SHAPEKEY_DATA")
            select_row = select_box.row(align=True)
            select_row.prop_search(props, "shapekey_name", obj.data.shape_keys, "key_blocks")
            select_row.prop(props, "lock_shapekey_selection", text="", icon="LOCKED" if props.lock_shapekey_selection else "UNLOCKED", emboss=True)
            
            if props.shapekey_name:
                # Overlay settings
                overlay_box = editor_box.box()
                overlay_box.label(text="Overlay", icon="OVERLAY")
                row = overlay_box.row(align=True)
                row.prop(props, "overlay_shapekey", text="Show", icon="OVERLAY")
                
                if props.overlay_shapekey:
                    settings_box = overlay_box.box()
                    settings_box.label(text="Settings", icon="PREFERENCES")
                    settings_box.prop(props, "display_threshold", slider=True)
                    settings_box.prop(props, "limit_display")
                    if props.limit_display:
                        settings_box.prop(props, "max_display_vertices", slider=True)
                
                # Scanning
                scan_box = editor_box.box()
                scan_box.label(text="Scan & Select", icon="VIEWZOOM")
                row = scan_box.row(align=True)
                row.operator("mesh.emesh_scan_shapekey", text="Scan", icon="VIEWZOOM")
                row.operator("mesh.emesh_shapekey_add_from_edit", text="From Edit", icon="EDITMODE_HLT")
                
                # Vertex list
                if props.vertex_list:
                    list_box = editor_box.box()
                    list_box.label(text=f"Modified Vertices: {len(props.vertex_list)}", icon="VERTEXSEL")
                    list_box.template_list(
                        "EMESH_UL_VertexList", "", props, "vertex_list",
                        props, "vertex_list_index", rows=5
                    )
                    
                    # Selection and editing
                    selected_count = len(ToolkitUtils.parse_vertex_indices(props.selected_vertices))
                    
                    if selected_count > 0:
                        edit_box = list_box.box()
                        edit_box.label(text=f"Edit {selected_count} Vertex(es)", icon="TOOL_SETTINGS")
                        
                        # Mode selection
                        mode_row = edit_box.row(align=True)
                        mode_row.prop(props, "apply_mode", expand=True)
                        
                        # Values
                        val_col = edit_box.column(align=True)
                        val_col.prop(props, "value_x")
                        val_col.prop(props, "value_y")
                        val_col.prop(props, "value_z")
                        
                        # Action buttons
                        action_row = edit_box.row(align=True)
                        action_row.operator("mesh.emesh_shapekey_apply_values", text="Apply", icon="CHECKMARK")
                        action_row.operator("mesh.emesh_shapekey_zero_out", text="Zero", icon="TRASH")
                        
                        # Clear selection
                        edit_box.operator("mesh.emesh_shapekey_clear_selection", text="Clear Selection", icon="X")
                    else:
                        list_box.label(text="Select vertices to edit", icon="INFO")


# ==================== REGISTRATION ====================

classes = (
    EMESH_OT_UpdateShapekeyOverlay,
    EMESH_OT_AutoSelectShapekey,
    EMESH_OT_DeleteUselessShapekeys,
    EMESH_OT_ScanShapekey,
    EMESH_OT_ShapekeySelectVertex,
    EMESH_OT_ShapekeyZeroOut,
    EMESH_OT_ShapekeyApplyValues,
    EMESH_OT_ShapeKeyAddFromEditMode,
    EMESH_OT_ShapeKeyClearSelection,
    EMESH_UL_VertexList,
    EMESH_PT_Shapekeys,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
