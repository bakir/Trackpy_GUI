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
        if hasattr(self, "right_panel"):
            self.right_panel.set_config_manager(config_manager)
        if hasattr(self, "frame_player"):
            self.frame_player.set_config_manager(config_manager)
        if hasattr(self, "errant_particle_gallery") and hasattr(
            self.errant_particle_gallery, "set_config_manager"
        ):
            self.errant_particle_gallery.set_config_manager(config_manager)
        if hasattr(self, "left_panel"):
            self.left_panel.set_config_manager(config_manager)
        # Update metadata display
        self._update_metadata_display()

    def set_file_controller(self, file_controller):
        """Set the file controller for this window."""
        self.file_controller = file_controller
        # Pass file controller to widgets that need it
        if hasattr(self, "right_panel"):
            self.right_panel.set_file_controller(file_controller)
        if hasattr(self, "frame_player"):
            self.frame_player.set_file_controller(file_controller)
        if hasattr(self, "errant_particle_gallery") and hasattr(
            self.errant_particle_gallery, "set_file_controller"
        ):
            self.errant_particle_gallery.set_file_controller(file_controller)
        if hasattr(self, "left_panel"):
            self.left_panel.set_file_controller(file_controller)

        # Load existing particle data if available
        self.load_particle_data()

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

        import_action = QAction("Import Video", self)
        import_action.triggered.connect(self.import_video)
        file_menu.addAction(import_action)

        options_menu = menubar.addMenu("Options")

        # Left Panel
        self.left_panel = DectectionPlottingWidget()
        self.left_panel.setMinimumWidth(200)
        splitter.addWidget(self.left_panel)

        # Middle Panel
        self.middle_panel = QWidget()
        self.middle_panel.setMinimumWidth(300)
        middle_layout = QVBoxLayout(self.middle_panel)

        self.frame_player = FramePlayerWidget()
        middle_layout.addWidget(self.frame_player, 2) # Add with 2/3 stretch
        self.errant_particle_gallery = ErrantParticleGalleryWidget()
        middle_layout.addWidget(self.errant_particle_gallery, 1) # Add with 1/3 stretch

        # Set the gallery reference in the frame player
        self.frame_player.set_errant_particle_gallery(
            self.errant_particle_gallery
        )

        splitter.addWidget(self.middle_panel)

        # Right Panel - Create container widget
        right_panel_container = QWidget()
        right_panel_container.setMinimumWidth(200)
        right_panel_layout = QVBoxLayout(right_panel_container)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Detection parameters widget
        self.right_panel = DetectionParametersWidget(self.left_panel)
        right_panel_layout.addWidget(self.right_panel)
        
        # Metadata display widget
        self.metadata_widget = self._create_metadata_widget()
        right_panel_layout.addWidget(self.metadata_widget)
        
        splitter.addWidget(right_panel_container)

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

        # Connect signals
        self.right_panel.parameter_changed.connect(
            self.clear_processed_data
        )
        self.right_panel.parameter_changed.connect(
            self.frame_player.update_feature_size
        )
        self.frame_player.frames_saved.connect(
            self.right_panel.set_total_frames
        )
        self.errant_particle_gallery.update_required.connect(
            self.frame_player.handle_gallery_update
        )
        self.frame_player.import_video_requested.connect(self.import_video)
        
        # Connect filtered data updates
        self.left_panel.filtering_widget.filteredParticlesUpdated.connect(
            self.frame_player.refresh_frame
        )
        self.left_panel.filtering_widget.filteredParticlesUpdated.connect(
            self.errant_particle_gallery.regenerate_errant_particles
        )


    def load_particle_data(self):
        if not self.file_controller:
            return

        # Reload frames into the frame player
        frame_count = 0
        if self.frame_player:
            frame_count = self.frame_player.reload_from_disk()

        if self.right_panel:
            if frame_count > 0:
                self.right_panel.set_total_frames(frame_count)
            # Reload parameters from config file
            self.right_panel.load_params()

        if self.errant_particle_gallery:
            self.errant_particle_gallery.reset_state()

        self.left_panel.blank_plot()
        # self.left_panel.refresh_plots()
        
        # Only apply filters if particle data actually exists
        # Check if all_particles.csv exists and has data before applying filters
        all_particles_path = os.path.join(self.file_controller.data_folder, "all_particles.csv")
        if os.path.exists(all_particles_path):
            try:
                particle_data = pd.read_csv(all_particles_path)
                # Only apply filters if there's actual particle data
                if not particle_data.empty:
                    self.left_panel.filtering_widget.apply_filters_and_notify()
            except (pd.errors.EmptyDataError, Exception):
                # File exists but is empty or invalid, don't apply filters
                pass

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
            self.right_panel.clear_processed_frames()
        except Exception as e:
            print(f"Error cleaning up old frame folders: {e}")

        self.frame_player.save_video_frames(file_path)

    def load_existing_frames(self, num_frames):
        """Load existing frames into the widgets."""
        self.right_panel.set_total_frames(num_frames)
        self.frame_player.load_frames(num_frames)

    def _create_metadata_widget(self):
        """Create the metadata display widget."""
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel("Project Metadata")
        title_font = title_label.font()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Metadata fields
        self.movie_taker_label = QLabel()
        self.person_doing_analysis_label = QLabel()
        self.movie_taken_date_label = QLabel()
        self.movie_filename_label = QLabel()
        self.movie_filename_label.setWordWrap(True)
        
        layout.addWidget(self.movie_taker_label)
        layout.addWidget(self.person_doing_analysis_label)
        layout.addWidget(self.movie_taken_date_label)
        layout.addWidget(self.movie_filename_label)
        
        layout.addStretch()
        
        return widget

    def _update_metadata_display(self):
        """Update the metadata display with current config values."""
        if not self.config_manager:
            return
        
        metadata = self.config_manager.get_metadata()
        
        movie_taker = metadata.get("movie_taker", "") or "-"
        person_doing_analysis = metadata.get("person_doing_analysis", "") or "-"
        movie_taken_date = metadata.get("movie_taken_date", "") or "-"
        movie_filename = metadata.get("movie_filename", "") or "-"
        
        self.movie_taker_label.setText(f"Movie Taker: {movie_taker}")
        self.person_doing_analysis_label.setText(f"Person Doing Analysis: {person_doing_analysis}")
        self.movie_taken_date_label.setText(f"Movie Taken Date: {movie_taken_date}")
        self.movie_filename_label.setText(f"Movie Filename: {movie_filename}")
