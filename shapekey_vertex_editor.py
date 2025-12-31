bl_info = {
    "name": "Shapekey Vertex Editor",
    "author": "Emil",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "description": "Edit individual vertex positions in shapekeys with visual overlay",
    "category": "Mesh",
}

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

_draw_handler = None


# ---------- utils ----------
def get_shapekeys_for_object(obj):
    """Get all shapekeys from active object mesh"""
    if obj and obj.type == "MESH" and obj.data.shape_keys:
        return obj.data.shape_keys.key_blocks
    return []


def get_shapekey_vertex_data(obj, shapekey_name, modified_only=False, threshold=0.0001):
    """Get vertex positions and indices for a shapekey
    
    Args:
        modified_only: If True, only return vertices that differ from base mesh
        threshold: Distance threshold to consider a vertex modified
    """
    if not obj or obj.type != "MESH":
        return []
    
    shape_keys = obj.data.shape_keys
    if not shape_keys:
        return []
    
    shapekey = shape_keys.key_blocks.get(shapekey_name)
    if not shapekey:
        return []
    
    result = []
    for i, vert in enumerate(obj.data.vertices):
        if i < len(shapekey.data):
            co = shapekey.data[i].co
            base_co = vert.co.copy()
            
            # Check if vertex is modified
            if modified_only:
                distance = (co - base_co).length
                if distance < threshold:
                    continue
            
            result.append({
                "index": i,
                "co": co.copy(),
                "base_co": base_co,
                "distance": (co - base_co).length
            })
    return result


def parse_selected_string(s):
    """Parse comma-separated vertex indices"""
    if not s:
        return set()
    parts = [p.strip() for p in s.split(",") if p.strip()]
    try:
        return set(int(p) for p in parts)
    except Exception:
        return set()


def join_selected_list(s):
    """Convert set to comma-separated string"""
    return ",".join(str(int(i)) for i in sorted(s))


# ---------- draw ----------
def draw_overlay():
    """Draw vertex overlay with positions and influence info (optimized)"""
    scn = bpy.context.scene
    props = scn.shapekey_editor
    
    # Skip if overlay disabled - use this to control visibility
    if not props.enabled:
        return
    
    # Skip if no vertex list populated (tool not actively used)
    if not props.vertex_list:
        return
    
    # Skip if no shapekey selected
    if not props.shapekey_name:
        return
    
    obj = bpy.context.view_layer.objects.active
    if not obj or obj.type != "MESH":
        return
    
    shape_keys = obj.data.shape_keys
    if not shape_keys:
        return
    
    shapekey = shape_keys.key_blocks.get(props.shapekey_name)
    if not shapekey:
        return
    
    selected_verts = parse_selected_string(props.selected_vertices)
    mat = obj.matrix_world
    
    # Build vertex data directly from the list
    vertex_data = []
    for item in props.vertex_list:
        # Apply distance threshold filter
        if item.distance < props.display_threshold:
            continue
        
        co = Vector((item.x, item.y, item.z))
        world_co = mat @ co
        
        vertex_data.append({
            "index": item.index,
            "world_co": world_co,
            "distance": item.distance
        })
    
    if not vertex_data:
        return
    
    # Apply display limit if enabled
    if props.limit_display and len(vertex_data) > props.max_display_vertices:
        # Sort by distance (largest movement first) and take top N
        vertex_data.sort(key=lambda v: v["distance"], reverse=True)
        vertex_data = vertex_data[:props.max_display_vertices]
    
    shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
    gpu.state.blend_set("ALPHA")
    
    # Separate selected and unselected vertices
    selected_coords = []
    unselected_coords = []
    
    for vdata in vertex_data:
        vid = vdata["index"]
        world_co = vdata["world_co"]
        
        if vid in selected_verts:
            selected_coords.append(world_co)
        else:
            unselected_coords.append(world_co)
    
    # Draw unselected modified vertices (gray)
    if unselected_coords:
        batch = batch_for_shader(shader, "POINTS", {"pos": unselected_coords})
        shader.bind()
        shader.uniform_float("color", (0.5, 0.5, 0.5, 0.8))
        gpu.state.point_size_set(6)
        batch.draw(shader)
    
    # Draw selected vertices (bright yellow)
    if selected_coords:
        batch = batch_for_shader(shader, "POINTS", {"pos": selected_coords})
        shader.bind()
        shader.uniform_float("color", (1.0, 1.0, 0.0, 1.0))
        gpu.state.point_size_set(10)
        batch.draw(shader)
    
    gpu.state.blend_set("NONE")


# ---------- operators ----------
class SKVERTED_OT_Scan(bpy.types.Operator):
    """Scan shapekey and populate vertex list (modified vertices only)"""
    bl_idname = "mesh.scan_shapekey_vertices"
    bl_label = "Scan Shapekey"
    
    def execute(self, context):
        props = context.scene.shapekey_editor
        obj = context.view_layer.objects.active
        
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "No active mesh object")
            return {"CANCELLED"}
        
        if not props.shapekey_name:
            self.report({"WARNING"}, "No shapekey selected")
            return {"CANCELLED"}
        
        shape_keys = obj.data.shape_keys
        if not shape_keys or props.shapekey_name not in shape_keys.key_blocks:
            self.report({"WARNING"}, "Shapekey not found")
            return {"CANCELLED"}
        
        # Clear and repopulate - only modified vertices
        props.vertex_list.clear()
        vertex_data = get_shapekey_vertex_data(obj, props.shapekey_name, modified_only=True)
        
        for vdata in vertex_data:
            item = props.vertex_list.add()
            item.index = vdata["index"]
            item.x = vdata["co"].x
            item.y = vdata["co"].y
            item.z = vdata["co"].z
            item.distance = vdata["distance"]
        
        self.report({"INFO"}, f"Found {len(vertex_data)} modified vertices")
        return {"FINISHED"}


class SKVERTED_OT_SelectVertex(bpy.types.Operator):
    """Toggle vertex selection via overlay click"""
    bl_idname = "mesh.select_shapekey_vertex"
    bl_label = "Select Vertex"
    
    vertex_index: bpy.props.IntProperty()
    
    def execute(self, context):
        props = context.scene.shapekey_editor
        selected = parse_selected_string(props.selected_vertices)
        
        if self.vertex_index in selected:
            selected.discard(self.vertex_index)
        else:
            selected.add(self.vertex_index)
        
        props.selected_vertices = join_selected_list(selected)
        return {"FINISHED"}


class SKVERTED_OT_ZeroOut(bpy.types.Operator):
    """Zero out selected vertices in shapekey"""
    bl_idname = "mesh.shapekey_zero_out"
    bl_label = "Zero Out"
    
    def execute(self, context):
        props = context.scene.shapekey_editor
        obj = context.view_layer.objects.active
        
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "No active mesh object")
            return {"CANCELLED"}
        
        shape_keys = obj.data.shape_keys
        if not shape_keys or props.shapekey_name not in shape_keys.key_blocks:
            self.report({"WARNING"}, "Shapekey not found")
            return {"CANCELLED"}
        
        shapekey = shape_keys.key_blocks[props.shapekey_name]
        selected = parse_selected_string(props.selected_vertices)
        
        if not selected:
            self.report({"WARNING"}, "No vertices selected")
            return {"CANCELLED"}
        
        for vid in selected:
            if vid < len(shapekey.data):
                shapekey.data[vid].co = obj.data.vertices[vid].co.copy()
        
        # Refresh list
        bpy.ops.mesh.scan_shapekey_vertices()
        self.report({"INFO"}, f"Zeroed out {len(selected)} vertices")
        return {"FINISHED"}


class SKVERTED_OT_ApplyValues(bpy.types.Operator):
    """Apply X, Y, Z values to selected vertices"""
    bl_idname = "mesh.shapekey_apply_values"
    bl_label = "Apply Values"
    
    def execute(self, context):
        props = context.scene.shapekey_editor
        obj = context.view_layer.objects.active
        
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "No active mesh object")
            return {"CANCELLED"}
        
        shape_keys = obj.data.shape_keys
        if not shape_keys or props.shapekey_name not in shape_keys.key_blocks:
            self.report({"WARNING"}, "Shapekey not found")
            return {"CANCELLED"}
        
        shapekey = shape_keys.key_blocks[props.shapekey_name]
        selected = parse_selected_string(props.selected_vertices)
        
        if not selected:
            self.report({"WARNING"}, "No vertices selected")
            return {"CANCELLED"}
        
        # Apply offset mode or absolute mode
        if props.apply_mode == "OFFSET":
            offset = (props.value_x, props.value_y, props.value_z)
            for vid in selected:
                if vid < len(shapekey.data):
                    shapekey.data[vid].co += offset
        else:  # ABSOLUTE
            value = (props.value_x, props.value_y, props.value_z)
            for vid in selected:
                if vid < len(shapekey.data):
                    shapekey.data[vid].co = value
        
        # Refresh list
        bpy.ops.mesh.scan_shapekey_vertices()
        self.report({"INFO"}, f"Applied values to {len(selected)} vertices")
        return {"FINISHED"}


class SKVERTED_OT_ClearSelection(bpy.types.Operator):
    """Clear all vertex selections"""
    bl_idname = "mesh.shapekey_clear_selection"
    bl_label = "Clear Selection"
    
    def execute(self, context):
        context.scene.shapekey_editor.selected_vertices = ""
        return {"FINISHED"}


class SKVERTED_OT_AddFromEditMode(bpy.types.Operator):
    """Add selected vertices from Edit Mode to selection"""
    bl_idname = "mesh.shapekey_add_from_edit_mode"
    bl_label = "Add from Edit Mode"
    
    def execute(self, context):
        props = context.scene.shapekey_editor
        obj = context.view_layer.objects.active
        
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "No active mesh object")
            return {"CANCELLED"}
        
        # Get current mode
        current_mode = obj.mode
        
        # Switch to object mode to read selection
        if current_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        
        # Get selected vertices
        selected_in_edit = [v.index for v in obj.data.vertices if v.select]
        
        if not selected_in_edit:
            if current_mode != "OBJECT":
                bpy.ops.object.mode_set(mode=current_mode)
            self.report({"WARNING"}, "No vertices selected in Edit Mode")
            return {"CANCELLED"}
        
        # Merge with existing selection
        current_selected = parse_selected_string(props.selected_vertices)
        current_selected.update(selected_in_edit)
        props.selected_vertices = join_selected_list(current_selected)
        
        # Switch back to original mode
        if current_mode != "OBJECT":
            bpy.ops.object.mode_set(mode=current_mode)
        
        self.report({"INFO"}, f"Added {len(selected_in_edit)} vertices from Edit Mode")
        return {"FINISHED"}


# ---------- UI / props ----------
class SKVertexItem(bpy.types.PropertyGroup):
    """Single vertex data in list"""
    index: bpy.props.IntProperty(name="Index")
    x: bpy.props.FloatProperty(name="X", precision=4)
    y: bpy.props.FloatProperty(name="Y", precision=4)
    z: bpy.props.FloatProperty(name="Z", precision=4)
    distance: bpy.props.FloatProperty(name="Distance", precision=4)


class SKVERTED_UL_VertexList(bpy.types.UIList):
    """List of vertices in shapekey"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        props = context.scene.shapekey_editor
        selected = parse_selected_string(props.selected_vertices)
        
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            
            # Selection indicator
            is_selected = item.index in selected
            row.label(text="✓" if is_selected else " ", icon="NONE")
            
            # Vertex info
            row.label(text=f"v{item.index}")
            row.label(text=f"Δ{item.distance:.4f}")
            row.label(text=f"({item.x:.3f}, {item.y:.3f}, {item.z:.3f})")
            
            # Click to select
            op = row.operator("mesh.select_shapekey_vertex", text="", icon="RESTRICT_SELECT_OFF")
            op.vertex_index = item.index


class ShapekeyEditorProps(bpy.types.PropertyGroup):
    """Main addon properties"""
    enabled: bpy.props.BoolProperty(name="Overlay", default=False, description="Toggle overlay visibility (enable when using, disable when done)")
    shapekey_name: bpy.props.StringProperty(name="Shapekey", default="")
    selected_vertices: bpy.props.StringProperty(name="Selected Vertices", default="")
    
    # Input values
    value_x: bpy.props.FloatProperty(name="X", default=0.0, precision=4)
    value_y: bpy.props.FloatProperty(name="Y", default=0.0, precision=4)
    value_z: bpy.props.FloatProperty(name="Z", default=0.0, precision=4)
    
    # Apply mode
    apply_mode: bpy.props.EnumProperty(
        name="Apply Mode",
        items=[
            ("ABSOLUTE", "Absolute", "Set to exact value"),
            ("OFFSET", "Offset", "Add offset to current value"),
        ],
        default="OFFSET"
    )
    
    # Influence
    influence: bpy.props.FloatProperty(
        name="Influence",
        default=1.0,
        min=0.0,
        max=1.0,
        precision=3
    )
    
    # Overlay optimization
    display_threshold: bpy.props.FloatProperty(
        name="Distance Filter",
        description="Minimum vertex movement to display (higher = fewer dots)",
        default=0.0001,
        min=0.0,
        max=1.0,
        precision=5
    )
    
    limit_display: bpy.props.BoolProperty(
        name="Limit Display",
        description="Limit number of vertices shown in overlay for performance",
        default=True
    )
    
    max_display_vertices: bpy.props.IntProperty(
        name="Max Display",
        description="Maximum vertices to show in overlay (largest movement first)",
        default=2000,
        min=100,
        max=50000
    )
    
    vertex_list: bpy.props.CollectionProperty(type=SKVertexItem)
    vertex_list_index: bpy.props.IntProperty(default=0)


class SKVERTED_PT_Tool(bpy.types.Panel):
    """Main UI panel"""
    bl_label = "Shapekey Vertex Editor"
    bl_idname = "SKVERTED_PT_Tool"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Shapekey"
    
    def draw(self, context):
        props = context.scene.shapekey_editor
        layout = self.layout
        obj = context.view_layer.objects.active
        
        # Overlay toggle
        layout.prop(props, "enabled")
        
        # Overlay optimization settings (collapsible)
        if props.enabled:
            opt_box = layout.box()
            opt_box.label(text="Overlay Settings:", icon="SETTINGS")
            opt_box.prop(props, "display_threshold")
            opt_box.prop(props, "limit_display")
            if props.limit_display:
                opt_box.prop(props, "max_display_vertices", slider=True)
        
        # Shapekey selection
        if obj and obj.type == "MESH" and obj.data.shape_keys:
            shapekeys = obj.data.shape_keys.key_blocks
            layout.prop_search(props, "shapekey_name", obj.data.shape_keys, "key_blocks")
            
            if props.shapekey_name and props.shapekey_name in shapekeys:
                shapekey = shapekeys[props.shapekey_name]
                layout.label(text=f"Influence: {shapekey.value:.3f}")
        else:
            layout.label(text="No active mesh with shapekeys", icon="INFO")
            return
        
        # Scan button
        layout.operator("mesh.scan_shapekey_vertices", icon="VIEWZOOM")
        
        # Add from edit mode button
        layout.operator("mesh.shapekey_add_from_edit_mode", icon="EDITMODE_HLT")
        
        # Vertex list
        box = layout.box()
        box.label(text="Modified Vertices:", icon="VERTEXSEL")
        if props.vertex_list:
            box.label(text=f"Total: {len(props.vertex_list)} vertices", icon="INFO")
        row = box.row()
        row.template_list(
            "SKVERTED_UL_VertexList", "", props, "vertex_list", 
            props, "vertex_list_index", rows=8
        )
        
        # Selection info
        selected_count = len(parse_selected_string(props.selected_vertices))
        layout.label(text=f"Selected: {selected_count} vertices", icon="OBJECT_DATA")
        
        if selected_count > 0:
            # Edit section
            edit_box = layout.box()
            edit_box.label(text="Edit Selected Vertices:", icon="TOOL_SETTINGS")
            
            # Apply mode
            edit_box.prop(props, "apply_mode", expand=True)
            
            # Value inputs
            col = edit_box.column(align=True)
            col.prop(props, "value_x")
            col.prop(props, "value_y")
            col.prop(props, "value_z")
            
            # Buttons
            row = edit_box.row(align=True)
            row.operator("mesh.shapekey_apply_values", icon="CHECKMARK")
            row.operator("mesh.shapekey_zero_out", text="Zero Out", icon="TRASH")
            
            # Clear selection
            edit_box.operator("mesh.shapekey_clear_selection", icon="X")


# ---------- register ----------
classes = (
    SKVertexItem,
    ShapekeyEditorProps,
    SKVERTED_UL_VertexList,
    SKVERTED_OT_Scan,
    SKVERTED_OT_SelectVertex,
    SKVERTED_OT_ZeroOut,
    SKVERTED_OT_ApplyValues,
    SKVERTED_OT_ClearSelection,
    SKVERTED_OT_AddFromEditMode,
    SKVERTED_PT_Tool,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.shapekey_editor = bpy.props.PointerProperty(type=ShapekeyEditorProps)
    
    global _draw_handler
    if _draw_handler is None:
        _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_overlay, (), "WINDOW", "POST_VIEW"
        )


def unregister():
    global _draw_handler
    if _draw_handler is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, "WINDOW")
        except:
            pass
        _draw_handler = None
    
    for c in reversed(classes):
        try:
            bpy.utils.unregister_class(c)
        except:
            pass
    
    if hasattr(bpy.types.Scene, "shapekey_editor"):
        try:
            del bpy.types.Scene.shapekey_editor
        except:
            pass


if __name__ == "__main__":
    # Unregister first for clean reload
    unregister()
    # Now register everything fresh
    register()
