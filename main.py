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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TrackPy GUI")
        self.setGeometry(100, 100, 1000, 600)

        # Main splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.splitter)

        # --- Left Panel (Video Player) ---
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.init_video()
        self.splitter.addWidget(self.left_panel)
        

        # --- Right Panel (Sliders) ---
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.init_param_controls()
        self.splitter.addWidget(self.right_panel)

        # Set initial sizes for the splitter
        self.splitter.setSizes([700, 300])

        # --- Media Player Setup ---
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)

        # --- Menu Bar ---
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        import_action = QAction("Import...", self)
        import_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(import_action)

        # --- Status Bar ---
        self.statusBar().showMessage("Ready")

    def init_video(self):
        self.video_widget = QVideoWidget()
        self.left_layout.addWidget(self.video_widget)


        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.left_layout.addWidget(self.play_pause_button)

        
        # Dummy photo display area
        self.photo_label = QLabel("Photo display")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            "background-color: #222; color: #ccc; border: 1px solid #555;"
        )
        self.photo_label.setMinimumHeight(200)

        self.left_layout.addWidget(self.photo_label)

        # --- Frame Navigation ---
        self.frame_nav_layout = QHBoxLayout()
        self.prev_frame_button = QPushButton("<")
        self.frame_number_display = QLineEdit("0")
        self.curr_particle_idx = 0
        self.frame_number_display.setReadOnly(True)
        self.frame_number_display.setAlignment(Qt.AlignCenter)
        self.next_frame_button = QPushButton("->")
        # self.prev_frame_button.clicked.connect(self.prev_frame)
        self.next_frame_button.clicked.connect(self.next_particle)
        self.frame_nav_layout.addWidget(self.prev_frame_button)
        self.frame_nav_layout.addWidget(self.frame_number_display)
        self.frame_nav_layout.addWidget(self.next_frame_button)
        self.left_layout.addLayout(self.frame_nav_layout)

    def next_particle(self):
        self.curr_particle_idx += 1
        pixmap = QPixmap(os.path.join(PARTICLES_FOLDER, sorted(os.listdir(PARTICLES_FOLDER))[self.curr_particle_idx]))
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self.photo_label.width(),
                self.photo_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            print("height  ", self.photo_label.height())
            self.photo_label.setPixmap(scaled)
            self.photo_label.setText("")
            self.photo_label.repaint()


    def init_param_controls(self):
        # Mass Slider
        self.mass_label = QLabel("Mass")
        self.mass_slider = QSlider(Qt.Horizontal)
        self.right_layout.addWidget(self.mass_label)
        self.right_layout.addWidget(self.mass_slider)

        # Eccentricity Slider
        self.ecc_label = QLabel("Eccentricity")
        self.ecc_slider = QSlider(Qt.Horizontal)
        self.right_layout.addWidget(self.ecc_label)
        self.right_layout.addWidget(self.ecc_slider)

        # Size Slider
        self.size_label = QLabel("Size")
        self.size_slider = QSlider(Qt.Horizontal)
        self.right_layout.addWidget(self.size_label)
        self.right_layout.addWidget(self.size_slider)

        self.right_layout.addStretch() # Pushes sliders to the top
        self.find_particles_button = QPushButton("Find Particles")
        self.find_particles_button.clicked.connect(self.find_particles)
        self.right_layout.addWidget(self.find_particles_button)
        self.splitter.addWidget(self.right_panel)

    
    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_name:
            self.player.setSource(QUrl.fromLocalFile(file_name))
            self.player.play()
            self.play_pause_button.setText("Pause")
            self.statusBar().showMessage(f"Playing {file_name}")

            save_video_frames(file_name, FRAMES_FOLDER)

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_pause_button.setText("Pause")
        else:
            self.player.play()
            self.play_pause_button.setText("Play")

    def prev_frame(self):
        if self.frame_files and self.current_frame_index > 0:
            self.current_frame_index -= 1
            self.show_frame()

    def find_particles(self):
        if True: #self.frame_files:
            current_image_path = os.path.join(FRAMES_FOLDER, "frame_00000.jpg")
            particle_processing.find_and_save_particles(current_image_path)
            pixmap = QPixmap(os.path.join(PARTICLES_FOLDER, sorted(os.listdir(PARTICLES_FOLDER))[0]))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.photo_label.width(),
                    self.photo_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.photo_label.setPixmap(scaled)
                self.photo_label.setText("")
                self.photo_label.repaint()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())