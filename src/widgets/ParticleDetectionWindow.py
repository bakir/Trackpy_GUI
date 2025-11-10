"""
Particle Detection Window

Description: Main window for Particle detection. Imports particle detection widgets.
             Generated boiler plate code using Cursor.
"""

import os
import sys
import cv2
import pandas as pd

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

from .ErrantParticleGalleryWidget import *
from .FramePlayerWidget import *
from .DetectionPlottingWidget import *
from .DetectionParametersWidget import *
from .TrajectoryLinkingWindow import *


import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from .. import particle_processing


class ParticleDetectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = None
        self.file_controller = None
        self.setup_ui()

    def set_config_manager(self, config_manager):
        """Set the config manager for this window."""
        self.config_manager = config_manager
        # Pass config manager to widgets that need it
        if hasattr(self, "main_layout") and hasattr(self.main_layout, "right_panel"):
            self.main_layout.right_panel.set_config_manager(config_manager)
        if hasattr(self, "frame_player"):
            self.frame_player.set_config_manager(config_manager)
        if hasattr(self, "errant_particle_gallery") and hasattr(
            self.errant_particle_gallery, "set_config_manager"
        ):
            self.errant_particle_gallery.set_config_manager(config_manager)
        if hasattr(self, "main_layout") and hasattr(self.main_layout, "left_panel"):
            self.main_layout.left_panel.set_config_manager(config_manager)

    def set_file_controller(self, file_controller):
        """Set the file controller for this window."""
        self.file_controller = file_controller
        # Pass file controller to widgets that need it
        if hasattr(self, "main_layout") and hasattr(self.main_layout, "right_panel"):
            self.main_layout.right_panel.set_file_controller(file_controller)
        if hasattr(self, "frame_player"):
            self.frame_player.set_file_controller(file_controller)
        if hasattr(self, "errant_particle_gallery") and hasattr(
            self.errant_particle_gallery, "set_file_controller"
        ):
            self.errant_particle_gallery.set_file_controller(file_controller)
        if hasattr(self, "main_layout") and hasattr(self.main_layout, "left_panel"):
            self.main_layout.left_panel.set_file_controller(file_controller)

        # Load existing particle data if available
        self.load_particle_data()

    def setup_ui(self):
        # Main Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.resize(1200, 500)

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        import_action = QAction("Import Video", self)
        import_action.triggered.connect(self.import_video)
        file_menu.addAction(import_action)

        # Create an "Export" QMenu instead of a QAction
        export_menu = file_menu.addMenu("Export Data")
        export_particle_data_menu = export_menu.addMenu("Particle Data")

        # Create the QActions for your sub-options
        export_particle_data_csv_action = QAction("as CSV", self)
        export_particle_data_pkl_action = QAction("as PKL", self)

        # Add the sub-option actions to the "Export" menu
        export_particle_data_menu.addAction(export_particle_data_csv_action)
        export_particle_data_menu.addAction(export_particle_data_pkl_action)

        # You can then connect your sub-actions to functions
        export_particle_data_csv_action.triggered.connect(self.export_particles_csv)
        export_particle_data_pkl_action.triggered.connect(self.export_particles_pkl)

        options_menu = menubar.addMenu("Options")
        stream_action = QAction("Stream", self)
        stream_action.triggered.connect(self.stream)
        options_menu.addAction(stream_action)

        # Left Panel
        self.main_layout.left_panel = DectectionPlottingWidget()
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
        self.main_layout.right_panel = DetectionParametersWidget(
            self.main_layout.left_panel
        )
        self.right_layout = QVBoxLayout(self.main_layout.right_panel)
        self.main_layout.addWidget(self.main_layout.right_panel)

        # Connect signals
        self.main_layout.right_panel.particlesUpdated.connect(self.on_particles_updated)
        self.main_layout.right_panel.openTrajectoryLinking.connect(
            self.open_trajectory_linking_window
        )
        self.main_layout.right_panel.parameter_changed.connect(
            self.clear_processed_data
        )
        self.main_layout.right_panel.parameter_changed.connect(
            self.frame_player.update_feature_size
        )
        self.frame_player.frames_saved.connect(
            self.main_layout.right_panel.set_total_frames
        )
        self.frame_player.errant_particles_updated.connect(
            self.errant_particle_gallery.refresh_particles
        )
        self.errant_particle_gallery.errant_particle_selected.connect(
            self.frame_player.on_errant_particle_selected
        )
        # Connect new signal for showing particle on frame
        self.errant_particle_gallery.show_particle_on_frame.connect(
            self.frame_player.jump_to_frame_and_highlight_particle
        )
        # Connect frame changes to update gallery highlighting
        self.frame_player.frame_changed.connect(
            self.errant_particle_gallery.set_current_frame
        )
        self.frame_player.import_video_requested.connect(self.import_video)

    def on_particles_updated(self, particle_data):
        if self.frame_player:
            self.frame_player.display_frame(self.frame_player.current_frame_idx)
        # Refresh errant particle gallery after particles are detected
        if self.errant_particle_gallery:
            self.errant_particle_gallery.refresh_particles()

    def load_particle_data(self):
        if not self.file_controller:
            return

        # Reload frames into the frame player
        frame_count = 0
        if self.frame_player:
            frame_count = self.frame_player.reload_from_disk()

        if self.main_layout.right_panel:
            if frame_count > 0:
                self.main_layout.right_panel.set_total_frames(frame_count)
            self.main_layout.right_panel.refresh_from_disk()
            # Reload parameters from config file
            self.main_layout.right_panel.load_params()

        if self.errant_particle_gallery:
            self.errant_particle_gallery.reset_state()

        particles_df = pd.DataFrame()
        particles_file = os.path.join(
            self.file_controller.data_folder, "all_particles.csv"
        )
        if os.path.exists(particles_file):
            try:
                particles_df = pd.read_csv(particles_file)
            except Exception as e:
                print(f"Error loading particle data: {e}")
                particles_df = pd.DataFrame()

        if not particles_df.empty and self.main_layout.left_panel:
            self.main_layout.left_panel.set_particles(particles_df)
        elif self.main_layout.left_panel:
            self.main_layout.left_panel.blank_plot()

        # Update frame/errant displays as if particles were just detected
        self.on_particles_updated(particles_df)

    def clear_processed_data(self):
        print("Particle detection parameters changed. Clearing processed data...")
        if self.file_controller:
            try:
                self.file_controller.delete_all_files_in_folder(
                    self.file_controller.annotated_frames_folder
                )
                self.errant_particle_gallery.clear_gallery()
            except Exception as e:
                print(f"Error clearing processed data: {e}")

    def import_video(self):
        if not self.file_controller:
            print("File controller not set")
            return

        videos_folder = self.file_controller.videos_folder
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video",
            videos_folder,
            "Video Files (*.avi *.mp4 *.mov *.mkv);;All Files (*)",
        )
        if not file_path:
            return

        self.file_controller.ensure_folder_exists(
            self.file_controller.original_frames_folder
        )
        self.file_controller.ensure_folder_exists(
            self.file_controller.annotated_frames_folder
        )
        try:
            self.file_controller.delete_all_files_in_folder(
                self.file_controller.original_frames_folder
            )
            self.file_controller.delete_all_files_in_folder(
                self.file_controller.annotated_frames_folder
            )
            self.main_layout.right_panel.clear_processed_frames()
        except Exception as e:
            print(f"Error cleaning up old frame folders: {e}")

        self.frame_player.save_video_frames(file_path)

    def load_existing_frames(self, num_frames):
        """Load existing frames into the widgets."""
        self.main_layout.right_panel.set_total_frames(num_frames)
        self.frame_player.load_frames(num_frames)

    def _export_data(self, source_filename: str, target_format: str):
        if not self.file_controller:
            print("File controller not set")
            return

        data_folder = self.file_controller.data_folder
        source_file_path = os.path.join(data_folder, source_filename)

        if not os.path.exists(source_file_path):
            print("Could not find selected data")
            return

        if target_format == "csv":
            file_filter = "CSV Files (*.csv);;All Files (*)"
        elif target_format == "pkl":
            file_filter = "Pickle Files (*.pkl);;All Files (*)"
        else:
            print(f"Error: Unsupported export format '{target_format}'")
            return

        default_name = f"{os.path.splitext(source_filename)[0]}_export.{target_format}"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "desc", default_name, file_filter
        )

        if not save_path:
            return

        try:
            import pandas as pd

            df = pd.read_csv(source_file_path)

            if target_format == "csv":
                df.to_csv(save_path, index=False)
            elif target_format == "pkl":
                df.to_pickle(save_path)

            print(f"Data successfully exported to: {save_path}")

        except Exception as e:
            print(f"An error occurred during export: {e}")

    def export_particles_csv(self):
        """Exports the 'all_particles.csv' file to a user-selected CSV file."""
        self._export_data(source_filename="all_particles.csv", target_format="csv")

    def export_particles_pkl(self):
        """Exports the 'all_particles.csv' data as a user-selected pickle file."""
        self._export_data(source_filename="all_particles.csv", target_format="pkl")

    def stream(self):
        return

    def open_trajectory_linking_window(self):
        """Emit signal to switch to trajectory linking window."""
        # The controller will handle the actual window switching
        pass
