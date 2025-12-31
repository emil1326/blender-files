bl_info = {
    "name": "Select Siblings",
    "author": "Stanislav Blinov",
    "version": (1, 0, 0),
    "blender": (2, 74, 0),
    "description": "Select siblings in object mode (respecting distinct bone parents)",
    "category": "Object",
}

import bpy


class OBJECT_OT_select_siblings_deep(bpy.types.Operator):
    bl_idname = "object.select_siblings_deep"
    bl_label = "Select Siblings (Deep)"
    bl_options = {"REGISTER", "UNDO"}

    extend = bpy.props.BoolProperty(
        name="Extend",
        description="Extend selection instead of deselecting everything first",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and context.object

    def execute(self, context):
        ao = context.object
        if not self.extend:
            bpy.ops.object.select_all(action="DESELECT")
            ao.select = True
        for o in context.selectable_objects:
            if o.parent == ao.parent:
                if (o.parent_type != "BONE") or (o.parent_bone == ao.parent_bone):
                    o.select = True
        return {"FINISHED"}


def register():
    bpy.utils.register_class(OBJECT_OT_select_siblings_deep)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_select_siblings_deep)


# no work
