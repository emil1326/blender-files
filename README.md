# Emil's Mesh Toolkit - Modular Edition

Version 2.5 - A modular collection of Blender tools for mesh editing, shapekeys, weights, and rigging.

## Installation

1. Zip the entire `blender files` folder (or create a symlink/copy)
2. Install in Blender via Edit → Preferences → Add-ons → Install
3. Enable "Emil's Mesh Toolkit"
4. Find it in the 3D View sidebar under "Emil" tab

## Module Structure

The toolkit is now organized into independent, class-based modules:

### Core Files

- **`__init__.py`** - Package initializer for Blender add-on system
- **`toolkit_main.py`** - Main registration file, manages all modules and overlays
- **`toolkit_common.py`** - Shared utilities and base classes (no code duplication!)

### Tool Modules

- **`mod_shapekeys.py`** - Shapekey operations
  - Delete useless shapekeys (numpy-based comparison)
  - Vertex editor with overlay visualization
  - Select/modify individual vertices in shapekeys
  
- **`mod_weights.py`** - Weight tools
  - Check for over-limit vertex weights
  - Red overlay for problematic vertices
  
- **`mod_rigging.py`** - Rigging tools
  - Snap vertices to their most influential bone's root
  
- **`mod_selection.py`** - Advanced selection
  - Select sibling objects (by bone parent or object parent)

## Features

### Shared Utilities (toolkit_common.py)

**ToolkitUtils** - Static utility class:
- `parse_vertex_indices()` - Parse comma-separated vertex lists
- `join_vertex_indices()` - Convert sets to strings
- `get_active_mesh_obj()` - Get active mesh safely
- `set_mode()` - Switch object/edit mode
- `select_vertex_in_edit_mode()` - Edit mode vertex selection

**ToolkitOperator** - Base operator class:
- `report_info()`, `report_warning()`, `report_error()` - Consistent messaging

**ToolkitPanel** - Base panel class:
- Pre-configured for View3D sidebar

### Shapekey Vertex Editor

- **Scan shapekeys** to find modified vertices (distance threshold filter)
- **Visual overlay** with gray (unselected) and yellow (selected) dots
- **Performance optimized**: Handles 93k vertex meshes, displays top 2000 by movement distance
- **Edit modes**:
  - Click vertices in list to select
  - Add from Edit Mode selection
  - Apply offset or absolute values (X, Y, Z)
  - Zero-out selected vertices

### Weight Limit Checker

- Set maximum total weight per vertex
- Scan mesh for violations
- Red overlay shows over-limit vertices
- Select all violations for easy fixing

### Rigging Tools

- Snap selected vertices to their most influential bone's head position
- Works with armature modifiers
- Respects vertex group weights

### Selection Tools

- Select all sibling objects sharing the same parent
- Supports both object parents and bone parents
- Useful for batch operations on related objects

## Architecture

Each module:
- Imports from `toolkit_common` for shared functionality
- Defines its own operators, panels, and properties
- Registers/unregisters independently
- No code duplication across modules

Main toolkit handles:
- Property storage (Scene.emesh_toolkit)
- Global overlay rendering
- Module registration orchestration

## Performance Notes

- Shapekey overlay uses display limits (default 2000 vertices)
- Sorts vertices by movement distance (shows largest changes first)
- Distance threshold filter removes micro-movements
- Weight overlay uses evaluated mesh for accuracy

## Usage Tips

1. **Shapekey editing**: Scan first, then select vertices individually or from Edit Mode
2. **Weight checking**: Set limit, scan, then select violations to fix in weight paint
3. **Rigging**: Select vertices in Edit Mode, run snap operator
4. **Selection**: Select parent object, run "Select Deep" to grab siblings

## Original Scripts

This modular version combines and improves:
- `deleteUselessShapekeys.py`
- `highlight4.py` (weight checker)
- `selectDeep.py` (sibling selection)
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
