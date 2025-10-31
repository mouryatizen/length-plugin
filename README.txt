Length QGIS plugin (version 1)
------------------------------
Installation:
1. Unzip the directory 'length' into your QGIS plugins folder (e.g. ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/)
2. Restart QGIS and enable the plugin from Plugin Manager.
Usage:
1. Select a point layer in the Layers panel that contains a field named 'PHOTO_ID'.
2. Click Plugins -> Length -> Length (or use the toolbar icon if visible).
The plugin will run 'Points to Path' ordered by PHOTO_ID, then 'Explode Lines', then add a new field 'LENGTH' with values from $length.
