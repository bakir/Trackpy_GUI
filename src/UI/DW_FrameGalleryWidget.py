"""
Video Frame display window for particle detection window

Description: Widget displaying frames of the video with frame controls. Shows the particles tracked.
             Generated boiler plate code using Cursor.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

import cv2
import os
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QHBoxLayout,
    QLineEdit,
    QCheckBox,
)
from ..utils.InteractiveFrameViewer import InteractiveFrameViewer
from ..utils.ParticleProcessing import apply_frame_view_processing


class SaveFramesThread(QThread):
    """Thread for extracting and saving frames from video"""

    save_complete = Signal(int)  # total_frames

    def __init__(self, video_path, output_folder):
        super().__init__()
        self.video_path = video_path
        self.output_folder = output_folder
        self.cap = None

    def run(self):
        """Extract frames from video and save them to disk"""
        try:
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                return

            frame_idx = 0
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break

                frame_path = os.path.join(self.output_folder, f"frame_{frame_idx:05d}.jpg")
                cv2.imwrite(frame_path, frame)
                frame_idx += 1

            self.save_complete.emit(frame_idx)

        except Exception as e:
            print(f"Error saving frames: {e}")
        finally:
            if self.cap:
                self.cap.release()


class DWFrameGalleryWidget(QWidget):
    """Widget for displaying video frames from a folder of images"""

    frames_saved = Signal(int)
    frame_changed = Signal(int)  # Emits current frame number when frame changes
    particleClickedOnFrame = Signal(dict)

    def __init__(self):
        super().__init__()
        self.config_manager = None
        self.file_controller = None
        self.errant_particle_gallery = None
        self.setup_ui()
        self.setup_variables()

    def set_config_manager(self, config_manager):
        """Set the config manager and update folder paths."""
        self.config_manager = config_manager
        if config_manager:
            self.original_frames_folder = config_manager.get_path("original_frames_folder")
            self.annotated_frames_folder = config_manager.get_path("annotated_frames_folder")
            self.update_feature_size()

    def update_feature_size(self):
        """Update feature size from config."""
        if self.config_manager:
            self.feature_size = self.config_manager.get_detection_params().get("feature_size", 15)

    def set_file_controller(self, file_controller):
        """Set the file controller."""
        self.file_controller = file_controller
        if file_controller:
            self.original_frames_folder = file_controller.original_frames_folder
            self.annotated_frames_folder = file_controller.annotated_frames_folder

    def set_errant_particle_gallery(self, gallery_widget):
        """Set the errant particle gallery widget."""
        self.errant_particle_gallery = gallery_widget

    def setup_ui(self):
        """Setup the frame viewer UI components"""
        layout = QVBoxLayout(self)

        self.frame_viewer = InteractiveFrameViewer()
        self.frame_viewer.viewOptionsChanged.connect(self._on_view_options_changed)
        self.frame_viewer.particleClicked.connect(self._on_viewer_particle_click)
        layout.addWidget(self.frame_viewer, 1)

        viewer_hint = QLabel(
            "Scroll to zoom, drag to pan. Right-click the frame for view options."
        )
        viewer_hint.setAlignment(Qt.AlignCenter)
        viewer_hint.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(viewer_hint)

        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setRange(0, 0)
        self.frame_slider.valueChanged.connect(self.slider_value_changed)
        layout.addWidget(self.frame_slider)

        self.current_frame_label = QLabel("Frame: 0 / 0")
        self.current_frame_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_frame_label)

        nav_layout = QHBoxLayout()

        self.annotate_toggle = QCheckBox("Show Annotated")
        self.annotate_toggle.stateChanged.connect(self.on_toggle_annotate)
        nav_layout.addWidget(self.annotate_toggle)

        self.reset_view_button = QPushButton("Reset view")
        self.reset_view_button.setToolTip("Fit the full frame in the viewer")
        self.reset_view_button.clicked.connect(self.frame_viewer.reset_view)
        nav_layout.addWidget(self.reset_view_button)

        self.prev_button = QPushButton("◀")
        self.prev_button.clicked.connect(self.previous_frame)
        nav_layout.addWidget(self.prev_button)

        nav_layout.addWidget(QLabel("Select frame"))
        self.frame_input = QLineEdit()
        self.frame_input.setPlaceholderText("Enter frame number")
        self.frame_input.returnPressed.connect(self.go_to_frame)
        nav_layout.addWidget(self.frame_input)

        self.next_button = QPushButton("▶")
        self.next_button.clicked.connect(self.next_frame)
        nav_layout.addWidget(self.next_button)

        layout.addLayout(nav_layout)

    def setup_variables(self):
        """Setup internal variables"""
        self.video_path = None
        self.total_frames = 0
        self.current_frame_idx = 0
        self._last_rendered_frame_idx = None
        self.save_thread = None
        self.original_frames_folder = "original_frames"
        self.annotated_frames_folder = "annotated_frames"
        self.feature_size = 15
        self.current_particles_in_frame = None
        self.video_loaded = False
        self.scatter_highlight_info = None
        self._raw_frame_bgr = None
        self._raw_frame_number = None

    def _on_view_options_changed(self):
        if self._raw_frame_bgr is not None and 0 <= self.current_frame_idx < self.total_frames:
            self.display_frame(self.current_frame_idx, reset_view=False)

    def _on_viewer_particle_click(self, x, y):
        """Find the nearest particle on the current frame and sync to scatter plots."""
        if not self.file_controller:
            return
        try:
            particles = self.file_controller.load_particles_data("all_particles.csv")
        except Exception:
            return
        if particles.empty:
            return

        frame_particles = particles[particles["frame"] == self.current_frame_idx]
        if frame_particles.empty:
            return

        radius = max(self.feature_size / 1.5, 5.0)
        dx = frame_particles["x"] - x
        dy = frame_particles["y"] - y
        dist_sq = dx * dx + dy * dy
        nearest_idx = dist_sq.idxmin()
        if float(dist_sq.loc[nearest_idx]) > radius * radius:
            return

        particle = frame_particles.loc[nearest_idx].to_dict()
        self.scatter_highlight_info = {
            "frame": int(particle["frame"]),
            "x": float(particle["x"]),
            "y": float(particle["y"]),
        }
        if not self.annotate_toggle.isChecked():
            self.annotate_toggle.setChecked(True)
        self.display_frame(self.current_frame_idx, reset_view=False)
        self.particleClickedOnFrame.emit(particle)

    def _load_frame_bgr(self, frame_path):
        image = cv2.imread(frame_path)
        if image is None:
            print(f"Warning: Failed to read frame: {frame_path}")
        return image

    @staticmethod
    def _bgr_to_rgb(image_bgr):
        return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    def save_video_frames(self, video_path):
        """Save video frames to disk in a background thread"""
        self.video_path = video_path
        self.current_frame_idx = 0
        self.annotate_toggle.setChecked(False)
        self.video_loaded = True

        self.save_thread = SaveFramesThread(video_path, self.original_frames_folder)
        self.save_thread.save_complete.connect(self.on_save_complete)
        self.save_thread.start()

    def on_save_complete(self, total_frames):
        """Handle save completion"""
        self.total_frames = total_frames
        if self.total_frames > 0:
            self.frame_slider.setRange(0, self.total_frames - 1)
        self.display_frame(0)
        self.frames_saved.emit(self.total_frames)

    def load_frames(self, num_frames):
        """Load existing frames."""
        self.total_frames = num_frames
        if self.total_frames > 0:
            self.frame_slider.setRange(0, self.total_frames - 1)
            self.video_loaded = True
        else:
            self.video_loaded = False
        self.display_frame(0)

    def handle_gallery_update(self):
        """
        Slot for when the gallery's state changes.

        If the gallery's "show on frame" is checked, this will jump
        the player to the particle's frame. Otherwise, it just refreshes
        the current frame.
        """
        if self.errant_particle_gallery and self.errant_particle_gallery.is_show_on_frame_checked():
            info = self.errant_particle_gallery.get_current_particle_info()
            if info and info.get("frame") is not None:
                self.display_frame(info.get("frame"))
        else:
            self.display_frame(self.current_frame_idx, reset_view=False)

    def refresh_frame(self):
        """Force a refresh of the current frame."""
        self.display_frame(self.current_frame_idx, reset_view=False)

    def on_toggle_annotate(self, state):
        """Handle annotation toggle state change."""
        self.display_frame(self.current_frame_idx, reset_view=False)

    def reload_from_disk(self):
        """Reload available frames from disk and display the current one."""
        frames_folder = self.original_frames_folder
        if self.file_controller:
            frames_folder = self.file_controller.original_frames_folder

        frame_files = []
        if frames_folder and os.path.exists(frames_folder):
            frame_files = sorted(
                f
                for f in os.listdir(frames_folder)
                if f.startswith("frame_") and f.lower().endswith(".jpg")
            )

        self.total_frames = len(frame_files)

        if self.total_frames > 0:
            self.frame_slider.setRange(0, self.total_frames - 1)
            self.current_frame_idx = min(self.current_frame_idx, self.total_frames - 1)
        else:
            self.current_frame_idx = 0

        self.display_frame(self.current_frame_idx)
        return self.total_frames

    def display_frame(self, frame_number, reset_view=None):
        """
        Load the specified frame and overlays annotations and/or highlights.

        Pan/zoom is preserved when refreshing the same frame (e.g. toggling
        annotations). Changing frames resets the view to fit.
        """
        if reset_view is None:
            reset_view = frame_number != self._last_rendered_frame_idx

        if not (0 <= frame_number < self.total_frames):
            if self.total_frames == 0:
                self.frame_viewer.set_message("No video loaded")
            self.update_frame_display()
            return

        self.current_frame_idx = frame_number

        original_frame_path = os.path.join(
            self.original_frames_folder, f"frame_{frame_number:05d}.jpg"
        )
        if (
            frame_number == self._raw_frame_number
            and self._raw_frame_bgr is not None
        ):
            raw_bgr = self._raw_frame_bgr
        else:
            raw_bgr = self._load_frame_bgr(original_frame_path)
            if raw_bgr is None:
                self.frame_viewer.set_message("Frame not found")
                self._raw_frame_bgr = None
                self._raw_frame_number = None
                self.update_frame_display()
                return
            self._raw_frame_bgr = raw_bgr
            self._raw_frame_number = frame_number

        view_opts = self.frame_viewer.get_view_options()
        image_bgr = apply_frame_view_processing(
            raw_bgr,
            greyscale=view_opts["greyscale"],
            threshold_enabled=view_opts["threshold_enabled"],
            threshold_percent=view_opts["threshold_percent"],
        )

        show_annotations = self.annotate_toggle.isChecked()
        highlight_info = None
        if self.errant_particle_gallery and self.errant_particle_gallery.is_show_on_frame_checked():
            info = self.errant_particle_gallery.get_current_particle_info()
            if info and info.get("frame") == frame_number:
                highlight_info = info

        scatter_highlight = None
        if (
            self.scatter_highlight_info
            and self.scatter_highlight_info.get("frame") == frame_number
        ):
            scatter_highlight = self.scatter_highlight_info

        needs_annotation = (
            show_annotations or highlight_info is not None or scatter_highlight is not None
        )

        if needs_annotation and self.file_controller:
            if show_annotations:
                particle_data = self.file_controller.load_particles_data("filtered_particles.csv")
                if not particle_data.empty:
                    particles_in_frame = particle_data[particle_data["frame"] == frame_number]
                    if not particles_in_frame.empty:
                        from ..utils.ParticleProcessing import (
                            _get_invert_setting,
                            calculate_optimal_annotation_color,
                        )

                        invert = _get_invert_setting()
                        annotation_color = calculate_optimal_annotation_color(image_bgr, invert)

                        for _, particle in particles_in_frame.iterrows():
                            cv2.circle(
                                image_bgr,
                                (int(particle["x"]), int(particle["y"])),
                                int(self.feature_size / 1.5),
                                annotation_color,
                                2,
                            )

            if highlight_info:
                x, y = int(highlight_info["x"]), int(highlight_info["y"])
                crop_radius = 25
                cv2.rectangle(
                    image_bgr,
                    (x - crop_radius, y - crop_radius),
                    (x + crop_radius, y + crop_radius),
                    (255, 0, 0),
                    3,
                )

            if scatter_highlight:
                x, y = int(scatter_highlight["x"]), int(scatter_highlight["y"])
                crop_radius = 25
                cv2.rectangle(
                    image_bgr,
                    (x - crop_radius, y - crop_radius),
                    (x + crop_radius, y + crop_radius),
                    (0, 200, 0),
                    3,
                )

        self.frame_viewer.set_frame_image(
            self._bgr_to_rgb(image_bgr), reset_view=reset_view
        )
        self._last_rendered_frame_idx = frame_number

        self.update_frame_display()
        self.frame_changed.emit(frame_number)

    def highlight_particle(self, particle_info):
        """Jump to and highlight a particle selected from a scatter plot."""
        if not particle_info or "frame" not in particle_info:
            self.clear_scatter_highlight()
            return

        frame_number = int(particle_info["frame"])
        self.scatter_highlight_info = {
            "frame": frame_number,
            "x": float(particle_info["x"]),
            "y": float(particle_info["y"]),
        }
        if not self.annotate_toggle.isChecked():
            self.annotate_toggle.setChecked(True)

        same_frame = frame_number == self.current_frame_idx
        self.display_frame(frame_number, reset_view=not same_frame)

    def clear_scatter_highlight(self):
        """Remove scatter-plot particle highlight from the frame view."""
        if self.scatter_highlight_info is None:
            return
        self.scatter_highlight_info = None
        self.display_frame(self.current_frame_idx, reset_view=False)

    def update_frame_display(self):
        """Update the frame display and input"""
        if self.total_frames > 0:
            self.current_frame_label.setText(
                f"Frame: {self.current_frame_idx + 1} / {self.total_frames}"
            )
            if self.frame_slider.value() != self.current_frame_idx:
                self.frame_slider.setValue(self.current_frame_idx)
        else:
            self.current_frame_label.setText("Frame: 0 / 0")
        self.frame_input.setText(str(self.current_frame_idx + 1))

    def previous_frame(self):
        """Go to previous frame"""
        if self.current_frame_idx > 0:
            self.display_frame(self.current_frame_idx - 1)

    def next_frame(self):
        """Go to next frame"""
        if self.current_frame_idx < self.total_frames - 1:
            self.display_frame(self.current_frame_idx + 1)

    def go_to_frame(self):
        """Go to frame specified in input"""
        try:
            frame_number = int(self.frame_input.text()) - 1
            if 0 <= frame_number < self.total_frames:
                self.display_frame(frame_number)
        except ValueError:
            pass

    def slider_value_changed(self, value):
        """Go to frame specified by slider"""
        if value != self.current_frame_idx:
            self.display_frame(value)
