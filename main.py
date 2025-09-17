import sys
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QAction
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TrackPy GUI")
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget to display the video
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.video_widget = QVideoWidget()
        self.layout.addWidget(self.video_widget)

        self.play_pause_button = QPushButton("Play")
        self.layout.addWidget(self.play_pause_button)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        self.player.playbackStateChanged.connect(self.update_button_text)


        # Create the menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        import_action = QAction("Import", self)
        import_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(import_action)

        # Create a status bar
        self.statusBar().showMessage("Ready")

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi *.mov)")
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
