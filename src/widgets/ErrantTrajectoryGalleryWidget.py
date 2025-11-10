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
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from ..config_parser import get_config


class ErrantTrajectoryGalleryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None

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

        # Info display (similar to ErrantParticleGalleryWidget)
        self.info_label = QLabel("Info")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(
            "background-color: #333; color: #ccc; padding: 10px; border: 1px solid #555;"
        )
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

        # Store metadata for regenerating images
        self.trajectory_metadata = {}  # Will store frame info, particle positions, etc.

        # RB gallery directory and files (will be set via dependency injection)
        self.rb_gallery_dir = None
        self.rb_gallery_files = []  # All files
        self.filtered_gallery_files = []  # Files filtered by current frame pair
        self.current_pixmap = None
        self.original_frames_folder = None
        self.current_frame_pair = None  # (frame_i, frame_i1) for current filter

        # Show initial trajectory if available
        self._display_trajectory(self.curr_trajectory_idx)

    def set_config_manager(self, config_manager):
        """Set the config manager for this widget."""
        self.config_manager = config_manager
        self._update_rb_gallery_path()

    def set_file_controller(self, file_controller):
        """Set the file controller for this widget."""
        self.file_controller = file_controller
        if self.file_controller:
            self.original_frames_folder = self.file_controller.original_frames_folder
        self._update_rb_gallery_path()

    def _update_rb_gallery_path(self):
        """Update RB gallery path from injected dependencies."""
        if self.file_controller:
            self.rb_gallery_dir = self.file_controller.rb_gallery_folder
        elif self.config_manager:
            self.rb_gallery_dir = self.config_manager.get_path("rb_gallery_folder")
        else:
            # Fall back to global config
            config = get_config()
            self.rb_gallery_dir = config.get("rb_gallery_folder", "rb_gallery")

        # Reload gallery files if path is set
        if self.rb_gallery_dir:
            self.rb_gallery_files = self._load_rb_gallery_files(self.rb_gallery_dir)
            self._filter_by_frame_pair(self.current_frame_pair)
            self.curr_trajectory_idx = (
                min(self.curr_trajectory_idx, len(self.filtered_gallery_files) - 1)
                if self.filtered_gallery_files
                else 0
            )
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
        if 0 <= index < len(self.filtered_gallery_files):
            file_path = self.filtered_gallery_files[index]

            # Try to regenerate image with current threshold, otherwise load from file
            regenerated_pixmap = self._regenerate_current_image(index)
            if regenerated_pixmap is not None:
                self.current_pixmap = regenerated_pixmap
            else:
                # Fallback to loading from file
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    self.current_pixmap = pixmap
                else:
                    self.photo_label.setText("Failed to load RB overlay image")
                    self._update_display_text()
                    return

            # Scale to fit while keeping aspect ratio
            if self.current_pixmap is not None:
                scaled = self.current_pixmap.scaled(
                    self.photo_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.photo_label.setPixmap(scaled)

            # Load and display info
            # Remove _rb_overlay suffix if present, then add .txt
            base_name = os.path.splitext(file_path)[0]
            if base_name.endswith("_rb_overlay"):
                base_name = base_name[:-11]  # Remove '_rb_overlay' suffix
            info_path = base_name + ".txt"
            if os.path.exists(info_path):
                with open(info_path, "r") as f:
                    self.info_label.setText(f.read())
            else:
                self.info_label.setText("")

            self._update_display_text()
        else:
            # Out of bounds or no files
            if not self.filtered_gallery_files:
                if self.current_frame_pair:
                    self.photo_label.setText(
                        f"No RB overlay images found for frames {self.current_frame_pair[0]}-{self.current_frame_pair[1]}"
                    )
                else:
                    self.photo_label.setText("No RB overlay images found")
            self.info_label.setText("")
            self._update_display_text()

    def _update_display_text(self):
        total = len(self.filtered_gallery_files)
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
        total = len(self.filtered_gallery_files)
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
        if not self.filtered_gallery_files:
            return
        if self.curr_trajectory_idx < len(self.filtered_gallery_files) - 1:
            self.curr_trajectory_idx += 1
            self._display_trajectory(self.curr_trajectory_idx)
        else:
            # Already at last image; do nothing
            pass

    def prev_trajectory(self):
        """Go to the previous trajectory and update display."""
        if not self.filtered_gallery_files:
            return
        if self.curr_trajectory_idx > 0:
            self.curr_trajectory_idx -= 1
            self._display_trajectory(self.curr_trajectory_idx)
        else:
            # Already at first image; do nothing
            pass

    def refresh_rb_gallery(self):
        """Reload the list of RB overlay image files and refresh display."""
        # Update path first in case it changed
        self._update_rb_gallery_path()
        # Reload files
        if self.rb_gallery_dir:
            self.rb_gallery_files = self._load_rb_gallery_files(self.rb_gallery_dir)
        else:
            self.rb_gallery_files = []
        # Filter by current frame pair if set
        self._filter_by_frame_pair(self.current_frame_pair)
        # Clamp current index within bounds
        if self.filtered_gallery_files:
            self.curr_trajectory_idx = min(
                self.curr_trajectory_idx, len(self.filtered_gallery_files) - 1
            )
        else:
            self.curr_trajectory_idx = 0
        self._display_trajectory(self.curr_trajectory_idx)

    def _on_threshold_changed(self, value):
        """Handle threshold slider change - regenerate current image."""
        self.threshold_label.setText(f"Threshold: {value}%")
        # Regenerate current image with new threshold
        self._display_trajectory(self.curr_trajectory_idx)

    def reset_state(self):
        """Reload gallery files when returning to the linking screen."""
        self.curr_trajectory_idx = 0
        self._update_rb_gallery_path()
        self._display_trajectory(self.curr_trajectory_idx)

    def _filter_by_frame_pair(self, frame_pair):
        """
        Filter gallery files by frame pair.

        Parameters
        ----------
        frame_pair : tuple or None
            (frame_i, frame_i1) to filter by. If None, shows all files.
        """
        self.current_frame_pair = frame_pair

        if frame_pair is None:
            # Show all files if no frame pair is set
            self.filtered_gallery_files = self.rb_gallery_files.copy()
            return

        frame_i, frame_i1 = frame_pair

        # Filter files by parsing filename
        # Format: particle_{id}_link_{frame_i}_to_{frame_i1}_rb_overlay.png
        self.filtered_gallery_files = []
        for file_path in self.rb_gallery_files:
            filename = os.path.basename(file_path)
            # Extract frame numbers from filename
            try:
                # Format: particle_{id}_link_{frame_i}_to_{frame_i1}_rb_overlay.png
                if f"_link_{frame_i}_to_{frame_i1}_rb_overlay" in filename:
                    self.filtered_gallery_files.append(file_path)
            except:
                continue

        # Sort filtered files
        self.filtered_gallery_files.sort()

    def set_frame_pair_filter(self, frame_i, frame_i1):
        """
        Set the frame pair filter and update the gallery display.

        Parameters
        ----------
        frame_i : int
            First frame number
        frame_i1 : int
            Second frame number (frame_i + 1)
        """
        self._filter_by_frame_pair((frame_i, frame_i1))
        # Reset to first item in filtered list
        self.curr_trajectory_idx = 0
        self._display_trajectory(self.curr_trajectory_idx)

    def _regenerate_current_image(self, index):
        """Regenerate RB overlay image for current index with current threshold setting."""
        if index < 0 or index >= len(self.filtered_gallery_files):
            return None

        if not self.original_frames_folder:
            return None

        # Parse filename to get particle info
        file_path = self.filtered_gallery_files[index]
        base_name = os.path.basename(file_path)
        # Format: particle_{id}_link_{frame_i}_to_{frame_i1}_rb_overlay.png

        try:
            # Extract particle_id, frame_i, frame_i1 from filename
            parts = base_name.replace("_rb_overlay.png", "").split("_")
            particle_id = None
            frame_i = None
            frame_i1 = None

            for i, part in enumerate(parts):
                if part == "particle" and i + 1 < len(parts):
                    particle_id = int(parts[i + 1])
                elif part == "link" and i + 1 < len(parts):
                    frame_i = int(parts[i + 1])
                elif part == "to" and i + 1 < len(parts):
                    frame_i1 = int(parts[i + 1])

            if particle_id is None or frame_i is None or frame_i1 is None:
                return None

            # Load metadata to get particle positions
            base_name_no_ext = base_name.replace("_rb_overlay.png", "")
            metadata_path = os.path.join(self.rb_gallery_dir, base_name_no_ext + ".txt")

            x_i, y_i, x_i1, y_i1 = None, None, None, None
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    for line in f:
                        if "POSITION (Frame" in line and "x=" in line:
                            # Parse: POSITION (Frame X): x=123.45, y=678.90
                            try:
                                if f"Frame {frame_i}" in line:
                                    x_part = line.split("x=")[1].split(",")[0].strip()
                                    y_part = line.split("y=")[1].strip()
                                    x_i = float(x_part)
                                    y_i = float(y_part)
                                elif f"Frame {frame_i1}" in line:
                                    x_part = line.split("x=")[1].split(",")[0].strip()
                                    y_part = line.split("y=")[1].strip()
                                    x_i1 = float(x_part)
                                    y_i1 = float(y_part)
                            except (ValueError, IndexError):
                                pass

            # Load frames and regenerate
            frame1_filename = os.path.join(
                self.original_frames_folder, f"frame_{frame_i:05d}.jpg"
            )
            frame2_filename = os.path.join(
                self.original_frames_folder, f"frame_{frame_i1:05d}.jpg"
            )

            if not os.path.exists(frame1_filename) or not os.path.exists(
                frame2_filename
            ):
                return None

            if x_i is None or y_i is None or x_i1 is None or y_i1 is None:
                # Can't regenerate without positions
                return None

            frame1 = cv2.imread(frame1_filename)
            frame2 = cv2.imread(frame2_filename)

            if frame1 is None or frame2 is None:
                return None

            # Get threshold percentage
            threshold_percent = self.threshold_slider.value()

            # Crop around particle positions (same logic as in create_rb_gallery)
            crop_size = 200
            x1, y1 = int(x_i), int(y_i)
            x2, y2 = int(x_i1), int(y_i1)

            # Calculate crop boundaries for frame1
            x1_min = max(0, x1 - crop_size // 2)
            y1_min = max(0, y1 - crop_size // 2)
            x1_max = min(frame1.shape[1], x1 + crop_size // 2)
            y1_max = min(frame1.shape[0], y1 + crop_size // 2)

            # Calculate crop boundaries for frame2
            x2_min = max(0, x2 - crop_size // 2)
            y2_min = max(0, y2 - crop_size // 2)
            x2_max = min(frame2.shape[1], x2 + crop_size // 2)
            y2_max = min(frame2.shape[0], y2 + crop_size // 2)

            # Crop the frames
            crop1 = frame1[y1_min:y1_max, x1_min:x1_max]
            crop2 = frame2[y2_min:y2_max, x2_min:x2_max]

            # Generate RB overlay with current threshold
            from ..particle_processing import create_rb_overlay_image

            rb_image = create_rb_overlay_image(
                crop1,
                crop2,
                x1 - x1_min,
                y1 - y1_min,  # Relative positions in crop
                x2 - x2_min,
                y2 - y2_min,
                threshold_percent=threshold_percent,
                crop_size=crop_size,
            )

            if rb_image is not None:
                # rb_image is already RGB from create_rb_overlay_image
                # Convert to QPixmap
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
            print(f"Error regenerating image: {e}")

        return None

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