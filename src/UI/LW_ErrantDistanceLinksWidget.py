"""
Errant Trajectory Gallery Widget

Description: GUI widget highlighting potentially errant linkings by overlaying red and blue frames with transparency.
             Boiler plate code built with Cursor.

This widget provides an image gallery interface for reviewing trajectory linking
quality through red-blue overlay visualizations.
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QSlider,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
import cv2
import numpy as np
import os
import json

from ..utils.ScaledLabel import ScaledLabel


class LWErrantDistanceLinksWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None

        self.layout = QVBoxLayout(self)

        # Photo display for RB overlay images
        self.photo_label = ScaledLabel("RB Overlay Display")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.photo_label, 1)

        # Info display (similar to ErrantParticleGalleryWidget)
        self.info_label = QLabel("Info")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)

        # Threshold slider
        self.threshold_layout = QHBoxLayout()
        self.threshold_label = QLabel("Threshold: 50%")
        self.threshold_label.setMinimumWidth(100)
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(50)
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)
        self.threshold_layout.addWidget(self.threshold_label)
        self.threshold_layout.addWidget(self.threshold_slider)
        self.layout.addLayout(self.threshold_layout)

        # Navigation controls
        self.nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("◀")
        self.trajectory_display = QLineEdit("0 / 0")
        self.curr_link_idx = 0
        self.trajectory_display.setReadOnly(False)
        self.trajectory_display.setAlignment(Qt.AlignCenter)
        self.next_button = QPushButton("▶")
        self.prev_button.clicked.connect(self.prev_link)
        self.next_button.clicked.connect(self.next_link)
        self.trajectory_display.returnPressed.connect(
            self._jump_to_input_link
        )
        self.trajectory_display.editingFinished.connect(
            self._jump_to_input_link
        )
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addWidget(self.trajectory_display)
        self.nav_layout.addWidget(self.next_button)
        self.layout.addLayout(self.nav_layout)
        
        # This list will hold the metadata for the links to be displayed
        self.rb_links = []
        self.current_pixmap = None
        self.original_frames_folder = None

        # Show initial trajectory if available
        self._display_link(self.curr_link_idx)

    def set_config_manager(self, config_manager):
        """Set the config manager for this widget."""
        self.config_manager = config_manager
        self._update_errant_distance_links_path()

    def set_file_controller(self, file_controller):
        """Set the file controller for this widget."""
        self.file_controller = file_controller
        if self.file_controller:
            self.original_frames_folder = (
                self.file_controller.original_frames_folder
            )
        self._update_errant_distance_links_path()

    def _update_errant_distance_links_path(self):
        """Update errant_distance_links path from injected dependencies."""
        if self.file_controller:
            self.errant_distance_links_dir = self.file_controller.errant_distance_links_folder
        elif self.config_manager:
            self.errant_distance_links_dir = self.config_manager.get_path(
                "errant_distance_links_folder"
            )
        else:
            # Fall back to default
            self.errant_distance_links_dir = "errant_distance_links/"

        # Reload gallery files if path is set
        if self.errant_distance_links_dir:
            self.rb_links = self._load_rb_links(
                self.errant_distance_links_dir
            )
            self.curr_link_idx = (
                min(
                    self.curr_link_idx,
                    len(self.rb_links) - 1,
                )
                if self.rb_links
                else 0
            )
            self._display_link(self.curr_link_idx)

    def _load_rb_links(self, directory_path):
        """Return a sorted list of RB overlay image file paths."""
        metadata_path = os.path.join(directory_path, "rb_links.json")
        if not os.path.exists(metadata_path):
            return []
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading RB links metadata: {e}")
            return []

    def _display_link(self, index):
        """Update UI to display RB overlay image and index if within bounds."""
        if 0 <= index < len(self.rb_links):
            link_info = self.rb_links[index]

            # Regenerate image with current threshold
            self.current_pixmap = self._generate_image_for_link(link_info)

            # Scale to fit while keeping aspect ratio
            if self.current_pixmap is not None:
                self.photo_label.setPixmap(self.current_pixmap)
            else:
                self.photo_label.setText("Failed to generate RB overlay image")
                self._update_display_text()
                return

            # Populate info text from metadata
            info_text = f"""Particle ID: {link_info.get('particle_id')}
Frame Transition: {link_info.get('frame_i')} → {link_info.get('frame_i1')}
Jump Distance: {link_info.get('jump_dist', 0):.2f} pixels
Search Range: {link_info.get('search_range', 0)} pixels"""
            self.info_label.setText(info_text)

            self._update_display_text()
        else:
            # Out of bounds or no files
            if not self.rb_links:
                self.photo_label.setText("No RB overlay images found")
            self.info_label.setText("")
            self._update_display_text()

    def _update_display_text(self):
        total = len(self.rb_links)
        current_display = self.curr_link_idx + 1 if total > 0 else 0
        text = f"{current_display} / {total}"
        # Avoid recursive signals while editing
        old_block = self.trajectory_display.blockSignals(True)
        self.trajectory_display.setText(text)
        self.trajectory_display.blockSignals(old_block)

    def _jump_to_input_link(self):
        """Parse the input and jump to the requested trajectory index if valid."""
        text = self.trajectory_display.text().strip()
        # Accept formats like "12" or "12 / 200"
        if "/" in text:
            first = text.split("/", 1)[0].strip()
        else:
            first = text
        try:
            requested = int(first) - 1
        except ValueError:
            # Restore correct text
            self._update_display_text()
            return
        total = len(self.rb_links)
        if total == 0:
            self._update_display_text()
            return
        # Clamp to valid range
        requested = max(0, min(requested, total - 1))
        if requested != self.curr_link_idx:
            self.curr_link_idx = requested
            self._display_link(self.curr_link_idx)
        else:
            # Even if unchanged, ensure text format is correct
            self._update_display_text()

    def next_link(self):
        """Advance to the next trajectory and update display."""
        if not self.rb_links:
            return
        if self.curr_link_idx < len(self.rb_links) - 1:
            self.curr_link_idx += 1
            self._display_link(self.curr_link_idx)
        else:
            # Already at last image; do nothing
            pass

    def prev_link(self):
        """Go to the previous trajectory and update display."""
        if not self.rb_links:
            return
        if self.curr_link_idx > 0:
            self.curr_link_idx -= 1
            self._display_link(self.curr_link_idx)
        else:
            # Already at first image; do nothing
            pass

    def refresh_errant_distance_links(self):
        """Reload the list of errant distance link image files and refresh display."""
        # Update path first in case it changed
        self._update_errant_distance_links_path()
        # Reload files
        if self.errant_distance_links_dir:
            self.rb_links = self._load_rb_links(
                self.errant_distance_links_dir
            )
        else:
            self.rb_links = []
        # Clamp current index within bounds
        if self.rb_links:
            self.curr_link_idx = min(
                self.curr_link_idx, len(self.rb_links) - 1
            )
        else:
            self.curr_link_idx = 0
        self._display_link(self.curr_link_idx)

    def _on_threshold_changed(self, value):
        """Handle threshold slider change - regenerate current image."""
        self.threshold_label.setText(f"Threshold: {value}%")
        # Regenerate current image with new threshold
        self._display_link(self.curr_link_idx)

    def reset_state(self):
        """Reload gallery files when returning to the linking screen."""
        self.curr_link_idx = 0
        self._update_errant_distance_links_path()
        self._display_link(self.curr_link_idx)

    def _generate_image_for_link(self, link_info):
        """Generate RB overlay image for the given link metadata."""
        if not self.original_frames_folder:
            return None

        try:
            frame_i = link_info.get("frame_i")
            frame_i1 = link_info.get("frame_i1")
            x_i = link_info.get("x_i")
            y_i = link_info.get("y_i")
            x_i1 = link_info.get("x_i1")
            y_i1 = link_info.get("y_i1")

            if any(v is None for v in [frame_i, frame_i1, x_i, y_i, x_i1, y_i1]):
                return None

            frame1_filename = os.path.join(
                self.original_frames_folder, f"frame_{frame_i:05d}.jpg"
            )
            frame2_filename = os.path.join(
                self.original_frames_folder, f"frame_{frame_i1:05d}.jpg"
            )

            if not os.path.exists(frame1_filename) or not os.path.exists(frame2_filename):
                return None

            full_frame1 = cv2.imread(frame1_filename)
            full_frame2 = cv2.imread(frame2_filename)

            if full_frame1 is None or full_frame2 is None:
                return None

            threshold_percent = self.threshold_slider.value()
            crop_size = 200
            crop_radius = crop_size // 2

            # Calculate midpoint and single crop origin
            mid_x = (x_i + x_i1) / 2
            mid_y = (y_i + y_i1) / 2
            crop_origin_x = int(mid_x - crop_radius)
            crop_origin_y = int(mid_y - crop_radius)

            # Function to create padded crops
            def create_padded_crop(full_frame):
                canvas = np.zeros((crop_size, crop_size, 3), dtype=np.uint8)
                
                src_x_start = max(0, crop_origin_x)
                src_y_start = max(0, crop_origin_y)
                src_x_end = min(full_frame.shape[1], crop_origin_x + crop_size)
                src_y_end = min(full_frame.shape[0], crop_origin_y + crop_size)

                dest_x_start = max(0, -crop_origin_x)
                dest_y_start = max(0, -crop_origin_y)
                dest_x_end = dest_x_start + (src_x_end - src_x_start)
                dest_y_end = dest_y_start + (src_y_end - src_y_start)

                canvas[dest_y_start:dest_y_end, dest_x_start:dest_x_end] = full_frame[src_y_start:src_y_end, src_x_start:src_x_end]
                return canvas

            padded_crop1 = create_padded_crop(full_frame1)
            padded_crop2 = create_padded_crop(full_frame2)

            from ..utils.ParticleProcessing import create_rb_overlay_image

            rb_image = create_rb_overlay_image(
                padded_crop1,
                padded_crop2,
                x_i - crop_origin_x,  # Relative positions in the new unified crop
                y_i - crop_origin_y,
                x_i1 - crop_origin_x,
                y_i1 - crop_origin_y,
                threshold_percent=threshold_percent,
                crop_size=crop_size,
            )

            if rb_image is not None:
                height, width, channel = rb_image.shape
                bytes_per_line = 3 * width
                q_image = QPixmap.fromImage(
                    QImage(
                        rb_image.data,
                        width,
                        height,
                        bytes_per_line,
                        QImage.Format_RGB888,
                    )
                )
                return q_image

        except Exception as e:
            print(f"Error generating image for link: {e}")

        return None