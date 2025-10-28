"""
Errant particle gallery widget

Description: Widget displaying errant particles to inform user if particle tracking parameters need adjustment.
             Generated boiler plate code using Cursor AI.
"""

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
from PySide6 import QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure

import particle_processing
from config_parser import get_config
config = get_config()
PARTICLES_FOLDER = config.get('particles_folder', 'particles/')

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
        self.photo_label.setScaledContents(False)
        self.layout.addWidget(self.photo_label)

        # info
        self.info_label = QLabel("Info")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.info_label)

        # --- Frame Navigation ---
        self.frame_nav_layout = QHBoxLayout()
        self.prev_frame_button = QPushButton("<")
        self.frame_number_display = QLineEdit("0 / 0")
        self.curr_particle_idx = 0
        self.frame_number_display.setReadOnly(False)
        self.frame_number_display.setAlignment(Qt.AlignCenter)
        self.next_frame_button = QPushButton("->")
        self.prev_frame_button.clicked.connect(self.prev_particle)
        self.next_frame_button.clicked.connect(self.next_particle)
        self.frame_number_display.returnPressed.connect(self._jump_to_input_particle)
        self.frame_number_display.editingFinished.connect(self._jump_to_input_particle)
        self.frame_nav_layout.addWidget(self.prev_frame_button)
        self.frame_nav_layout.addWidget(self.frame_number_display)
        self.frame_nav_layout.addWidget(self.next_frame_button)
        self.layout.addLayout(self.frame_nav_layout)

        # particles directory and files
        self.particles_dir = PARTICLES_FOLDER
        self.particle_files = self._load_particle_files(self.particles_dir)
        self.current_pixmap = None

        # show initial particle if available
        self._display_particle(self.curr_particle_idx)

    def refresh_particles(self):
        """Reload the list of particle image files and refresh display."""
        self.particle_files = self._load_particle_files(self.particles_dir)
        # clamp current index within bounds
        if self.particle_files:
            self.curr_particle_idx = min(self.curr_particle_idx, len(self.particle_files) - 1)
        else:
            self.curr_particle_idx = 0
        self._display_particle(self.curr_particle_idx)

    def clear_gallery(self):
        """Clears all displayed errant particles and deletes the corresponding files."""
        try:
            particle_processing.delete_all_files_in_folder(self.particles_dir)
            self.particle_files = []
            self.curr_particle_idx = 0
            self._display_particle(self.curr_particle_idx)
            print(f"Cleared errant particle gallery and deleted files in {self.particles_dir}")
        except Exception as e:
            print(f"Error clearing errant particle gallery: {e}")

    def _load_particle_files(self, directory_path):
        """Return a sorted list of image file paths in the particles directory."""
        if not os.path.isdir(directory_path):
            return []
        valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
        files = []
        try:
            for name in os.listdir(directory_path):
                if os.path.splitext(name)[1].lower() in valid_exts:
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
                self.current_pixmap = pixmap
                # scale to fit while keeping aspect ratio
                scaled = self.current_pixmap.scaled(self.photo_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.photo_label.setPixmap(scaled)
            else:
                self.photo_label.setText("Failed to load image")
            
            # Load and display info
            info_path = os.path.splitext(file_path)[0] + ".txt"
            if os.path.exists(info_path):
                with open(info_path, 'r') as f:
                    self.info_label.setText(f.read())
            else:
                self.info_label.setText("")

            self._update_display_text()
        else:
            # out of bounds or no files
            if not self.particle_files:
                self.photo_label.setText("No particle images found")
            self.info_label.setText("")
            self._update_display_text()

    def resizeEvent(self, event):
        """Ensure the currently shown image keeps aspect ratio on resize."""
        super().resizeEvent(event)
        if self.current_pixmap is not None and not self.current_pixmap.isNull():
            scaled = self.current_pixmap.scaled(
                self.photo_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.photo_label.setPixmap(scaled)

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

    def prev_particle(self):
        """Go to the previous particle and update display."""
        if not self.particle_files:
            return
        if self.curr_particle_idx > 0:
            self.curr_particle_idx -= 1
            self._display_particle(self.curr_particle_idx)
        else:
            # already at first image; do nothing
            pass

    def _update_display_text(self):
        total = len(self.particle_files)
        text = f"{self.curr_particle_idx} / {total}"
        # avoid recursive signals while editing
        old_block = self.frame_number_display.blockSignals(True)
        self.frame_number_display.setText(text)
        self.frame_number_display.blockSignals(old_block)

    def _jump_to_input_particle(self):
        """Parse the input and jump to the requested particle index if valid."""
        text = self.frame_number_display.text().strip()
        # Accept formats like "12" or "12 / 200"
        if "/" in text:
            first = text.split("/", 1)[0].strip()
        else:
            first = text
        try:
            requested = int(first)
        except ValueError:
            # restore correct text
            self._update_display_text()
            return
        total = len(self.particle_files)
        if total == 0:
            self._update_display_text()
            return
        # clamp to valid range
        requested = max(0, min(requested, total - 1))
        if requested != self.curr_particle_idx:
            self.curr_particle_idx = requested
            self._display_particle(self.curr_particle_idx)
        else:
            # even if unchanged, ensure text format is correct
            self._update_display_text()