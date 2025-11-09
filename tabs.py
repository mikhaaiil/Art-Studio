from PyQt6.QtWidgets import *
from drawing_widgets import ToolPanel, DrawingWidget
from database import ArtsDatabaseWidget


class DrawingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        self.drawing_area = DrawingWidget()
        main_layout.addWidget(self.drawing_area)
        self.tool_panel = ToolPanel()
        main_layout.addWidget(self.tool_panel, 1)
        self.setLayout(main_layout)
        self.connect_signals()

    def connect_signals(self):
        self.tool_panel.tool_changed.connect(self.drawing_area.set_tool)
        self.tool_panel.color_changed.connect(self.drawing_area.set_pen_color)
        self.tool_panel.thickness_changed.connect(
            self.drawing_area.set_pen_width
        )
        self.tool_panel.clear_requested.connect(self.drawing_area.clear)
        self.tool_panel.publish_requested.connect(
            self.drawing_area.publish_art
        )


class GalleryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        self.database_widget = ArtsDatabaseWidget()
        main_layout.addWidget(self.database_widget)
        self.setLayout(main_layout)
