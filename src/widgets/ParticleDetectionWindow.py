"""
Particle Detection Window

Description: Main window for Particle detection. Imports particle detection widgets.
             Generated boiler plate code using Cursor.
"""

import os
import pandas as pd

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
from PySide6 import QtWidgets

from .ErrantParticleGalleryWidget import *
from .FramePlayerWidget import *
from .DetectionPlottingWidget import *
from .DetectionParametersWidget import *


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
        if hasattr(self, "main_layout") and hasattr(
            self.main_layout, "right_panel"
        ):
            self.main_layout.right_panel.set_config_manager(config_manager)
        if hasattr(self, "frame_player"):
            self.frame_player.set_config_manager(config_manager)
        if hasattr(self, "errant_particle_gallery") and hasattr(
            self.errant_particle_gallery, "set_config_manager"
        ):
            self.errant_particle_gallery.set_config_manager(config_manager)
        if hasattr(self, "main_layout") and hasattr(
            self.main_layout, "left_panel"
        ):
            self.main_layout.left_panel.set_config_manager(config_manager)

    def set_file_controller(self, file_controller):
        """Set the file controller for this window."""
        self.file_controller = file_controller
        # Pass file controller to widgets that need it
        if hasattr(self, "main_layout") and hasattr(
            self.main_layout, "right_panel"
        ):
            self.main_layout.right_panel.set_file_controller(file_controller)
        if hasattr(self, "frame_player"):
            self.frame_player.set_file_controller(file_controller)
        if hasattr(self, "errant_particle_gallery") and hasattr(
            self.errant_particle_gallery, "set_file_controller"
        ):
            self.errant_particle_gallery.set_file_controller(file_controller)
        if hasattr(self, "main_layout") and hasattr(
            self.main_layout, "left_panel"
        ):
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

        options_menu = menubar.addMenu("Options")

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

        # Set the gallery reference in the frame player
        self.frame_player.set_errant_particle_gallery(
            self.errant_particle_gallery
        )

        self.main_layout.addWidget(self.main_layout.middle_panel)

        # Right Panel
        self.main_layout.right_panel = DetectionParametersWidget(
            self.main_layout.left_panel
        )
        self.right_layout = QVBoxLayout(self.main_layout.right_panel)
        self.main_layout.addWidget(self.main_layout.right_panel)

        # Connect signals
        self.main_layout.right_panel.particlesUpdated.connect(
            self.on_particles_updated
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
        # Connect the gallery's need for an update to the player's handler
        self.errant_particle_gallery.update_required.connect(
            self.frame_player.handle_gallery_update
        )
        self.frame_player.import_video_requested.connect(self.import_video)

    def on_particles_updated(self, particle_data):
        if self.frame_player:
            self.frame_player.display_frame(
                self.frame_player.current_frame_idx
            )
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
        print(
            "Particle detection parameters changed. Clearing processed data..."
        )
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
