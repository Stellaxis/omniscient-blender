import bpy


def is_blender_4():
    from bpy.app import version
    return version >= (4, 0, 0)


def create_projection_shader_group():
    node_group_name = "CameraProjector_Omni"
    if node_group_name in bpy.data.node_groups:
        return bpy.data.node_groups[node_group_name]

    node_group = bpy.data.node_groups.new(name=node_group_name, type='ShaderNodeTree')

    def create_node_in_group(node_tree, node_type, name, location, **kwargs):
        node = node_tree.nodes.new(type=node_type)
        node.name = name
        node.location = location
        for attr, value in kwargs.items():
            setattr(node, attr, value)
        return node

    group_input_node = create_node_in_group(node_group,
                                            "NodeGroupInput",
                                            "Group Input",
                                            (-1060.0, 40.0))
    group_output_node = create_node_in_group(node_group,
                                             "NodeGroupOutput",
                                             "Group Output",
                                             (720.0, -20.0),
                                             is_active_output=True)

    if is_blender_4():
        node_group.interface.new_socket(name="Vector Input", in_out='INPUT')
        node_group.interface.new_socket(name="Vector Output", in_out='OUTPUT')
        focal_length_socket = node_group.interface.new_socket(name="Focal Length",
                                                              in_out='INPUT',
                                                              socket_type='NodeSocketFloat')
        sensor_size_socket = node_group.interface.new_socket(name="Sensor Size",
                                                             in_out='INPUT',
                                                             socket_type='NodeSocketFloat')
    else:
        node_group.inputs.new(name="Vector Input", type='NodeSocketVector')
        node_group.outputs.new(name="Vector Output", type='NodeSocketVector')
        focal_length_socket = node_group.inputs.new(name="Focal Length", type='NodeSocketFloat')
        sensor_size_socket = node_group.inputs.new(name="Sensor Size", type='NodeSocketFloat')

    separate_xyz_node = create_node_in_group(node_group, "ShaderNodeSeparateXYZ", "Separate XYZ", (-860.0, 100.0))
    combine_xyz_node = create_node_in_group(node_group, "ShaderNodeCombineXYZ", "Combine XYZ", (-40.0, 0.0))
    combine_xyz_node.inputs['Z'].default_value = 1.0

    x_res_node = create_node_in_group(node_group,
                                      "ShaderNodeValue",
                                      "X Resolution",
                                      (-880.0, -160.0),
                                      label='X Resolution')
    y_res_node = create_node_in_group(node_group,
                                      "ShaderNodeValue",
                                      "Y Resolution",
                                      (-880.0, -260.0),
                                      label='Y Resolution')

    math_divide_1 = create_node_in_group(node_group,
                                         "ShaderNodeMath",
                                         "Math Divide 1",
                                         (-640.0, -260.0),
                                         operation='DIVIDE')
    math_divide_2 = create_node_in_group(node_group,
                                         "ShaderNodeMath",
                                         "Math Divide 2",
                                         (-260.0, 60.0),
                                         operation='DIVIDE')
    math_divide_3 = create_node_in_group(node_group,
                                         "ShaderNodeMath",
                                         "Math Divide 3",
                                         (-640.0, -420.0),
                                         operation='DIVIDE')
    math_multiply_1 = create_node_in_group(node_group,
                                           "ShaderNodeMath",
                                           "Math Multiply 1",
                                           (-260.0, -140.0),
                                           operation='MULTIPLY')
    math_divide_4 = create_node_in_group(node_group,
                                         "ShaderNodeMath",
                                         "Math Divide 4",
                                         (-380.0, -20.0),
                                         operation='DIVIDE')
    math_multiply_2 = create_node_in_group(node_group, 
                                           "ShaderNodeMath",
                                           "Math Multiply 2",
                                           (-620.0, 0.0),
                                           operation='MULTIPLY')
    math_multiply_2.inputs[1].default_value = -1.0

    vector_math_add = create_node_in_group(node_group,
                                           "ShaderNodeVectorMath",
                                           "Vector Math Add",
                                           (500.0, -20.0),
                                           operation='ADD')
    vector_math_add.inputs[1].default_value = (0.5, 0.5, 0.5)

    vector_math_scale = create_node_in_group(node_group,
                                             "ShaderNodeVectorMath",
                                             "Vector Math Scale",
                                             (240.0, -60.0),
                                             operation='SCALE')

    def create_link_in_group(node_tree, from_node, from_socket, to_node, to_socket):
        try:
            node_tree.links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])
        except IndexError as e:
            print(f"Failed to create link: {from_node.name} \
                  [{from_socket}] -> {to_node.name} [{to_socket}]. Error: {e}")

    create_link_in_group(node_group, group_input_node, 0, separate_xyz_node, 0)
    create_link_in_group(node_group, separate_xyz_node, 0, math_divide_2, 0)
    create_link_in_group(node_group, separate_xyz_node, 1, math_divide_4, 0)
    create_link_in_group(node_group, separate_xyz_node, 2, math_multiply_2, 0)
    create_link_in_group(node_group, math_multiply_2, 0, math_divide_4, 1)
    create_link_in_group(node_group, math_divide_1, 0, math_multiply_1, 1)
    create_link_in_group(node_group, math_multiply_1, 0, combine_xyz_node, 1)
    create_link_in_group(node_group, combine_xyz_node, 0, vector_math_scale, "Vector")
    create_link_in_group(node_group, math_divide_3, 0, vector_math_scale, "Scale")
    create_link_in_group(node_group, math_divide_4, 0, math_multiply_1, 0)
    create_link_in_group(node_group, math_multiply_2, 0, math_divide_2, 1)
    create_link_in_group(node_group, math_divide_2, 0, combine_xyz_node, 0)
    create_link_in_group(node_group, vector_math_scale, 0, vector_math_add, 0)
    create_link_in_group(node_group, vector_math_add, 0, group_output_node, 0)
    create_link_in_group(node_group, x_res_node, 0, math_divide_1, 0)
    create_link_in_group(node_group, y_res_node, 0, math_divide_1, 1)

    create_link_in_group(node_group, group_input_node, 1, math_divide_3, 0)
    create_link_in_group(node_group, group_input_node, 2, math_divide_3, 1)

    def add_driver(socket, data_path):
        driver = socket.driver_add("default_value").driver
        driver.type = 'SCRIPTED'
        var = driver.variables.new()
        var.name = 'resolution'
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = bpy.context.scene
        var.targets[0].data_path = data_path
        driver.expression = var.name

    add_driver(x_res_node.outputs[0], "render.resolution_x")
    add_driver(y_res_node.outputs[0], "render.resolution_y")

    return node_group
