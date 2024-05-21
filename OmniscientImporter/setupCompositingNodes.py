import bpy

def setup_compositing_nodes(image):
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

    # Clear existing nodes
    nodes.clear()

    # Create new nodes based on the extracted script
    node = nodes.new(type='CompositorNodeComposite')
    node.name = 'Composite'
    node.location = (720.0, 60.0)
    node.inputs['Alpha'].default_value = 1.0

    node = nodes.new(type='CompositorNodeRLayers')
    node.name = 'Render Layers'
    node.location = (-520.0, -20.0)

    node = nodes.new(type='CompositorNodeViewer')
    node.name = 'Viewer'
    node.location = (720.0, 220.0)
    node.inputs['Alpha'].default_value = 1.0

    node = nodes.new(type='CompositorNodeImage')
    node.name = 'Image'
    node.location = (-480.0, 440.0)
    node.image = image  # Use the provided image object
    node.label = ''

    node = nodes.new(type='CompositorNodeAlphaOver')
    node.name = 'Alpha Over'
    node.location = (260.0, 180.0)
    node.inputs['Fac'].default_value = 1.0

    node = nodes.new(type='CompositorNodeMixRGB')
    node.name = 'Mix'
    node.location = (-140.0, 280.0)
    node.inputs['Fac'].default_value = 1.0

    # Create links
    links.new(nodes['Render Layers'].outputs['Image'], nodes['Alpha Over'].inputs['Image'])
    links.new(nodes['Alpha Over'].outputs['Image'], nodes['Composite'].inputs['Image'])
    links.new(nodes['Mix'].outputs['Image'], nodes['Alpha Over'].inputs['Image'])
    links.new(nodes['Alpha Over'].outputs['Image'], nodes['Viewer'].inputs['Image'])
    links.new(nodes['Image'].outputs['Image'], nodes['Mix'].inputs['Image'])
    links.new(nodes['Render Layers'].outputs['Shadow Catcher'], nodes['Mix'].inputs['Image'])
