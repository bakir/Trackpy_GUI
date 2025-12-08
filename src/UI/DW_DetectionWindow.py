"""
Particle Detection Window

Description: Main window for Particle detection. Imports particle detection widgets.
             Generated boiler plate code using Cursor.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
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
    QGroupBox,
    QPushButton,
    QApplication,
)
from PySide6 import QtWidgets

from .DW_ErrantParticleWidget import *
from .DW_FrameGalleryWidget import *
from .DW_PlottingWidget import *
from .DW_ParametersWidget import *


class DWDetectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = None
        self.file_controller = None
        self.main_controller = None  # Reference to main controller for undo
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
        # Update metadata and parameters displays
        if hasattr(self, "_update_metadata_display"):
            self._update_metadata_display()
        if hasattr(self, "_update_parameters_info"):
            self._update_parameters_info()

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
        # File menu removed - video import is handled through frame player
        options_menu = menubar.addMenu("Options")

        # Left Panel - make it much wider to show bigger plots
        self.left_panel = DWPlottingWidget()
        self.left_panel.setMinimumWidth(400)
        splitter.addWidget(self.left_panel)

        # Middle Panel
        self.middle_panel = QWidget()
        self.middle_panel.setMinimumWidth(300)
        middle_layout = QVBoxLayout(self.middle_panel)

        self.frame_player = DWFrameGalleryWidget()
        middle_layout.addWidget(self.frame_player, 2)  # Add with 2/3 stretch
        self.errant_particle_gallery = DWErrantParticleWidget()
        middle_layout.addWidget(self.errant_particle_gallery, 1)  # Add with 1/3 stretch

        # Set the gallery reference in the frame player
        self.frame_player.set_errant_particle_gallery(self.errant_particle_gallery)

        splitter.addWidget(self.middle_panel)

        # Right Panel - Create container widget
        right_panel_container = QWidget()
        right_panel_container.setMinimumWidth(200)
        right_panel_layout = QVBoxLayout(right_panel_container)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)

        # Detection parameters widget
        self.right_panel = DWParametersWidget(self.left_panel)
        right_panel_layout.addWidget(self.right_panel)

        # Add Undo button to the same row as "All frames" and "Find Particles"
        self.undo_button = QPushButton("Undo")
        self.undo_button.setToolTip("Restore previous particle analysis state")
        self.undo_button.clicked.connect(self.undo_last_state)
        # Add to the buttons row layout in the parameters widget
        if hasattr(self.right_panel, "buttons_row_layout"):
            self.right_panel.buttons_row_layout.addWidget(self.undo_button)

        # Parameters info box (shows parameters used for current results)
        self.parameters_info_widget = self._create_parameters_info_widget()
        right_panel_layout.addWidget(self.parameters_info_widget)

        # Metadata display widget
        self.metadata_widget = self._create_metadata_widget()
        right_panel_layout.addWidget(self.metadata_widget)

        # Next button at bottom corner
        right_panel_layout.addStretch()
        right_panel_layout.addWidget(self.right_panel.next_button, alignment=Qt.AlignRight)

        splitter.addWidget(right_panel_container)

        # Set initial sizes for smooth resizing - give left panel more space for plots
        # This prevents the splitter from jumping when clicked
        splitter.setSizes([500, 600, 300])

        # Set stretch factors for the splitter - give left panel more weight
        splitter.setStretchFactor(0, 2)  # Left panel (plots) gets more space
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        # Make splitter handle thinner and elegant black line for easy clicking
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(
            """
            QSplitter::handle {
                background-color: black;
                border: none;
            }
            QSplitter::handle:hover {
                background-color: #444444;
            }
        """
        )

        # Connect signals
        # Only update feature size when parameters change, don't clear gallery
        self.right_panel.parameter_changed.connect(self.frame_player.update_feature_size)
        # Clear gallery only when Find Particles is clicked
        self.right_panel.particles_found.connect(self.clear_processed_data)
        # Update parameters info when particles are found
        self.right_panel.particles_found.connect(self._update_parameters_info)
        self.frame_player.frames_saved.connect(self.right_panel.set_total_frames)
        self.errant_particle_gallery.update_required.connect(
            self.frame_player.handle_gallery_update
        )

        # Connect filtered data updates
        self.left_panel.filtering_widget.filteredParticlesUpdated.connect(
            self.frame_player.refresh_frame
        )
        self.left_panel.filtering_widget.filteredParticlesUpdated.connect(
            self.errant_particle_gallery.regenerate_errant_particles
        )

        # Update undo button state
        self.update_undo_button_state()

    def refresh_detection_ui(
        self, particles_df, config_manager=None, frame_range=None, block_signals=False
    ):
        """
        Centralized function to refresh all UI elements after loading new particle data.

        This is used by:
        - Undo functionality (load_spreadsheet_and_config)
        - Find Particles (on_find_finished)
        - Filter application (when filters change)

        Parameters
        ----------
        particles_df : pd.DataFrame
            The particle data to display
        config_manager : ConfigManager, optional
            Config manager to use. If None, uses existing config_manager.
        frame_range : dict, optional
            Dictionary with 'start_frame', 'end_frame', 'step_frame' keys
        block_signals : bool, default False
            If True, blocks parameter input widget signals to prevent saving config
        """
        # Block signals if requested (for undo scenarios)
        if block_signals and hasattr(self, "right_panel"):
            right_panel = self.right_panel
            right_panel.feature_size_input.blockSignals(True)
            right_panel.min_mass_input.blockSignals(True)
            right_panel.threshold_input.blockSignals(True)
            right_panel.invert_input.blockSignals(True)

        try:
            # Update config manager if provided
            if config_manager:
                self.set_config_manager(config_manager)
                QApplication.processEvents()

            # Update frame range inputs if provided
            if frame_range and hasattr(self, "right_panel"):
                self.right_panel.start_frame_input.setValue(frame_range["start_frame"])
                self.right_panel.end_frame_input.setValue(frame_range["end_frame"])
                self.right_panel.step_frame_input.setValue(frame_range["step_frame"])

            # 1. Set particles on the graphing panel (this loads the data)
            if hasattr(self, "right_panel") and hasattr(self.right_panel, "graphing_panel"):
                self.right_panel.graphing_panel.set_particles(particles_df)

            # 2. Emit allParticlesUpdated signal
            if hasattr(self, "right_panel") and hasattr(self.right_panel, "allParticlesUpdated"):
                self.right_panel.allParticlesUpdated.emit()

            # 3. Update frame info
            if hasattr(self, "right_panel") and hasattr(self.right_panel, "_update_frame_info"):
                self.right_panel._update_frame_info()

            # 4. Apply filters and notify - this triggers filteredParticlesUpdated signal
            # which is connected to regenerate_errant_particles() in DW_DetectionWindow
            if hasattr(self, "right_panel") and hasattr(self.right_panel, "graphing_panel"):
                if hasattr(self.right_panel.graphing_panel, "filtering_widget"):
                    self.right_panel.graphing_panel.filtering_widget.apply_filters_and_notify()

            # 5. Update parameters info display
            self._update_parameters_info()

            # 6. Update metadata display LAST, after everything else is done
            self._update_metadata_display()

        finally:
            # Re-enable signals if they were blocked
            if block_signals and hasattr(self, "right_panel"):
                right_panel = self.right_panel
                right_panel.feature_size_input.blockSignals(False)
                right_panel.min_mass_input.blockSignals(False)
                right_panel.threshold_input.blockSignals(False)
                right_panel.invert_input.blockSignals(False)

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

        # Only apply filters if particle data actually exists
        # Use FileController to load particles data
        try:
            particle_data = self.file_controller.load_particles_data("all_particles.csv")
            # Only apply filters if there's actual particle data
            if not particle_data.empty:
                # Use centralized refresh function
                self.refresh_detection_ui(particle_data)
        except Exception:
            # File exists but is empty or invalid, don't apply filters
            pass

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

    def load_existing_frames(self, num_frames):
        """Load existing frames into the widgets."""
        self.right_panel.set_total_frames(num_frames)
        self.frame_player.load_frames(num_frames)

    def _create_parameters_info_widget(self):
        """Create the parameters info display widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Title
        title_label = QLabel("Parameters")
        title_font = title_label.font()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Parameters display in a group box (no title to avoid redundancy)
        parameters_group = QGroupBox()
        parameters_layout = QVBoxLayout(parameters_group)

        self.parameters_info_label = QLabel("No particles detected yet")
        self.parameters_info_label.setWordWrap(True)
        self.parameters_info_label.setStyleSheet(
            """
            QLabel {
                background-color: #f0f0f0;
                padding: 8px;
                border-radius: 4px;
            }
        """
        )
        parameters_layout.addWidget(self.parameters_info_label)

        layout.addWidget(parameters_group)

        return widget

    def _create_metadata_widget(self):
        """Create the metadata display widget."""
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

    def _update_parameters_info(self):
        """Update the parameters info display with current detection parameters."""
        if not self.config_manager:
            return

        params = self.config_manager.get_detection_params()

        feature_size = params.get("feature_size", "-")
        min_mass = params.get("min_mass", "-")
        threshold = params.get("threshold", "-")
        invert = "Yes" if params.get("invert", False) else "No"

        info_text = (
            f"Feature size: {feature_size}\n"
            f"Min mass: {min_mass}\n"
            f"Threshold: {threshold}\n"
            f"Invert: {invert}"
        )

        self.parameters_info_label.setText(info_text)

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

    def update_undo_button_state(self):
        """Update the undo button enabled state based on whether save exists."""
        if hasattr(self, "undo_button"):
            # Use stored main controller reference
            if self.main_controller and hasattr(self.main_controller, "has_undo_state"):
                self.undo_button.setEnabled(self.main_controller.has_undo_state())
            else:
                self.undo_button.setEnabled(False)

    def undo_last_state(self):
        """Restore the previous state using undo functionality."""
        if self.main_controller and hasattr(self.main_controller, "undo_last_state"):
            if self.main_controller.undo_last_state():
                # Update undo button state after undo
                self.update_undo_button_state()
