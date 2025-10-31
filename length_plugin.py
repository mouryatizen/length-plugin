\
    # -*- coding: utf-8 -*-
    """
    QGIS plugin 'Length' - version 1.0
    - Works on QGIS 3.x and later
    - For the selected layer checks if PHOTO_ID column exists
    - Runs: native:pointstopath (order by PHOTO_ID) -> native:explodelines -> native:fieldcalculator (new field LENGTH = $length)
    - Adds resulting layer to project and starts editing on the final 'Exploded' layer
    """
    from qgis.PyQt.QtWidgets import QAction, QMessageBox
    from qgis.core import QgsProject, QgsVectorLayer
    import processing
    import os

    class LengthPlugin:
        def __init__(self, iface):
            self.iface = iface
            self.plugin_dir = os.path.dirname(__file__)
            self.action = None

        def initGui(self):
            icon = None
            self.action = QAction("Length", self.iface.mainWindow())
            self.action.triggered.connect(self.run)
            self.iface.addPluginToMenu("&Length", self.action)
            self.iface.addToolBarIcon(self.action)

        def unload(self):
            if self.action:
                self.iface.removePluginMenu("&Length", self.action)
                self.iface.removeToolBarIcon(self.action)

        def _show_error(self, text):
            QMessageBox.critical(self.iface.mainWindow(), "Length plugin - Error", text)

        def _show_info(self, text):
            QMessageBox.information(self.iface.mainWindow(), "Length plugin", text)

        def run(self):
            layer = self.iface.activeLayer()
            if not layer:
                self._show_error("No active layer selected. Please select a point layer.")
                return

            # Check PHOTO_ID exists
            fields = [f.name() for f in layer.fields()]
            if "PHOTO_ID" not in fields:
                self._show_error("PHOTO_ID column not found")
                return

            # Keep snapshot of existing layer IDs to detect new layers added by processing
            project = QgsProject.instance()
            existing_ids = set(project.mapLayers().keys())

            try:
                # 1) Points to Path
                params_ptp = {
                    'INPUT': layer,
                    'ORDER_EXPRESSION': '"PHOTO_ID"',
                    'GROUP_EXPRESSION': None,
                    'CLOSE_PATH': False,
                    'OUTPUT': 'memory:'
                }
                res1 = processing.run("native:pointstopath", params_ptp)
                # 2) Explode Lines
                params_explode = {
                    'INPUT': res1['OUTPUT'],
                    'OUTPUT': 'memory:'
                }
                res2 = processing.run("native:explodelines", params_explode)

                # 3) Add LENGTH field and populate with $length using Field Calculator
                params_fc = {
                    'INPUT': res2['OUTPUT'],
                    'FIELD_NAME': 'LENGTH',
                    'FIELD_TYPE': 1,            # 0=int, 1=float/double
                    'FIELD_LENGTH': 24,
                    'FIELD_PRECISION': 6,
                    'NEW_FIELD': True,
                    'FORMULA': '$length',
                    'OUTPUT': 'memory:'
                }
                res3 = processing.run("native:fieldcalculator", params_fc)

                # Add the final layer to the project (run may already register it in the project, but ensure it's visible)
                final_output_ref = res3['OUTPUT']
                # Attempt to create a QgsVectorLayer object for the memory output and add if not present
                final_layer = None
                try:
                    # If processing returned an actual layer object, use it
                    if isinstance(final_output_ref, QgsVectorLayer):
                        final_layer = final_output_ref
                    else:
                        # Try to load the layer by its result path (may be 'memory:' or temporary path)
                        final_layer = QgsVectorLayer(final_output_ref, "Exploded_with_LENGTH", "memory")
                except Exception:
                    final_layer = None

                # If we don't have a valid final_layer object, try to find new layer(s) added to the project
                new_layers = []
                after_ids = set(project.mapLayers().keys())
                added = after_ids - existing_ids
                for lid in added:
                    lyr = project.mapLayer(lid)
                    if lyr and lyr.type() == lyr.VectorLayer:
                        new_layers.append(lyr)

                if final_layer and final_layer.isValid():
                    # If final_layer isn't already in the project, add it
                    if final_layer.id() not in project.mapLayers().keys():
                        project.addMapLayer(final_layer)
                elif new_layers:
                    # Prefer the last added vector layer as the final layer
                    final_layer = new_layers[-1]

                if not final_layer or not final_layer.isValid():
                    self._show_error("Failed to create final 'Exploded' layer with LENGTH field. Check processing providers are available.")
                    return

                # Start editing the final layer (as requested)
                try:
                    if not final_layer.isEditable():
                        final_layer.startEditing()
                except Exception:
                    # Some memory layers may not support startEditing; ignore safely
                    pass

                self._show_info("Completed: 'Points to Path' -> 'Explode Lines' -> Added 'LENGTH' field and populated with $length. Final layer: '{}'".format(final_layer.name()))
            except Exception as e:
                self._show_error("An error occurred while running processing algorithms:\\n{}".format(str(e)))
