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
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QPen
import os
import shutil
import cv2
import numpy as np


class OverlayLabel(QLabel):
    """A custom QLabel that can draw overlays on top of its pixmap."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_pos = None
        self.end_pos = None
        self.crop_origin = None
        self._pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()  # Trigger a repaint

    def pixmap(self):
        return self._pixmap

    def set_overlay_data(self, start_pos, end_pos, crop_origin):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.crop_origin = crop_origin
        self.update()

    def paintEvent(self, event):
        # First, draw the label's default content (like text if no pixmap)
        super().paintEvent(event)

        if self._pixmap is None or self._pixmap.isNull():
            return

        painter = QPainter(self)
        
        # Calculate the scaled pixmap's rect to draw it centered
        pixmap_size = self._pixmap.size()
        widget_size = self.size()
        
        scaled_pixmap = self._pixmap.scaled(widget_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        x = (widget_size.width() - scaled_pixmap.width()) / 2
        y = (widget_size.height() - scaled_pixmap.height()) / 2
        
        # Draw the pixmap
        painter.drawPixmap(x, y, scaled_pixmap)

        # Now draw the overlay if data is available
        if self.start_pos and self.end_pos and self.crop_origin:
            
            # Calculate scaling factor of the displayed image
            scale_w = scaled_pixmap.width() / pixmap_size.width()
            scale_h = scaled_pixmap.height() / pixmap_size.height()
            scale = min(scale_w, scale_h)

            # Transform coordinates from original full-frame to widget space
            def transform(pos_str):
                # 1. Relative to crop origin
                rel_x = pos_str[0] - self.crop_origin[0]
                rel_y = pos_str[1] - self.crop_origin[1]
                
                # 2. Scale to displayed pixmap size and add offset
                widget_x = (rel_x * scale) + x
                widget_y = (rel_y * scale) + y
                return QPoint(int(widget_x), int(widget_y))

            painter.setPen(Qt.NoPen) # No outline for a solid dot
            painter.setBrush(QColor(255, 255, 0)) # Yellow fill

            # Draw filled circles (dots) with 4-pixel diameter (radius 2)
            # QPainter.drawEllipse takes QPoint and two radii (rx, ry)
            # For a 4-pixel diameter, radius is 2.
            painter.drawEllipse(transform(self.start_pos), 2, 2)
            painter.drawEllipse(transform(self.end_pos), 2, 2)


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
        self.photo_label = OverlayLabel("No memory links available")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            "background-color: white; color: #333; border: 1px solid #555;"
        )
        self.photo_label.setMinimumHeight(300)
        self.layout.addWidget(self.photo_label)

        # Current link and frame display
        self.current_display_label = QLabel("Particle ID: N/A | Memory Link: 0 / 0 | Frame: 0 / 0")
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
        self.memory_folder = None
        self.links = []  # List of link folders
        self.link_data = {} # Dict to store data for each link
        self.current_link_idx = 0
        self.current_frame_idx = 0
        self.current_link_frames = []  # List of frame files for current link

    def set_config_manager(self, config_manager):
        self.config_manager = config_manager

    def set_file_controller(self, file_controller):
        self.file_controller = file_controller
        if file_controller:
            self.memory_folder = file_controller.memory_folder
            self._load_links()

    def _load_links(self):
        """Load available memory links and their metadata from the memory folder."""
        if not self.memory_folder or not os.path.exists(self.memory_folder):
            self.links = []
            self.link_data = {}
            self.current_link_frames = []
            self._update_display()
            return

        link_folders = []
        self.link_data = {}
        for item in sorted(os.listdir(self.memory_folder)):
            item_path = os.path.join(self.memory_folder, item)
            if os.path.isdir(item_path) and item.startswith("memory_link_"):
                link_idx = len(link_folders)
                link_folders.append(item_path)
                
                # Helper to read and parse metadata files
                def read_file(path):
                    if not os.path.exists(path): return None
                    with open(path, 'r') as f: return f.read().strip()

                def parse_coords(s):
                    if not s: return None
                    try: return tuple(map(float, s.split(',')))
                    except (ValueError, IndexError): return None

                # Load all metadata
                pid = read_file(os.path.join(item_path, "particle_id.txt"))
                start_pos = parse_coords(read_file(os.path.join(item_path, "start_pos.txt")))
                end_pos = parse_coords(read_file(os.path.join(item_path, "end_pos.txt")))
                crop_origin = parse_coords(read_file(os.path.join(item_path, "crop_origin.txt")))

                self.link_data[link_idx] = {
                    'particle_id': pid or "N/A",
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'crop_origin': crop_origin
                }

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
        frame_files = [os.path.join(link_folder, f) for f in sorted(os.listdir(link_folder)) if f.startswith("frame_") and f.lower().endswith(".jpg")]

        self.current_link_frames = frame_files
        if len(self.current_link_frames) > 0:
            self.current_frame_idx = 0
            self._display_current_frame()
        else:
            self.photo_label.setText(f"No frames in memory link {self.current_link_idx}")

    def _display_current_frame(self):
        """Display the current frame and pass overlay data to the label."""
        if (self.current_frame_idx < 0 or 
            self.current_frame_idx >= len(self.current_link_frames)):
            self.photo_label.setPixmap(None)
            self.photo_label.setText("No Frames")
            return

        frame_path = self.current_link_frames[self.current_frame_idx]
        if not os.path.exists(frame_path):
            self.photo_label.setPixmap(None)
            self.photo_label.setText("Frame file not found")
            return

        image = cv2.imread(frame_path)
        if image is None:
            self.photo_label.setPixmap(None)
            self.photo_label.setText("Failed to load frame")
            return

        # Convert BGR (OpenCV) to RGB for Qt
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, channel = image_rgb.shape
        bytes_per_line = 3 * width
        q_image = QImage(image_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        # Get overlay data for the current link
        current_link_data = self.link_data.get(self.current_link_idx, {})
        start_pos = current_link_data.get('start_pos')
        end_pos = current_link_data.get('end_pos')
        crop_origin = current_link_data.get('crop_origin')

        # Pass data to the overlay label
        self.photo_label.set_overlay_data(start_pos, end_pos, crop_origin)
        
        if not pixmap.isNull():
            self.photo_label.setPixmap(pixmap)
        else:
            self.photo_label.setPixmap(None)
            self.photo_label.setText("Failed to create pixmap")

    def _update_display(self):
        """Update the display labels."""
        if len(self.current_link_frames) > 0:
            self.frame_display.setText(f"{self.current_frame_idx} / {len(self.current_link_frames) - 1}")
        else:
            self.frame_display.setText("0 / 0")

        if len(self.links) > 0 and len(self.current_link_frames) > 0:
            frame_filename = os.path.basename(self.current_link_frames[self.current_frame_idx])
            try:
                frame_num = int(frame_filename.split('_')[1].split('.')[0])
            except (ValueError, IndexError):
                frame_num = self.current_frame_idx
            
            particle_id = self.link_data.get(self.current_link_idx, {}).get('particle_id', 'N/A')

            self.current_display_label.setText(
                f"Particle ID: {particle_id} | "
                f"Memory Link: {self.current_link_idx} / {len(self.links) - 1} | "
                f"Frame: {self.current_frame_idx} / {len(self.current_link_frames) - 1} "
                f"(Original: {frame_num})"
            )
        else:
            self.current_display_label.setText("Particle ID: N/A | Memory Link: 0 / 0 | Frame: 0 / 0")

    def previous_link(self):
        if len(self.links) > 0 and self.current_link_idx > 0:
            self.current_link_idx -= 1
            self._load_link_frames()
            self._update_display()

    def next_link(self):
        if len(self.links) > 0 and self.current_link_idx < len(self.links) - 1:
            self.current_link_idx += 1
            self._load_link_frames()
            self._update_display()

    def previous_frame(self):
        if len(self.current_link_frames) > 0 and self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            self._display_current_frame()
            self._update_display()

    def next_frame(self):
        if len(self.current_link_frames) > 0 and self.current_frame_idx < len(self.current_link_frames) - 1:
            self.current_frame_idx += 1
            self._display_current_frame()
            self._update_display()

    def refresh_links(self):
        self._load_links()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # The paintEvent of OverlayLabel will handle the scaling,
        # but we need to trigger a repaint.
        self.photo_label.update()

    def reset_state(self):
        self.current_link_idx = 0
        self.current_frame_idx = 0
        self.refresh_links()
