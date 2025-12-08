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
from .LW_ErrantDistanceLinksWidget import *
from .LW_ErrantMemoryLinksWidget import *
from .LW_PlottingWidget import *
from .LW_ParametersWidget import *


class LWLinkingWindow(QMainWindow):
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
            self.errant_particle_gallery.refresh_errant_distance_links()
        if hasattr(self, "left_panel"):
            self.left_panel.set_config_manager(self.config_manager)
            self.left_panel.set_file_controller(self.file_controller)
        # Update parameters info and frame range if trajectories exist
        self._update_parameters_info()
        self._update_frame_range_info()

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

        # Left Panel - make it much wider to show bigger plots
        self.left_panel = LWPlottingWidget()
        self.left_panel.setMinimumWidth(400)
        splitter.addWidget(self.left_panel)

        # Middle Panel
        self.middle_panel = QWidget()
        self.middle_panel.setMinimumWidth(300)
        self.middle_layout = QVBoxLayout(self.middle_panel)

        self.frame_player = LWErrantMemoryLinksWidget()
        self.middle_layout.addWidget(self.frame_player, 1) # Add with 1/2 stretch
        self.errant_particle_gallery = LWErrantDistanceLinksWidget()
        self.middle_layout.addWidget(self.errant_particle_gallery, 1) # Add with 1/2 stretch

        splitter.addWidget(self.middle_panel)

        # Right Panel - Create container widget
        right_panel_container = QWidget()
        right_panel_container.setMinimumWidth(200)
        right_panel_layout = QVBoxLayout(right_panel_container)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Linking parameters widget
        self.right_panel = LWParametersWidget(self.left_panel)
        right_panel_layout.addWidget(self.right_panel)
        
        # Frame range info widget (shows frames links were found between)
        self.frame_range_widget = self._create_frame_range_widget()
        right_panel_layout.addWidget(self.frame_range_widget)
        
        # Parameters info box (shows parameters used for current results)
        self.parameters_info_widget = self._create_parameters_info_widget()
        right_panel_layout.addWidget(self.parameters_info_widget)
        
        # Metadata display widget
        self.metadata_widget = self._create_metadata_widget()
        right_panel_layout.addWidget(self.metadata_widget)
        
        # Add stretch to push buttons to bottom
        right_panel_layout.addStretch()
        
        # Extract buttons from parameters widget and add them at the bottom
        self._move_buttons_to_bottom(right_panel_layout)
        
        splitter.addWidget(right_panel_container)

        # Set initial sizes for smooth resizing - give left panel more space for plots
        # This prevents the splitter from jumping when clicked
        splitter.setSizes([500, 600, 300])
        
        # Set stretch factors for the splitter - give left panel more weight
        splitter.setStretchFactor(0, 2)  # Left panel (plots) gets more space
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        # Make splitter handle thinner and elegant black line for easy clicking
        splitter.setHandleWidth(8)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: black;
                border: none;
            }
            QSplitter::handle:hover {
                background-color: #444444;
            }
        """)

        # Connect trajectory linking signal to refresh memory links when trajectories are found
        self.right_panel.trajectoriesLinked.connect(
            self.frame_player.refresh_links
        )
        # Update parameters info and frame range when trajectories are linked
        self.right_panel.trajectoriesLinked.connect(
            self._update_parameters_info
        )
        self.right_panel.trajectoriesLinked.connect(
            self._update_frame_range_info
        )

        # Connect filtered data updates to refresh relevant widgets
        self.left_panel.filteredTrajectoriesUpdated.connect(
            self.frame_player.refresh_links
        )
        self.left_panel.filteredTrajectoriesUpdated.connect(
            self.errant_particle_gallery.refresh_errant_distance_links
        )

        # Connect back button signal to return to detection window
        self.right_panel.goBackToDetection.connect(
            self.go_back_to_detection
        )

        # Connect RB gallery creation signal to refresh the trajectory gallery
        self.right_panel.errantDistanceLinksGalleryCreated.connect(
            self.errant_particle_gallery.refresh_errant_distance_links
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

    def _create_frame_range_widget(self):
        """Create the frame range info display widget."""
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Frame range display (initially empty, will show when trajectories are found)
        self.frame_range_label = QLabel("")
        self.frame_range_label.setWordWrap(True)
        self.frame_range_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.frame_range_label)
        
        return widget

    def _create_parameters_info_widget(self):
        """Create the parameters info display widget."""
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel("Linking Parameters Used")
        title_font = title_label.font()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Parameters display
        self.parameters_info_label = QLabel("No trajectories linked yet")
        self.parameters_info_label.setWordWrap(True)
        self.parameters_info_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.parameters_info_label)
        
        return widget

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

    def _update_parameters_info(self):
        """Update the parameters info display with current linking parameters and detection parameters."""
        if not self.config_manager or not self.file_controller:
            return
        
        linking_params = self.config_manager.get_linking_params()
        detection_params = self.config_manager.get_detection_params()
        
        # Linking parameters
        search_range = linking_params.get("search_range", "-")
        memory = linking_params.get("memory", "-")
        min_trajectory_length = linking_params.get("min_trajectory_length", "-")
        drift = "Yes" if linking_params.get("drift", False) else "No"
        
        # Detection parameters
        feature_size = detection_params.get("feature_size", "-")
        min_mass = detection_params.get("min_mass", "-")
        threshold = detection_params.get("threshold", "-")
        invert = "Yes" if detection_params.get("invert", False) else "No"
        
        info_text = (
            f"Linking Parameters:\n"
            f"Search range: {search_range}\n"
            f"Memory: {memory}\n"
            f"Min trajectory length: {min_trajectory_length}\n"
            f"Subtract drift: {drift}\n\n"
            f"Detection Parameters:\n"
            f"Feature size: {feature_size}\n"
            f"Min mass: {min_mass}\n"
            f"Threshold: {threshold}\n"
            f"Invert: {invert}"
        )
        
        self.parameters_info_label.setText(info_text)

    def _update_frame_range_info(self):
        """Update the frame range info display with comprehensive trajectory information."""
        if not self.file_controller:
            self.frame_range_label.setText("")
            return
        
        # Only show frame range if trajectories exist
        trajectories_file = os.path.join(self.file_controller.data_folder, "trajectories.csv")
        
        if not os.path.exists(trajectories_file):
            self.frame_range_label.setText("")
            return
        
        try:
            df = pd.read_csv(trajectories_file)
            if df is not None and not df.empty and "frame" in df.columns:
                # Calculate statistics
                frames = sorted(df["frame"].unique())
                frames_1indexed = [int(f) + 1 for f in frames]  # Convert to 1-indexed
                total_frames_used = len(frames_1indexed)
                min_frame = frames_1indexed[0]
                max_frame = frames_1indexed[-1]
                total_trajectories = df["particle"].nunique() if "particle" in df.columns else 0
                total_links = len(df)
                
                # Format frame range
                if len(frames_1indexed) == 1:
                    frame_range_text = f"Frame {min_frame}"
                elif max_frame - min_frame == len(frames_1indexed) - 1:
                    # Consecutive frames
                    frame_range_text = f"Frames {min_frame}-{max_frame}"
                else:
                    # Non-consecutive frames
                    frame_range_text = f"Frames {min_frame}-{max_frame} (non-consecutive)"
                
                # Create comprehensive info text
                info_text = (
                    f"Frames used: {total_frames_used} | "
                    f"Range: {frame_range_text} | "
                    f"Trajectories: {total_trajectories} | "
                    f"Total links: {total_links}"
                )
                self.frame_range_label.setText(info_text)
            else:
                self.frame_range_label.setText("")
        except Exception as e:
            print(f"Error reading trajectories for frame range: {e}")
            self.frame_range_label.setText("")

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

    def _move_buttons_to_bottom(self, layout):
        """Extract buttons from parameters widget and add them to the bottom of the layout."""
        # Get buttons from the parameters widget
        find_trajectories_button = self.right_panel.find_trajectories_button
        back_button = self.right_panel.back_button
        export_close_button = self.right_panel.export_close_button
        
        # Create a container widget for buttons at the bottom
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(10, 10, 10, 10)
        buttons_layout.setSpacing(5)
        
        # Add buttons to the new layout
        buttons_layout.addWidget(find_trajectories_button, alignment=Qt.AlignRight)
        buttons_layout.addWidget(back_button, alignment=Qt.AlignRight)
        buttons_layout.addWidget(export_close_button, alignment=Qt.AlignRight)
        
        # Add buttons container to the main layout
        layout.addWidget(buttons_container)
