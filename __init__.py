# -*- coding: utf-8 -*-
def classFactory(iface):
    """插件入口函数，必须存在且命名正确"""
    from .neighbor_highlighter import NeighborHighlighterPlugin
    return NeighborHighlighterPlugin(iface)