"""
Emil's Mesh Toolkit - Modular Edition
Main registration file and shared overlay system

Author: Emil
Version: 2.5 (Modular)
"""

bl_info = {
    "name": "Emil's Mesh Toolkit",
    "author": "Emil",
    "version": (2, 5, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Emil",
    "description": "Collection of tools for shapekeys, weights, rigging, and selection",
    "category": "Mesh",
}

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

# Import modules
if "bpy" in locals():
    import importlib
    if "toolkit_common" in locals():
        importlib.reload(toolkit_common)
    if "mod_shapekeys" in locals():
        importlib.reload(mod_shapekeys)
    if "mod_weights" in locals():
        importlib.reload(mod_weights)
    if "mod_rigging" in locals():
        importlib.reload(mod_rigging)
    if "mod_selection" in locals():
        importlib.reload(mod_selection)

from . import toolkit_common
from . import mod_shapekeys
from . import mod_weights
from . import mod_rigging
from . import mod_selection


# ==================== PROPERTIES ====================

class EMESH_VertexItem(bpy.types.PropertyGroup):
    """Vertex data for shapekey editing"""
    index: bpy.props.IntProperty()
    x: bpy.props.FloatProperty()
    y: bpy.props.FloatProperty()
    z: bpy.props.FloatProperty()
    distance: bpy.props.FloatProperty()


class EMESH_CoordItem(bpy.types.PropertyGroup):
    """Simple 3D coordinate storage"""
    x: bpy.props.FloatProperty()
    y: bpy.props.FloatProperty()
    z: bpy.props.FloatProperty()


class EMESH_ToolkitProperties(bpy.types.PropertyGroup):
    """Main property group for all toolkit settings"""
    
    # Shapekey properties
    shapekey_name: bpy.props.StringProperty(name="Shapekey")
    vertex_list: bpy.props.CollectionProperty(type=EMESH_VertexItem)
    vertex_list_index: bpy.props.IntProperty()
    selected_vertices: bpy.props.StringProperty(default="")
    overlay_shapekey: bpy.props.BoolProperty(
        name="Show Overlay",
        default=False,
        description="Display shapekey vertex overlay"
    )
    display_threshold: bpy.props.FloatProperty(
        name="Distance Threshold",
        default=0.0001,
        min=0.0,
        max=1.0,
        precision=4,
        description="Minimum distance to show vertex"
    )
    limit_display: bpy.props.BoolProperty(
        name="Limit Display",
        default=True,
        description="Limit number of displayed vertices"
    )
    max_display_vertices: bpy.props.IntProperty(
        name="Max Vertices",
        default=2000,
        min=10,
        max=50000,
        description="Maximum vertices to display in overlay"
    )
    apply_mode: bpy.props.EnumProperty(
        name="Apply Mode",
        items=[
            ("OFFSET", "Offset", "Add values to current position"),
            ("ABSOLUTE", "Absolute", "Set exact position"),
        ],
        default="OFFSET"
    )
    value_x: bpy.props.FloatProperty(name="X", default=0.0, precision=4)
    value_y: bpy.props.FloatProperty(name="Y", default=0.0, precision=4)
    value_z: bpy.props.FloatProperty(name="Z", default=0.0, precision=4)
    
    # Weight properties
    overlay_weights: bpy.props.BoolProperty(
        name="Show Weight Overlay",
        default=False,
        description="Display over-limit vertices"
    )
    weight_limit: bpy.props.FloatProperty(
        name="Weight Limit",
        default=1.0,
        min=0.0,
        max=5.0,
        description="Maximum total weight per vertex"
    )
    weight_overlay_data: bpy.props.CollectionProperty(type=EMESH_CoordItem)


# ==================== OVERLAY DRAWING ====================

def draw_shapekey_overlay():
    """Draw overlay for shapekey vertex editor"""
    context = bpy.context
    props = context.scene.emesh_toolkit
    
    if not props.overlay_shapekey:
        return
    
    obj = toolkit_common.ToolkitUtils.get_active_mesh_obj(context)
    if not obj or not props.vertex_list:
        return
    
    try:
        selected = toolkit_common.ToolkitUtils.parse_vertex_indices(props.selected_vertices)
        
        # Build vertex data from props.vertex_list
        vertex_data = []
        for item in props.vertex_list:
            co_world = obj.matrix_world @ Vector((item.x, item.y, item.z))
            vertex_data.append({
                "index": item.index,
                "co": co_world,
                "distance": item.distance,
                "is_selected": item.index in selected
            })
        
        # Sort by distance and limit display
        vertex_data.sort(key=lambda v: v["distance"], reverse=True)
        
        if props.limit_display:
            vertex_data = vertex_data[:props.max_display_vertices]
        
        # Separate selected and unselected
        unselected_coords = []
        selected_coords = []
        
        for vd in vertex_data:
            coord = (vd["co"].x, vd["co"].y, vd["co"].z)
            if vd["is_selected"]:
                selected_coords.append(coord)
            else:
                unselected_coords.append(coord)
        
        # Draw unselected (gray)
        if unselected_coords:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            batch = batch_for_shader(shader, "POINTS", {"pos": unselected_coords})
            shader.bind()
            shader.uniform_float("color", (0.5, 0.5, 0.5, 0.8))
            gpu.state.point_size_set(6.0)
            batch.draw(shader)
        
        # Draw selected (yellow)
        if selected_coords:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            batch = batch_for_shader(shader, "POINTS", {"pos": selected_coords})
            shader.bind()
            shader.uniform_float("color", (1.0, 1.0, 0.0, 1.0))
            gpu.state.point_size_set(8.0)
            batch.draw(shader)
        
        gpu.state.point_size_set(1.0)
    except:
        pass


# ==================== MAIN PANEL ====================

class EMESH_PT_MainPanel(bpy.types.Panel):
    """Main toolkit panel"""
    bl_label = "Emil's Mesh Toolkit"
    bl_idname = "EMESH_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Emil"
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Modular Toolkit v2.5", icon="TOOL_SETTINGS")


# ==================== REGISTRATION ====================

classes = (
    EMESH_VertexItem,
    EMESH_CoordItem,
    EMESH_ToolkitProperties,
    EMESH_PT_MainPanel,
)

_draw_handler = None

def register():
    global _draw_handler
    
    # Register common utilities
    toolkit_common.register()
    
    # Register main classes
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register properties
    bpy.types.Scene.emesh_toolkit = bpy.props.PointerProperty(type=EMESH_ToolkitProperties)
    
    # Register modules
    mod_shapekeys.register()
    mod_weights.register()
    mod_rigging.register()
    mod_selection.register()
    
    # Register shapekey overlay
    _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
        draw_shapekey_overlay, (), "WINDOW", "POST_VIEW"
    )
    
    print("Emil's Mesh Toolkit (Modular) registered successfully")


def unregister():
    global _draw_handler
    
    # Unregister shapekey overlay
    if _draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, "WINDOW")
        _draw_handler = None
    
    # Unregister modules
    mod_selection.unregister()
    mod_rigging.unregister()
    mod_weights.unregister()
    mod_shapekeys.unregister()
    
    # Unregister properties
    del bpy.types.Scene.emesh_toolkit
    
    # Unregister main classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Unregister common utilities
    toolkit_common.unregister()
    
    print("Emil's Mesh Toolkit (Modular) unregistered")


if __name__ == "__main__":
    register()
