bl_info = {
    "name": "Vertex Weight Limit Checker + Overlay",
    "author": "Emil",
    "version": (1, 2),
    "blender": (3, 6, 0),
    "description": "Find and highlight vertices exceeding weight-group limit (fixed storage + overlay)",
    "category": "Mesh",
}

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

_draw_handler = None


# ---------- utils ----------
def get_overlimit_vertices(obj, limit):
    if obj.type != "MESH" or not obj.vertex_groups:
        return []

    # Helper: collect names of deform bones from any Armature modifier on the object
    deform_group_names = set()
    for mod in obj.modifiers:
        if mod.type == "ARMATURE" and mod.object and mod.object.type == "ARMATURE":
            for bone in mod.object.data.bones:
                if bone.use_deform:
                    deform_group_names.add(bone.name)

    use_deform_filter = len(deform_group_names) > 0

    res = []
    for v in obj.data.vertices:
        # count groups with nonzero weight assigned to that vertex
        # v.groups is a sequence of VertexGroupElement with .group and .weight
        count = 0
        for g in v.groups:
            try:
                if g.weight == 0:
                    continue
                # get the vertex group's name (guard against index errors)
                group_name = None
                if 0 <= g.group < len(obj.vertex_groups):
                    group_name = obj.vertex_groups[g.group].name

                # if an armature exists we only count groups that match deform bones
                if not use_deform_filter or (
                    group_name and group_name in deform_group_names
                ):
                    count += 1
            except Exception:
                # defensive: if group element shape unexpected, count it
                count += 1
        if count > limit:
            res.append(v.index)
    return res


def parse_vertices_string(s):
    if not s:
        return []
    # guard against spaces
    parts = [p for p in s.split(",") if p.strip() != ""]
    try:
        return [int(p) for p in parts]
    except Exception:
        return []


def join_vertices_list(lst):
    return ",".join(str(int(i)) for i in lst)


# ---------- draw ----------
def draw_overlay():
    scn = bpy.context.scene
    wm = scn.weight_tool
    # Skip if overlay disabled - use this to control visibility
    if not wm.enabled:
        return
    # Skip if no results to display
    if not wm.results:
        return
    shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
    gpu.state.blend_set("ALPHA")
    # for every result entry
    for r in wm.results:
        obj = bpy.data.objects.get(r.obj, None)
        if not obj or obj.type != "MESH":
            continue
        vids = parse_vertices_string(r.vertices)
        if not vids:
            continue
        coords = []
        mat = obj.matrix_world
        # build world-space coords
        for vid in vids:
            if vid < 0 or vid >= len(obj.data.vertices):
                continue
            coords.append(mat @ obj.data.vertices[vid].co)
        if not coords:
            continue
        batch = batch_for_shader(shader, "POINTS", {"pos": coords})
        shader.bind()
        shader.uniform_float("color", (1.0, 0.2, 0.2, 1.0))
        gpu.state.point_size_set(8)
        batch.draw(shader)
    gpu.state.blend_set("NONE")


# ---------- operators ----------
class VWEIGHT_OT_Scan(bpy.types.Operator):
    bl_idname = "mesh.scan_weight_limit"
    bl_label = "Scan Mesh"
    bl_description = "Find vertices with weights exceeding limit"

    def execute(self, context):
        wm = context.scene.weight_tool
        wm.results.clear()
        limit = wm.max_weights
        # scan selected objects
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            indices = get_overlimit_vertices(obj, limit)
            if indices:
                item = wm.results.add()
                item.obj = obj.name
                item.vertices = join_vertices_list(indices)
        # ensure index valid
        if wm.results and wm.results_index >= len(wm.results):
            wm.results_index = len(wm.results) - 1
        elif not wm.results:
            wm.results_index = 0
        return {"FINISHED"}


class VWEIGHT_OT_Select(bpy.types.Operator):
    bl_idname = "mesh.select_weight_problem_vert"
    bl_label = "Select Vertex"

    index: bpy.props.IntProperty()
    obj: bpy.props.StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.obj)
        if obj is None:
            self.report({"WARNING"}, "Object not found")
            return {"CANCELLED"}

        # ensure we're in object mode and have active view layer object set properly
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except Exception:
            pass

        # deselect all then select the target
        for o in context.view_layer.objects:
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # ensure vertex index is valid
        if self.index < 0 or self.index >= len(obj.data.vertices):
            self.report({"WARNING"}, "Vertex index out of range")
            return {"CANCELLED"}

        # select the vertex in edit mode
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        obj.data.vertices[self.index].select = True
        bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}


# ---------- UI / props ----------
class VWeightResult(bpy.types.PropertyGroup):
    obj: bpy.props.StringProperty()  # object name
    vertices: bpy.props.StringProperty()  # comma-separated vertex indices


class VWEIGHT_UL_results(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            row.label(text=item.obj)
            vids = parse_vertices_string(item.vertices)
            row.label(text=f"{len(vids)} verts")
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="")


class VWEIGHT_PT_Tool(bpy.types.Panel):
    bl_label = "Weight Limit Checker"
    bl_idname = "VWEIGHT_PT_Tool"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Weights"

    def draw(self, context):
        wm = context.scene.weight_tool
        layout = self.layout
        layout.prop(wm, "enabled")
        layout.prop(wm, "max_weights")
        layout.operator("mesh.scan_weight_limit", icon="VIEWZOOM")

        box = layout.box()
        box.label(text="Vertices over limit:")
        row = box.row()
        row.template_list(
            "VWEIGHT_UL_results", "", wm, "results", wm, "results_index", rows=6
        )

        # show details for selected result
        if wm.results:
            idx = wm.results_index
            if idx >= 0 and idx < len(wm.results):
                r = wm.results[idx]
                vids = parse_vertices_string(r.vertices)
                if vids:
                    subbox = box.box()
                    subbox.label(text=f"Object: {r.obj} — {len(vids)} verts")
                    for vid in vids:
                        rrow = subbox.row(align=True)
                        rrow.label(text=f"v{vid}")
                        op = rrow.operator("mesh.select_weight_problem_vert", text="Go")
                        op.obj = r.obj
                        op.index = vid


class VWeightSettings(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="Overlay", default=True)
    max_weights: bpy.props.IntProperty(name="Max Allowed", default=4, min=1)
    results: bpy.props.CollectionProperty(type=VWeightResult)
    results_index: bpy.props.IntProperty(name="Results Index", default=0)


# ---------- register ----------
classes = (
    VWeightResult,
    VWeightSettings,
    VWEIGHT_UL_results,
    VWEIGHT_OT_Scan,
    VWEIGHT_OT_Select,
    VWEIGHT_PT_Tool,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.weight_tool = bpy.props.PointerProperty(type=VWeightSettings)
    global _draw_handler
    if _draw_handler is None:
        _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_overlay, (), "WINDOW", "POST_VIEW"
        )


def unregister():
    global _draw_handler
    if _draw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, "WINDOW")
        _draw_handler = None
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.weight_tool


if __name__ == "__main__":
    register()
