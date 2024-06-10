import bpy

def get_or_create_node(nodes, node_type, location, **kwargs):
    node = next((node for node in nodes if node.type == node_type), None)
    if not node:
        node = nodes.new(type=node_type)
        node.location = location
    for attr, value in kwargs.items():
        setattr(node.inputs[attr], 'default_value', value)
    return node

def create_link(node_tree, from_node, from_socket, to_node, to_socket):
    try:
        node_tree.links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])
    except (IndexError, AttributeError) as e:
        print(f"Failed to create link: {from_node} [{from_socket}] -> {to_node} [{to_socket}]. Error: {e}")

def add_driver(node, input_name_or_index, target, target_id_type, data_path):
    try:
        if isinstance(input_name_or_index, int):
            input_name = node.inputs[input_name_or_index].name
        else:
            input_name = input_name_or_index
        
        if input_name not in node.inputs:
            raise KeyError(f"Input '{input_name}' not found in node '{node.name}'")
        
        driver_fcurve = node.inputs[input_name].driver_add("default_value")
        driver = driver_fcurve.driver
        driver.type = 'SCRIPTED'
        var = driver.variables.new()
        var.name = 'prop'
        var.targets[0].id_type = target_id_type
        var.targets[0].id = target
        var.targets[0].data_path = data_path
        driver.expression = var.name
    except AttributeError as e:
        print(f"Failed to add driver to {input_name} on node {node.name}: {e}")
    except KeyError as e:
        print(e)

def hide_specific_nodes(node_tree, node_types):
    for node in node_tree.nodes:
        if node.bl_idname in node_types:
            node.hide = True
