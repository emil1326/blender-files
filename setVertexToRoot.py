import bpy

print("Script Start")

# Get the active object
obj = bpy.context.active_object

# Check if the active object is a mesh and has an armature parent
if obj and obj.type == 'MESH' and obj.parent and obj.parent.type == 'ARMATURE':
    # Get the mesh data
    mesh = obj.data
    
    # Get the armature object
    armature = obj.parent
    
    print("Active Mesh Vertices:", len(mesh.vertices))
    print("Armature:", armature)
    
    # Iterate through selected vertices
    for v in mesh.vertices:
        if v.select:
            print("Selected Vertex:", v.index)
            
            # Check if the vertex has any vertex groups
            if v.groups:
                # Initialize variables for max weight and corresponding bone
                max_weight = 0.0
                max_bone = None
                
                # Iterate through vertex groups
                for group in v.groups:
                    group_index = group.group
                    if group_index < len(armature.vertex_groups):
                        weight = group.weight
                        bone_name = armature.vertex_groups[group_index].name
                        bone = armature.pose.bones.get(bone_name)
                        if bone:
                            print("Bone:", bone_name, "Weight:", weight)
                            if weight > max_weight:
                                max_weight = weight
                                max_bone = bone
                
                # Set vertex position to the head (root) position of the bone with max influence
                if max_bone:
                    start_position = v.co
                    end_position = armature.matrix_world @ max_bone.head
                    print("Start Position:", start_position)
                    print("End Position:", end_position)
                    v.co = end_position
                    print("Translated Position:", v.co)
                else:
                    print("No valid bone found with influence on vertex.")
            else:
                print("Vertex has no vertex groups assigned.")
    print("Selected vertex positions adjusted based on bone weights.")
    print("Script End")
else:
    print("Error: Active object is not a mesh with an armature parent.")
