from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
import os
import sys
import cv2

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QFormLayout,
    QPushButton,
    QSlider,
    QLabel,
    QSplitter,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
    QLineEdit,

)
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6 import QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure

class ErrantParticleGalleryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)


            # photo
        self.photo_label = QLabel("Photo display")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            "background-color: #222; color: #ccc; border: 1px solid #555;"
        )
        self.photo_label.setMinimumHeight(200)
        self.photo_label.setScaledContents(True)
        self.layout.addWidget(self.photo_label)

        # --- Frame Navigation ---
        self.frame_nav_layout = QHBoxLayout()
        self.prev_frame_button = QPushButton("<")
        self.frame_number_display = QLineEdit("0")
        self.curr_particle_idx = 0
        self.frame_number_display.setReadOnly(True)
        self.frame_number_display.setAlignment(Qt.AlignCenter)
        self.next_frame_button = QPushButton("->")
        # self.prev_frame_button.clicked.connect(self.prev_frame)
        self.next_frame_button.clicked.connect(self.next_particle)
        self.frame_nav_layout.addWidget(self.prev_frame_button)
        self.frame_nav_layout.addWidget(self.frame_number_display)
        self.frame_nav_layout.addWidget(self.next_frame_button)
        self.layout.addLayout(self.frame_nav_layout)

        # particles directory and files
        self.particles_dir = os.path.join(os.path.dirname(__file__), "particles")
        self.particle_files = self._load_particle_files(self.particles_dir)

        # show initial particle if available
        self._display_particle(self.curr_particle_idx)

    def _load_particle_files(self, directory_path):
        """Return a sorted list of image file paths in the particles directory."""
        if not os.path.isdir(directory_path):
            return []
        valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
        files = []
        try:
            for name in os.listdir(directory_path):
                root, ext = os.path.splitext(name)
                if ext.lower() in valid_exts:
                    files.append(os.path.join(directory_path, name))
        except Exception:
            return []
        files.sort()
        return files

    def _display_particle(self, index):
        """Update UI to display particle image and index if within bounds."""
        if 0 <= index < len(self.particle_files):
            file_path = self.particle_files[index]
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # scale to fit while keeping aspect ratio
                scaled = pixmap.scaled(self.photo_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.photo_label.setPixmap(scaled)
            else:
                self.photo_label.setText("Failed to load image")
            self.frame_number_display.setText(str(index))
        else:
            # out of bounds or no files
            if not self.particle_files:
                self.photo_label.setText("No particle images found")
            self.frame_number_display.setText(str(self.curr_particle_idx))

    def next_particle(self):
        """Advance to the next particle and update display."""
        if not self.particle_files:
            return
        if self.curr_particle_idx < len(self.particle_files) - 1:
            self.curr_particle_idx += 1
            self._display_particle(self.curr_particle_idx)
        else:
            # already at last image; do nothing
            pass
