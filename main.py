import sys
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
    QHBoxLayout,
)
from PySide6.QtGui import QAction
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget


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

        self.video_widget = QVideoWidget()
        self.left_layout.addWidget(self.video_widget)

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.left_layout.addWidget(self.play_pause_button)

        self.splitter.addWidget(self.left_panel)

        # --- Right Panel (Sliders) ---
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)

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
        self.splitter.addWidget(self.right_panel)

        # Set initial sizes for the splitter
        self.splitter.setSizes([700, 300])


        # --- Media Player Setup ---
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        self.player.playbackStateChanged.connect(self.update_button_text)

        # --- Menu Bar ---
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        import_action = QAction("Import...", self)
        import_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(import_action)

        # --- Status Bar ---
        self.statusBar().showMessage("Ready")

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "", "Video Files (*.mp4 *.avi *.mov)"
        )
        if file_name:
            self.player.setSource(QUrl.fromLocalFile(file_name))
            self.player.play()
            self.statusBar().showMessage(f"Playing {file_name}")

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def update_button_text(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_button.setText("Pause")
        else:
            self.play_pause_button.setText("Play")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
