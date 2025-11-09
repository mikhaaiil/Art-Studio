from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QCursor
from database import ArtsDatabaseWidget


class DrawingWidget(QWidget):
    publishRequest = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)

        self.drawing = False
        self.last_point = QPoint()
        self.pen_color = QColor(0, 0, 0)
        self.pen_width = 3
        self.tool = "pen"
        self.pixmap = QPixmap(600, 400)
        self.pixmap.fill(Qt.GlobalColor.white)
        self.temp_pixmap = QPixmap(600, 400)
        self.temp_pixmap.fill(Qt.GlobalColor.transparent)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.start_point = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            self.start_point = event.pos()

            if self.tool == "pen":
                self.draw_point(event.pos())

    def mouseMoveEvent(self, event):
        if self.drawing and event.buttons() & Qt.MouseButton.LeftButton:
            if self.tool == "pen":
                self.draw_line(self.last_point, event.pos())
                self.last_point = event.pos()
            elif self.tool == "eraser":
                self.erase(event.pos())
                self.last_point = event.pos()
            else:
                self.temp_pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(self.temp_pixmap)
                self.setup_painter(painter)

                if self.tool == "line":
                    painter.drawLine(self.start_point, event.pos())
                elif self.tool == "rectangle":
                    rect = QRect(self.start_point, event.pos()).normalized()
                    painter.drawRect(rect)
                elif self.tool == "ellipse":
                    rect = QRect(self.start_point, event.pos()).normalized()
                    painter.drawEllipse(rect)

                painter.end()
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False

            if self.tool in ["line", "rectangle", "ellipse"]:
                painter = QPainter(self.pixmap)
                self.setup_painter(painter)

                if self.tool == "line":
                    painter.drawLine(self.start_point, event.pos())
                elif self.tool == "rectangle":
                    rect = QRect(self.start_point, event.pos()).normalized()
                    painter.drawRect(rect)
                elif self.tool == "ellipse":
                    rect = QRect(self.start_point, event.pos()).normalized()
                    painter.drawEllipse(rect)

                painter.end()
                self.temp_pixmap.fill(Qt.GlobalColor.transparent)
                self.update()

    def draw_point(self, point):
        painter = QPainter(self.pixmap)
        self.setup_painter(painter)
        painter.drawPoint(point)
        painter.end()
        self.update()

    def draw_line(self, start, end):
        painter = QPainter(self.pixmap)
        self.setup_painter(painter)
        painter.drawLine(start, end)
        painter.end()
        self.update()

    def erase(self, point):
        painter = QPainter(self.pixmap)
        painter.setPen(QPen(Qt.GlobalColor.white, self.pen_width * 2))
        painter.drawPoint(point)
        painter.end()
        self.update()

    def setup_painter(self, painter):
        if self.tool == "eraser":
            painter.setPen(QPen(Qt.GlobalColor.white, self.pen_width * 2))
        else:
            painter.setPen(QPen(self.pen_color, self.pen_width,
                                Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                Qt.PenJoinStyle.RoundJoin))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)
        painter.drawPixmap(0, 0, self.temp_pixmap)

    def clear(self):
        self.pixmap.fill(Qt.GlobalColor.white)
        self.temp_pixmap.fill(Qt.GlobalColor.transparent)
        self.update()

    def set_tool(self, tool):
        self.tool = tool

    def set_pen_color(self, color):
        self.pen_color = color

    def set_pen_width(self, width):
        self.pen_width = width

    def resizeEvent(self, event):
        new_pixmap = QPixmap(self.size())
        new_pixmap.fill(Qt.GlobalColor.white)

        painter = QPainter(new_pixmap)
        painter.drawPixmap(0, 0, self.pixmap)
        painter.end()

        self.pixmap = new_pixmap
        self.temp_pixmap = QPixmap(self.size())
        self.temp_pixmap.fill(Qt.GlobalColor.transparent)
        super().resizeEvent(event)

    def publish_art(self, data):
        artist_name, art_name = data
        converted_pixmap = ArtsDatabaseWidget.pixmap_to_bytes(self.pixmap)
        self.publishRequest.emit((art_name, artist_name, converted_pixmap))


class ToolPanel(QWidget):
    tool_changed = pyqtSignal(str)
    color_changed = pyqtSignal(QColor)
    thickness_changed = pyqtSignal(int)
    clear_requested = pyqtSignal()
    save_requested = pyqtSignal()
    publish_requested = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setFixedWidth(200)
        layout = QVBoxLayout()

        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout()

        self.tool_group = QButtonGroup()

        tools = [
            ("Pen", "pen"),
            ("Line", "line"),
            ("Rectangle", "rectangle"),
            ("Ellipse", "ellipse"),
            ("Eraser", "eraser")
        ]

        for text, tool in tools:
            radio = QRadioButton(text)
            radio.tool = tool
            self.tool_group.addButton(radio)
            tools_layout.addWidget(radio)

        self.tool_group.buttons()[0].setChecked(True)
        self.tool_group.buttonClicked.connect(self.on_tool_changed)

        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)

        brush_group = QGroupBox("Brush settings")
        brush_layout = QVBoxLayout()

        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(30, 30)
        self.color_btn.setStyleSheet("background-color: black;")
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        brush_layout.addLayout(color_layout)

        thickness_layout = QHBoxLayout()
        thickness_layout.addWidget(QLabel("Width:"))

        self.thickness_slider = QSlider(Qt.Orientation.Horizontal)
        self.thickness_slider.setRange(1, 20)
        self.thickness_slider.setValue(3)
        self.thickness_slider.valueChanged.connect(self.on_thickness_changed)

        self.thickness_spin = QSpinBox()
        self.thickness_spin.setRange(1, 20)
        self.thickness_spin.setValue(3)
        self.thickness_spin.valueChanged.connect(
            self.on_thickness_spin_changed)

        thickness_layout.addWidget(self.thickness_slider)
        thickness_layout.addWidget(self.thickness_spin)
        brush_layout.addLayout(thickness_layout)

        brush_group.setLayout(brush_layout)
        layout.addWidget(brush_group)

        control_group = QGroupBox("Settings")
        control_layout = QVBoxLayout()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_requested.emit)
        control_layout.addWidget(clear_btn)

        save_btn = QPushButton("Save (to device)")
        save_btn.clicked.connect(self.save_requested.emit)
        control_layout.addWidget(save_btn)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        layout.addStretch()

        publish_group = QGroupBox("Publication")
        publish_layout = QVBoxLayout()

        self.art_name = QLineEdit()
        self.art_name.setPlaceholderText("Artwork name...")
        publish_layout.addWidget(self.art_name)

        self.artist_name = QLineEdit()
        self.artist_name.setPlaceholderText("Your nickname...")
        publish_layout.addWidget(self.artist_name)

        publish_btn = QPushButton("Publish")
        publish_btn.clicked.connect(self.prepare_publish)
        publish_layout.addWidget(publish_btn)

        publish_group.setLayout(publish_layout)
        layout.addWidget(publish_group)

        layout.addStretch()
        self.setLayout(layout)

    def on_tool_changed(self, button):
        self.tool_changed.emit(button.tool)

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_changed.emit(color)
            self.color_btn.setStyleSheet(f"background-color: {color.name()};")

    def on_thickness_changed(self, value):
        self.thickness_changed.emit(value)
        self.thickness_spin.setValue(value)

    def on_thickness_spin_changed(self, value):
        self.thickness_changed.emit(value)
        self.thickness_slider.setValue(value)

    def prepare_publish(self):
        self.publish_requested.emit(
            (self.artist_name.text(), self.art_name.text()))
