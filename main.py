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

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Tab Widget Demo')
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()

        self.tab_widget.addTab(self.tab1, "Tab 1")
        self.tab_widget.addTab(self.tab2, "Tab 2")
        self.tab_widget.addTab(self.tab3, "Tab 3")

        self.layout.addWidget(self.tab_widget)

        self.initTab1()
        self.initTab2()

    def initTab1(self):
        layout = QVBoxLayout(self.tab1)
        label = QLabel("Content of Tab 1")
        layout.addWidget(label)

    def initTab2(self):
        layout = QVBoxLayout(self.tab2)
        label = QLabel("Content of Tab 2")
        layout.addWidget(label)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TrackPy GUI")
        self.setGeometry(100, 100, 1000, 600)

        # Tabs (hopefully)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()

        self.tab_widget.addTab(self.tab1, "Particle Detection")
        self.tab_widget.addTab(self.tab2, "Trajectory Detection")

        self.layout.addWidget(self.tab_widget)

        self.initTab1()
        self.initTab2()

    def initTab1(self):
        layout = QVBoxLayout(self.tab1)
        
        # Main splitter
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)

        # --- Left Panel (Video Player) ---
        layout.left_panel = QWidget()
        self.left_layout = QVBoxLayout(layout.left_panel)
        self.init_video()
        self.splitter.addWidget(layout.left_panel)
        

        # --- Right Panel (Sliders) ---
        layout.right_panel = QWidget()
        self.right_layout = QVBoxLayout(layout.right_panel)
        self.init_param_controls_tab1()
        self.splitter.addWidget(layout.right_panel)

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

    def initTab2(self):
        layout = QVBoxLayout(self.tab2)
        
        # Main splitter
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)

        # --- Left Panel (Video Player) ---
        layout.left_panel = QWidget()
        self.left_layout = QVBoxLayout(layout.left_panel)
        self.init_video()
        self.splitter.addWidget(layout.left_panel)
        

        # --- Right Panel (Sliders) ---
        layout.right_panel = QWidget()
        self.right_layout = QVBoxLayout(layout.right_panel)
        self.init_param_controls_tab2()
        self.splitter.addWidget(layout.right_panel)

        # Set initial sizes for the splitter
        self.splitter.setSizes([700, 300])

        # --- Media Player Setup ---
        # self.player = QMediaPlayer()
        # self.player.setVideoOutput(self.video_widget)

        # # --- Menu Bar ---
        # menu_bar = self.menuBar()
        # file_menu = menu_bar.addMenu("File")
        # import_action = QAction("Import...", self)
        # import_action.triggered.connect(self.open_file_dialog)
        # file_menu.addAction(import_action)

        # # --- Status Bar ---
        # self.statusBar().showMessage("Ready")


    def init_video(self):
        self.video_widget = QVideoWidget()
        self.left_layout.addWidget(self.video_widget)

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.left_layout.addWidget(self.play_pause_button)

    def init_param_controls_tab1(self):
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

    def init_param_controls_tab2(self):
        # Mass Slider
        self.mass_label = QLabel("Trajectory things")
        self.mass_slider = QSlider(Qt.Horizontal)
        self.right_layout.addWidget(self.mass_label)
        self.right_layout.addWidget(self.mass_slider)

        # Eccentricity Slider
        self.ecc_label = QLabel("idk")
        self.ecc_slider = QSlider(Qt.Horizontal)
        self.right_layout.addWidget(self.ecc_label)
        self.right_layout.addWidget(self.ecc_slider)

        # Size Slider
        self.size_label = QLabel("what varibles go here")
        self.size_slider = QSlider(Qt.Horizontal)
        self.right_layout.addWidget(self.size_label)
        self.right_layout.addWidget(self.size_slider)

        self.right_layout.addStretch() # Pushes sliders to the top

    
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
    app.setStyle(QtWidgets.QStyleFactory.create("Windows"))
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
