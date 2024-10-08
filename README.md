# Omniscient Blender &middot; [![GitHub license](https://img.shields.io/badge/license-GPL-blue.svg)](LICENSE)

An add-on to easily import shots, with their corresponding tracking datas and LiDAR scans recorded with the [Omniscient iOS app](https://omniscient-app.com/), into Blender.

## Compatibility

The Omniscient Blender addon is compatible with Blender 3.0 and above.

## Installation

To install the Omniscient Blender addon, you have two choices:

### Option 1: Install from Blender Extension Market (Recommended, requires Blender 4.2+)

1. Go to the [Omniscient Importer add-on page](https://extensions.blender.org/add-ons/omniscient/).
2. Click on the "Get Add-on" button.

### Option 2: Manual Installation

1. Download the latest release from the [releases page](https://github.com/Stellaxis/omniscient-blender/releases).
2. In Blender, go to Edit > Preferences > Add-ons.
3. Click the Install button and select the downloaded file.
4. Enable the add-on by checking the box next to it in the list of installed add-ons.

## Usage

To use the Omniscient Blender addon, follow these steps:

1. Launch the [Omniscient iOS app](https://omniscient-app.com/) and capture your shots.
2. Export the videos, cameras and geometries from the app.
3. In Blender, go to File > Import > Omniscient (.omni).
4. Select the exported .omni file.
5. The tracked data will be imported in the scene.

## Packaging the addon

To package the addon into a zip file, use the package.py script provided in the repository.

## Support

For support with the Omniscient Blender addon, please contact us through our [website](https://omniscient-app.com/) or open an issue on the [GitHub repository](https://github.com/Stellaxis/omniscient-blender/issues).

## Contributing

We welcome contributions to the Omniscient Blender addon.

Please follow Flake8 rules to ensure code quality and consistency.

### Checking Code Compliance

To check the compliance of your code with Flake8 rules, follow these steps:

1. Install Flake8:

    ```bash
    python -m pip install flake8
    ```

2. Run Flake8 on your code:

    ```bash
    flake8 .
    ```

## License

The Omniscient Blender addon is licensed under the [GPL License](LICENSE).