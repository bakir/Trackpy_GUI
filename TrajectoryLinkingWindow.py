import os
import sys
import cv2

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QFormLayout,
    QPushButton,
    QSlider,
    QLabel,
    QSplitter,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
    QLineEdit,

)
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6 import QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure

from ErrantTrajectoryGalleryWidget import *
from TrajectoryPlayerWidget import *
from TrajectoryPlottingWidget import *
from LinkingParametersWidget import *
from ParticleDetectionWindow import *


import particle_processing
from config_parser import get_config
config = get_config()
PARTICLES_FOLDER = config.get('particles_folder', 'particles/')
FRAMES_FOLDER = config.get('frames_folder', 'frames/')
VIDEOS_FOLDER = config.get('videos_folder', 'videos/')

def save_video_frames(video_path: str, output_folder: str):
    """
    Extracts all frames from a video and saves them as .jpg in the output folder.

    Args:
        video_path (str): Path to the video file.
        output_folder (str): Path to the folder where frames will be saved.
    """
    # Make sure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret or frame_idx > 5:
            break  # End of video

        frame_path = os.path.join(output_folder, f"frame_{frame_idx:05d}.jpg")
        cv2.imwrite(frame_path, frame)
        frame_idx += 1

    cap.release()
    print(f"Saved {frame_idx} frames to {output_folder}")

class TrajectoryLinkingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Main Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.resize(1200, 500)

        # Left Panel
        self.main_layout.left_panel = TrajectoryPlottingWidget()
        self.main_layout.addWidget(self.main_layout.left_panel)

        # Middle Panel
        self.main_layout.middle_panel = QWidget()
        self.middle_layout = QVBoxLayout(self.main_layout.middle_panel)

        self.frame_player = TrajectoryPlayerWidget()
        self.middle_layout.addWidget(self.frame_player)
        self.errant_particle_gallery = ErrantTrajectoryGalleryWidget()
        self.middle_layout.addWidget(self.errant_particle_gallery)

        self.main_layout.addWidget(self.main_layout.middle_panel)

        # Right Panel
        self.main_layout.right_panel = LinkingParametersWidget()
        self.right_layout = QVBoxLayout(self.main_layout.right_panel)
        self.main_layout.addWidget(self.main_layout.right_panel)
        
        # Connect trajectory visualization signal to display in trajectory player
        self.main_layout.right_panel.trajectoryVisualizationCreated.connect(
            self.frame_player.display_trajectory_image
        )
        
        # Connect back button signal to return to detection window
        self.main_layout.right_panel.goBackToDetection.connect(self.go_back_to_detection)
        
        # Connect RB gallery creation signal to refresh the trajectory gallery
        self.main_layout.right_panel.rbGalleryCreated.connect(
            self.errant_particle_gallery.refresh_rb_gallery
        )

    def go_back_to_detection(self):
        """Close trajectory linking window and open particle detection window."""
        # Close current window
        self.close()
        # Open particle detection window
        self.detection_window = ParticleDetectionWindow()
        self.detection_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Sets the style of the gui
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    detection_win = TrajectoryLinkingWindow()
    detection_win.show()
    sys.exit(app.exec())
