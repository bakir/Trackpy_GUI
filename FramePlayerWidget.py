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
)
from PySide6.QtGui import QPixmap, QImage

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

                frame_path = os.path.join(self.output_folder, f"original_frame_{frame_idx:05d}.jpg")
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

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_variables()

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

        # Previous frame button
        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedSize(40, 30)
        self.prev_button.clicked.connect(self.previous_frame)
        nav_layout.addWidget(self.prev_button)

        # select frame widget
        nav_layout.addWidget(QLabel("Select frame"))
        self.frame_input = QLineEdit()
        self.frame_input.setPlaceholderText("Enter frame number")
        self.frame_input.returnPressed.connect(self.go_to_frame)
        nav_layout.addWidget(self.frame_input)

        # Frame slider
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setRange(0, 0)
        self.frame_slider.valueChanged.connect(self.slider_value_changed)
        nav_layout.addWidget(self.frame_slider)

        # Next frame button
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
        self.frame_files = []
        self.save_thread = None
        self.frames_folder = "frames"

    def save_video_frames(self, video_path):
        """Save video frames to disk in a background thread"""
        self.video_path = video_path
        self.frame_files = []
        self.current_frame_idx = 0

        # Start frame saving in a separate thread
        self.save_thread = SaveFramesThread(video_path, self.frames_folder)
        self.save_thread.save_complete.connect(self.on_save_complete)
        self.save_thread.start()

    def on_save_complete(self, total_frames):
        """Handle save completion"""
        self.total_frames = total_frames
        self._load_frames_from_disk()
        if self.total_frames > 0:
            self.frame_slider.setRange(0, self.total_frames - 1)
            self.display_frame(0)
        self.update_frame_display()
        self.frames_saved.emit(self.total_frames)

    def _load_frames_from_disk(self):
        """Load the list of frame files from the frames directory"""
        if not os.path.isdir(self.frames_folder):
            self.frame_files = []
            return
        
        files = [f for f in os.listdir(self.frames_folder) if f.startswith("original_frame_") and f.endswith(".jpg")]
        files.sort()
        self.frame_files = [os.path.join(self.frames_folder, f) for f in files]
        self.total_frames = len(self.frame_files)

    def display_frame(self, frame_number):
        """Display a specific frame from a file"""
        if 0 <= frame_number < self.total_frames:
            pixmap = QPixmap(self.frame_files[frame_number])
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
        if 0 <= self.current_frame_idx < len(self.frame_files):
            self.display_frame(self.current_frame_idx)