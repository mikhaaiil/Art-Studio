from PyQt6.QtWidgets import *
from PyQt6.QtSql import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class ArtsDatabaseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        self.current_pixmap = None
        self.model = None
        self.init_ui()
        self.init_db()
        
    def init_db(self):
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('arts.sqlite')
        
        if not self.db.open():
            QMessageBox.critical(self, "Error", "Database connection failed")
            return False
    
        if not self.create_tables_if_needed():
            QMessageBox.critical(self, "Error", "Table creation failed")
            return False
            
        self.model = QSqlTableModel(self, self.db)
        self.update_model()
        return True

    def create_tables_if_needed(self):
        query = QSqlQuery(self.db)
        
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS artists (
                ArtistId INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL UNIQUE
            )
        """):
            return False
        
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS arts (
                Artld INTEGER PRIMARY KEY AUTOINCREMENT,
                Title TEXT NOT NULL,
                ArtistId INTEGER NOT NULL,
                Pixmap BLOB,
                FOREIGN KEY (ArtistId) REFERENCES artists(ArtistId)
            )
        """):
            return False
        
        self.add_sample_data_if_empty()
        return True

    def add_sample_data_if_empty(self):
        query = QSqlQuery(self.db)
        query.exec("SELECT COUNT(*) FROM artists")
        if query.next() and query.value(0) == 0:
            artists = ["Leonardo da Vinci", "Vincent van Gogh", "Pablo Picasso", "Claude Monet"]
            for artist in artists:
                query.prepare("INSERT INTO artists (Name) VALUES (?)")
                query.addBindValue(artist)
                query.exec()

    def update_model(self):
        if not self.model:
            return
            
        query = QSqlQuery(self.db)
        query.exec("""
            CREATE TEMPORARY VIEW IF NOT EXISTS arts_display AS
            SELECT a.Artld, a.Title, ar.Name as ArtistName, a.Pixmap, a.ArtistId
            FROM arts a
            LEFT JOIN artists ar ON a.ArtistId = ar.ArtistId
        """)
        
        self.model.setTable("arts_display")
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnRowChange)
        
        self.model.setHeaderData(0, Qt.Orientation.Horizontal, "ID")
        self.model.setHeaderData(1, Qt.Orientation.Horizontal, "Title")
        self.model.setHeaderData(2, Qt.Orientation.Horizontal, "Artist")
        self.model.setHeaderData(3, Qt.Orientation.Horizontal, "Image")
        
        if not self.model.select():
            print("Data selection error:", self.model.lastError().text())
        
        self.table_view.setModel(self.model)
        self.table_view.setColumnHidden(3, True)
        self.table_view.setColumnHidden(4, True)
        
        if self.table_view.selectionModel():
            self.table_view.selectionModel().selectionChanged.connect(self.show_details)
        
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by title or artist...")
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_edit)
        
        button_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Delete")
        self.edit_btn = QPushButton("Edit")
        self.refresh_btn = QPushButton("Refresh")
        
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.doubleClicked.connect(self.edit_record)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        details_label = QLabel("Artwork Details")
        details_label.setStyleSheet("font-weight: bold; font-size: 16px; margin: 10px;")
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(300, 300)
        self.image_label.setStyleSheet("QLabel { border: 2px solid #ccc; background-color: #f9f9f9; border-radius: 5px; }")
        self.image_label.setText("Select artwork to view")
        
        self.details_group = QGroupBox("Information")
        self.details_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        details_form = QFormLayout(self.details_group)
        
        self.id_label = QLabel("—")
        self.title_label = QLabel("—")
        self.artist_label = QLabel("—")
        
        details_form.addRow("ID:", self.id_label)
        details_form.addRow("Title:", self.title_label)
        details_form.addRow("Artist:", self.artist_label)
        
        left_layout.addLayout(search_layout)
        left_layout.addLayout(button_layout)
        left_layout.addWidget(self.table_view)
        
        right_layout.addWidget(details_label)
        right_layout.addWidget(self.image_label)
        right_layout.addWidget(self.details_group)
        right_layout.addStretch()
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
        
        self.delete_btn.clicked.connect(self.delete_record)
        self.edit_btn.clicked.connect(self.edit_record)
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.search_edit.textChanged.connect(self.search_records)
        
    def search_records(self):
        if not self.model:
            return
            
        search_text = self.search_edit.text().strip()
        if search_text:
            filter_str = f"Title LIKE '%{search_text}%' OR ArtistName LIKE '%{search_text}%'"
            self.model.setFilter(filter_str)
        else:
            self.model.setFilter("")
        
        self.model.select()
        
    def refresh_data(self):
        if self.model:
            self.model.select()
            self.clear_details()
        
    def show_details(self, selected=None, deselected=None):
        if not self.model:
            return
            
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            self.clear_details()
            return
            
        row = selected[0].row()
        record = self.model.record(row)
        
        self.id_label.setText(str(record.value("Artld")))
        self.title_label.setText(record.value("Title"))
        self.artist_label.setText(record.value("ArtistName"))
        
        pixmap_data = record.value("Pixmap")
        self.display_pixmap(pixmap_data)
        
    def display_pixmap(self, pixmap_data):
        if pixmap_data:
            try:
                pixmap = QPixmap()
                
                if isinstance(pixmap_data, QByteArray):
                    success = pixmap.loadFromData(pixmap_data)
                elif isinstance(pixmap_data, (bytes, bytearray)):
                    success = pixmap.loadFromData(pixmap_data)
                else:
                    self.image_label.setText("Unknown image format")
                    return
                
                if success and not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        self.image_label.width() - 20, 
                        self.image_label.height() - 20,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    self.current_pixmap = pixmap_data
                    return
                else:
                    self.image_label.setText("Image load error")
                    
            except Exception as e:
                self.image_label.setText("Image load error")
        
        self.image_label.setText("Image unavailable")
        self.current_pixmap = None
        
    def clear_details(self):
        self.id_label.setText("—")
        self.title_label.setText("—")
        self.artist_label.setText("—")
        self.image_label.clear()
        self.image_label.setText("Select artwork to view")
        self.current_pixmap = None
        
    def delete_record(self):
        if not self.model:
            return
            
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Warning", "Select record to delete")
            return
            
        row = selected[0].row()
        record = self.model.record(row)
        title = record.value("Title")
        artist_name = record.value("ArtistName")
        
        reply = QMessageBox.question(
            self, 
            "Confirm deletion", 
            f"Delete artwork?\n\nTitle: {title}\nArtist: {artist_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            art_id = record.value("Artld")
            query = QSqlQuery(self.db)
            query.prepare("DELETE FROM arts WHERE Artld = ?")
            query.addBindValue(art_id)
            
            if query.exec():
                self.model.select()
                self.clear_details()
                QMessageBox.information(self, "Success", "Record deleted")
            else:
                QMessageBox.critical(self, "Error", "Delete failed")
                
    def edit_record(self):
        if not self.model:
            return
            
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Warning", "Select record to edit")
            return
            
        row = selected[0].row()
        record = self.model.record(row)
        
        art_id = record.value("Artld")
        
        dialog = EditArtDialog(record, self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_title = record.value("Title")
            new_artist_id = record.value("ArtistId")
            query = QSqlQuery(self.db)
            query.prepare("UPDATE arts SET Title = ?, ArtistId = ? WHERE Artld = ?")
            query.addBindValue(new_title)
            query.addBindValue(new_artist_id)
            query.addBindValue(art_id)
            
            if query.exec():
                self.model.select()
                self.show_details()
            else:
                QMessageBox.critical(self, "Error", f"Update failed: {query.lastError().text()}")
    
    def get_or_create_artist(self, artist_name):
        if not artist_name or not artist_name.strip():
            return None
            
        query = QSqlQuery(self.db)
        query.prepare("SELECT ArtistId FROM artists WHERE Name = ?")
        query.addBindValue(artist_name.strip())
        
        if query.exec() and query.next():
            return query.value(0)
        else:
            query.prepare("INSERT INTO artists (Name) VALUES (?)")
            query.addBindValue(artist_name.strip())
            if query.exec():
                return query.lastInsertId()
            return None
            
    def add_art_record(self, title, artist_id, pixmap_data):
        if not self.model:
            return False
            
        if not artist_id:
            QMessageBox.critical(self, "Error", "Artist ID not specified")
            return False
            
        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO arts (Title, ArtistId, Pixmap) VALUES (?, ?, ?)")
        query.addBindValue(title)
        query.addBindValue(artist_id)
        
        if isinstance(pixmap_data, QByteArray):
            query.addBindValue(pixmap_data)
        elif isinstance(pixmap_data, (bytes, bytearray)):
            query.addBindValue(pixmap_data)
        else:
            query.addBindValue(QByteArray())
        
        if query.exec():
            self.model.select()
            self.table_view.selectRow(self.model.rowCount() - 1)
            return True
        else:
            QMessageBox.critical(self, "Error", f"Add failed: {query.lastError().text()}")
            return False

    def publish_art(self, args):
        title, artist_name, pixmap_data = args
        try:
            artist_id = self.get_or_create_artist(artist_name)
            if not artist_id:
                QMessageBox.critical(self, "Error", f"Failed to get/create artist: {artist_name}")
                return False
            
            success = self.add_art_record(title, artist_id, pixmap_data)
            
            if success:
                self.refresh_data()
                
            return success
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Publish error: {str(e)}")
            return False
            
    def get_artists_list(self):
        artists = []
        if not self.db:
            return artists
            
        query = QSqlQuery(self.db)
        query.exec("SELECT ArtistId, Name FROM artists ORDER BY Name")
        
        while query.next():
            artists.append({
                'id': query.value(0),
                'name': query.value(1)
            })
        return artists

    @staticmethod
    def pixmap_to_bytes(pixmap, format="PNG"):
        if pixmap.isNull():
            return None
            
        try:
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            
            success = pixmap.save(buffer, format)
            buffer.close()
            
            if success:
                return byte_array
            return None
                
        except Exception as e:
            return None

class EditArtDialog(QDialog):
    def __init__(self, record, db, parent=None):
        super().__init__(parent)
        self.record = record
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Edit Artwork")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.title_edit = QLineEdit(self.record.value("Title"))
        
        self.artist_combo = QComboBox()
        self.load_artists()
        
        current_artist_id = self.record.value("ArtistId")
        index = self.artist_combo.findData(current_artist_id)
        if index >= 0:
            self.artist_combo.setCurrentIndex(index)
        
        form_layout.addRow("Title:", self.title_edit)
        form_layout.addRow("Artist:", self.artist_combo)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_changes)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
        
    def load_artists(self):
        query = QSqlQuery(self.db)
        query.exec("SELECT ArtistId, Name FROM artists ORDER BY Name")
        
        while query.next():
            artist_id = query.value(0)
            artist_name = query.value(1)
            self.artist_combo.addItem(artist_name, artist_id)
            
    def save_changes(self):
        new_title = self.title_edit.text().strip()
        new_artist_id = self.artist_combo.currentData()
        
        if not new_title:
            QMessageBox.warning(self, "Error", "Enter title")
            return
            
        self.record.setValue("Title", new_title)
        self.record.setValue("ArtistId", new_artist_id)
        
        self.accept()