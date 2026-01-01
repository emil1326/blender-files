# Emil's Mesh Toolkit - Changelog

## Version 2.5.4 - Auto-Selection, Weight Normalization & Reactive Updates

### Major Features
- **Auto-Shapekey Selection**: Automatically selects shapekeys when switching objects
  - Tries to find shapekey with same name as previously selected
  - Falls back to first non-Basis shapekey if not found
  - Lock button (🔒) prevents auto-selection when needed
  - Auto-rescans vertex list when switching objects

- **Weight Normalization**: New buttons for normalizing vertex weights
  - "Normalize All" - Normalizes weights for all vertices
  - "Selected" - Normalizes weights for selected vertices only
  - Only affects deform groups (respects armature setup)
  - Maintains influence ratios while ensuring weights sum to 1.0

- **Reactive Overlays**: Overlays update automatically on property changes
  - Changing Weight Limit automatically rescans and updates overlay
  - Changing Max Groups automatically rescans and updates overlay
  - Shapekey dropdown selection triggers automatic rescan
  - All three operators (scan, zero, apply) trigger overlay updates for smooth feedback

- **Lock Option**: Prevents unwanted automatic shapekey selection
  - Toggle button next to shapekey dropdown shows lock state
  - Locked (🔒) = no auto-selection on object change
  - Unlocked (🔓) = auto-selection enabled

### Bug Fixes
- Fixed duplicate `overlay_weights` property in toolkit_main.py
- All version numbers aligned to 2.5.4

### Technical Improvements
- Added `scene_update_handler` for monitoring object selection changes
- Added `EMESH_OT_AutoSelectShapekey` operator for intelligent shapekey selection
- Added `EMESH_OT_NormalizeWeights` operator with selected_only parameter
- Added update callbacks to properties for reactive behavior
- Proper handler registration/unregistration in register/unregister functions

---

## Version 2.5.3 - UI Organization & Bug Fixes

### Major Changes
- **UI Reorganization**: Complete redesign of all panel layouts with clear visual hierarchy
  - Shapekeys panel: Separate sections for Cleanup, Vertex Editor, Overlay Settings, and Edit Controls
  - Weights panel: Clear distinction between Weight Limit and Vertex Group sections
  - Selection panel: Parent information and selection modes organized logically
  - Rigging panel: Object info and snap-to-bone settings in separate boxes

- **Bug Fixes**:
  - Fixed shapekey active index access: Changed `obj.data.shape_keys.active_index` to `obj.active_shape_key_index`
  - This was causing AttributeError on non-existent attribute on Key object

- **Version Tracking**: Updated all version numbers to 2.5.3

### UI Improvements

#### Shapekey Tools Panel
```
📦 Cleanup
  - Delete Useless Shapekeys button

📊 Vertex Editor
  - Shapekey Selection (search + lock button)
  - Overlay Toggle + Settings (collapsible)
    - Display Threshold slider
    - Limit Display checkbox
    - Max Display Vertices
  - Scan & Select buttons
  - Vertex List display
  - Edit Controls (only visible when vertices selected)
    - Mode selection (Offset/Absolute)
    - X, Y, Z value inputs
    - Apply & Zero buttons
    - Clear Selection button
```

#### Weight Tools Panel
```
⚖️ Weight Limit Checker
  - Limit slider + Overlay toggle
  - Scan button
  - Normalize All / Normalize Selected buttons
  - Results display (if vertices found)
  - Select Over-Limit button

🔗 Vertex Group Counter
  - Max Groups slider + Overlay toggle
  - Scan button
  - Results display (if vertices found)
  - Select Over-Group button
```

#### Selection Tools Panel
```
ℹ️ Parent Information
  - Shows armature/parent object
  - Shows bone name
  - Shows "No parent" if not assigned

🔀 Select Relatives
  - Siblings (same parent)
  - Children (recursive)
  - Parents (up the chain)
  - Full Hierarchy (entire family tree)
```

#### Rigging Tools Panel
```
ℹ️ Object Information
  - Armature name
  - Active shapekey (if in shapekey mode)
  - Error if no armature found

📌 Snap Vertices to Bone Root
  - Settings explanation
  - Interpolation Options (1-4 bone buttons)
```

### Technical Details

#### Fixed Attributes
- `shapekey.active_index` → `obj.active_shape_key_index`
  - Proper Blender API access for active shapekey index
  - Prevents AttributeError on Key data block

#### UI Organization Principles
1. **Separation of Concerns**: Each tool type in separate box
2. **Visual Hierarchy**: Headers with icons for clarity
3. **Progressive Disclosure**: Settings only visible when relevant
4. **Compact Buttons**: Grouped related actions in rows
5. **Information First**: Show state before action options

### Files Modified
- `toolkit_main.py`: Version bump 2.5.0 → 2.5.3
- `mod_shapekeys.py`: Complete UI reorganization
- `mod_weights.py`: Clearer section separation
- `mod_selection.py`: Better organization with info box
- `mod_rigging.py`: Improved layout with separate sections

### Testing Checklist
- [ ] Shapekey panel displays correctly with all sections
- [ ] Vertex list shows properly when scanned
- [ ] Edit controls only visible when vertices selected
- [ ] Weight overlays toggle independently
- [ ] Vertex group counter works correctly
- [ ] Selection operators work for all 4 modes
- [ ] Rigging buttons (1-4) appear and function
- [ ] No AttributeError on active shapekey access
- [ ] Overlay updates are smooth and responsive

### Known Limitations
- View layer objects filtering prevents crash on cross-layer selections
- Overlay reactivity depends on manual scan operations
- UI improvements do not affect addon functionality, only presentation

### Future Improvements
- Add status indicator showing current mode/selection
- Implement collapsible sections for very long panels
- Add keyboard shortcuts for frequent operations
- Implement undo/redo panel for recent operations
