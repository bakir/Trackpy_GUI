"""
Trajectory Linking Window

Description: Main window for Trajectory Linkning. Imports trajectory linking widgets.
             Generated boiler plate code using Cursor.
"""

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

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        export_menu = file_menu.addMenu("Export Data")
        export_particle_data_menu = export_menu.addMenu("Particle Data")
        export_trajectory_data_menu = export_menu.addMenu("Trajectory Data")

        # Create the QActions for your sub-options
        export_particle_data_csv_action = QAction("as CSV", self)
        export_particle_data_pkl_action = QAction("as PKL", self)
        export_trajectory_data_csv_action = QAction("as CSV", self)
        export_trajectory_data_pkl_action = QAction("as PKL", self)
        # Add the sub-option actions to the "Export" menu
        export_particle_data_menu.addAction(export_particle_data_csv_action)
        export_particle_data_menu.addAction(export_particle_data_pkl_action)
        export_trajectory_data_menu.addAction(export_trajectory_data_csv_action)
        export_trajectory_data_menu.addAction(export_trajectory_data_pkl_action)
        # You can then connect your sub-actions to functions
        export_particle_data_csv_action.triggered.connect(self.export_particles_csv)
        export_particle_data_pkl_action.triggered.connect(self.export_particles_pkl)
        export_trajectory_data_csv_action.triggered.connect(self.export_trajectories_csv)
        export_trajectory_data_pkl_action.triggered.connect(self.export_trajectories_pkl)

        options_menu = menubar.addMenu("Options")
        stream_action = QAction("Stream", self)
        stream_action.triggered.connect(self.stream)
        options_menu.addAction(stream_action)

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
        self.main_layout.right_panel.trajectoryVisualizationCreated.connect(self.frame_player.display_trajectory_image)
        
        # Connect back button signal to return to detection window
        self.main_layout.right_panel.goBackToDetection.connect(self.go_back_to_detection)
        
        # Connect RB gallery creation signal to refresh the trajectory gallery
        self.main_layout.right_panel.rbGalleryCreated.connect(self.errant_particle_gallery.refresh_rb_gallery)

    
    def _export_data(self, source_filename: str, target_format: str):
        config = get_config()
        particles_folder = config.get('particles_folder', 'particles/')
        
        source_file_path = os.path.join(particles_folder, source_filename)
    
        
        # 1. Check if the source file exists
        if not os.path.exists(source_file_path):
            print("Could not find selected data")
            return

        # 2. Prepare file dialog options based on target format
        if target_format == 'csv':
            file_filter = "CSV Files (*.csv);;All Files (*)"
        elif target_format == 'pkl':
            file_filter = "Pickle Files (*.pkl);;All Files (*)"
        else:
            print(f"Error: Unsupported export format '{target_format}'")
            return

        # 3. Open the 'Save File' dialog
        default_name = f"{os.path.splitext(source_filename)[0]}_export.{target_format}"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "desc",
            default_name,
            file_filter
        )

        # 4. If the user cancelled, exit the method
        if not save_path:
            return

        # 5. Perform the export operation
        try:
            # For both formats, read the source CSV with pandas
            df = pd.read_csv(source_file_path)

            if target_format == 'csv':
                # Save the DataFrame to a new CSV file, without the index column
                df.to_csv(save_path, index=False)
            elif target_format == 'pkl':
                # Save the DataFrame to a pickle file
                df.to_pickle(save_path)
            
            print(f"Data successfully exported to: {save_path}")

        except Exception as e:
            print(f"An error occurred during export: {e}")
            # Consider showing a QMessageBox to inform the user of the error.

    def export_particles_csv(self):
        """Exports the 'all_particles.csv' file to a user-selected CSV file."""
        self._export_data(source_filename='all_particles.csv', target_format='csv')

    def export_particles_pkl(self):
        """Exports the 'all_particles.csv' data as a user-selected pickle file."""
        self._export_data(source_filename='all_particles.csv', target_format='pkl')

    def export_trajectories_csv(self):
        """Exports the 'trajectories.csv' file to a user-selected CSV file."""
        self._export_data(source_filename='trajectories.csv', target_format='csv')

    def export_trajectories_pkl(self):
        self._export_data(source_filename='trajectories.csv', target_format='pkl')

    def stream(self):
        return
    
    def go_back_to_detection(self):
        """Emit signal to switch back to particle detection window."""
        # The controller will handle the actual window switching
        pass

    
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Sets the style of the gui
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    detection_win = TrajectoryLinkingWindow()
    detection_win.show()
    sys.exit(app.exec())
