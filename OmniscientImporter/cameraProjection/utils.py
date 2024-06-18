

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


def add_driver(node, input_name_or_index, target, target_id_type, data_path, target_is_output=False, is_color=False):
    try:
        if target_is_output:
            if isinstance(input_name_or_index, int):
                socket = node.outputs[input_name_or_index]
            else:
                socket = node.outputs[input_name_or_index]
        else:
            if isinstance(input_name_or_index, int):
                socket = node.inputs[input_name_or_index]
            else:
                socket = node.inputs[input_name_or_index]

        if socket.name not in (node.outputs if target_is_output else node.inputs):
            raise KeyError(f"{'Output' if target_is_output else 'Input'} '{socket.name}' not found in node '{node.name}'")

        if is_color and hasattr(socket, 'default_value') and len(socket.default_value) == 4:
            channels = ['R', 'G', 'B', 'A']
            for i, channel in enumerate(channels):
                driver_fcurve = socket.driver_add("default_value", i)
                driver = driver_fcurve.driver
                driver.type = 'SCRIPTED'
                var = driver.variables.new()
                var.name = 'prop'
                var.targets[0].id_type = target_id_type
                var.targets[0].id = target
                var.targets[0].data_path = f"{data_path}[{i}]"
                driver.expression = var.name
        else:
            driver_fcurve = socket.driver_add("default_value")
            driver = driver_fcurve.driver
            driver.type = 'SCRIPTED'
            var = driver.variables.new()
            var.name = 'prop'
            var.targets[0].id_type = target_id_type
            var.targets[0].id = target
            var.targets[0].data_path = data_path
            driver.expression = var.name
    except AttributeError as e:
        print(f"Failed to add driver to {socket.name} on node {node.name}: {e}")
    except KeyError as e:
        print(e)


def hide_specific_nodes(node_tree, node_types):
    for node in node_tree.nodes:
        if node.bl_idname in node_types:
            node.hide = True


def find_node(nodes, node_type, node_name=None):
    if node_name:
        return next((node for node in nodes if node.type == node_type and node.name == node_name), None)
    return next((node for node in nodes if node.type == node_type), None)


def is_blender_4():
    from bpy.app import version
    return version >= (4, 0, 0)
