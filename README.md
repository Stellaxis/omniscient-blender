# Omniscient Blender &middot; [![GitHub license](https://img.shields.io/badge/license-GPL-blue.svg)](LICENSE)

An add-on to easily import shots, with their corresponding tracking datas and LiDAR scans recorded with the [Omniscient iOS app](https://omniscient-app.com/), into Blender.

## Compatibility

The Omniscient Blender addon is compatible with Blender 3.0 and above.

## Installation

To install the Omniscient Blender addon, follow these steps:

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

To package the addon into a zip file, use the package.py script provided in the repository. Unzip the outup zip. Rename the unziped folder to "OmniscientImporter". Zip the "OmniscientImporter" folder and rename the resulting zip with the name of the inital zip file generated with package.py.

## Support

For support with the Omniscient Blender addon, please contact us through our [website](https://omniscient-app.com/) or open an issue on the [GitHub repository](https://github.com/Stellaxis/omniscient-blender/issues).

## Contributing

We welcome contributions to the Omniscient Blender addon.

## License

The Omniscient Blender addon is licensed under the [GPL License](LICENSE).