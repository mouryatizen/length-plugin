# -*- coding: utf-8 -*-
def classFactory(iface):
    from .length_plugin import LengthPlugin
    return LengthPlugin(iface)
