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

from ErrantParticleGalleryWidget import *
from FramePlayerWidget import *
from GraphingPanelWidget import *
from DetectionParametersWidget import *


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
        if not ret or frame_idx >= 5:
            break  # End of video

        frame_path = os.path.join(output_folder, f"frame_{frame_idx:05d}.jpg")
        cv2.imwrite(frame_path, frame)
        frame_idx += 1

    cap.release()
    print(f"Saved {frame_idx} frames to {output_folder}")

class ParticleDetectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Main Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.resize(1200, 500)

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        import_action = QAction("Import Video...", self)
        import_action.triggered.connect(self.import_video)
        file_menu.addAction(import_action)

        # Left Panel
        self.main_layout.left_panel = GraphingPanelWidget()
        self.main_layout.addWidget(self.main_layout.left_panel)

        # Middle Panel
        self.main_layout.middle_panel = QWidget()
        self.middle_layout = QVBoxLayout(self.main_layout.middle_panel)

        self.frame_player = FramePlayerWidget()
        self.middle_layout.addWidget(self.frame_player)
        self.errant_particle_gallery = ErrantParticleGalleryWidget()
        self.middle_layout.addWidget(self.errant_particle_gallery)

        self.main_layout.addWidget(self.main_layout.middle_panel)

        # Right Panel
        self.main_layout.right_panel = DetectionParametersWidget()
        self.right_layout = QVBoxLayout(self.main_layout.right_panel)
        self.main_layout.addWidget(self.main_layout.right_panel)
        # When particles are found, refresh gallery
        self.main_layout.right_panel.particlesUpdated.connect(self.errant_particle_gallery.refresh_particles)

    def import_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", VIDEOS_FOLDER, "Video Files (*.avi *.mp4 *.mov *.mkv);;All Files (*)")
        if not file_path:
            return
        # Ensure frames folder exists and is clean
        os.makedirs(FRAMES_FOLDER, exist_ok=True)
        try:
            particle_processing.delete_all_files_in_folder(FRAMES_FOLDER)
        except Exception:
            pass
        save_video_frames(file_path, FRAMES_FOLDER)
        # Load the selected video into the frame player
        self.frame_player.load_video(file_path)


# clean up temp folders on exit for now
def cleanup_temp_folders():
    """Delete all files in frames and particles folders on app shutdown."""
    # pass
    try:
        particle_processing.delete_all_files_in_folder(PARTICLES_FOLDER)
    except Exception:
        pass
    try:
        particle_processing.delete_all_files_in_folder(FRAMES_FOLDER)
    except Exception:
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Sets the style of the gui
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    detection_win = ParticleDetectionWindow()
    detection_win.show()
    # Clean up temp folders on exit
    app.aboutToQuit.connect(cleanup_temp_folders)
    sys.exit(app.exec())
