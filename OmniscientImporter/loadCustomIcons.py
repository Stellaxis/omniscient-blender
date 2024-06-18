import os
from bpy.utils.previews import new, remove

# Global dictionary to store icon previews
preview_collections = {}


def load_custom_icons():
    if "main" in preview_collections:
        return preview_collections["main"]

    pcoll = new()

    # Path to the icon files
    icon_folder = os.path.join(os.path.dirname(__file__), "icons")
    icon_cameraProjector_on = os.path.join(icon_folder, "icon_cameraProjector_on.png")
    icon_cameraProjector_off = os.path.join(icon_folder, "icon_cameraProjector_off.png")

    # Load the icons and store them in the previews collection
    pcoll.load("icon_cameraProjector_on", icon_cameraProjector_on, 'IMAGE')
    pcoll.load("icon_cameraProjector_off", icon_cameraProjector_off, 'IMAGE')

    preview_collections["main"] = pcoll

    return pcoll


def unregister_custom_icons():
    for pcoll in preview_collections.values():
        remove(pcoll)
    preview_collections.clear()


def register():
    load_custom_icons()


def unregister():
    unregister_custom_icons()
