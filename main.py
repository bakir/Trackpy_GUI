import sys
from PySide6.QtCore import QUrl, Qt
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
    QTabWidget
)
from PySide6.QtGui import QAction
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6 import QtWidgets
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # --- Main splitter ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # --- Left Panel (Video Player) ---
        self.main_layout.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.main_layout.left_panel)
        self.init_video()
        self.splitter.addWidget(self.main_layout.left_panel)

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

        # --- Right Panel (Tabs) ---
        self.main_layout.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.main_layout.right_panel)
        self.tab_widget = QTabWidget(self.main_layout.right_panel)

        self.tab1 = QWidget()
        self.tab2 = QWidget()

        self.tab_widget.addTab(self.tab1, "Particle Detection")
        self.tab_widget.addTab(self.tab2, "Trajectory Detection")

        self.splitter.addWidget(self.tab_widget)

        self.initTab1()
        self.initTab2()

        self.splitter.setSizes([700, 300])

    def initTab1(self):
        self.tab1_layout = QVBoxLayout(self.tab1)

        # Mass Slider
        self.mass_label = QLabel("Mass")
        self.mass_slider = QSlider(Qt.Horizontal)
        self.tab1_layout.addWidget(self.mass_label)
        self.tab1_layout.addWidget(self.mass_slider)

        # Eccentricity Slider
        self.ecc_label = QLabel("Eccentricity")
        self.ecc_slider = QSlider(Qt.Horizontal)
        self.tab1_layout.addWidget(self.ecc_label)
        self.tab1_layout.addWidget(self.ecc_slider)

        # Size Slider
        self.size_label = QLabel("Size")
        self.size_slider = QSlider(Qt.Horizontal)
        self.tab1_layout.addWidget(self.size_label)
        self.tab1_layout.addWidget(self.size_slider)

        self.tab1_layout.addStretch() # Pushes sliders to the top

    def initTab2(self):
        self.tab2_layout = QVBoxLayout(self.tab2)

        # Whatever We Want Slider
        self.mass_label = QLabel("Trajectory things")
        self.mass_slider = QSlider(Qt.Horizontal)
        self.tab2_layout.addWidget(self.mass_label)
        self.tab2_layout.addWidget(self.mass_slider)

        # Slider
        self.ecc_label = QLabel("idk")
        self.ecc_slider = QSlider(Qt.Horizontal)
        self.tab2_layout.addWidget(self.ecc_label)
        self.tab2_layout.addWidget(self.ecc_slider)

        # Slider
        self.size_label = QLabel("what varibles go here")
        self.size_slider = QSlider(Qt.Horizontal)
        self.tab2_layout.addWidget(self.size_label)
        self.tab2_layout.addWidget(self.size_slider)

        self.tab2_layout.addStretch() # Pushes sliders to the top
 
    def init_video(self):
        self.video_widget = QVideoWidget(self)
        self.left_layout.addWidget(self.video_widget)

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.left_layout.addWidget(self.play_pause_button)
  
    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_name:
            self.player.setSource(QUrl.fromLocalFile(file_name))
            self.player.play()
            self.statusBar().showMessage(f"Playing {file_name}")

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_pause_button.setText("Pause")
        else:
            self.player.play()
            self.play_pause_button.setText("Play")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Sets the style of the gui
    app.setStyle(QtWidgets.QStyleFactory.create("Windows"))
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
