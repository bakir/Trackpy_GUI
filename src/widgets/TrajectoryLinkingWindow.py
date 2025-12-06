"""
Trajectory Linking Window

Description: Main window for Trajectory Linkning. Imports trajectory linking widgets.
             Generated boiler plate code using Cursor.
"""
import pandas as pd
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
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
        if hasattr(self, "right_panel"):
            self.right_panel.set_config_manager(config_manager)
        if hasattr(self, "frame_player"):
            self.frame_player.set_config_manager(config_manager)
        if hasattr(self, "errant_particle_gallery"):
            self.errant_particle_gallery.set_config_manager(config_manager)

    def set_file_controller(self, file_controller):
        """Set the file controller for this window."""
        self.file_controller = file_controller
        # Pass file controller to widgets that need it
        if hasattr(self, "right_panel"):
            self.right_panel.set_file_controller(file_controller)
        if hasattr(self, "frame_player"):
            self.frame_player.set_file_controller(file_controller)
        if hasattr(self, "errant_particle_gallery"):
            self.errant_particle_gallery.set_file_controller(file_controller)
        self.load_initial_overlay()

    def load_initial_overlay(self):
        """Ensure the memory links are loaded when the window opens."""
        if hasattr(self, "frame_player") and self.frame_player:
            self.frame_player.refresh_links()
        if (
            hasattr(self, "errant_particle_gallery")
            and self.errant_particle_gallery
        ):
            self.errant_particle_gallery.refresh_rb_gallery()
        if hasattr(self, "left_panel"):
            self.left_panel.set_config_manager(self.config_manager)
            self.left_panel.set_file_controller(self.file_controller)

    def setup_ui(self):
        # Main Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Use a QSplitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Main layout will now be the layout of the central widget
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.addWidget(splitter)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        export_action = QAction("Export...", self)
        export_action.triggered.connect(self.export_all_data)
        file_menu.addAction(export_action)

        options_menu = menubar.addMenu("Options")

        # Left Panel
        self.left_panel = TrajectoryPlottingWidget()
        self.left_panel.setMinimumWidth(200)
        splitter.addWidget(self.left_panel)

        # Middle Panel
        self.middle_panel = QWidget()
        self.middle_panel.setMinimumWidth(300)
        self.middle_layout = QVBoxLayout(self.middle_panel)

        self.frame_player = TrajectoryPlayerWidget()
        self.middle_layout.addWidget(self.frame_player, 1) # Add with 1/2 stretch
        self.errant_particle_gallery = ErrantTrajectoryGalleryWidget()
        self.middle_layout.addWidget(self.errant_particle_gallery, 1) # Add with 1/2 stretch

        splitter.addWidget(self.middle_panel)

        # Right Panel
        self.right_panel = LinkingParametersWidget(self.left_panel)
        self.right_panel.setMinimumWidth(200)
        self.right_layout = QVBoxLayout(self.right_panel)
        splitter.addWidget(self.right_panel)

        # Set initial sizes for smooth resizing (proportional: 1:2:1)
        # This prevents the splitter from jumping when clicked
        splitter.setSizes([300, 600, 300])
        
        # Set stretch factors for the splitter
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        # Make splitter handle wider and black for easy clicking
        splitter.setHandleWidth(20)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: black;
                border: 1px solid black;
            }
            QSplitter::handle:hover {
                background-color: #333333;
            }
        """)

        # Connect trajectory linking signal to refresh memory links when trajectories are found
        self.right_panel.trajectoriesLinked.connect(
            self.frame_player.refresh_links
        )

        # Connect filtered data updates to refresh relevant widgets
        self.left_panel.filtering_widget.filteredParticlesUpdated.connect(
            self.frame_player.refresh_links
        )
        self.left_panel.filtering_widget.filteredParticlesUpdated.connect(
            self.errant_particle_gallery.refresh_rb_gallery
        )

        # Connect back button signal to return to detection window
        self.right_panel.goBackToDetection.connect(
            self.go_back_to_detection
        )

        # Connect RB gallery creation signal to refresh the trajectory gallery
        self.right_panel.rbGalleryCreated.connect(
            self.errant_particle_gallery.refresh_rb_gallery
        )

        # Connect export and close signal
        self.right_panel.export_and_close.connect(
            self.on_export_and_close
        )

    def export_all_data(self):
        """
        Exports all particle and trajectory data to a user-selected directory.
        Returns True if the export was initiated, False if cancelled.
        """
        if not self.file_controller:
            print("File controller not set")
            return False

        directory = QFileDialog.getExistingDirectory(
            self, "Select Export Directory"
        )
        if not directory:
            return False

        data_sources = {
            "all_particles": "all_particles.csv",
            "trajectories": "trajectories.csv",
        }

        for name, filename in data_sources.items():
            source_path = os.path.join(
                self.file_controller.data_folder, filename
            )
            if not os.path.exists(source_path):
                print(f"Source file not found, skipping: {filename}")
                continue

            try:
                df = pd.read_csv(source_path)

                # Export to CSV
                csv_path = os.path.join(directory, f"{name}.csv")
                df.to_csv(csv_path, index=False)
                print(f"Successfully exported to: {csv_path}")

                # Export to PKL
                pkl_path = os.path.join(directory, f"{name}.pkl")
                df.to_pickle(pkl_path)
                print(f"Successfully exported to: {pkl_path}")

            except Exception as e:
                print(f"An error occurred during export of {name}: {e}")
        return True

    def on_export_and_close(self):
        """Export all data and then close the application."""
        if self.export_all_data():
            QApplication.instance().quit()

    def go_back_to_detection(self):
        """Emit signal to switch back to particle detection window."""
        if hasattr(self, "frame_player") and self.frame_player:
            self.frame_player.reset_state()
        if (
            hasattr(self, "errant_particle_gallery")
            and self.errant_particle_gallery
        ):
            self.errant_particle_gallery.reset_state()
