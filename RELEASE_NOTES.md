# Emil's Mesh Toolkit - Version 2.5.4 Release Notes

## 🎉 Release Status: READY FOR PRODUCTION

**Release Date**: December 31, 2025  
**Version**: 2.5.4  
**Blender Compatibility**: 3.6.0+

---

## ✅ Quality Assurance Summary

### Code Review Status
- ✅ **Syntax Check**: All 6 modules (PASSED)
- ✅ **Import Verification**: All dependencies correctly structured
- ✅ **Property Registration**: All properties properly defined and registered
- ✅ **Operator Registration**: All 28+ operators in correct class tuples
- ✅ **Handler Management**: Scene update handler properly registered/unregistered
- ✅ **Duplicate Check**: No duplicate property definitions (fixed in this release)
- ✅ **Version Alignment**: All files at 2.5.4

### Files Verified

| File | Status | Operators | Classes | Issues |
|------|--------|-----------|---------|--------|
| `toolkit_main.py` | ✅ PASS | 0 | 4 | FIXED: Duplicate overlay_weights |
| `mod_shapekeys.py` | ✅ PASS | 8 | 12 | None |
| `mod_weights.py` | ✅ PASS | 5 | 6 | None |
| `mod_rigging.py` | ✅ PASS | 1 | 2 | None |
| `mod_selection.py` | ✅ PASS | 1 | 2 | None |
| `toolkit_common.py` | ✅ PASS | 3 base classes | 3 | None |

---

## 🆕 New Features in 2.5.4

### 1. Auto-Shapekey Selection
**Intelligent shapekey management when switching objects**

- Automatically selects shapekey with same name on new object
- Falls back to first non-Basis shapekey if name not found
- Auto-rescans vertex list immediately
- Scene update handler monitors object changes (`depsgraph_update_post`)

**Lock Option**:
- Toggle button (🔒/🔓) prevents unwanted auto-selection
- Useful when you want to stay focused on a specific shapekey
- Property: `lock_shapekey_selection`

**Implementation**:
```python
class EMESH_OT_AutoSelectShapekey(ToolkitOperator):
    # Handles intelligent shapekey matching and selection
```

### 2. Weight Normalization
**Normalize vertex weights to sum to 1.0**

Two variants:
- **Normalize All** - Process entire mesh
- **Normalize Selected** - Process only selected vertices

Features:
- Only affects deform groups (respects armature bone structure)
- Maintains influence ratios while normalizing
- Fully undoable (REGISTER, UNDO)
- Works with any deform setup

**Implementation**:
```python
class EMESH_OT_NormalizeWeights(ToolkitOperator):
    selected_only: bpy.props.BoolProperty()
    # Scales deform groups proportionally to sum = 1.0
```

### 3. Reactive Overlays
**Automatic overlay updates when parameters change**

Updates triggered by:
- Weight limit slider changes → Auto-rescan weights
- Max groups changes → Auto-rescan groups
- Shapekey selection → Auto-scan vertices
- Edit operations (zero, apply) → Overlay updates

**Implementation**:
```python
def update_weight_limit(self, context):
    bpy.ops.mesh.emesh_scan_weights()

def update_max_bone_groups(self, context):
    bpy.ops.mesh.emesh_scan_vertex_groups()

def update_shapekey_selection(self, context):
    bpy.ops.mesh.emesh_scan_shapekey()
```

---

## 🔧 Bug Fixes in 2.5.4

| Bug | Severity | Status | Fix |
|-----|----------|--------|-----|
| Duplicate `overlay_weights` property | CRITICAL | ✅ FIXED | Removed first definition, kept better description |
| Version mismatch (2.5.3 in main) | HIGH | ✅ FIXED | Updated toolkit_main.py to 2.5.4 |

---

## 📊 Complete Feature Matrix

### Shapekey Tools
- [x] Delete useless shapekeys
- [x] Scan and detect modified vertices
- [x] Visual overlay (gray/yellow points)
- [x] Select individual vertices
- [x] Add vertices from Edit Mode selection
- [x] Apply offset or absolute values (X, Y, Z)
- [x] Zero-out selected vertices
- [x] Auto-shapekey selection with lock option
- [x] Real-time overlay updates

### Weight Tools
- [x] Weight limit checker with red overlay
- [x] Vertex group counter with orange overlay
- [x] Normalize all vertices
- [x] Normalize selected vertices only
- [x] Auto-update on limit/group changes
- [x] Select violations for batch fixing

### Rigging Tools
- [x] Snap to bone root
- [x] 1-4 bone interpolation
- [x] Weighted averaging
- [x] Shapekey mode detection
- [x] Works with armature modifiers

### Selection Tools
- [x] Select siblings (by parent)
- [x] Select children (recursive)
- [x] Select parents (up chain)
- [x] Select full hierarchy
- [x] View layer filtering

### Performance Features
- [x] 93k vertex handling
- [x] 5000 vertex display limit
- [x] Distance-based sorting
- [x] GPU-accelerated overlays
- [x] Efficient deform-only filtering

---

## 📦 File Structure

```
blender files/
├── __init__.py              # Package initializer (v2.5.4)
├── toolkit_main.py          # Main registration, properties (v2.5.4)
├── toolkit_common.py        # Shared utilities, base classes
├── mod_shapekeys.py         # Shapekey operations + auto-selection
├── mod_weights.py           # Weight checking + normalization
├── mod_rigging.py           # Snap to bone root
├── mod_selection.py         # Deep selection (4 modes)
├── README.md                # User documentation (updated)
├── CHANGELOG.md             # Version history (updated)
└── RELEASE_NOTES.md         # This file
```

---

## 🚀 Installation & Activation

### Install
1. Zip the `blender files` folder
2. Edit → Preferences → Add-ons → Install
3. Search "Emil's Mesh Toolkit"
4. Enable the add-on

### Access
- Open 3D View sidebar (press N)
- Find "Emil" tab
- Expand each category to access tools

---

## 📋 Testing Checklist

- [x] All operators register without errors
- [x] Shapekey editor scans and displays vertices
- [x] Auto-shapekey selection works on object switch
- [x] Lock button prevents auto-selection
- [x] Weight limit scanner detects violations
- [x] Weight normalization rescales properly
- [x] Vertex group counter works
- [x] Snap to bone interpolation with 1-4 bones
- [x] Selection operators work for all 4 modes
- [x] Overlays render correctly and update reactively
- [x] UI organizes cleanly with proper sections
- [x] No duplicate properties
- [x] All version numbers aligned (2.5.4)
- [x] Scene handlers register/unregister properly

---

## 🔍 Known Limitations

- Snap-to-root requires armature modifier (checked via operator.poll)
- Weight normalization only affects deform groups (by design)
- View layer filtering may skip objects in hidden collections
- Overlay reactivity depends on property update callbacks (not keyboard-driven)

---

## 📞 Support

For issues or feature requests, refer to:
- CHANGELOG.md - Version history
- README.md - Feature documentation
- Code comments - Implementation details

---

## 📈 Version History Summary

| Version | Focus | Status |
|---------|-------|--------|
| 2.5.4 | Auto-Selection, Normalization, Reactive Updates | ✅ CURRENT |
| 2.5.3 | UI Reorganization & Bug Fixes | Archived |
| 2.5.0 | Modular Architecture | Archived |

---

**Emil's Mesh Toolkit v2.5.4 is ready for production use.**

All quality checks passed. No critical issues remaining.
