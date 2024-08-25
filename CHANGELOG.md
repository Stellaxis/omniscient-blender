# 2.3.2 - (2024.08.25)

### Fixes
- Camera projection when rendering with Cycles

# 2.3.1 - (2024.08.16)

### Fixes
- Ensured Omniscient scene is visible by default in render

# 2.3.0 - (2024.07.29)

### Features
- Drag & Drop import (Blender 4.2 and newer versions)

### Chore
- Add blender store manifest
- Update packaging instructions

### Refactor
- Conform code to Flake8 (Except C901)

# 2.2.0 - (2024.06.13)

### Features
- Shots organized per scene
- Projection as emissive
- Luminance-based emission
- Base mesh color control

### Fixes
- Proportional scaling using resolution percentage

# 2.1.0 - (2024.06.09)

### Features
- Bake keyframes preference
- Scale comp image based on project resolution
- Save render settings per shot

### Fix
- Reorder projection nodes on active collection

# 2.0.0 - (2024.06.01)

### Features
- Omniscient panel with import preferences and shot switcher
- Animated focus distance and focal length
- Setup scene’s shutter speed based on the shot
- Auto switch shot when changing camera
- Camera projection setup per shot
- Multi-camera projection with priority to the active camera
- Setup shadow catcher and holdout
- Base setup compositing graph
- Inform user of the ideal version
- Contact info and documentation link
- Shade smooth imported mesh
- Set background image default opacity to 100%
- Adjust timeline view to fit frame range
- Minimum omni file version
- Popup fbx f-stop
- Remove popup success

# 1.4.1 - (2024.04.16)

### Fix
- Sync camera of omni v1 files

# 1.4.0 - (2024.04.15)

### Features
- Support omni file v2.0.0
- Support usd camera import
- Support fbx camera import
- Support abc camera with different fps
- Import camera with any names

# 1.3.1 - (2023.11.21)

### Fix
- Blender 4.0 support

# 1.3.0 - (2023.07.16)

### Features
- Support usd/ply/stl import
- Rename add-on

# 1.2.0 - (2023.01.22)

### Features
- Support vertical camera
- Guide the user to download the latest version

# 1.1.0 - (2023.01.14)

### Features
- Scene fps match shot fps

# 1.0.1 - (2023.01.08)

### Fix
- Import .omni without missing files
- .omni import version check
- No frame offset video start
- 4:3 video display
- Video doesn't freeze after scene edit

# 1.0.0 - (2023.01.06)

### Features
- Import omniscient file (.omni) from dynamic menu
- Load camera (.abc)
- Load video (.mov)
- Load single geometry (.obj)
- Allow to correct not located files