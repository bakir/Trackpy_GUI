from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import os
from config_parser import get_config

class ErrantTrajectoryGalleryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        # Photo display for RB overlay images
        self.photo_label = QLabel("RB Overlay Display")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            "background-color: #222; color: #ccc; border: 1px solid #555;"
        )
        self.photo_label.setMinimumHeight(200)
        self.photo_label.setScaledContents(False)
        self.layout.addWidget(self.photo_label)

        # Navigation controls
        self.nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("<")
        self.trajectory_display = QLineEdit("0 / 0")
        self.curr_trajectory_idx = 0
        self.trajectory_display.setReadOnly(False)
        self.trajectory_display.setAlignment(Qt.AlignCenter)
        self.next_button = QPushButton("->")
        self.prev_button.clicked.connect(self.prev_trajectory)
        self.next_button.clicked.connect(self.next_trajectory)
        self.trajectory_display.returnPressed.connect(self._jump_to_input_trajectory)
        self.trajectory_display.editingFinished.connect(self._jump_to_input_trajectory)
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addWidget(self.trajectory_display)
        self.nav_layout.addWidget(self.next_button)
        self.layout.addLayout(self.nav_layout)

        # RB gallery directory and files
        config = get_config()
        self.rb_gallery_dir = config.get('rb_gallery_folder', 'rb_gallery')
        self.rb_gallery_files = self._load_rb_gallery_files(self.rb_gallery_dir)
        self.current_pixmap = None

        # Show initial trajectory if available
        self._display_trajectory(self.curr_trajectory_idx)

    def _load_rb_gallery_files(self, directory_path):
        """Return a sorted list of RB overlay image file paths."""
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

    def _display_trajectory(self, index):
        """Update UI to display RB overlay image and index if within bounds."""
        if 0 <= index < len(self.rb_gallery_files):
            file_path = self.rb_gallery_files[index]
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.current_pixmap = pixmap
                # Scale to fit while keeping aspect ratio
                scaled = self.current_pixmap.scaled(
                    self.photo_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.photo_label.setPixmap(scaled)
            else:
                self.photo_label.setText("Failed to load RB overlay image")
            self._update_display_text()
        else:
            # Out of bounds or no files
            if not self.rb_gallery_files:
                self.photo_label.setText("No RB overlay images found")
            self._update_display_text()

    def _update_display_text(self):
        total = len(self.rb_gallery_files)
        text = f"{self.curr_trajectory_idx} / {total}"
        # Avoid recursive signals while editing
        old_block = self.trajectory_display.blockSignals(True)
        self.trajectory_display.setText(text)
        self.trajectory_display.blockSignals(old_block)

    def _jump_to_input_trajectory(self):
        """Parse the input and jump to the requested trajectory index if valid."""
        text = self.trajectory_display.text().strip()
        # Accept formats like "12" or "12 / 200"
        if "/" in text:
            first = text.split("/", 1)[0].strip()
        else:
            first = text
        try:
            requested = int(first)
        except ValueError:
            # Restore correct text
            self._update_display_text()
            return
        total = len(self.rb_gallery_files)
        if total == 0:
            self._update_display_text()
            return
        # Clamp to valid range
        requested = max(0, min(requested, total - 1))
        if requested != self.curr_trajectory_idx:
            self.curr_trajectory_idx = requested
            self._display_trajectory(self.curr_trajectory_idx)
        else:
            # Even if unchanged, ensure text format is correct
            self._update_display_text()

    def next_trajectory(self):
        """Advance to the next trajectory and update display."""
        if not self.rb_gallery_files:
            return
        if self.curr_trajectory_idx < len(self.rb_gallery_files) - 1:
            self.curr_trajectory_idx += 1
            self._display_trajectory(self.curr_trajectory_idx)
        else:
            # Already at last image; do nothing
            pass

    def prev_trajectory(self):
        """Go to the previous trajectory and update display."""
        if not self.rb_gallery_files:
            return
        if self.curr_trajectory_idx > 0:
            self.curr_trajectory_idx -= 1
            self._display_trajectory(self.curr_trajectory_idx)
        else:
            # Already at first image; do nothing
            pass

    def refresh_rb_gallery(self):
        """Reload the list of RB overlay image files and refresh display."""
        self.rb_gallery_files = self._load_rb_gallery_files(self.rb_gallery_dir)
        # Clamp current index within bounds
        if self.rb_gallery_files:
            self.curr_trajectory_idx = min(self.curr_trajectory_idx, len(self.rb_gallery_files) - 1)
        else:
            self.curr_trajectory_idx = 0
        self._display_trajectory(self.curr_trajectory_idx)

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
