from PyQt6.QtWidgets import *
import sys
from tabs import DrawingTab, GalleryTab


class ArtStudio(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(900, 600)
        self.setWindowTitle("Art Studio")
        main_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.drawing_tab = DrawingTab()
        self.tab_widget.addTab(self.drawing_tab, "Drawing")
        self.gallery_tab = GalleryTab()
        self.tab_widget.addTab(self.gallery_tab, "Gallery")
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
        self.connect_signals()

    def connect_signals(self):
        self.drawing_tab.tool_panel.save_requested.connect(self.save_drawing)
        self.drawing_tab.drawing_area.publishRequest.connect(
            self.gallery_tab.database_widget.publish_art
        )

    def save_drawing(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "save art", "art.png", "Арт (*.png, *.jpg, *.svg)"
        )
        if filename:
            self.drawing_tab.drawing_area.pixmap.save(filename)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArtStudio()
    window.show()
    sys.exit(app.exec())
