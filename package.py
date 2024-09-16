import os
import shutil
import zipfile
import re

# Define the name of the addon folder
addon_name = "OmniscientImporter"

# Define the root directory of the addon
addon_dir = os.path.join(os.getcwd(), addon_name)

# Define the output folder
output_folder = os.path.join(os.getcwd(), "output")
os.makedirs(output_folder, exist_ok=True)

# Parse version number from bl_info
bl_info_path = os.path.join(addon_dir, "__init__.py")
with open(bl_info_path, "r") as f:
    bl_info = f.read()

# Regex to find the version in the bl_info file
version_regex = r'"version"\s*:\s*\((\d+),\s*(\d+),\s*(\d+)\)'
version_match = re.search(version_regex, bl_info)

if version_match:
    version_str = f"v{version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)}"
else:
    version_str = ""

# Define the name of the zip file to create
zip_name = f"{addon_name}_blender_{version_str}.zip"

# Define the path to the output zip file
output_zip_path = os.path.join(output_folder, zip_name)

# Remove all __pycache__ folders
for root, dirs, files in os.walk(addon_dir):
    for dir_name in dirs:
        if dir_name == "__pycache__":
            dir_path = os.path.join(root, dir_name)
            shutil.rmtree(dir_path)

# Remove Mac related files
for root, dirs, files in os.walk(addon_dir):
    for file_name in files:
        if file_name.startswith(".DS_Store"):
            file_path = os.path.join(root, file_name)
            os.remove(file_path)

# Create the zip file with the folder inside named "OmniscientImporter"
with zipfile.ZipFile(output_zip_path, "w") as zip_file:
    for root, dirs, files in os.walk(addon_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            # Ensure that the files inside the zip are under a folder named "OmniscientImporter"
            relative_path = os.path.relpath(file_path, addon_dir)
            zip_file.write(file_path, os.path.join(addon_name, relative_path))

print(f"Addon packaged into {output_zip_path}")
