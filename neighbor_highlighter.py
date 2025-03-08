from qgis.gui import QgsHighlight, QgsMapToolIdentify
from qgis.core import QgsGeometry
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import Qt
from qgis.utils import iface

class NeighborHighlighterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.highlights = []
        self.map_tool = None

    def initGui(self):
        # 创建工具栏按钮
        self.action = QAction(
            QIcon(":/plugins/NeighborHighlighter/icon.png"),
            "邻区高亮工具",
            self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        
        # 初始化地图工具
        self.map_tool = MapClickTool(self.iface.mapCanvas(), self)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.mapCanvas().unsetMapTool(self.map_tool)
        self.clear_highlights()

    def run(self):  # 函数定义开始（注意冒号）
        """主执行函数"""  # 文档字符串
        self.clear_highlights()  # 必须缩进
        layer = self.iface.activeLayer()
        
        if not layer:
            self.show_message("请先选择一个图层", level=2)
            return
        
        selected = layer.selectedFeatures()
        if not selected:
            self.show_message("请在地图上选择一个小区", level=1)
            return
        
        try:
            self.highlight_features(selected[0], layer)
            self.iface.mapCanvas().setMapTool(self.map_tool)
        except KeyError as e:
            self.show_message(f"字段缺失: {str(e)}", level=3)
        except Exception as e:
            self.show_message(f"未知错误: {str(e)}", level=3)

    def highlight_features(self, source_feature, layer):
        # 高亮主小区
        h_main = QgsHighlight(self.iface.mapCanvas(), source_feature, layer)
        h_main.setColor(QColor('#61DED0'))
        h_main.setWidth(3)
        self.highlights.append(h_main)

        # 处理邻区
        if 'neighhex' not in source_feature.fields().names():
            raise KeyError("字段 'neighhex' 不存在")
        
        neighbor_list = (source_feature['neighhex'] or '').split('|')
        for feat in layer.getFeatures():
            if feat['gcihex'] in neighbor_list:
                h = QgsHighlight(self.iface.mapCanvas(), feat, layer)
                h.setColor(QColor('black'))
                h.setWidth(2)
                self.highlights.append(h)

    def clear_highlights(self):
        for h in self.highlights:
            h.hide()
        self.highlights.clear()
        self.iface.mapCanvas().refresh()

    def show_message(self, msg, level=0):
        """显示消息 (0=Info, 1=Warning, 2=Critical)"""
        self.iface.messageBar().pushMessage(
            "邻区高亮工具",
            msg,
            level=level,
            duration=5
        )

class MapClickTool(QgsMapToolIdentify):
    """自定义地图点击工具"""
    def __init__(self, canvas, plugin):
        super().__init__(canvas)
        self.plugin = plugin

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            res = self.identify(
                event.x(), event.y(), 
                [self.plugin.iface.activeLayer()],
                QgsMapToolIdentify.TopDownAll
            )
            
            if res:
                self.plugin.highlight_features(res[0].mFeature, self.plugin.iface.activeLayer())
            else:
                self.plugin.clear_highlights()