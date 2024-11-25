import bpy


def setup_compositing_nodes(image, renderer):
    scene = bpy.context.scene

    # Ensure compositing nodes are enabled
    scene.use_nodes = True

    # Get or create the node tree
    node_tree = scene.node_tree
    if node_tree is None:
        node_tree = bpy.data.node_groups.new(name="CompositingNodeTree", type="CompositorNodeTree")
        scene.node_tree = node_tree

    nodes = node_tree.nodes
    links = node_tree.links

    # Find or create the image node
    image_node = nodes.get('Image')
    if image_node is None:
        # Clear existing nodes
        nodes.clear()

        # Create new nodes
        composite_node = nodes.new(type='CompositorNodeComposite')
        composite_node.name = 'Composite'
        composite_node.location = (720.0, 60.0)
        composite_node.show_options = True
        composite_node.show_preview = False
        composite_node.show_texture = False
        composite_node.use_alpha = True
        composite_node.use_custom_color = False
        composite_node.label = ''
        composite_node.inputs['Alpha'].default_value = 1.0

        render_layers_node = nodes.new(type='CompositorNodeRLayers')
        render_layers_node.name = 'Render Layers'
        render_layers_node.location = (-516.5458374023438, -130.2813262939453)
        render_layers_node.show_options = True
        render_layers_node.show_preview = True
        render_layers_node.show_texture = False
        render_layers_node.use_custom_color = False
        render_layers_node.label = ''

        viewer_node = nodes.new(type='CompositorNodeViewer')
        viewer_node.name = 'Viewer'
        viewer_node.location = (717.6785888671875, 210.71133422851562)
        viewer_node.show_options = True
        viewer_node.show_preview = False
        viewer_node.show_texture = False
        viewer_node.use_alpha = True
        viewer_node.use_custom_color = False
        viewer_node.label = ''
        viewer_node.inputs['Alpha'].default_value = 1.0

        image_node = nodes.new(type='CompositorNodeImage')
        image_node.name = 'Image'
        image_node.location = (-480.0, 440.0)
        image_node.show_options = True
        image_node.show_preview = True
        image_node.show_texture = False
        image_node.use_auto_refresh = True
        image_node.use_custom_color = False
        image_node.use_cyclic = False
        image_node.use_straight_alpha_output = False
        image_node.label = ''

        alpha_over_node = nodes.new(type='CompositorNodeAlphaOver')
        alpha_over_node.name = 'Alpha Over'
        alpha_over_node.location = (260.0, 180.0)
        alpha_over_node.show_options = True
        alpha_over_node.show_preview = False
        alpha_over_node.show_texture = False
        alpha_over_node.use_custom_color = False
        alpha_over_node.use_premultiply = False
        alpha_over_node.label = ''
        alpha_over_node.inputs['Fac'].default_value = 1.0

        mix_node = nodes.new(type='CompositorNodeMixRGB')
        mix_node.name = 'Mix'
        mix_node.location = (-84.93910217285156, 282.1185302734375)
        mix_node.blend_type = 'MULTIPLY'
        mix_node.show_options = True
        mix_node.show_preview = False
        mix_node.show_texture = False
        mix_node.use_alpha = False
        mix_node.use_clamp = False
        mix_node.use_custom_color = False
        mix_node.label = ''
        mix_node.inputs['Fac'].default_value = 1.0

        # Add a scale node
        scale_node = nodes.new(type='CompositorNodeScale')
        scale_node.name = 'Scale'
        scale_node.location = (-280.0, 280.0)
        scale_node.space = 'RELATIVE'

        # Create links
        links.new(render_layers_node.outputs['Image'], alpha_over_node.inputs[2])
        links.new(alpha_over_node.outputs['Image'], composite_node.inputs['Image'])
        links.new(mix_node.outputs['Image'], alpha_over_node.inputs[1])
        links.new(alpha_over_node.outputs['Image'], viewer_node.inputs['Image'])
        links.new(image_node.outputs['Image'], scale_node.inputs['Image'])
        links.new(scale_node.outputs['Image'], mix_node.inputs[1])

        if renderer == 'CYCLES':
            links.new(render_layers_node.outputs['Shadow Catcher'], mix_node.inputs[2])

    # If the image node exists, ensure the scale node is created
    scale_node = nodes.get('Scale')
    if scale_node is None:
        scale_node = nodes.new(type='CompositorNodeScale')
        scale_node.name = 'Scale'
        scale_node.location = (-250.0, 280.0)
        scale_node.space = 'RELATIVE'
        links.new(image_node.outputs['Image'], scale_node.inputs['Image'])

    # Update the image in the image node
    image_node.image = image
    image_node.frame_duration = image.frame_duration

    # Add drivers to the scale node
    def add_driver(
        socket, scene_data_path, image_data_path, var_name_scene, var_name_image, 
        var_name_percentage, expression
    ):
        driver = socket.driver_add("default_value").driver
        driver.type = 'SCRIPTED'

        def find_or_create_var(driver, var_name, id_type, target_id, data_path):
            for var in driver.variables:
                if var.name == var_name:
                    var.targets[0].id = target_id
                    var.targets[0].data_path = data_path
                    return var
            var = driver.variables.new()
            var.name = var_name
            var.targets[0].id_type = id_type
            var.targets[0].id = target_id
            var.targets[0].data_path = data_path
            return var

        find_or_create_var(driver, var_name_scene, 'SCENE', bpy.context.scene, scene_data_path)
        find_or_create_var(driver, var_name_image, 'IMAGE', image, image_data_path)
        find_or_create_var(driver, var_name_percentage, 'SCENE', bpy.context.scene, "render.resolution_percentage")

        driver.expression = expression

    # Create expressions for the drivers
    add_driver(scale_node.inputs[1],
               "render.resolution_x",
               "size[0]",
               "project_res_x",
               "image_x",
               "res_percentage",
               "(project_res_x / image_x) * (res_percentage / 100.0)")
    add_driver(scale_node.inputs[2],
               "render.resolution_y",
               "size[1]",
               "project_res_y",
               "image_y",
               "res_percentage",
               "(project_res_y / image_y) * (res_percentage / 100.0)")

    # Refresh the compositor
    node_tree.update_tag()
