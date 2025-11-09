"""
Video Frame display window for particle detection window

Description: Widget displaying frames of the video with frame controls. Shows the particles tracked.
             Generated boiler plate code using Cursor.
"""

import sys
import cv2
import os
import pandas as pd
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QHBoxLayout,
    QLineEdit,
    QCheckBox,
    QGridLayout, # Added QGridLayout
)
from PySide6.QtGui import QPixmap, QImage

from ..particle_processing import annotate_frame, save_errant_particle_crops_for_frame


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

                frame_path = os.path.join(
                    self.output_folder, f"frame_{frame_idx:05d}.jpg"
                )
                cv2.imwrite(frame_path, frame)
                frame_idx += 1

            self.save_complete.emit(frame_idx)

        except Exception as e:
            print(f"Error saving frames: {e}")
        finally:
            if self.cap:
                self.cap.release()


class FramePlayerWidget(QWidget):
    """Widget for displaying video frames from a folder of images"""

    frames_saved = Signal(int)
    errant_particles_updated = Signal()
    frame_changed = Signal(int)  # Emits current frame number when frame changes
    import_video_requested = Signal() # New signal to request video import

    def __init__(self):
        super().__init__()
        self.config_manager = None
        self.file_controller = None
        self.setup_ui()
        self.setup_variables()

    def set_config_manager(self, config_manager):
        """Set the config manager and update folder paths."""
        self.config_manager = config_manager
        if config_manager:
            self.original_frames_folder = config_manager.get_path(
                "original_frames_folder"
            )
            self.annotated_frames_folder = config_manager.get_path(
                "annotated_frames_folder"
            )
            self.update_feature_size()

    def update_feature_size(self):
        """Update feature size from config."""
        if self.config_manager:
            self.feature_size = self.config_manager.get_detection_params().get(
                "feature_size", 15
            )

    def set_file_controller(self, file_controller):
        """Set the file controller."""
        self.file_controller = file_controller
        if file_controller:
            self.original_frames_folder = file_controller.original_frames_folder
            self.annotated_frames_folder = file_controller.annotated_frames_folder

    def setup_ui(self):
        """Setup the frame viewer UI components"""
        layout = QVBoxLayout(self)

        # Frame display area
        self.frame_container = QWidget()
        self.frame_layout = QGridLayout(self.frame_container) # Changed to QGridLayout
        self.frame_layout.setContentsMargins(0, 0, 0, 0)

        self.frame_label = QLabel()
        self.frame_label.setAlignment(Qt.AlignCenter)
        self.frame_label.setMinimumSize(640, 480)
        self.frame_label.setStyleSheet(
            "border: 1px solid gray; background-color: black;"
        )
        self.frame_label.setText("No video loaded")

        self.import_video_button = QPushButton("Click to import video")
        self.import_video_button.clicked.connect(self.import_video_requested.emit)
        self.import_video_button.setStyleSheet(
            "QPushButton { background-color: black; color: white; font-size: 14px; padding: 20px; border: 2px solid black; }"
            "QPushButton:hover { background-color: #333; }"
        )
        self.import_video_button.setFixedSize(640, 480) # Re-add fixed size

        self.frame_layout.addWidget(self.frame_label, 0, 0, 1, 1)
        self.frame_layout.addWidget(self.import_video_button, 0, 0, 1, 1, alignment=Qt.AlignCenter)
        self.import_video_button.show() # Ensure button is visible initially

        layout.addWidget(self.frame_container)

        # Current frame display
        self.current_frame_label = QLabel("Frame: 0 / 0")
        self.current_frame_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_frame_label)

        # Frame navigation controls
        nav_layout = QHBoxLayout()

        self.annotate_toggle = QCheckBox("Show Annotated")
        self.annotate_toggle.stateChanged.connect(self.on_toggle_annotate)
        nav_layout.addWidget(self.annotate_toggle)

        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedSize(40, 30)
        self.prev_button.clicked.connect(self.previous_frame)
        nav_layout.addWidget(self.prev_button)

        nav_layout.addWidget(QLabel("Select frame"))
        self.frame_input = QLineEdit()
        self.frame_input.setPlaceholderText("Enter frame number")
        self.frame_input.returnPressed.connect(self.go_to_frame)
        nav_layout.addWidget(self.frame_input)

        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setRange(0, 0)
        self.frame_slider.valueChanged.connect(self.slider_value_changed)
        nav_layout.addWidget(self.frame_slider)

        self.next_button = QPushButton("▶")
        self.next_button.setFixedSize(40, 30)
        self.next_button.clicked.connect(self.next_frame)
        nav_layout.addWidget(self.next_button)

        layout.addLayout(nav_layout)

    def setup_variables(self):
        """Setup internal variables"""
        self.video_path = None
        self.total_frames = 0
        self.current_frame_idx = 0
        self.save_thread = None
        self.show_annotated = False
        self.original_frames_folder = "original_frames"
        self.annotated_frames_folder = "annotated_frames"
        self.feature_size = 15
        self.selected_errant_particle_index = -1
        self.current_original_pixmap = None
        self.current_particles_in_frame = None
        self.highlighted_particle_x = None
        self.highlighted_particle_y = None
        self.is_highlight_jump = (
            False  # Flag to indicate we're jumping to highlight a particle
        )
        self.video_loaded = False

    def on_errant_particle_selected(self, particle_index):
        """Slot to receive the selected errant particle index."""
        self.selected_errant_particle_index = particle_index
        self._update_annotations()

    def save_video_frames(self, video_path):
        """Save video frames to disk in a background thread"""
        self.video_path = video_path
        self.current_frame_idx = 0
        self.annotate_toggle.setChecked(False)
        self.video_loaded = True # Set video_loaded to True when saving frames

        self.save_thread = SaveFramesThread(video_path, self.original_frames_folder)
        self.save_thread.save_complete.connect(self.on_save_complete)
        self.save_thread.start()

    def on_save_complete(self, total_frames):
        """Handle save completion"""
        self.total_frames = total_frames
        if self.total_frames > 0:
            self.frame_slider.setRange(0, self.total_frames - 1)
            self.display_frame(0)
            self.import_video_button.hide() # Hide button when video loaded
        else:
            self.import_video_button.show() # Show button if no frames
        self.update_frame_display()
        self.frames_saved.emit(self.total_frames)

    def load_frames(self, num_frames):
        """Load existing frames."""
        self.total_frames = num_frames
        if self.total_frames > 0:
            self.frame_slider.setRange(0, self.total_frames - 1)
            self.display_frame(0)
            self.import_video_button.hide() # Hide button when video loaded
            self.video_loaded = True
        else:
            self.import_video_button.show() # Show button if no frames
            self.video_loaded = False
        self.update_frame_display()

    def on_toggle_annotate(self, state):
        self.show_annotated = self.annotate_toggle.isChecked()
        self._update_annotations()

    def display_frame(self, frame_number):
        if not (0 <= frame_number < self.total_frames):
            if self.total_frames == 0: # If no frames are loaded at all
                self.import_video_button.show()
            return

        # Store whether we have a highlighted particle before we potentially clear things
        has_highlight = (
            self.highlighted_particle_x is not None
            and self.highlighted_particle_y is not None
        )

        self.current_frame_idx = frame_number

        # Always delete all annotated frames to ensure only one exists at a time
        if self.file_controller:
            self.file_controller.delete_all_files_in_folder(
                self.annotated_frames_folder
            )

        file_name = f"frame_{frame_number:05d}.jpg"
        original_frame_path = os.path.join(self.original_frames_folder, file_name)

        if not os.path.exists(original_frame_path):
            self.frame_label.clear()
            self.frame_label.setText(f"Frame not found: {file_name}")
            self.current_original_pixmap = None
            self.current_particles_in_frame = pd.DataFrame()
            self.import_video_button.show() # Show button if frame not found
        else:
            self.current_original_pixmap = QPixmap(original_frame_path)
            self.import_video_button.hide() # Hide button if frame found

            if self.file_controller:
                particle_data = self.file_controller.load_particles_data(
                    "found_particles.csv"
                )
                if not particle_data.empty:
                    self.current_particles_in_frame = particle_data[
                        particle_data["frame"] == frame_number
                    ]
                else:
                    self.current_particles_in_frame = pd.DataFrame()
            else:
                self.current_particles_in_frame = pd.DataFrame()

        self._update_annotations()
        self.update_frame_display()
        # Emit frame change signal
        self.frame_changed.emit(frame_number)

    def _update_annotations(self):
        """Renders the frame with or without annotations.

        Creates exactly one annotated frame if:
        - Show annotated checkbox is checked (draws particle circles), OR
        - A particle is highlighted (draws blue box only, no circles unless checkbox is checked)

        The annotated frame will include:
        - Particle circles ONLY if show_annotated is True
        - Blue box around highlighted particle if one is set
        """
        frame_path_to_display = None
        import cv2

        # Case 1: Show annotated checkbox is checked - create annotated frame with particle circles
        if (
            self.show_annotated
            and self.file_controller
            and self.current_particles_in_frame is not None
            and not self.current_particles_in_frame.empty
        ):
            annotated_path = annotate_frame(
                self.current_frame_idx,
                self.current_particles_in_frame,
                self.feature_size,
                highlighted_particle_index=None,  # We'll add blue box separately if needed
            )
            if annotated_path and os.path.exists(annotated_path):
                frame_path_to_display = annotated_path

        # Case 2: We have a highlighted particle - add blue box
        # If show_annotated is False, we start with original frame (no circles)
        # If show_annotated is True, we use the annotated frame (with circles) from above
        if (
            self.highlighted_particle_x is not None
            and self.highlighted_particle_y is not None
        ):
            image_to_modify = None
            # Use annotated frame if available (from show_annotated), otherwise use original frame
            if frame_path_to_display and os.path.exists(frame_path_to_display):
                image_to_modify = cv2.imread(frame_path_to_display)
            elif self.file_controller:
                original_frame_path = os.path.join(
                    self.original_frames_folder,
                    f"frame_{self.current_frame_idx:05d}.jpg",
                )
                if os.path.exists(original_frame_path):
                    image_to_modify = cv2.imread(original_frame_path)
                    # Create annotated frame path for saving (even if no circles, we need to save the blue box)
                    frame_path_to_display = os.path.join(
                        self.annotated_frames_folder,
                        f"frame_{self.current_frame_idx:05d}.jpg",
                    )
                    self.file_controller.ensure_folder_exists(
                        self.annotated_frames_folder
                    )

            if image_to_modify is not None:
                x, y = int(self.highlighted_particle_x), int(
                    self.highlighted_particle_y
                )
                # Blue square should match the zoom-in crop size: 25 pixels radius (50x50 total)
                crop_radius = 25
                cv2.rectangle(
                    image_to_modify,
                    (x - crop_radius, y - crop_radius),
                    (x + crop_radius, y + crop_radius),
                    (255, 0, 0),
                    3,
                )  # Blue square

                # Save the modified image (this will be the only annotated frame)
                # Ensure the directory exists
                if self.file_controller:
                    self.file_controller.ensure_folder_exists(
                        self.annotated_frames_folder
                    )
                success = cv2.imwrite(frame_path_to_display, image_to_modify)
                if not success:
                    print(
                        f"Warning: Failed to save annotated frame to {frame_path_to_display}"
                    )
                # Verify the file was actually created and wait a moment for filesystem to sync
                import time

                max_retries = 10
                retry_count = 0
                while (
                    not os.path.exists(frame_path_to_display)
                    and retry_count < max_retries
                ):
                    time.sleep(0.001)  # Wait 1ms
                    retry_count += 1
                if not os.path.exists(frame_path_to_display):
                    print(
                        f"Error: Annotated frame file was not created at {frame_path_to_display} after {max_retries} retries"
                    )

        # Display the frame - prioritize annotated frame if it exists
        if frame_path_to_display and os.path.exists(frame_path_to_display):
            # Load the pixmap from the annotated frame - force reload by clearing cache
            pixmap = QPixmap()
            if not pixmap.load(frame_path_to_display):
                # If pixmap failed to load, fall back to original
                print(
                    f"Warning: Failed to load annotated frame from {frame_path_to_display}, using original"
                )
                if self.current_original_pixmap:
                    pixmap = self.current_original_pixmap
                else:
                    self.frame_label.clear()
                    self.frame_label.setText(f"Frame not found")
                    return
        elif self.current_original_pixmap:
            pixmap = self.current_original_pixmap
        else:
            self.frame_label.clear()
            self.frame_label.setText(f"Frame not found")
            return

        scaled_pixmap = pixmap.scaled(
            self.frame_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.frame_label.setPixmap(scaled_pixmap)

    def jump_to_frame_and_highlight_particle(
        self, frame_number, particle_x, particle_y
    ):
        """Jump to a specific frame and highlight a particle with a blue box."""
        if 0 <= frame_number < self.total_frames:
            # Set highlighted particle coordinates FIRST, before displaying frame
            # This ensures _update_annotations() sees them when it runs
            self.highlighted_particle_x = particle_x
            self.highlighted_particle_y = particle_y
            # Now display the frame (which will call _update_annotations with the coordinates set)
            self.display_frame(frame_number)

    def update_frame_display(self):
        """Update the frame display and input"""
        if self.total_frames > 0:
            self.current_frame_label.setText(
                f"Frame: {self.current_frame_idx} / {self.total_frames - 1}"
            )
            self.frame_slider.setValue(self.current_frame_idx)
        else:
            self.current_frame_label.setText("Frame: 0 / 0")
        self.frame_input.setText(str(self.current_frame_idx))

    def previous_frame(self):
        """Go to previous frame"""
        if self.current_frame_idx > 0:
            # Clear highlighted particle when navigating normally (unless we're on the same frame)
            if self.current_frame_idx - 1 != self.current_frame_idx:
                self.highlighted_particle_x = None
                self.highlighted_particle_y = None
            self.display_frame(self.current_frame_idx - 1)

    def next_frame(self):
        """Go to next frame"""
        if self.current_frame_idx < self.total_frames - 1:
            # Clear highlighted particle when navigating normally (unless we're on the same frame)
            if self.current_frame_idx + 1 != self.current_frame_idx:
                self.highlighted_particle_x = None
                self.highlighted_particle_y = None
            self.display_frame(self.current_frame_idx + 1)

    def go_to_frame(self):
        """Go to frame specified in input"""
        try:
            frame_number = int(self.frame_input.text())
            if 0 <= frame_number < self.total_frames:
                # Clear highlighted particle when navigating normally (unless we're on the same frame)
                if frame_number != self.current_frame_idx:
                    self.highlighted_particle_x = None
                    self.highlighted_particle_y = None
                self.display_frame(frame_number)
        except ValueError:
            pass

    def slider_value_changed(self, value):
        """Go to frame specified by slider"""
        if 0 <= value < self.total_frames:
            # Clear highlighted particle when navigating normally (unless we're on the same frame)
            if value != self.current_frame_idx:
                self.highlighted_particle_x = None
                self.highlighted_particle_y = None
            self.display_frame(value)

    def resizeEvent(self, event):
        """Handle widget resize to update frame display"""
        super().resizeEvent(event)
        self._update_annotations()
