import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty
from .utils import get_or_create_node, create_link, add_driver, hide_specific_nodes, find_node, is_blender_4
from .projection_shader_group import create_projection_shader_group
from ..ui.utils import find_collection_and_shot_index_by_camera

def create_projection_shader(material_name, new_image_name, new_camera):
        
    collection, shot, collection_index, shot_index = find_collection_and_shot_index_by_camera(new_camera)

    material = bpy.data.materials.get(material_name) or bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    vertical_spacing = 400.0

    principled_bsdf_node = get_or_create_node(nodes, 'BSDF_PRINCIPLED', (800.0, 0.0), Metallic=0.5, Roughness=0.8)
    output_node = get_or_create_node(nodes, 'OUTPUT_MATERIAL', (1100.0, 0.0))

    existing_image_nodes = [node for node in nodes if node.type == 'TEX_IMAGE']
    previous_image_node = existing_image_nodes[0] if existing_image_nodes else None
    previous_mix_node = next((node for node in nodes if node.type == 'MIX_RGB'), None)

    def create_tex_coord_node(camera):
        node = nodes.new("ShaderNodeTexCoord")
        node.location = (-1200.0, -vertical_spacing * (len(existing_image_nodes) + 1))
        node.width = 170.8
        node.object = camera
        return node

    def create_image_texture_node(image_name):
        node = nodes.new("ShaderNodeTexImage")
        node.location = (-750.0, -vertical_spacing * (len(existing_image_nodes) + 1))
        node.width = 240.0
        node.image = bpy.data.images.get(image_name)
        node.projection = 'FLAT'
        node.interpolation = 'Linear'
        node.extension = 'CLIP'
        node.image_user.use_auto_refresh = True
        scene = bpy.context.scene
        node.image_user.frame_start = scene.frame_start
        node.image_user.frame_duration = scene.frame_end - scene.frame_start + 1
        return node

    tex_coord_node = create_tex_coord_node(new_camera)
    new_image_texture_node = create_image_texture_node(new_image_name)

    node_group = create_projection_shader_group()
    camera_projector_group_node = nodes.new("ShaderNodeGroup")
    camera_projector_group_node.location = (-1000.0, -vertical_spacing * (len(existing_image_nodes) + 1))
    camera_projector_group_node.width = 166.7
    camera_projector_group_node.label = 'Camera Projector Omni'
    camera_projector_group_node.node_tree = node_group

    if new_camera:
        add_driver(camera_projector_group_node, "Focal Length", new_camera, 'OBJECT', "data.lens")
        add_driver(camera_projector_group_node, "Sensor Size", new_camera, 'OBJECT', "data.sensor_width")

    create_link(material.node_tree, tex_coord_node, 3, camera_projector_group_node, 0)
    create_link(material.node_tree, camera_projector_group_node, 0, new_image_texture_node, 0)

    mix_rgb_visibility_node = nodes.new("ShaderNodeMixRGB")
    mix_rgb_visibility_node.location = (-200.0, -vertical_spacing * (len(existing_image_nodes) + 1))
    mix_rgb_visibility_node.blend_type = 'MIX'
    mix_rgb_visibility_node.name = "MixRGBVisibilityNode" 

    # Add drivers for mix rgb colors
    if collection:
        add_driver(mix_rgb_visibility_node, 1, bpy.context.scene, 'SCENE', f"Omni_Collections[{collection_index}].color_scan", False, True)
        add_driver(mix_rgb_visibility_node, 2, bpy.context.scene, 'SCENE', f"Omni_Collections[{collection_index}].color_scan", False, True)

    if shot:
        shot.mix_node_name = mix_rgb_visibility_node.name

    multiply_visibility_node = nodes.new("ShaderNodeMath")
    multiply_visibility_node.location = (-400.0, -vertical_spacing * (len(existing_image_nodes) + 1))
    multiply_visibility_node.operation = 'MULTIPLY'
    multiply_visibility_node.name = "MultiplyVisibilityNode" 
    create_link(material.node_tree, new_image_texture_node, 1, multiply_visibility_node, 0)

    def add_driver_for_multiply(node, collection_index, shot_index, data_path):
        driver = node.inputs[1].driver_add("default_value").driver
        driver.type = 'SCRIPTED'
        var = driver.variables.new()
        var.name = 'projection_multiply'
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = bpy.context.scene
        var.targets[0].data_path = f"Omni_Collections[{collection_index}].shots[{shot_index}].{data_path}"
        driver.expression = var.name
        bpy.context.scene.update_tag()
        bpy.context.view_layer.update()

    add_driver_for_multiply(multiply_visibility_node, collection_index, shot_index, "camera_projection_multiply")

    if previous_mix_node:
        create_link(material.node_tree, previous_mix_node, 0, mix_rgb_visibility_node, 1)
    else:
        create_link(material.node_tree, previous_image_node, 0, mix_rgb_visibility_node, 1)
    create_link(material.node_tree, new_image_texture_node, 0, mix_rgb_visibility_node, 2)
    create_link(material.node_tree, multiply_visibility_node, 0, mix_rgb_visibility_node, 0)

    create_link(material.node_tree, mix_rgb_visibility_node, 0, principled_bsdf_node, 0)
    create_link(material.node_tree, principled_bsdf_node, 0, output_node, 0)

    total_rows = len(existing_image_nodes) + 2
    bsdf_vertical_position = -vertical_spacing * total_rows / 2
    principled_bsdf_node.location.y = bsdf_vertical_position
    output_node.location.y = bsdf_vertical_position

    # -------------------------------------------------------------------
    # Emission control (only create if it doesn't already exist)
    # -------------------------------------------------------------------

    mix_rgb_emission_node = find_node(nodes, 'MIX_RGB', 'MixRGBEmissionNode')

    if not mix_rgb_emission_node:

        color_ramp_emission_node = nodes.new("ShaderNodeValToRGB")
        color_ramp_emission_node.location = (100.0, bsdf_vertical_position - 350)
        color_ramp_emission_node.name = "ColorRampEmissionNode" 

        value_node = nodes.new("ShaderNodeValue")
        value_node.location = (200.0, bsdf_vertical_position - 650)
        value_node.outputs[0].default_value = 1.0
        value_node.name = "ValueEmissionNode"

        multiply_emission_node = nodes.new("ShaderNodeMath")
        multiply_emission_node.location = (400.0, bsdf_vertical_position - 500)
        multiply_emission_node.operation = 'MULTIPLY'
        multiply_emission_node.name = "MultiplyEmissionNode"
        
        mix_rgb_emission_node = nodes.new("ShaderNodeMixRGB")
        mix_rgb_emission_node.location = (600.0, bsdf_vertical_position - 550.0)
        mix_rgb_emission_node.hide = True
        mix_rgb_emission_node.name = "MixRGBEmissionNode"

        if collection:
            add_driver(value_node, 0, bpy.context.scene, 'SCENE', f"Omni_Collections[{collection_index}].emission_value", True)
            add_driver(mix_rgb_emission_node, 0, bpy.context.scene, 'SCENE', f"Omni_Collections[{collection_index}].mix_rgb_emission_input")

        create_link(material.node_tree, color_ramp_emission_node, 0, multiply_emission_node, 0)
        create_link(material.node_tree, value_node, 0, multiply_emission_node, 1)
        create_link(material.node_tree, multiply_emission_node, 0, mix_rgb_emission_node, 2)
        create_link(material.node_tree, value_node, 0, mix_rgb_emission_node, 1)
    else:
        # Update positions if nodes already exist
        color_ramp_emission_node = find_node(nodes, 'VALTORGB', 'ColorRampEmissionNode')
        value_node = find_node(nodes, 'VALUE', 'ValueEmissionNode')
        multiply_emission_node = find_node(nodes, 'MATH', 'MultiplyEmissionNode')

        color_ramp_emission_node.location = (100.0, bsdf_vertical_position - 350)
        value_node.location = (200.0, bsdf_vertical_position - 650)
        multiply_emission_node.location = (400.0, bsdf_vertical_position - 500)
        mix_rgb_emission_node.location = (600.0, bsdf_vertical_position - 550.0)
    
    node_types_to_hide = {"ShaderNodeMath"}
    hide_specific_nodes(material.node_tree, node_types_to_hide)
    hide_specific_nodes(node_group, node_types_to_hide)

    scene = bpy.context.scene
    node_entry = scene.camera_projection_nodes.add()
    node_entry.name = new_camera.name
    node_entry.material_name = material_name
    node_entry.tex_coord_node = tex_coord_node.name
    node_entry.image_texture_node = new_image_texture_node.name
    node_entry.camera_projector_group_node = camera_projector_group_node.name
    node_entry.mix_rgb_visibility_node = mix_rgb_visibility_node.name
    node_entry.multiply_visibility_node = multiply_visibility_node.name

    print(f"Added camera projection node: {node_entry.name}, Material: {node_entry.material_name}, Mix Node: {node_entry.mix_rgb_visibility_node}")

    return material

def ensure_bsdf_connection(material, latest_mix_rgb_visibility_node):
    if not material or not material.node_tree:
        return

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    principled_bsdf_node = find_node(nodes, 'BSDF_PRINCIPLED')
    output_node = find_node(nodes, 'OUTPUT_MATERIAL')
    
    if latest_mix_rgb_visibility_node and principled_bsdf_node:
        # Remove existing links to the BSDF node
        links_to_remove = [link for link in links if link.to_node == principled_bsdf_node]
        for link in links_to_remove:
            links.remove(link)
        # Create a new link from the latest mix node to the BSDF node
        try:
            links.new(latest_mix_rgb_visibility_node.outputs[0], principled_bsdf_node.inputs[0])
            print(f"Linked {latest_mix_rgb_visibility_node.name} to {principled_bsdf_node.name}")
        except IndexError as e:
            print(f"Failed to create link: {latest_mix_rgb_visibility_node.name} [0] -> {principled_bsdf_node.name} [0]. Error: {e}")

        try:
            emission_input_name = "Emission Color" if is_blender_4() else "Emission"
            emission_input = principled_bsdf_node.inputs.get(emission_input_name)
            if emission_input is not None:
                links.new(latest_mix_rgb_visibility_node.outputs[0], emission_input)
            else:
                print(f"{emission_input_name} input not found in {principled_bsdf_node.name}")
        except Exception as e:
            print(f"Failed to create link: {latest_mix_rgb_visibility_node.name} [0] -> {principled_bsdf_node.name} [{emission_input_name}]. Error: {e}")
                
        # Create a new link from the mix_rgb_emission_node to the Emission Strength input of the BSDF node
        mix_rgb_emission_node = find_node(nodes, 'MIX_RGB', 'MixRGBEmissionNode')
        if mix_rgb_emission_node:
            try:
                if is_blender_4():
                    emission_strength_input_name = "Emission Strength"
                    emission_strength_input = principled_bsdf_node.inputs.get(emission_strength_input_name)
                else:
                    emission_strength_input_index = 20
                    emission_strength_input = principled_bsdf_node.inputs[emission_strength_input_index]

                if emission_strength_input is not None:
                    links.new(mix_rgb_emission_node.outputs[0], emission_strength_input)
                    print(f"Linked {mix_rgb_emission_node.name} to {principled_bsdf_node.name} [{emission_strength_input_name if is_blender_4() else emission_strength_input_index}]")
                else:
                    print(f"Emission Strength input not found in {principled_bsdf_node.name}")
            except Exception as e:
                print(f"Failed to create link: {mix_rgb_emission_node.name} [0] -> {principled_bsdf_node.name} [{emission_strength_input_name if is_blender_4() else emission_strength_input_index}]. Error: {e}")
        else:
            print("Mix RGB Emission Node not found")

        # Connect latest mix RGB visibility node to the color ramp emission node
        color_ramp_emission_node = find_node(nodes, 'VALTORGB', 'ColorRampEmissionNode')
        if color_ramp_emission_node:
            try:
                links.new(latest_mix_rgb_visibility_node.outputs[0], color_ramp_emission_node.inputs[0])
                print(f"Linked {latest_mix_rgb_visibility_node.name} to {color_ramp_emission_node.name}")
            except IndexError as e:
                print(f"Failed to create link: {latest_mix_rgb_visibility_node.name} [0] -> {color_ramp_emission_node.name} [0]. Error: {e}")
        else:
            print("Color Ramp Emission Node not found")

    # Ensure BSDF node is connected to the output node
    if principled_bsdf_node and principled_bsdf_node.outputs and output_node and output_node.inputs:
        connected = any(link.from_node == principled_bsdf_node and link.to_node == output_node for link in links)
        if not connected:
            try:
                links.new(principled_bsdf_node.outputs[0], output_node.inputs[0])
            except IndexError as e:
                print(f"Failed to create link: {principled_bsdf_node.name} [0] -> {output_node.name} [0]. Error: {e}")

def delete_projection_nodes(camera_name):
    scene = bpy.context.scene
    node_index = scene.camera_projection_nodes.find(camera_name)
    if node_index != -1:
        node_entry = scene.camera_projection_nodes[node_index]
        material = bpy.data.materials.get(node_entry.material_name)
        if material:
            nodes = material.node_tree.nodes
            links = material.node_tree.links
            node_names = [node_entry.tex_coord_node, node_entry.image_texture_node, node_entry.camera_projector_group_node, node_entry.mix_rgb_visibility_node, node_entry.multiply_visibility_node]
            
            principled_bsdf_node = find_node(nodes, 'BSDF_PRINCIPLED')
            output_node = find_node(nodes, 'OUTPUT_MATERIAL')

            # Find the previous and next ShaderNodeMixRGB nodes
            prev_mix_rgb_visibility_node = None
            next_mix_rgb_visibility_node = None
            for i, proj_node in enumerate(scene.camera_projection_nodes):
                if proj_node.name == camera_name:
                    if i > 0:
                        prev_proj_node = scene.camera_projection_nodes[i - 1]
                        prev_mix_rgb_visibility_node = nodes.get(prev_proj_node.mix_rgb_visibility_node)
                    if i < len(scene.camera_projection_nodes) - 1:
                        next_proj_node = scene.camera_projection_nodes[i + 1]
                        next_mix_rgb_visibility_node = nodes.get(next_proj_node.mix_rgb_visibility_node)
                    break

            # Remove the nodes
            for node_name in node_names:
                if node_name in nodes:
                    nodes.remove(nodes[node_name])
            
            # Reconnect the previous mix node to the next mix node, if they exist
            if prev_mix_rgb_visibility_node and next_mix_rgb_visibility_node:
                # Remove the specific link from the deleted mix node to the next mix node
                links_to_remove = [link for link in links if link.to_node == next_mix_rgb_visibility_node and link.from_node.name == node_entry.mix_rgb_visibility_node]
                for link in links_to_remove:
                    links.remove(link)
                
                # Reconnect previous mix to next mix
                try:
                    links.new(prev_mix_rgb_visibility_node.outputs[0], next_mix_rgb_visibility_node.inputs[1])
                except IndexError as e:
                    print(f"Failed to create link: {prev_mix_rgb_visibility_node.name} [0] -> {next_mix_rgb_visibility_node.name} [1]. Error: {e}")

            # Find the latest ShaderNodeMixRGB node from remaining CameraProjectionNodes
            latest_mix_rgb_visibility_node = None
            for proj_node in reversed(scene.camera_projection_nodes):
                if proj_node.name != camera_name:
                    potential_mix_rgb_visibility_node = nodes.get(proj_node.mix_rgb_visibility_node)
                    if potential_mix_rgb_visibility_node:
                        latest_mix_rgb_visibility_node = potential_mix_rgb_visibility_node
                        break

            # Ensure the latest mix_rgb_visibility_node is connected to the BSDF node
            ensure_bsdf_connection(material, latest_mix_rgb_visibility_node)
        
        # Remove the entry from the scene collection
        scene.camera_projection_nodes.remove(node_index)

def reorder_projection_nodes(camera_name, mesh):
    scene = bpy.context.scene

    if not mesh:
        print(f"Error: Mesh not provided or not found.")
        return

    print("Current camera_projection_nodes:")
    for entry in scene.camera_projection_nodes:
        print(f" - Camera: {entry.name}, Material: {entry.material_name}, Mix Node: {entry.mix_rgb_visibility_node}")

    # Filter the nodes to only include those related to the provided mesh
    mesh_materials = [mat.name for mat in mesh.data.materials]
    relevant_nodes = [entry for entry in scene.camera_projection_nodes if entry.material_name in mesh_materials]

    if not relevant_nodes:
        print(f"Error: No projection nodes found for the mesh '{mesh.name}'.")
        return

    # Find the specified CameraProjectionNodes entry
    node_entry = None
    for entry in relevant_nodes:
        if entry.name == camera_name:
            node_entry = entry
            break

    if not node_entry:
        print(f"Error: Camera '{camera_name}' not found in relevant projection nodes.")
        return

    print(f"Reordering nodes with '{camera_name}' as the first camera.")

    # Create a list of node entries ordered with the specified camera first and then reverse the order
    ordered_nodes = [node_entry] + [entry for entry in relevant_nodes if entry.name != camera_name]
    ordered_nodes.reverse()

    print("Ordered nodes (inverted):")
    for entry in ordered_nodes:
        print(f" - Camera: {entry.name}, Material: {entry.material_name}, Mix Node: {entry.mix_rgb_visibility_node}")

    # Collect valid entries
    valid_entries = []
    for entry in ordered_nodes:
        if entry.name and entry.material_name and entry.mix_rgb_visibility_node:
            valid_entries.append({
                'name': entry.name,
                'material_name': entry.material_name,
                'tex_coord_node': entry.tex_coord_node,
                'image_texture_node': entry.image_texture_node,
                'camera_projector_group_node': entry.camera_projector_group_node,
                'mix_rgb_visibility_node': entry.mix_rgb_visibility_node,
                'multiply_visibility_node': entry.multiply_visibility_node
            })
            print(f"Valid entry found: Camera: {entry.name}, Material: {entry.material_name}, Mix Node: {entry.mix_rgb_visibility_node}")
        else:
            print(f"Invalid entry found: Camera: {entry.name}, Material: {entry.material_name}, Mix Node: {entry.mix_rgb_visibility_node}")

    print(f"Valid entries before clearing: {len(valid_entries)}")

    # Remove relevant nodes by index
    indices_to_remove = [i for i, entry in enumerate(scene.camera_projection_nodes) if entry in relevant_nodes]
    for index in reversed(indices_to_remove):
        scene.camera_projection_nodes.remove(index)

    # Re-add valid entries
    for entry in valid_entries:
        new_entry = scene.camera_projection_nodes.add()
        new_entry.name = entry['name']
        new_entry.material_name = entry['material_name']
        new_entry.tex_coord_node = entry['tex_coord_node']
        new_entry.image_texture_node = entry['image_texture_node']
        new_entry.camera_projector_group_node = entry['camera_projector_group_node']
        new_entry.mix_rgb_visibility_node = entry['mix_rgb_visibility_node']
        new_entry.multiply_visibility_node = entry['multiply_visibility_node']
        print(f"Re-added valid entry: Camera: {new_entry.name}, Material: {new_entry.material_name}, Mix Node: {new_entry.mix_rgb_visibility_node}")

    print(f"Entries after clearing and re-adding: {len(scene.camera_projection_nodes)}")

    # Disconnect the input [1] of the first mix RGB node from the relevant nodes
    if valid_entries:
        first_node_entry = valid_entries[0]
        first_material = bpy.data.materials.get(first_node_entry['material_name'])
        if first_material and first_material.node_tree:
            nodes = first_material.node_tree.nodes
            first_mix_rgb_visibility_node = nodes.get(first_node_entry['mix_rgb_visibility_node'])
            if first_mix_rgb_visibility_node:
                # Remove links to input [1] of the first mix RGB node
                links_to_remove = [link for link in first_material.node_tree.links if link.to_node == first_mix_rgb_visibility_node and link.to_socket == first_mix_rgb_visibility_node.inputs[1]]
                for link in links_to_remove:
                    first_material.node_tree.links.remove(link)
                print(f"Disconnected input [1] of the first mix RGB node: {first_mix_rgb_visibility_node.name}")

    # Reconnect the nodes in the material node tree
    prev_mix_rgb_visibility_node = None
    for entry in valid_entries:
        material = bpy.data.materials.get(entry['material_name'])
        if not material or not material.node_tree:
            print(f"Error: Material '{entry['material_name']}' not found or has no node tree.")
            continue

        nodes = material.node_tree.nodes
        mix_rgb_visibility_node = nodes.get(entry['mix_rgb_visibility_node'])
        if prev_mix_rgb_visibility_node and mix_rgb_visibility_node:
            # Remove the existing link from the previous mix node to the current mix node
            links_to_remove = [link for link in material.node_tree.links if link.to_node == mix_rgb_visibility_node and link.from_node == prev_mix_rgb_visibility_node]
            for link in links_to_remove:
                material.node_tree.links.remove(link)

            # Create a new link from the previous mix node to the current mix node
            try:
                material.node_tree.links.new(prev_mix_rgb_visibility_node.outputs[0], mix_rgb_visibility_node.inputs[1])
                print(f"Linked {prev_mix_rgb_visibility_node.name} to {mix_rgb_visibility_node.name}")
            except IndexError as e:
                print(f"Failed to create link: {prev_mix_rgb_visibility_node.name} [0] -> {mix_rgb_visibility_node.name} [1]. Error: {e}")

        prev_mix_rgb_visibility_node = mix_rgb_visibility_node

    # Ensure the latest mix_rgb_visibility_node is connected to the BSDF node
    if prev_mix_rgb_visibility_node:
        last_entry = valid_entries[-1]
        material = bpy.data.materials.get(last_entry['material_name'])
        latest_mix_rgb_visibility_node = None
        if material and material.node_tree:
            nodes = material.node_tree.nodes
            latest_mix_rgb_visibility_node = nodes.get(last_entry['mix_rgb_visibility_node'])
        
        ensure_bsdf_connection(material, latest_mix_rgb_visibility_node)

def register():
    bpy.types.Scene.camera_projection_nodes = bpy.props.CollectionProperty(type=CameraProjectionNodes)

def unregister():
    del bpy.types.Scene.camera_projection_nodes

class CameraProjectionNodes(PropertyGroup):
    material_name: StringProperty()
    tex_coord_node: StringProperty()
    image_texture_node: StringProperty()
    camera_projector_group_node: StringProperty()
    mix_rgb_visibility_node: StringProperty()
    multiply_visibility_node: StringProperty()
