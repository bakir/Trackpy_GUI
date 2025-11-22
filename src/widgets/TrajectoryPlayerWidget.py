"""
Trajectory Player Widget - Memory Link Gallery

Description: Displays a gallery of high-memory links (particles that disappeared
for many frames before reappearing). Allows navigation through links and frames
within each link.
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
import os
import shutil
import cv2
import numpy as np
import json


class TrajectoryPlayerWidget(QWidget):
    """Widget for displaying memory link galleries."""

    def __init__(self, parent=None):
        """Initialize trajectory player widget.

        Parameters
        ----------
        parent : QWidget, optional
            Parent widget
        """
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None
        self.layout = QVBoxLayout(self)

        # Photo display for current frame
        self.photo_label = QLabel("No memory links available")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            "background-color: white; color: #333; border: 1px solid #555;"
        )
        self.photo_label.setMinimumHeight(300)
        self.photo_label.setScaledContents(False)
        self.layout.addWidget(self.photo_label)

        # Current link and frame display
        self.current_display_label = QLabel("Memory Link: 0 / 0 | Frame: 0 / 0")
        self.current_display_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.current_display_label)

        # Combined navigation controls
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()

        # Memory Link navigation
        nav_layout.addWidget(QLabel("Memory Link:"))
        self.prev_link_button = QPushButton("◀◀")
        self.prev_link_button.setFixedSize(40, 30)
        self.prev_link_button.clicked.connect(self.previous_link)
        nav_layout.addWidget(self.prev_link_button)

        # Frame navigation
        self.prev_frame_button = QPushButton("◀")
        self.prev_frame_button.setFixedSize(40, 30)
        self.prev_frame_button.clicked.connect(self.previous_frame)
        nav_layout.addWidget(self.prev_frame_button)

        self.frame_display = QLabel("0 / 0")
        self.frame_display.setAlignment(Qt.AlignCenter)
        self.frame_display.setMinimumWidth(60)
        nav_layout.addWidget(self.frame_display)

        self.next_frame_button = QPushButton("▶")
        self.next_frame_button.setFixedSize(40, 30)
        self.next_frame_button.clicked.connect(self.next_frame)
        nav_layout.addWidget(self.next_frame_button)

        self.next_link_button = QPushButton("▶▶")
        self.next_link_button.setFixedSize(40, 30)
        self.next_link_button.clicked.connect(self.next_link)
        nav_layout.addWidget(self.next_link_button)

        nav_layout.addStretch()
        self.layout.addLayout(nav_layout)

        # Store state
        self.current_pixmap = None
        self.memory_folder = None
        self.links = []  # List of link folders
        self.current_link_idx = 0
        self.current_frame_idx = 0
        self.current_link_frames = []  # List of frame files for current link

    def set_config_manager(self, config_manager):
        """Set the config manager for this widget.

        Parameters
        ----------
        config_manager : ConfigManager
            Configuration manager instance
        """
        self.config_manager = config_manager

    def set_file_controller(self, file_controller):
        """Set the file controller for this widget.

        Parameters
        ----------
        file_controller : FileController
            File controller instance
        """
        self.file_controller = file_controller
        if file_controller:
            self.memory_folder = file_controller.memory_folder
            self._load_links()

    def _load_links(self):
        """Load available memory links from the memory folder."""
        if not self.memory_folder or not os.path.exists(self.memory_folder):
            self.links = []
            self.current_link_frames = []
            self._update_display()
            return

        # Find all link folders (memory_link_0, memory_link_1, etc.)
        link_folders = []
        for item in sorted(os.listdir(self.memory_folder)):
            item_path = os.path.join(self.memory_folder, item)
            if os.path.isdir(item_path) and item.startswith("memory_link_"):
                link_folders.append(item_path)

        self.links = link_folders
        if len(self.links) > 0:
            self.current_link_idx = 0
            self._load_link_frames()
        else:
            self.current_link_frames = []
            self.photo_label.setText("No memory links available")
        self._update_display()

    def _load_link_frames(self):
        """Load frame files for the current link."""
        if self.current_link_idx < 0 or self.current_link_idx >= len(self.links):
            self.current_link_frames = []
            return

        link_folder = self.links[self.current_link_idx]
        frame_files = []
        
        # Get all frame files and sort by frame number (extracted from filename)
        for filename in sorted(os.listdir(link_folder)):
            if filename.startswith("frame_") and filename.lower().endswith(".jpg"):
                frame_path = os.path.join(link_folder, filename)
                if os.path.isfile(frame_path):
                    frame_files.append(frame_path)

        self.current_link_frames = frame_files
        if len(self.current_link_frames) > 0:
            self.current_frame_idx = 0
            self._display_current_frame()
        else:
            self.photo_label.setText(f"No frames in memory link {self.current_link_idx}")

    def _display_current_frame(self):
        """Display the current frame from the current link."""
        if (self.current_frame_idx < 0 or 
            self.current_frame_idx >= len(self.current_link_frames)):
            self.photo_label.setText("No Frames")
            return

        frame_path = self.current_link_frames[self.current_frame_idx]
        if not os.path.exists(frame_path):
            self.photo_label.setText("Frame file not found")
            return

        image = cv2.imread(frame_path)
        if image is None:
            self.photo_label.setText("Failed to load frame")
            return

        # Convert BGR (OpenCV default) to RGB for Qt display
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Convert to QPixmap
        height, width, channel = image_rgb.shape
        bytes_per_line = 3 * width
        q_image = QImage(image_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        if not pixmap.isNull():
            self.current_pixmap = pixmap
            scaled = pixmap.scaled(
                self.photo_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.photo_label.setPixmap(scaled)
        else:
            self.photo_label.setText("Failed to create pixmap")

    def _update_display(self):
        """Update the display labels."""
        # Update frame display
        if len(self.current_link_frames) > 0:
            self.frame_display.setText(f"{self.current_frame_idx} / {len(self.current_link_frames) - 1}")
        else:
            self.frame_display.setText("0 / 0")

        # Update combined display
        if len(self.links) > 0 and len(self.current_link_frames) > 0:
            frame_filename = os.path.basename(self.current_link_frames[self.current_frame_idx])
            # Extract frame number from filename (frame_00010.jpg -> 10)
            try:
                frame_num = int(frame_filename.split('_')[1].split('.')[0])
            except (ValueError, IndexError):
                frame_num = self.current_frame_idx
            self.current_display_label.setText(
                f"Memory Link: {self.current_link_idx} / {len(self.links) - 1} | "
                f"Frame: {self.current_frame_idx} / {len(self.current_link_frames) - 1} "
                f"(Original: {frame_num})"
            )
        else:
            self.current_display_label.setText("Memory Link: 0 / 0 | Frame: 0 / 0")

    def previous_link(self):
        """Go to previous link."""
        if len(self.links) == 0:
            return
        if self.current_link_idx > 0:
            self.current_link_idx -= 1
            self._load_link_frames()
            self._update_display()

    def next_link(self):
        """Go to next link."""
        if len(self.links) == 0:
            return
        if self.current_link_idx < len(self.links) - 1:
            self.current_link_idx += 1
            self._load_link_frames()
            self._update_display()

    def previous_frame(self):
        """Go to previous frame in current link."""
        if len(self.current_link_frames) == 0:
            return
        if self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            self._display_current_frame()
            self._update_display()

    def next_frame(self):
        """Go to next frame in current link."""
        if len(self.current_link_frames) == 0:
            return
        if self.current_frame_idx < len(self.current_link_frames) - 1:
            self.current_frame_idx += 1
            self._display_current_frame()
            self._update_display()

    def refresh_links(self):
        """Reload links from disk (called when trajectories are found)."""
        self._load_links()

    def resizeEvent(self, event):
        """Handle widget resize to update image display."""
        super().resizeEvent(event)
        if (
            self.current_pixmap is not None
            and not self.current_pixmap.isNull()
        ):
            scaled = self.current_pixmap.scaled(
                self.photo_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.photo_label.setPixmap(scaled)

    def reset_state(self):
        self.current_link_idx = 0
        self.current_frame_idx = 0
        self.refresh_links()
