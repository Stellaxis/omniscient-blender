import bpy

def create_projection_shader(material_name, image_name, camera):
    # Create a new material
    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    nodes = material.node_tree.nodes

    # Clear existing nodes
    nodes.clear()

    # Create main nodes
    tex_coord_node = nodes.new("ShaderNodeTexCoord")
    tex_coord_node.location = (-1100.0, 100.0)
    tex_coord_node.width = 170.8
    tex_coord_node.object = camera

    # Create image texture node
    image_texture_node = nodes.new("ShaderNodeTexImage")
    image_texture_node.location = (-420.0, 200.0)
    image_texture_node.width = 240.0
    image_texture_node.image = bpy.data.images.get(image_name)
    image_texture_node.projection = 'FLAT'
    image_texture_node.interpolation = 'Linear'
    image_texture_node.extension = 'CLIP'
    image_texture_node.image_user.use_auto_refresh = True
    scene = bpy.context.scene
    image_texture_node.image_user.frame_start = scene.frame_start
    image_texture_node.image_user.frame_duration = scene.frame_end

    emission_node = nodes.new("ShaderNodeEmission")
    emission_node.location = (-100.0, 200.0)
    emission_node.width = 140.0

    output_node = nodes.new("ShaderNodeOutputMaterial")
    output_node.location = (80.0, 200.0)
    output_node.width = 140.0
    output_node.is_active_output = True
    output_node.target = 'ALL'

    # Create or reuse the Camera Projector node group
    node_group_name = "CameraProjector_Omni"
    if node_group_name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[node_group_name]
    else:
        node_group = bpy.data.node_groups.new(name=node_group_name, type='ShaderNodeTree')

        # Function to create nodes inside the node group
        def create_node_in_group(node_tree, node_type, name, location, **kwargs):
            node = node_tree.nodes.new(type=node_type)
            node.name = name
            node.location = location
            for attr, value in kwargs.items():
                setattr(node, attr, value)
            return node

        # Create nodes inside the group
        group_input_node = create_node_in_group(node_group, "NodeGroupInput", "Group Input", (-1060.0, 40.0))
        group_output_node = create_node_in_group(node_group, "NodeGroupOutput", "Group Output", (720.0, -20.0), is_active_output=True)

        # Adding vector input and output sockets
        node_group.interface.new_socket(name="Vector Input", in_out='INPUT')
        node_group.interface.new_socket(name="Vector Output", in_out='OUTPUT')

        separate_xyz_node = create_node_in_group(node_group, "ShaderNodeSeparateXYZ", "Separate XYZ", (-860.0, 100.0))
        combine_xyz_node = create_node_in_group(node_group, "ShaderNodeCombineXYZ", "Combine XYZ", (-40.0, 0.0))
        combine_xyz_node.inputs['Z'].default_value = 1.0

        focal_length_node = create_node_in_group(node_group, "ShaderNodeValue", "Focal Length", (-880.0, -360.0), label='Focal Length')
        sensor_size_node = create_node_in_group(node_group, "ShaderNodeValue", "Sensor Size", (-880.0, -460.0), label='Sensor Size')
        x_res_node = create_node_in_group(node_group, "ShaderNodeValue", "X Resolution", (-880.0, -160.0), label='X Resolution')
        y_res_node = create_node_in_group(node_group, "ShaderNodeValue", "Y Resolution", (-880.0, -260.0), label='Y Resolution')

        math_divide_1 = create_node_in_group(node_group, "ShaderNodeMath", "Math Divide 1", (-640.0, -260.0), operation='DIVIDE')
        math_divide_2 = create_node_in_group(node_group, "ShaderNodeMath", "Math Divide 2", (-260.0, 60.0), operation='DIVIDE')
        math_divide_3 = create_node_in_group(node_group, "ShaderNodeMath", "Math Divide 3", (-640.0, -420.0), operation='DIVIDE')
        math_multiply_1 = create_node_in_group(node_group, "ShaderNodeMath", "Math Multiply 1", (-260.0, -140.0), operation='MULTIPLY')
        math_divide_4 = create_node_in_group(node_group, "ShaderNodeMath", "Math Divide 4", (-380.0, -20.0), operation='DIVIDE')
        math_multiply_2 = create_node_in_group(node_group, "ShaderNodeMath", "Math Multiply 2", (-620.0, 0.0), operation='MULTIPLY')
        math_multiply_2.inputs[1].default_value = -1.0

        vector_math_add = create_node_in_group(node_group, "ShaderNodeVectorMath", "Vector Math Add", (500.0, -20.0), operation='ADD')
        vector_math_add.inputs[1].default_value = (0.5, 0.5, 0.5)

        vector_math_scale = create_node_in_group(node_group, "ShaderNodeVectorMath", "Vector Math Scale", (240.0, -60.0), operation='SCALE')

        # Create links inside the group
        def create_link_in_group(node_tree, from_node, from_socket, to_node, to_socket):
            try:
                node_tree.links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])
            except IndexError as e:
                print(f"Failed to create link: {from_node.name} [{from_socket}] -> {to_node.name} [{to_socket}]. Error: {e}")

        create_link_in_group(node_group, group_input_node, 0, separate_xyz_node, 0)
        create_link_in_group(node_group, separate_xyz_node, 0, math_divide_2, 0)
        create_link_in_group(node_group, separate_xyz_node, 1, math_divide_4, 0)
        create_link_in_group(node_group, separate_xyz_node, 2, math_multiply_2, 0)
        create_link_in_group(node_group, math_multiply_2, 0, math_divide_4, 1)
        create_link_in_group(node_group, math_divide_1, 0, math_multiply_1, 1)
        create_link_in_group(node_group, math_multiply_1, 0, combine_xyz_node, 1)
        create_link_in_group(node_group, combine_xyz_node, 0, vector_math_scale, "Vector")
        create_link_in_group(node_group, focal_length_node, 0, math_divide_3, 0)
        create_link_in_group(node_group, math_divide_3, 0, vector_math_scale, "Scale")
        create_link_in_group(node_group, math_divide_4, 0, math_multiply_1, 0)
        create_link_in_group(node_group, math_multiply_2, 0, math_divide_2, 1)
        create_link_in_group(node_group, sensor_size_node, 0, math_divide_3, 1)
        create_link_in_group(node_group, math_divide_2, 0, combine_xyz_node, 0)
        create_link_in_group(node_group, vector_math_scale, 0, vector_math_add, 0)
        create_link_in_group(node_group, vector_math_add, 0, group_output_node, 0)
        create_link_in_group(node_group, x_res_node, 0, math_divide_1, 0)
        create_link_in_group(node_group, y_res_node, 0, math_divide_1, 1)

        # Add drivers to the resolution nodes
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

        # Add drivers to the focal length and sensor size nodes
        def add_camera_driver(socket, camera, data_path):
            driver = socket.driver_add("default_value").driver
            driver.type = 'SCRIPTED'
            var = driver.variables.new()
            var.name = 'prop'
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = camera
            var.targets[0].data_path = data_path
            driver.expression = var.name

        if camera:
            add_camera_driver(focal_length_node.outputs[0], camera, "data.lens")
            add_camera_driver(sensor_size_node.outputs[0], camera, "data.sensor_width")

    # Create the node group in the new material
    camera_projector_group_node = nodes.new("ShaderNodeGroup")
    camera_projector_group_node.location = (-820.0, 60.0)
    camera_projector_group_node.width = 166.7
    camera_projector_group_node.label = 'Camera Projector Omni'
    camera_projector_group_node.node_tree = node_group

    # Create links in the main material
    def create_link(node_tree, from_node, from_socket, to_node, to_socket):
        try:
            node_tree.links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])
        except IndexError as e:
                print(f"Failed to create link: {from_node.name} [{from_socket}] -> {to_node.name} [{to_socket}]. Error: {e}")

    create_link(material.node_tree, tex_coord_node, 3, camera_projector_group_node, 0)
    create_link(material.node_tree, camera_projector_group_node, 0, image_texture_node, 0)
    create_link(material.node_tree, image_texture_node, 0, emission_node, 0)
    create_link(material.node_tree, emission_node, 0, output_node, 0)

    # Function to hide (collapse) specific nodes in a node tree
    def hide_specific_nodes(node_tree, node_types):
        for node in node_tree.nodes:
            if node.bl_idname in node_types:
                node.hide = True

    # List of node types to hide
    node_types_to_hide = {"ShaderNodeMath"}

    # Hide specific nodes in the material and group node trees
    hide_specific_nodes(material.node_tree, node_types_to_hide)
    hide_specific_nodes(node_group, node_types_to_hide)

    return material

