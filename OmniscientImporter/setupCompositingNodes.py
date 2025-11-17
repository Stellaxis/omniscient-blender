import bpy

def _get_or_create_compositor_tree(scene):
    """Return a compositor node tree, handling old and new APIs"""
    if hasattr(scene, "compositing_node_group"):
        if hasattr(scene, "render") and hasattr(scene.render, "use_compositing"):
            scene.render.use_compositing = True

        node_tree = scene.compositing_node_group
        if node_tree is None:
            node_tree = bpy.data.node_groups.new(
                name="CompositingNodeTree",
                type="CompositorNodeTree",
            )
            try:
                scene.compositing_node_group = node_tree
            except AttributeError:
                pass
        return node_tree

    if hasattr(scene, "use_nodes"):
        scene.use_nodes = True

    node_tree = getattr(scene, "node_tree", None)
    if node_tree is None:
        node_tree = bpy.data.node_groups.new(
            name="CompositingNodeTree",
            type="CompositorNodeTree",
        )
        try:
            scene.node_tree = node_tree
        except AttributeError:
            pass

    return node_tree


def _ensure_image_output_socket(node_tree):
    """Ensure the compositor tree has an 'Image' output socket"""
    iface = getattr(node_tree, "interface", None)
    if iface is None:
        # Pre‑4.0: outputs live directly on the tree
        outputs = getattr(node_tree, "outputs", None)
        if outputs and "Image" not in {s.name for s in outputs}:
            outputs.new("NodeSocketColor", "Image")
        return

    # 4.0+ interface API
    for item in getattr(iface, "items_tree", []):
        if (
            getattr(item, "item_type", None) == "SOCKET"
            and getattr(item, "in_out", None) == "OUTPUT"
            and item.name == "Image"
        ):
            return

    iface.new_socket(
        name="Image",
        description="Final image",
        in_out="OUTPUT",
        socket_type="NodeSocketColor",
    )


def _new_mix_node(nodes):
    """Create a Mix node that works across Blender versions"""

    def _try_new(idname):
        try:
            return nodes.new(type=idname)
        except Exception:
            return None

    # Try common node IDs, newest first
    for idname in (
        "NodeMix",            # potential generic Mix node type
        "CompositorNodeMix",  # if a new compositor mix exists
        "CompositorNodeMixRGB",
    ):
        node = _try_new(idname)
        if node is not None:
            return node

    # Fallback: search all node types
    candidate_ids = []
    for attr_name in dir(bpy.types):
        cls = getattr(bpy.types, attr_name, None)
        if not isinstance(cls, type):
            continue

        # Require a Node subclass of some kind
        try:
            if not issubclass(cls, bpy.types.Node):
                continue
        except TypeError:
            continue

        label = getattr(cls, "bl_label", "") or ""
        bl_idname = getattr(cls, "bl_idname", "") or ""
        text = f"{attr_name} {label} {bl_idname}".lower()

        # Heuristic search for color mix nodes
        if "mix" in text and ("color" in text or "rgb" in text or "multiply" in text):
            identifier = bl_idname or attr_name
            if identifier not in candidate_ids:
                candidate_ids.append(identifier)

    for idname in candidate_ids:
        node = _try_new(idname)
        if node is not None:
            return node

    # Still nothing; let the caller handle the fallback
    return None


def _new_value_node(nodes):
    """Create a numeric Value node that works across Blender versions"""

    def _try_new(idname):
        try:
            return nodes.new(type=idname)
        except Exception:
            return None

    # Try the recommended replacement first (5.0+), then legacy compositor value
    for idname in ("ShaderNodeValue", "CompositorNodeValue"):
        node = _try_new(idname)
        if node is not None:
            return node

    # Fallback: search for any Node subclass that looks like a Value node
    candidate_ids = []
    for attr_name in dir(bpy.types):
        cls = getattr(bpy.types, attr_name, None)
        if not isinstance(cls, type):
            continue

        try:
            if not issubclass(cls, bpy.types.Node):
                continue
        except TypeError:
            continue

        label = getattr(cls, "bl_label", "") or ""
        bl_idname = getattr(cls, "bl_idname", "") or ""
        text = f"{attr_name} {label} {bl_idname}".lower()

        if "value" in text:
            identifier = bl_idname or attr_name
            if identifier not in candidate_ids:
                candidate_ids.append(identifier)

    for idname in candidate_ids:
        node = _try_new(idname)
        if node is not None:
            return node

    # Nothing usable found
    return None


def setup_compositing_nodes(image, renderer):
    scene = bpy.context.scene

    node_tree = _get_or_create_compositor_tree(scene)

    nodes = node_tree.nodes
    links = node_tree.links

    use_group_output = bpy.app.version >= (5, 0, 0)

    # Find or create the image node
    image_node = nodes.get('Image')
    if image_node is None:
        # Clear existing nodes
        nodes.clear()

        # Output node: Composite (pre‑5.0) or Group Output (5.0+).
        if use_group_output:
            _ensure_image_output_socket(node_tree)

            composite_node = nodes.new(type='NodeGroupOutput')
            composite_node.name = 'Group Output'
            composite_node.is_active_output = True
        else:
            composite_node = nodes.new(type='CompositorNodeComposite')
            composite_node.name = 'Composite'
            try:
                composite_node.use_alpha = True
            except AttributeError:
                pass

        composite_node.location = (720.0, 60.0)

        render_layers_node = nodes.new(type='CompositorNodeRLayers')
        render_layers_node.name = 'Render Layers'
        render_layers_node.location = (-480, -160)
        render_layers_node.label = ''

        viewer_node = nodes.new(type='CompositorNodeViewer')
        viewer_node.name = 'Viewer'
        viewer_node.location = (720, 210)
        viewer_node.label = ''

        image_node = nodes.new(type='CompositorNodeImage')
        image_node.name = 'Image'
        image_node.location = (-480.0, 550.0)
        image_node.use_auto_refresh = True
        image_node.use_cyclic = False

        # Blender <= 4.x only
        if hasattr(image_node, "use_straight_alpha_output"):
            image_node.use_straight_alpha_output = False

        image_node.label = ''

        alpha_over_node = nodes.new(type='CompositorNodeAlphaOver')
        alpha_over_node.name = 'Alpha Over'
        alpha_over_node.location = (260.0, 180.0)
        alpha_over_node.inputs['Fac'].default_value = 1.0
        alpha_over_node.label = ''

        mix_node = _new_mix_node(nodes)
        if mix_node is not None:
            mix_node.name = 'Mix'
            mix_node.location = (-30, 280)
            mix_node.blend_type = 'MULTIPLY'
            mix_node.label = ''

            # Factor input - first socket on both old MixRGB and new Mix nodes
            if "Fac" in mix_node.inputs:
                mix_node.inputs["Fac"].default_value = 1.0
            elif len(mix_node.inputs) > 0:
                mix_node.inputs[0].default_value = 1.0

        # Add a scale node; 'space' only exists on some versions
        scale_node = nodes.new(type='CompositorNodeScale')
        scale_node.name = 'Scale'
        scale_node.location = (-280.0, 280.0)
        if hasattr(scale_node, "space"):
            scale_node.space = 'RELATIVE'

        # Create links and resolve BG/FG sockets by name or index
        alpha_inputs = alpha_over_node.inputs
        bg_socket = None
        fg_socket = None

        # Blender 5.0+ has explicit Background / Foreground names
        try:
            if "Background" in alpha_inputs and "Foreground" in alpha_inputs:
                bg_socket = alpha_inputs["Background"]
                fg_socket = alpha_inputs["Foreground"]
        except Exception:
            # Older builds may not support membership tests by name; ignore.
            pass

        # Pre-5.0 (fallback): two image sockets after Fac, BG = 1, FG = 2
        if bg_socket is None or fg_socket is None:
            if len(alpha_inputs) > 2:
                bg_socket = alpha_inputs[1]
                fg_socket = alpha_inputs[2]

        # Foreground (CG) from Render Layers
        if fg_socket is not None:
            links.new(render_layers_node.outputs['Image'], fg_socket)

        # Plate image goes through the Scale (and optional Mix) chain
        links.new(image_node.outputs['Image'], scale_node.inputs['Image'])

        if mix_node is not None and bg_socket is not None:
            # First output is the mixed result on both node versions
            if "Image" in mix_node.outputs:
                mix_output = mix_node.outputs["Image"]
            elif "Result" in mix_node.outputs:
                mix_output = mix_node.outputs["Result"]
            else:
                mix_output = mix_node.outputs[0]

            # Background plate (possibly multiplied with shadow catcher)
            links.new(mix_output, bg_socket)
            links.new(scale_node.outputs['Image'], mix_node.inputs[1])
        elif bg_socket is not None:
            # Fallback: no Mix node; feed the scaled image directly into Alpha Over
            links.new(scale_node.outputs['Image'], bg_socket)

        links.new(alpha_over_node.outputs['Image'], viewer_node.inputs['Image'])

        # Link final image to Composite / Group Output
        links.new(alpha_over_node.outputs['Image'], composite_node.inputs['Image'])

        if renderer == 'CYCLES' and mix_node is not None:
            # Guard optional Shadow Catcher pass
            out = render_layers_node.outputs.get('Shadow Catcher')
            if out is not None:
                links.new(out, mix_node.inputs[2])

    # If the image node exists, ensure the Scale node is created
    scale_node = nodes.get('Scale')
    if scale_node is None:
        scale_node = nodes.new(type='CompositorNodeScale')
        scale_node.name = 'Scale'
        scale_node.location = (-250.0, 280.0)
        if hasattr(scale_node, "space"):
            scale_node.space = 'RELATIVE'
        links = node_tree.links  # in case it changed
        links.new(image_node.outputs['Image'], scale_node.inputs['Image'])

    # Ensure driver Value nodes exist and are wired into the Scale node
    scale_x_val = nodes.get("OmniScaleX")
    if scale_x_val is None:
        scale_x_val = _new_value_node(nodes)
        if scale_x_val is None:
            print("OmniscientImporter: could not create Value node for X scale, drivers disabled")
            return
        scale_x_val.name = "OmniScaleX"
        scale_x_val.label = "OmniScaleX"
        scale_x_val.location = (-480,
                                scale_node.location.y - 40.0)
        scale_x_val.outputs[0].default_value = 1.0

    scale_y_val = nodes.get("OmniScaleY")
    if scale_y_val is None:
        scale_y_val = _new_value_node(nodes)
        if scale_y_val is None:
            print("OmniscientImporter: could not create Value node for Y scale, drivers disabled")
            return
        scale_y_val.name = "OmniScaleY"
        scale_y_val.label = "OmniScaleY"
        scale_y_val.location = (-480,
                                scale_node.location.y - 100.0)
        scale_y_val.outputs[0].default_value = 1.0

    # Wire Value outputs into the Scale node X/Y inputs in a version-agnostic way
    x_input = None
    y_input = None

    # Prefer named sockets when available
    try:
        x_input = scale_node.inputs.get("X")
        y_input = scale_node.inputs.get("Y")
    except AttributeError:
        # Very old builds may not support .get on inputs; fall back to indices below.
        pass

    # Fallback to index-based access if names are not found
    if x_input is None and len(scale_node.inputs) > 1:
        x_input = scale_node.inputs[1]
    if y_input is None and len(scale_node.inputs) > 2:
        y_input = scale_node.inputs[2]

    if x_input is not None and not x_input.is_linked:
        links.new(scale_x_val.outputs[0], x_input)
    if y_input is not None and not y_input.is_linked:
        links.new(scale_y_val.outputs[0], y_input)

    # Update the image in the Image node
    image_node.image = image
    image_node.frame_duration = image.frame_duration

    # Add drivers to the Value nodes that feed the Scale node
    def add_driver(
        socket, scene_data_path, image_data_path,
        var_name_scene, var_name_image, var_name_percentage,
        expression
    ):
        """Attach a scripted driver if possible, otherwise set a static value"""
        try:
            fcurve = socket.driver_add("default_value")
        except TypeError:
            # Fallback: property is not animatable; only set numeric defaults once
            try:
                current = socket.default_value
            except Exception:
                return

            if not isinstance(current, (int, float)):
                return

            scene = bpy.context.scene
            render = scene.render
            img = image  # captured from outer scope

            # Same math as the driver expression:
            # (project_res / image_size) * (res_percentage / 100.0)
            res_scale = render.resolution_percentage / 100.0

            if scene_data_path == "render.resolution_x" and image_data_path == "size[0]":
                w = img.size[0] or 1.0
                socket.default_value = (render.resolution_x * res_scale) / w
            elif scene_data_path == "render.resolution_y" and image_data_path == "size[1]":
                h = img.size[1] or 1.0
                socket.default_value = (render.resolution_y * res_scale) / h

            # No driver attached; use a static value
            return

        driver = fcurve.driver
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

    # Configure drivers
    add_driver(scale_x_val.outputs[0],
               "render.resolution_x",
               "size[0]",
               "project_res_x",
               "image_x",
               "res_percentage",
               "(project_res_x / image_x) * (res_percentage / 100.0)")
    add_driver(scale_y_val.outputs[0],
               "render.resolution_y",
               "size[1]",
               "project_res_y",
               "image_y",
               "res_percentage",
               "(project_res_y / image_y) * (res_percentage / 100.0)")

    # Refresh the compositor
    node_tree.update_tag()
