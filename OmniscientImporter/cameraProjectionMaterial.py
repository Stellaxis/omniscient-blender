import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty
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
    new_image_texture_node.location = (-750.0, -vertical_spacing * (len(existing_image_nodes) + 1))
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
            focal_length_socket = node_group.interface.new_socket(name="Focal Length", in_out='INPUT', socket_type='NodeSocketFloat',)
            sensor_size_socket = node_group.interface.new_socket(name="Sensor Size", in_out='INPUT', socket_type='NodeSocketFloat',)
        else:
            node_group.inputs.new(name="Vector Input", type='NodeSocketVector')
            node_group.outputs.new(name="Vector Output", type='NodeSocketVector')
            focal_length_socket = node_group.inputs.new(name="Focal Length", type='NodeSocketFloat')
            sensor_size_socket = node_group.inputs.new(name="Sensor Size", type='NodeSocketFloat')

        separate_xyz_node = create_node_in_group(node_group, "ShaderNodeSeparateXYZ", "Separate XYZ", (-860.0, 100.0))
        combine_xyz_node = create_node_in_group(node_group, "ShaderNodeCombineXYZ", "Combine XYZ", (-40.0, 0.0))
        combine_xyz_node.inputs['Z'].default_value = 1.0

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
        create_link_in_group(node_group, math_divide_3, 0, vector_math_scale, "Scale")
        create_link_in_group(node_group, math_divide_4, 0, math_multiply_1, 0)
        create_link_in_group(node_group, math_multiply_2, 0, math_divide_2, 1)
        create_link_in_group(node_group, math_divide_2, 0, combine_xyz_node, 0)
        create_link_in_group(node_group, vector_math_scale, 0, vector_math_add, 0)
        create_link_in_group(node_group, vector_math_add, 0, group_output_node, 0)
        create_link_in_group(node_group, x_res_node, 0, math_divide_1, 0)
        create_link_in_group(node_group, y_res_node, 0, math_divide_1, 1)

        # Link focal length and sensor size inputs
        create_link_in_group(node_group, group_input_node, 1, math_divide_3, 0)  # Focal length
        create_link_in_group(node_group, group_input_node, 2, math_divide_3, 1)  # Sensor size

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

    # Create the node group in the new material
    camera_projector_group_node = nodes.new("ShaderNodeGroup")
    camera_projector_group_node.location = (-1000.0, -vertical_spacing * (len(existing_image_nodes) + 1))
    camera_projector_group_node.width = 166.7
    camera_projector_group_node.label = 'Camera Projector Omni'
    camera_projector_group_node.node_tree = node_group

    # Add drivers to the inputs of the node group
    def add_camera_driver(node, input_name, camera, data_path):
        # Verify the input name is valid and the node has such an input
        if input_name not in node.inputs:
            print(f"Error: No input named {input_name} in node {node.name}")
            return

        input_socket = node.inputs[input_name]

        # Attempt to add a driver to the input socket
        try:
            driver_fcurve = input_socket.driver_add("default_value")
            driver = driver_fcurve.driver
            driver.type = 'SCRIPTED'

            var = driver.variables.new()
            var.name = 'prop'
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = camera
            var.targets[0].data_path = data_path

            driver.expression = var.name

        except AttributeError as e:
            print(f"Failed to add driver to {input_name} on node {node.name}: {e}")
            
    if new_camera:
        add_camera_driver(camera_projector_group_node, "Focal Length", new_camera, "data.lens")  # Focal Length
        add_camera_driver(camera_projector_group_node, "Sensor Size", new_camera, "data.sensor_width")  # Sensor Size

    # Create links in the main material
    def create_link(node_tree, from_node, from_socket, to_node, to_socket):
        if from_node is None or to_node is None:
            print(f"Linking error: {from_node} to {to_node}")
            return
        try:
            node_tree.links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])
        except IndexError as e:
            print(f"Failed to create link: {from_node.name} [{from_socket}] -> {to_node.name} [{to_socket}]. Error: {e}")
        except AttributeError as e:
            print(f"AttributeError: {from_node} or {to_node} is not valid. Error: {e}")

    create_link(material.node_tree, tex_coord_node, 3, camera_projector_group_node, 0)
    create_link(material.node_tree, camera_projector_group_node, 0, new_image_texture_node, 0)

    # Create a mix RGB node to control the visibility of the projection
    mix_rgb_node = nodes.new("ShaderNodeMixRGB")
    mix_rgb_node.location = (-200.0, -vertical_spacing * (len(existing_image_nodes) + 1))
    mix_rgb_node.blend_type = 'MIX'

    # Store the mix node reference in the shot property
    shot = bpy.context.scene.Omni_Shots[-1]
    shot.mix_node_name = mix_rgb_node.name

    # Create a new multiply node for alpha
    multiply_node = nodes.new("ShaderNodeMath")
    multiply_node.location = (-400.0, -vertical_spacing * (len(existing_image_nodes) + 1))
    multiply_node.operation = 'MULTIPLY'
    create_link(material.node_tree, new_image_texture_node, 1, multiply_node, 0)  # Alpha to multiply node

    # Add driver for the camera projection multiply
    def add_driver_for_multiply(node, shot_index, data_path):
        driver = node.inputs[1].driver_add("default_value").driver
        driver.type = 'SCRIPTED'
        var = driver.variables.new()
        var.name = 'projection_multiply'
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = bpy.context.scene
        var.targets[0].data_path = f"Omni_Shots[{shot_index}].{data_path}"
        driver.expression = var.name

        # Force update dependencies
        bpy.context.scene.update_tag()
        bpy.context.view_layer.update()

    # Use the index of the current shot
    shot_index = bpy.context.scene.Omni_Shots.find(shot.name)
    add_driver_for_multiply(multiply_node, shot_index, "camera_projection_multiply")

    # Link mix RGB node to the material's node tree
    if previous_mix_node:
        create_link(material.node_tree, previous_mix_node, 0, mix_rgb_node, 1)
    else:
        create_link(material.node_tree, previous_image_node, 0, mix_rgb_node, 1)
    create_link(material.node_tree, new_image_texture_node, 0, mix_rgb_node, 2)
    create_link(material.node_tree, multiply_node, 0, mix_rgb_node, 0)  # Multiply output to mix node input 0

    previous_mix_node = mix_rgb_node

    # Create link to BSDF and Output nodes
    create_link(material.node_tree, mix_rgb_node, 0, principled_bsdf_node, 0)
    create_link(material.node_tree, principled_bsdf_node, 0, output_node, 0)

    # Position the BSDF and Output nodes in between the rows
    total_rows = len(existing_image_nodes) + 2
    bsdf_vertical_position = -vertical_spacing * total_rows / 2

    principled_bsdf_node.location.y = bsdf_vertical_position
    output_node.location.y = bsdf_vertical_position

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

    # Custom property to store the node references
    scene = bpy.context.scene
    node_entry = scene.camera_projection_nodes.add()
    node_entry.name = new_camera.name
    node_entry.material_name = material_name
    node_entry.tex_coord_node = tex_coord_node.name
    node_entry.image_texture_node = new_image_texture_node.name
    node_entry.camera_projector_group_node = camera_projector_group_node.name
    node_entry.mix_rgb_node = mix_rgb_node.name
    node_entry.multiply_node = multiply_node.name

    return material

def delete_projection_nodes(camera_name):
    scene = bpy.context.scene
    node_index = scene.camera_projection_nodes.find(camera_name)
    if node_index != -1:
        node_entry = scene.camera_projection_nodes[node_index]
        material = bpy.data.materials.get(node_entry.material_name)
        if material:
            nodes = material.node_tree.nodes
            links = material.node_tree.links
            node_names = [node_entry.tex_coord_node, node_entry.image_texture_node, node_entry.camera_projector_group_node, node_entry.mix_rgb_node, node_entry.multiply_node]
            
            principled_bsdf_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)
            output_node = next((node for node in nodes if node.type == 'OUTPUT_MATERIAL'), None)

            # Remove the nodes
            for node_name in node_names:
                if node_name in nodes:
                    nodes.remove(nodes[node_name])
            
            # Find the latest ShaderNodeMixRGB node from remaining CameraProjectionNodes
            latest_mix_rgb_node = None
            for proj_node in reversed(scene.camera_projection_nodes):
                if proj_node.name != camera_name:
                    potential_mix_rgb_node = nodes.get(proj_node.mix_rgb_node)
                    if potential_mix_rgb_node:
                        latest_mix_rgb_node = potential_mix_rgb_node
                        break

            # Ensure the latest mix_rgb_node is connected to the BSDF node
            if latest_mix_rgb_node and latest_mix_rgb_node.outputs and principled_bsdf_node and principled_bsdf_node.inputs:
                connected = any(link.from_node == latest_mix_rgb_node and link.to_node == principled_bsdf_node for link in links)
                if not connected:
                    try:
                        links.new(latest_mix_rgb_node.outputs[0], principled_bsdf_node.inputs[0])
                    except IndexError as e:
                        print(f"Failed to create link: {latest_mix_rgb_node.name} [0] -> {principled_bsdf_node.name} [0]. Error: {e}")

            # Ensure BSDF node is connected to the output node
            if principled_bsdf_node and principled_bsdf_node.outputs and output_node and output_node.inputs:
                connected = any(link.from_node == principled_bsdf_node and link.to_node == output_node for link in links)
                if not connected:
                    try:
                        links.new(principled_bsdf_node.outputs[0], output_node.inputs[0])
                    except IndexError as e:
                        print(f"Failed to create link: {principled_bsdf_node.name} [0] -> {output_node.name} [0]. Error: {e}")
        
        # Remove the entry from the scene collection
        scene.camera_projection_nodes.remove(node_index)

class CameraProjectionNodes(PropertyGroup):
    material_name: StringProperty()
    tex_coord_node: StringProperty()
    image_texture_node: StringProperty()
    camera_projector_group_node: StringProperty()
    mix_rgb_node: StringProperty()
    multiply_node: StringProperty()

def register():
    bpy.types.Scene.camera_projection_nodes = bpy.props.CollectionProperty(type=CameraProjectionNodes)

def unregister():
    del bpy.types.Scene.camera_projection_nodes
