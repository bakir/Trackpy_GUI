"""
Video Frame display window for particle detection window

Description: Widget displaying frames of the video with frame controls. Shows the particles tracked.
             Generated boiler plate code using Cursor.
"""

import sys
import cv2
import os
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

                frame_path = os.path.join(self.output_folder, f"frame_{frame_idx:05d}.jpg")
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
            self.original_frames_folder = config_manager.get_path('original_frames_folder')
            self.annotated_frames_folder = config_manager.get_path('annotated_frames_folder')
            self.update_feature_size()

    def update_feature_size(self):
        """Update feature size from config."""
        if self.config_manager:
            self.feature_size = self.config_manager.get_detection_params().get('feature_size', 15)

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
        self.frame_label = QLabel()
        self.frame_label.setAlignment(Qt.AlignCenter)
        self.frame_label.setMinimumSize(640, 480)
        self.frame_label.setStyleSheet("border: 1px solid gray; background-color: black;")
        self.frame_label.setText("No video loaded")
        layout.addWidget(self.frame_label)

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

    def save_video_frames(self, video_path):
        """Save video frames to disk in a background thread"""
        self.video_path = video_path
        self.current_frame_idx = 0
        self.annotate_toggle.setChecked(False)

        self.save_thread = SaveFramesThread(video_path, self.original_frames_folder)
        self.save_thread.save_complete.connect(self.on_save_complete)
        self.save_thread.start()

    def on_save_complete(self, total_frames):
        """Handle save completion"""
        self.total_frames = total_frames
        if self.total_frames > 0:
            self.frame_slider.setRange(0, self.total_frames - 1)
            self.display_frame(0)
        self.update_frame_display()
        self.frames_saved.emit(self.total_frames)

    def load_frames(self, num_frames):
        """Load existing frames."""
        self.total_frames = num_frames
        if self.total_frames > 0:
            self.frame_slider.setRange(0, self.total_frames - 1)
            self.display_frame(0)
        self.update_frame_display()

    def on_toggle_annotate(self, state):
        self.show_annotated = self.annotate_toggle.isChecked()
        self.display_frame(self.current_frame_idx)

    def display_frame(self, frame_number):
        """Display a specific frame from a file"""
        if not (0 <= frame_number < self.total_frames):
            return

        if self.file_controller:
            self.file_controller.delete_all_files_in_folder(self.annotated_frames_folder)

        file_name = f"frame_{frame_number:05d}.jpg"
        frame_path_to_display = os.path.join(self.original_frames_folder, file_name)

        if self.file_controller:
            particle_data = self.file_controller.load_particles_data("found_particles.csv")
            if not particle_data.empty:
                particles_in_frame = particle_data[particle_data['frame'] == frame_number]
                if not particles_in_frame.empty:
                    params = self.config_manager.get_detection_params()
                    save_errant_particle_crops_for_frame(frame_number, particles_in_frame, params)
                    self.errant_particles_updated.emit()

                if self.show_annotated:
                    annotated_path = annotate_frame(frame_number, particles_in_frame, self.feature_size)
                    if annotated_path:
                        frame_path_to_display = annotated_path

        if not os.path.exists(frame_path_to_display):
            self.frame_label.clear()
            self.frame_label.setText(f"Frame not found: {file_name}")
        else:
            pixmap = QPixmap(frame_path_to_display)
            scaled_pixmap = pixmap.scaled(self.frame_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.frame_label.setPixmap(scaled_pixmap)

        self.current_frame_idx = frame_number
        self.update_frame_display()

    def update_frame_display(self):
        """Update the frame display and input"""
        if self.total_frames > 0:
            self.current_frame_label.setText(f"Frame: {self.current_frame_idx} / {self.total_frames - 1}")
            self.frame_slider.setValue(self.current_frame_idx)
        else:
            self.current_frame_label.setText("Frame: 0 / 0")
        self.frame_input.setText(str(self.current_frame_idx))

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
            frame_number = int(self.frame_input.text())
            if 0 <= frame_number < self.total_frames:
                self.display_frame(frame_number)
        except ValueError:
            pass

    def slider_value_changed(self, value):
        """Go to frame specified by slider"""
        if 0 <= value < self.total_frames:
            self.display_frame(value)

    def resizeEvent(self, event):
        """Handle widget resize to update frame display"""
        super().resizeEvent(event)
        if 0 <= self.current_frame_idx < self.total_frames:
            self.display_frame(self.current_frame_idx)