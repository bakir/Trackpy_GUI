import sys
import cv2
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
    QVBoxLayout,
    QSplitter,
    QHBoxLayout,
    QGroupBox,
    QLineEdit,
)
from PySide6.QtGui import QAction, QPixmap, QImage


class FrameExtractionThread(QThread):
    """Thread for extracting frames from video"""
    frame_extracted = Signal(int, QPixmap)  # frame_number, pixmap
    extraction_complete = Signal(int)  # total_frames

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.cap = None

    def run(self):
        """Extract frames from video"""
        try:
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                return

            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.extraction_complete.emit(total_frames)

            frame_count = 0
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break

                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w

                # Convert to QImage then QPixmap
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)

                self.frame_extracted.emit(frame_count, pixmap)
                frame_count += 1

        except Exception as e:
            print(f"Error extracting frames: {e}")
        finally:
            if self.cap:
                self.cap.release()

class FramePlayerWidget(QWidget):
    """Widget for displaying video frames as a slideshow"""

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

        # Frame navigation controls
        nav_layout = QHBoxLayout()

        # Previous frame button
        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedSize(40, 30)
        self.prev_button.clicked.connect(self.previous_frame)
        nav_layout.addWidget(self.prev_button)

        # Frame number display and input
        frame_info_layout = QVBoxLayout()

        # Current frame display
        self.current_frame_label = QLabel("Frame: 0 / 0")
        self.current_frame_label.setAlignment(Qt.AlignCenter)
        frame_info_layout.addWidget(self.current_frame_label)

        # Frame input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Go to frame:"))
        self.frame_input = QLineEdit()
        self.frame_input.setPlaceholderText("Enter frame number")
        self.frame_input.returnPressed.connect(self.go_to_frame)
        input_layout.addWidget(self.frame_input)
        input_layout.addStretch()

        frame_info_layout.addLayout(input_layout)
        nav_layout.addLayout(frame_info_layout)

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
        self.current_frame = 0
        self.frames = {}  # Dictionary to store extracted frames
        self.extraction_thread = None

    def load_video(self, file_path):
        """Load a video file and extract frames"""
        self.video_path = file_path
        self.frames.clear()
        self.current_frame = 0

        # Start frame extraction in a separate thread
        self.extraction_thread = FrameExtractionThread(file_path)
        self.extraction_thread.frame_extracted.connect(self.on_frame_extracted)
        self.extraction_thread.extraction_complete.connect(self.on_extraction_complete)
        self.extraction_thread.start()

    def on_frame_extracted(self, frame_number, pixmap):
        """Handle extracted frame"""
        self.frames[frame_number] = pixmap

        # Display first frame immediately
        if frame_number == 0:
            self.display_frame(0)

    def on_extraction_complete(self, total_frames):
        """Handle extraction completion"""
        self.total_frames = total_frames
        self.update_frame_display()

    def display_frame(self, frame_number):
        """Display a specific frame"""
        if frame_number in self.frames:
            # Scale the pixmap to fit the label while maintaining aspect ratio
            pixmap = self.frames[frame_number]
            scaled_pixmap = pixmap.scaled(self.frame_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.frame_label.setPixmap(scaled_pixmap)
            self.current_frame = frame_number
            self.update_frame_display()

    def update_frame_display(self):
        """Update the frame display and input"""
        self.current_frame_label.setText(f"Frame: {self.current_frame} / {self.total_frames - 1}")
        self.frame_input.setText(str(self.current_frame))

    def previous_frame(self):
        """Go to previous frame"""
        if self.current_frame > 0:
            self.display_frame(self.current_frame - 1)

    def next_frame(self):
        """Go to next frame"""
        if self.current_frame < self.total_frames - 1:
            self.display_frame(self.current_frame + 1)

    def go_to_frame(self):
        """Go to frame specified in input"""
        try:
            frame_number = int(self.frame_input.text())
            if 0 <= frame_number < self.total_frames:
                self.display_frame(frame_number)
        except ValueError:
            pass

    def resizeEvent(self, event):
        """Handle widget resize to update frame display"""
        super().resizeEvent(event)
        if hasattr(self, 'current_frame') and self.current_frame in self.frames:
            self.display_frame(self.current_frame)