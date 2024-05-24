import bpy
from bpy.app import version

def is_blender_4():
    return version >= (4, 0, 0)

def create_projection_shader(material_name, new_image_name, new_camera):
    # Get or create a new material
    material = bpy.data.materials.get(material_name) or bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    nodes = material.node_tree.nodes

    # Ensure the material uses nodes
    if not material.use_nodes:
        material.use_nodes = True

    # Calculate the vertical spacing
    vertical_spacing = 400.0

    # Create a principled BSDF node if it doesn't exist
    principled_bsdf_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)
    if not principled_bsdf_node:
        principled_bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_bsdf_node.location = (400.0, 0.0)
        principled_bsdf_node.inputs['Metallic'].default_value = 0.5
        principled_bsdf_node.inputs['Roughness'].default_value = 0.8

    # Create a material output node if it doesn't exist
    output_node = next((node for node in nodes if node.type == 'OUTPUT_MATERIAL'), None)
    if not output_node:
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = (600.0, 0.0)

    # Find existing texture coordinate and image texture nodes
    existing_image_nodes = [node for node in nodes if node.type == 'TEX_IMAGE']
    previous_image_node = existing_image_nodes[0] if existing_image_nodes else None
    previous_mix_node = None
    existing_mix_nodes = [node for node in nodes if node.type == 'MIX_RGB']
    if existing_mix_nodes:
        previous_mix_node = existing_mix_nodes[-1]

    # Create new texture coordinate node for the new camera
    tex_coord_node = nodes.new("ShaderNodeTexCoord")
    tex_coord_node.location = (-1200.0, -vertical_spacing * (len(existing_image_nodes) + 1))
    tex_coord_node.width = 170.8
    tex_coord_node.object = new_camera

    # Create new image texture node for the new image
    new_image_texture_node = nodes.new("ShaderNodeTexImage")
    new_image_texture_node.location = (-600.0, -vertical_spacing * (len(existing_image_nodes) + 1))
    new_image_texture_node.width = 240.0
    new_image_texture_node.image = bpy.data.images.get(new_image_name)
    new_image_texture_node.projection = 'FLAT'
    new_image_texture_node.interpolation = 'Linear'
    new_image_texture_node.extension = 'CLIP'
    new_image_texture_node.image_user.use_auto_refresh = True
    scene = bpy.context.scene
    new_image_texture_node.image_user.frame_start = scene.frame_start
    new_image_texture_node.image_user.frame_duration = scene.frame_end - scene.frame_start + 1

    # Check if the Camera Projector group already exists
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
        if is_blender_4():
            node_group.interface.new_socket(name="Vector Input", in_out='INPUT')
            node_group.interface.new_socket(name="Vector Output", in_out='OUTPUT')
        else:
            node_group.inputs.new(name="Vector Input", type='NodeSocketVector')
            node_group.outputs.new(name="Vector Output", type='NodeSocketVector')

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

        if new_camera:
            add_camera_driver(focal_length_node.outputs[0], new_camera, "data.lens")
            add_camera_driver(sensor_size_node.outputs[0], new_camera, "data.sensor_width")

    # Create the node group in the new material
    camera_projector_group_node = nodes.new("ShaderNodeGroup")
    camera_projector_group_node.location = (-1000.0, -vertical_spacing * (len(existing_image_nodes) + 1))
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
    create_link(material.node_tree, camera_projector_group_node, 0, new_image_texture_node, 0)

    # Create a mix RGB node if there's an existing image texture node
    if previous_image_node or previous_mix_node:
        new_mix_node = nodes.new("ShaderNodeMixRGB")
        new_mix_node.location = (-200.0, -vertical_spacing * (len(existing_image_nodes) + 1) + vertical_spacing / 2)
        new_mix_node.blend_type = 'MIX'
        new_mix_node.inputs[0].default_value = 0.5  # Adjust blend factor as needed

        if previous_mix_node:
            create_link(material.node_tree, previous_mix_node, 0, new_mix_node, 1)
        else:
            create_link(material.node_tree, previous_image_node, 0, new_mix_node, 1)

        create_link(material.node_tree, new_image_texture_node, 0, new_mix_node, 2)
        create_link(material.node_tree, new_image_texture_node, 1, new_mix_node, 0)  # Connect alpha to mix shader

        previous_mix_node = new_mix_node
        create_link(material.node_tree, previous_mix_node, 0, principled_bsdf_node, 0)
    else:
        create_link(material.node_tree, new_image_texture_node, 0, principled_bsdf_node, 0)

    # Position the BSDF and Output nodes in between the rows
    total_rows = len(existing_image_nodes) + 2
    bsdf_vertical_position = -vertical_spacing * total_rows / 2

    principled_bsdf_node.location.y = bsdf_vertical_position
    output_node.location.y = bsdf_vertical_position

    create_link(material.node_tree, principled_bsdf_node, 0, output_node, 0)

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
