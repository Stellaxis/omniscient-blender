import os
from bpy.utils.previews import new, remove

class IconManager:
    def __init__(self):
        self.preview_collections = {}
        self.icon_folder = os.path.join(os.path.dirname(__file__), "icons")

    def load_custom_icons(self):
        if "main" in self.preview_collections:
            return self.preview_collections["main"]

        pcoll = new()
        
        # List of icons to load
        icons = {
            "icon_cameraProjector_on": "icon_cameraProjector_on.png",
            "icon_cameraProjector_off": "icon_cameraProjector_off.png"
        }

        for icon_name, file_name in icons.items():
            icon_path = os.path.join(self.icon_folder, file_name)
            if os.path.exists(icon_path):
                pcoll.load(icon_name, icon_path, 'IMAGE')
            else:
                print(f"Icon file {file_name} not found in {self.icon_folder}")

        self.preview_collections["main"] = pcoll

        return pcoll

    def get_icon(self, name):
        return self.preview_collections["main"][name].icon_id

    def unregister_custom_icons(self):
        for pcoll in self.preview_collections.values():
            remove(pcoll)
        self.preview_collections.clear()


icon_manager = IconManager()
