"""
Trajectory Linking Window

Description: Main window for Trajectory Linkning. Imports trajectory linking widgets.
             Generated boiler plate code using Cursor.
"""

import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QHBoxLayout,
)
from .ErrantTrajectoryGalleryWidget import *
from .TrajectoryPlayerWidget import *
from .TrajectoryPlottingWidget import *
from .LinkingParametersWidget import *


class TrajectoryLinkingWindow(QMainWindow):
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
        if hasattr(self, "errant_particle_gallery"):
            self.errant_particle_gallery.set_config_manager(config_manager)

    def set_file_controller(self, file_controller):
        """Set the file controller for this window."""
        self.file_controller = file_controller
        # Pass file controller to widgets that need it
        if hasattr(self, "main_layout") and hasattr(self.main_layout, "right_panel"):
            self.main_layout.right_panel.set_file_controller(file_controller)
        if hasattr(self, "frame_player"):
            self.frame_player.set_file_controller(file_controller)
        if hasattr(self, "errant_particle_gallery"):
            self.errant_particle_gallery.set_file_controller(file_controller)
        self.load_initial_overlay()

    def load_initial_overlay(self):
        """Ensure the RB overlay preview is ready when the window opens."""
        if hasattr(self, "frame_player") and self.frame_player:
            self.frame_player.load_initial_overlay()
        if hasattr(self, "errant_particle_gallery") and self.errant_particle_gallery:
            self.errant_particle_gallery.refresh_rb_gallery()

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
        export_trajectory_data_csv_action.triggered.connect(
            self.export_trajectories_csv
        )
        export_trajectory_data_pkl_action.triggered.connect(
            self.export_trajectories_pkl
        )

        options_menu = menubar.addMenu("Options")

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
        self.main_layout.right_panel = LinkingParametersWidget(
            self.main_layout.left_panel
        )
        self.right_layout = QVBoxLayout(self.main_layout.right_panel)
        self.main_layout.addWidget(self.main_layout.right_panel)

        # Connect trajectory visualization signal - now loads frames for overlay display
        self.main_layout.right_panel.trajectoryVisualizationCreated.connect(
            self.frame_player.display_trajectory_image
        )

        # Connect back button signal to return to detection window
        self.main_layout.right_panel.goBackToDetection.connect(
            self.go_back_to_detection
        )

        # Connect RB gallery creation signal to refresh the trajectory gallery
        self.main_layout.right_panel.rbGalleryCreated.connect(
            self.errant_particle_gallery.refresh_rb_gallery
        )

        # Connect overlay change signal to filter gallery by frame pair
        self.frame_player.overlay_changed.connect(
            lambda frame_i, frame_i1: self.errant_particle_gallery.set_frame_pair_filter(
                frame_i, frame_i1
            )
        )

        # Connect threshold slider from errant_particle_gallery to frame_player
        # The connection is set up after widgets are created
        def connect_threshold_slider():
            if hasattr(self.errant_particle_gallery, "threshold_slider"):
                slider = self.errant_particle_gallery.threshold_slider
                self.frame_player.set_threshold_slider(slider)

        # Connect after a short delay to ensure widgets are fully initialized
        from PySide6.QtCore import QTimer

        QTimer.singleShot(100, connect_threshold_slider)

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

    def export_trajectories_csv(self):
        """Exports the 'trajectories.csv' file to a user-selected CSV file."""
        self._export_data(source_filename="trajectories.csv", target_format="csv")

    def export_trajectories_pkl(self):
        self._export_data(source_filename="trajectories.csv", target_format="pkl")


    def go_back_to_detection(self):
        """Emit signal to switch back to particle detection window."""
        if hasattr(self, "frame_player") and self.frame_player:
            self.frame_player.reset_state()
        if hasattr(self, "errant_particle_gallery") and self.errant_particle_gallery:
            self.errant_particle_gallery.reset_state()
        self.goBackToDetection.emit()
