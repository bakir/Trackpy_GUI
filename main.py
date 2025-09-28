import sys
import os
import cv2
from PySide6.QtCore import QUrl, Qt
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
)
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget


def save_video_frames(video_path: str, output_folder: str, max_frames: int = 5):
    """Extracts frames from a video and saves them as .jpg in the output folder."""
    os.makedirs(output_folder, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret or frame_idx >= max_frames:
            break

        frame_path = os.path.join(output_folder, f"frame_{frame_idx:05d}.jpg")
        cv2.imwrite(frame_path, frame)
        frame_idx += 1

    cap.release()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TrackPy GUI")
        self.setGeometry(100, 100, 1000, 600)

        # Main splitter (left: video/photo, right: controls)
        self.splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.splitter)

        # Left panel
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.init_video()
        self.splitter.addWidget(self.left_panel)

        # Right panel
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.init_param_controls()
        self.splitter.addWidget(self.right_panel)

        # Splitter proportions
        self.splitter.setSizes([700, 300])

        # Media Player
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)

        # Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        import_action = QAction("Import...", self)
        import_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(import_action)

        # Status Bar
        self.statusBar().showMessage("Ready")

    def init_video(self):
        self.video_widget = QVideoWidget()
        self.left_layout.addWidget(self.video_widget)

        self.photo_label = QLabel("Photo display")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            "background-color: #222; color: #ccc; border: 1px solid #555;"
        )
        self.photo_label.setMinimumHeight(200)
        self.left_layout.addWidget(self.photo_label)

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.left_layout.addWidget(self.play_pause_button)

    def init_param_controls(self):
        for label_text in ["Mass", "Eccentricity", "Size"]:
            label = QLabel(label_text)
            slider = QSlider(Qt.Horizontal)
            self.right_layout.addWidget(label)
            self.right_layout.addWidget(slider)

        self.right_layout.addStretch()

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "", "Video Files (*.mp4 *.avi *.mov)"
        )
        if file_name:
            self.player.setSource(QUrl.fromLocalFile(file_name))
            self.player.play()
            self.play_pause_button.setText("Pause")
            self.statusBar().showMessage(f"Playing {file_name}")

            frames_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "frames"
            )
            save_video_frames(file_name, frames_dir)

            first_frame = os.path.join(frames_dir, sorted(os.listdir(frames_dir))[0])
            pixmap = QPixmap(first_frame)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.photo_label.width(),
                    self.photo_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.photo_label.setPixmap(scaled)
                self.photo_label.setText("")

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_pause_button.setText("Play")
        else:
            self.player.play()
            self.play_pause_button.setText("Pause")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())