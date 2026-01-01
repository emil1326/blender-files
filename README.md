# Emil's Mesh Toolkit - Modular Edition

**Version 2.5.4** - A modular collection of Blender tools for mesh editing, shapekeys, weights, and rigging.

Designed for precise vertex-level editing with automatic updates, intelligent object switching, and comprehensive weight management.

## Installation

1. Zip the entire `blender files` folder (or create a symlink/copy)
2. Install in Blender via Edit → Preferences → Add-ons → Install
3. Enable "Emil's Mesh Toolkit"
4. Find it in the 3D View sidebar under "Emil" tab

## What's New in 2.5.4

✨ **Auto-Shapekey Selection** - Automatically finds shapekeys by name when switching objects  
✨ **Weight Normalization** - Normalize weights for all or selected vertices  
✨ **Reactive Overlays** - Overlays update instantly when changing parameters  
🔒 **Lock Option** - Prevent auto-selection when you want to keep focus on specific shapekeys  

## Module Structure

The toolkit is organized into independent, class-based modules with zero code duplication:

### Core Files

- **`__init__.py`** - Package initializer for Blender add-on system
- **`toolkit_main.py`** - Main registration, overlay handlers, scene monitoring
- **`toolkit_common.py`** - Shared utilities and base classes

### Tool Modules

- **`mod_shapekeys.py`** - Shapekey operations
  - Delete useless shapekeys
  - Vertex editor with real-time overlay visualization
  - Auto-select shapekeys by name when switching objects
  - Lock option to prevent auto-selection
  
- **`mod_weights.py`** - Weight tools
  - Check for over-limit vertex weights
  - Count vertex group assignments
  - Normalize weights (all or selected)
  - Color-coded overlays (red for over-limit, orange for over-group)
  
- **`mod_rigging.py`** - Rigging tools
  - Snap vertices to bone roots with 1-4 bone interpolation
  - Weighted averaging for smooth blending
  
- **`mod_selection.py`** - Advanced selection
  - Select siblings by bone or object parent
  - Recursive children selection
  - Select parents up the chain
  - Full hierarchy selection

## Features

### Smart Object Switching

- **Auto-Shapekey Selection**: When you change objects, the toolkit automatically:
  1. Tries to find a shapekey with the same name
  2. Falls back to the first non-Basis shapekey
  3. Auto-rescans the vertex list
  
- **Lock Button** (🔒/🔓): Prevents automatic selection when you want to focus on a specific shapekey

### Shapekey Vertex Editor

- **Scan shapekeys** to find modified vertices (distance threshold filter)
- **Visual overlay** with color-coded points (gray/yellow)
- **Performance optimized**: 93k vertex meshes, displays top 5000 by movement distance
- **Edit modes**:
  - Click vertices in list to toggle selection
  - Add vertices from Edit Mode selection
  - Apply offset or absolute values (X, Y, Z)
  - Zero-out selected vertices
  - Instant overlay updates on every action

### Weight Tools

- **Weight Limit Checker**:
  - Set maximum total weight per vertex (default 1.0)
  - Scan mesh for violations
  - Red overlay shows problematic vertices
  - Select all violations at once
  - **Normalize All**: Rescales weights for all vertices to sum to 1.0
  - **Normalize Selected**: Normalize weights only for selected vertices

- **Vertex Group Counter**:
  - Set max group assignments (default 4 for Unity compatibility)
  - Scan mesh for violations
  - Orange overlay shows vertices with too many deform groups
  - Auto-updates when you change the limit slider

### Rigging Tools

- **Snap to Bone Root**:
  - Snap selected vertices to their most influential bone's head position
  - Multi-bone interpolation (1-4 bones)
  - 1 bone = snap to single bone
  - 2+ bones = weighted average of top bones
  - Works with vertex groups

### Selection Tools

- **Siblings** - Select all objects sharing the same parent (bone or object)
- **Children** - Recursively select all child objects
- **Parents** - Select all parents up the hierarchy chain
- **Full Hierarchy** - Select entire family tree (parents + children + siblings)

## Shared Utilities (toolkit_common.py)

**ToolkitUtils** - Static utility class:
- `parse_vertex_indices()` - Parse comma-separated vertex lists
- `join_vertex_indices()` - Convert sets to strings
- `get_active_mesh_obj()` - Get active mesh safely
- `set_mode()` - Switch object/edit mode
- `select_vertex_in_edit_mode()` - Edit mode vertex selection

**ToolkitOperator** - Base operator class with standard methods:
- `report_info()`, `report_warning()`, `report_error()` - Consistent user feedback

**ToolkitPanel** - Base panel class:
- Pre-configured for View3D sidebar with consistent layout

## Architecture

### Module Organization

Each tool module is completely independent:
- Imports from `toolkit_common` for shared functionality
- Defines its own operators, panels, and properties
- Registers/unregisters independently
- No code duplication across modules

**Main toolkit (`toolkit_main.py`) handles:**
- Property storage (Scene.emesh_toolkit)
- Global overlay rendering (GPU-based)
- Module registration orchestration
- Scene update monitoring for auto-selection
- Callback system for reactive property updates

### Reactive System

Properties automatically trigger scans when changed:
- `weight_limit` slider → rescans weights
- `max_bone_groups` → rescans groups
- `shapekey_name` dropdown → rescans vertices
- All editing operations → update overlays instantly

## Performance Notes

- Shapekey overlay: Handles 93k vertex meshes with 5000 vertex display limit
- Vertex sorting: By movement distance (shows largest changes first)
- Distance threshold: Filters micro-movements (0.0001 default)
- Weight overlay: Uses evaluated mesh for accuracy
- View layer filtering: Prevents crashes when selecting across layers

## Usage Workflow

### Shapekey Editing

1. Select mesh with shapekeys
2. Lock shapekey selection if needed (🔒)
3. Shapekey auto-selects by name (or first available)
4. Scan to populate vertex list
5. Click vertices or select in Edit Mode
6. Apply offset/absolute values or zero-out
7. Overlay updates in real-time

### Weight Management

1. Set weight limit (default 1.0 for normalized)
2. Scan to find violations
3. Click "Normalize All" to fix all vertices
4. Or select specific vertices and click "Selected"
5. Red overlay shows remaining problems

### Rigging with Snap-to-Root

1. Select armature modifier is required
2. Enter Edit Mode, select target vertices
3. Choose bone blend mode (1-4)
4. Snap vertices to bone root
5. Works with current shapekey

## Known Limitations

- Snap-to-root requires armature modifier on active object
- Weight normalization only affects deform groups
- Auto-shapekey selection respects lock setting
- Overlays disabled by default (toggle in UI)

## Credits

Version 2.5.4: Auto-selection, normalization, reactive updates  
Built on modular foundation combining and improving:
- Original `deleteUselessShapekeys.py`
- `highlight4.py` (weight checking)
- `selectDeep.py` (relationship selection)
- `setVertexToRoot.py` (rigging)
- Plus new features for workflow improvement
- `setVertexToRoot.py` (vertex snapping)
- `shapekey_vertex_editor.py` (custom tool)

## Changes from v2.0

- **Modular architecture**: Separated into independent modules
- **No code duplication**: Shared utilities in toolkit_common.py
- **Class-based design**: Base classes for operators and panels
- **Better organization**: Each tool in its own file
- **Maintainability**: Easy to add new modules or disable existing ones
- **Import system**: Proper Python package structure with reload support
- **Generic branding**: No project-specific naming, just "Emil's Mesh Toolkit"

## Future Enhancements

Potential additions:
- UV tools module
- Mesh cleanup module
- Animation tools module
- Per-module enable/disable in preferences

Each module can be independently developed without affecting others!
