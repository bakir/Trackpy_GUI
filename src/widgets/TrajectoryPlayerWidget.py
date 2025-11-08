"""
Trajectory Player Widget

Description: Displays full-frame red-blue overlays for trajectory linking visualization.
Shows frame pairs (i, i+1) with red particles in frame i and blue particles in frame i+1,
both at 50% opacity on white background.
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


class TrajectoryPlayerWidget(QWidget):
    # Signal emitted when overlay changes
    overlay_changed = Signal(int, int)  # frame_i, frame_i1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None
        self.layout = QVBoxLayout(self)

        # Photo display for RB overlay
        self.photo_label = QLabel("RB Overlay Display")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            "background-color: white; color: #333; border: 1px solid #555;"
        )
        self.photo_label.setMinimumHeight(300)
        self.photo_label.setScaledContents(False)
        self.layout.addWidget(self.photo_label)

        # Current overlay display
        self.current_overlay_label = QLabel("Overlay: 0 / 0")
        self.current_overlay_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.current_overlay_label)

        # Navigation controls
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedSize(40, 30)
        self.prev_button.clicked.connect(self.previous_overlay)
        nav_layout.addWidget(self.prev_button)

        nav_layout.addWidget(QLabel("Overlay:"))
        self.overlay_input = QLineEdit()
        self.overlay_input.setPlaceholderText("Enter overlay number")
        self.overlay_input.returnPressed.connect(self.go_to_overlay)
        nav_layout.addWidget(self.overlay_input)

        self.overlay_slider = QSlider(Qt.Horizontal)
        self.overlay_slider.setRange(0, 0)
        self.overlay_slider.valueChanged.connect(self.slider_value_changed)
        nav_layout.addWidget(self.overlay_slider)

        self.next_button = QPushButton("▶")
        self.next_button.setFixedSize(40, 30)
        self.next_button.clicked.connect(self.next_overlay)
        nav_layout.addWidget(self.next_button)

        self.layout.addLayout(nav_layout)

        # Store current pixmap and state
        self.current_pixmap = None
        self.original_frames_folder = None
        self.total_frames = 0
        self.current_overlay_idx = 0
        self.threshold_percent = 50  # Default threshold
        self.threshold_slider = (
            None  # Will be connected from ErrantTrajectoryGalleryWidget
        )

    def set_config_manager(self, config_manager):
        """Set the config manager for this widget."""
        self.config_manager = config_manager
        if config_manager:
            self.original_frames_folder = config_manager.get_path(
                "original_frames_folder"
            )

    def set_file_controller(self, file_controller):
        """Set the file controller for this widget."""
        self.file_controller = file_controller
        if file_controller:
            self.original_frames_folder = file_controller.original_frames_folder
            # Load total frames count
            self._load_total_frames()

    def load_initial_overlay(self):
        """Load the first available RB overlay immediately."""
        self._load_total_frames()
        if self.total_frames > 1:
            self.display_overlay(0)
        elif self.total_frames == 1:
            self.photo_label.setText("Need at least 2 frames for overlay")
        else:
            self.photo_label.setText("No frames available")

    def set_threshold_slider(self, slider):
        """Connect to threshold slider from ErrantTrajectoryGalleryWidget."""
        self.threshold_slider = slider
        if slider:
            self.threshold_percent = slider.value()
            slider.valueChanged.connect(self._on_threshold_changed)

    def _on_threshold_changed(self, value):
        """Handle threshold slider change - regenerate current overlay."""
        self.threshold_percent = value
        self.display_overlay(self.current_overlay_idx)

    def _load_total_frames(self):
        """Load total number of frames from folder."""
        if not self.original_frames_folder or not os.path.exists(
            self.original_frames_folder
        ):
            self.total_frames = 0
            return

        frame_files = []
        for filename in sorted(os.listdir(self.original_frames_folder)):
            if filename.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
                frame_files.append(filename)

        self.total_frames = len(frame_files)
        # Overlays are frame pairs (i, i+1), so max overlay is total_frames - 2
        max_overlays = max(0, self.total_frames - 1)
        if max_overlays > 0:
            self.overlay_slider.setRange(0, max_overlays - 1)
        else:
            self.overlay_slider.setRange(0, 0)
        self.update_overlay_display()

    def display_trajectory_image(self, image_path):
        """Legacy method - now loads frames and displays overlay instead."""
        # When trajectories are linked, load frames and show overlay
        self._load_total_frames()
        if self.total_frames > 1:
            self.display_overlay(0)

    def display_overlay(self, overlay_idx):
        """Display RB overlay for overlay_idx (shows frames overlay_idx and overlay_idx+1)."""
        if self.total_frames < 2:
            self.photo_label.setText("Need at least 2 frames for overlay")
            return

        max_overlays = self.total_frames - 1
        if overlay_idx < 0 or overlay_idx >= max_overlays:
            return

        frame_i = overlay_idx
        frame_i1 = overlay_idx + 1

        # Load frames
        frame1_filename = os.path.join(
            self.original_frames_folder, f"frame_{frame_i:05d}.jpg"
        )
        frame2_filename = os.path.join(
            self.original_frames_folder, f"frame_{frame_i1:05d}.jpg"
        )

        if not os.path.exists(frame1_filename) or not os.path.exists(frame2_filename):
            self.photo_label.setText(f"Frames {frame_i} or {frame_i1} not found")
            return

        frame1 = cv2.imread(frame1_filename)
        frame2 = cv2.imread(frame2_filename)

        if frame1 is None or frame2 is None:
            self.photo_label.setText(f"Failed to load frames {frame_i} or {frame_i1}")
            return

        # Generate full-frame RB overlay
        from ..particle_processing import create_full_frame_rb_overlay

        rb_overlay = create_full_frame_rb_overlay(
            frame1, frame2, threshold_percent=self.threshold_percent
        )

        if rb_overlay is not None:
            # Convert to QPixmap
            height, width, channel = rb_overlay.shape
            bytes_per_line = 3 * width
            q_image = QPixmap.fromImage(
                QImage(
                    rb_overlay.data, width, height, bytes_per_line, QImage.Format_RGB888
                )
            )
            self.current_pixmap = q_image
            scaled = self.current_pixmap.scaled(
                self.photo_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.photo_label.setPixmap(scaled)

        self.current_overlay_idx = overlay_idx
        self.update_overlay_display()

        # Emit signal to notify errant trajectory gallery of frame pair change
        self.overlay_changed.emit(frame_i, frame_i1)

    def update_overlay_display(self):
        """Update overlay display and input."""
        max_overlays = max(0, self.total_frames - 1)
        if max_overlays > 0:
            self.current_overlay_label.setText(
                f"Overlay: {self.current_overlay_idx} / {max_overlays - 1} (Frames {self.current_overlay_idx} & {self.current_overlay_idx + 1})"
            )
            self.overlay_slider.setValue(self.current_overlay_idx)
        else:
            self.current_overlay_label.setText("Overlay: 0 / 0")
        self.overlay_input.setText(str(self.current_overlay_idx))

    def previous_overlay(self):
        """Go to previous overlay."""
        if self.current_overlay_idx > 0:
            self.display_overlay(self.current_overlay_idx - 1)

    def next_overlay(self):
        """Go to next overlay."""
        max_overlays = max(0, self.total_frames - 1)
        if self.current_overlay_idx < max_overlays - 1:
            self.display_overlay(self.current_overlay_idx + 1)

    def go_to_overlay(self):
        """Go to overlay specified in input."""
        try:
            overlay_idx = int(self.overlay_input.text())
            max_overlays = max(0, self.total_frames - 1)
            if 0 <= overlay_idx < max_overlays:
                self.display_overlay(overlay_idx)
        except ValueError:
            pass

    def slider_value_changed(self, value):
        """Go to overlay specified by slider."""
        max_overlays = max(0, self.total_frames - 1)
        if 0 <= value < max_overlays:
            self.display_overlay(value)

    def resizeEvent(self, event):
        """Handle widget resize to update image display."""
        super().resizeEvent(event)
        if self.current_pixmap is not None and not self.current_pixmap.isNull():
            scaled = self.current_pixmap.scaled(
                self.photo_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.photo_label.setPixmap(scaled)
