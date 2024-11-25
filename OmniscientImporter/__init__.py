# Copyright (C) 2023 Stellaxis OÜ
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from . import auto_load

bl_info = {
    "name": "Import Omniscient(.omni)",
    "author": "Stellaxis OÜ",
    "description": "Import data recorded by the Omniscient iOS application.",
    "blender": (3, 0, 0),
    "version": (2, 3, 3),
    "location": "File > Import > Omniscient (.omni)",
    "warning": "",
    "category": "Import-Export"
}

auto_load.init()


def register():
    auto_load.register()


def unregister():
    auto_load.unregister()
