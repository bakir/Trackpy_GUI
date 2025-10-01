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
    def __init__(self, page):
        super().__init__()
        self.page = page

        self.determine_page()
        
        

    def determine_page(self):
        if self.page == "particle detection":
            self.particle_detection_window()
        elif self.page == "trajectory tracking":
            self.trajectory_tracking_window()

    def particle_detection_window(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.resize(1200, 500)

        # --- Right Panel (Graphing) ---
        self.main_layout.graph_panel = QWidget()
        self.graph_layout = QVBoxLayout(self.main_layout.graph_panel)
        self.main_layout.addWidget(self.main_layout.graph_panel)
        self.filler_plot()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setFixedSize(300, 400)
        self.canvas.hide()
        self.graph_layout.addWidget(self.canvas)
        self.sb_button = QPushButton(text="Plot Subpixel Bias", parent=self)
        self.sb_button.setFixedSize(150, 40)
        self.sb_button.clicked.connect(self.show_graph)
        self.graph_layout.addWidget(self.sb_button)
        
        # --- Main splitter ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # --- Middle Panel (Video Player) ---
        self.main_layout.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.main_layout.left_panel)
        self.init_video()
        self.splitter.addWidget(self.main_layout.left_panel)

        # --- Media Player Setup ---
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)

        # --- Menu Bar ---
        self.create_menu_bar()

        # --- Status Bar ---
        self.statusBar().showMessage("Ready")

        # --- Right Panel (Tabs) ---
        self.main_layout.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.main_layout.right_panel)
        self.detection_parameters()
        self.splitter.addWidget(self.main_layout.right_panel)

    def trajectory_tracking_window(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.resize(1200, 500)

        # --- Left Panel (Graphing) ---
        self.main_layout.graph_panel = QWidget()
        self.graph_layout = QVBoxLayout(self.main_layout.graph_panel)
        self.main_layout.addWidget(self.main_layout.graph_panel)
        self.filler_plot()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setFixedSize(300, 400)
        self.graph_layout.addWidget(self.canvas)
        self.canvas.hide()
        self.sb_button = QPushButton(text="Plot Subpixel Bias", parent=self)
        self.sb_button.setFixedSize(150, 40)
        self.sb_button.clicked.connect(self.show_graph)
        self.graph_layout.addWidget(self.sb_button)

        # --- Main splitter ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # --- Middle Panel (Video Player) ---
        self.main_layout.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.main_layout.left_panel)
        self.init_video()
        self.splitter.addWidget(self.main_layout.left_panel)

        # --- Media Player Setup ---
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)

        # --- Menu Bar ---
        self.create_menu_bar()

        # --- Status Bar ---
        self.statusBar().showMessage("Ready")

        # --- Right Panel (Parameters) ---
        self.main_layout.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.main_layout.right_panel)
        self.trajectory_parameters()
        self.splitter.addWidget(self.main_layout.right_panel)


    def detection_parameters(self):
        self.detection_layout = self.right_layout



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





    def init_video(self):
        self.video_widget = QVideoWidget(self)
        self.left_layout.addWidget(self.video_widget)

        self.right_layout.addStretch() # Pushes sliders to the top
        self.find_particles_button = QPushButton("Find Particles")
        self.find_particles_button.clicked.connect(self.find_particles)
        self.right_layout.addWidget(self.find_particles_button)
        self.splitter.addWidget(self.right_panel)

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.left_layout.addWidget(self.play_pause_button)
  
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


    def create_menu_bar(self):
        # import 
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        import_action = QAction("Import...", self)
        import_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(import_action)
        # save parameters (doesnt actually work)
        particle_menu = menu_bar.addMenu("Particles")
        save_action = QAction("Save Particle Parameters", self)
        save_action.triggered.connect(self.save_parameters)
        particle_menu.addAction(save_action)
        # reopen parameters
        open_detection_action = QAction("Change Particle Parameters", self)
        open_detection_action.triggered.connect(self.open_detection_page)
        particle_menu.addAction(open_detection_action)
        # go to trajetories
        open_trajectories_action = QAction("Go to Trajectory Tracking", self)
        open_trajectories_action.triggered.connect(self.open_trajectories_page)
        particle_menu.addAction(open_trajectories_action)

    def save_parameters(self):
        pass

    def open_detection_page(self):
        if detection_win.isHidden():
            trajectory_win.hide()
            detection_win.show()

    def open_trajectories_page(self):
        if trajectory_win.isHidden():
            detection_win.hide()
            trajectory_win.show()

    def filler_plot(self):
        self.fig = Figure()
        x = [1, 2, 3, 4, 5]
        y = [1, 4, 9, 16, 25]
        ax = self.fig.add_subplot()
        ax.plot(x, y)

    def show_graph(self):
        self.canvas.show()

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

    # Sets the style of the gui
    app.setStyle(QtWidgets.QStyleFactory.create("Windows"))
    detection_win = MainWindow("particle detection")
    trajectory_win = MainWindow("trajectory tracking")
    detection_win.show()
    sys.exit(app.exec())
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())

