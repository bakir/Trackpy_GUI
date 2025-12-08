"""
Linking Parameters Widget

Description: GUI widget for configuring trajectory linking parameters.
             Boiler plate code generated with Cursor.
             This widget provides user interface controls for adjusting trackpy linking
             parameters and managing the trajectory linking and visualization workflow.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QProgressBar,
    QApplication,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal, QTimer
import os
import traceback
import trackpy as tp
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import cv2
from ..utils import ParticleProcessing
from ..utils.UIUtils import create_label_with_info


class LWParametersWidget(QWidget):
    trajectoriesLinked = Signal()
    trajectoryVisualizationCreated = Signal(str)  # Emits image path
    errantDistanceLinksGalleryCreated = (
        Signal()
    )  # Signal that errant distance links gallery was created
    goBackToDetection = Signal()  # Signal to go back to detection window
    export_and_close = Signal()

    def __init__(self, trajectory_plotting, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None
        self.trajectory_plotting = trajectory_plotting

        # Store detected particles and linked trajectories
        self.detected_particles = None
        self.linked_trajectories = None

        self.layout = QVBoxLayout(self)

        self.form = QFormLayout()

        # Inputs for trajectory linking parameters
        self.search_range_input = QSpinBox()
        self.search_range_input.setRange(1, 1000)
        self.search_range_input.setSingleStep(1)
        self.search_range_input.setToolTip(
            "Maximum distance a particle can move between frames (pixels)."
        )

        self.memory_input = QSpinBox()
        self.memory_input.setRange(0, 100)
        self.memory_input.setSingleStep(1)
        self.memory_input.setToolTip(
            "Number of frames a particle can disappear and still be linked."
        )

        self.min_trajectory_length_input = QSpinBox()
        self.min_trajectory_length_input.setRange(1, 1000)
        self.min_trajectory_length_input.setSingleStep(1)
        self.min_trajectory_length_input.setToolTip(
            "Minimum number of frames for a valid trajectory."
        )

        self.sub_drift = QCheckBox()
        self.sub_drift.setToolTip("Subtract drift from trajectories to correct for overall motion.")

        self.form.addRow(
            create_label_with_info(
                "Search range", "Maximum distance a particle can move between frames (pixels)."
            ),
            self.search_range_input,
        )
        self.form.addRow(
            create_label_with_info(
                "Memory", "Number of frames a particle can disappear and still be linked."
            ),
            self.memory_input,
        )
        self.form.addRow(
            create_label_with_info(
                "Min trajectory length", "Minimum number of frames for a valid trajectory."
            ),
            self.min_trajectory_length_input,
        )
        self.form.addRow(
            create_label_with_info(
                "Subtract Drift", "Subtract drift from trajectories to correct for overall motion."
            ),
            self.sub_drift,
        )

        self.layout.addLayout(self.form)

        # Progress indicator
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setWordWrap(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress bar
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.layout.addWidget(self.progress_label)
        self.layout.addWidget(self.progress_bar)

        # Buttons
        self.find_trajectories_button = QPushButton("Find Trajectories")
        self.find_trajectories_button.clicked.connect(self.find_trajectories)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)

        self.export_close_button = QPushButton("Export & Close")
        self.export_close_button.clicked.connect(self.export_and_close.emit)

        # Buttons layout will be moved to parent window, so don't add it to main layout
        # The buttons will be accessed from LW_LinkingWindow

        # Load existing values
        self.load_params()

        # Save on Enter / editing finished
        self.search_range_input.editingFinished.connect(self.save_params)
        self.memory_input.editingFinished.connect(self.save_params)
        self.min_trajectory_length_input.editingFinished.connect(self.save_params)
        self.sub_drift.stateChanged.connect(self.save_params)
        # Also catch Return in the embedded line edits
        self.search_range_input.lineEdit().returnPressed.connect(self.save_params)
        self.memory_input.lineEdit().returnPressed.connect(self.save_params)
        self.min_trajectory_length_input.lineEdit().returnPressed.connect(self.save_params)

    def set_config_manager(self, config_manager):
        """Set the config manager for this widget."""
        self.config_manager = config_manager
        # Reload parameters from config when config_manager is set
        self.load_params()

    def set_file_controller(self, file_controller):
        """Set the file controller for this widget."""
        self.file_controller = file_controller

    def load_params(self):
        if not self.config_manager:
            return
        params = self.config_manager.get_linking_params()
        self.search_range_input.setValue(int(params.get("search_range", 10)))
        self.memory_input.setValue(int(params.get("memory", 10)))
        self.min_trajectory_length_input.setValue(int(params.get("min_trajectory_length", 10)))
        self.sub_drift.setChecked(bool(params.get("drift", False)))

    def save_params(self):
        if not self.config_manager:
            return
        params = {
            "search_range": int(self.search_range_input.value()),
            "memory": int(self.memory_input.value()),
            "min_trajectory_length": int(self.min_trajectory_length_input.value()),
            "drift": bool(self.sub_drift.isChecked()),
        }
        self.config_manager.save_linking_params(params)

    def calc_drift(self, particle_data):
        try:
            scaling = self.config_manager.get_detection_params().get("scaling", 1.0)
            particle_data = particle_data.copy()
            drift = tp.compute_drift(particle_data, smoothing=15) * scaling

            particle_data = tp.subtract_drift(particle_data, drift)
            particle_data = particle_data.reset_index(drop=True)
            return particle_data
        except Exception as e:
            print(f"Error linking trajectories: {e}")
            self.linked_trajectories = None

    def find_trajectories(self):
        """Load detected particles and link them into trajectories."""
        self.save_params()
        if not self.config_manager or not self.file_controller:
            return

        linking_params = self.config_manager.get_linking_params()
        data_folder = self.file_controller.data_folder

        # Use FileController to get file paths
        all_particles_file = self.file_controller.get_data_file_path("all_particles.csv")
        filtered_particles_file = self.file_controller.get_data_file_path("filtered_particles.csv")

        # Check if filtered particles file exists using FileController
        filtered_particles_df = self.file_controller.load_particles_data("filtered_particles.csv")
        if filtered_particles_df.empty:
            print(f"Filtered particles file not found: {filtered_particles_file}")
            print("Please run 'Find Particles' and 'Apply Filters' first.")
            return

        # Show progress indicator and disable button
        self.find_trajectories_button.setEnabled(False)
        self.progress_label.setText("Working... Linking trajectories. This may take a moment.")
        self.progress_label.setVisible(True)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()  # Update UI immediately

        try:
            search_range = int(linking_params.get("search_range", 10))
            memory = int(linking_params.get("memory", 10))
            min_trajectory_length = int(linking_params.get("min_trajectory_length", 10))

            # --- Process ALL_PARTICLES.CSV for unfiltered trajectory visualization ---
            trajectories_all = None
            # Use FileController to load all particles data
            all_particles_df = self.file_controller.load_particles_data("all_particles.csv")
            if not all_particles_df.empty:
                print("Linking ALL particles for unfiltered visualization...")
                self.progress_label.setText("Working... Linking all particles...")
                QApplication.processEvents()
                trajectories_all = tp.link_df(
                    all_particles_df, search_range=search_range, memory=memory
                )

                self.progress_label.setText("Working... Filtering trajectories...")
                QApplication.processEvents()
                trajectories_all = tp.filter_stubs(trajectories_all, min_trajectory_length)
                if self.sub_drift.isChecked():
                    trajectories_all = self.calc_drift(trajectories_all)
                print(
                    f"Created {trajectories_all['particle'].nunique()} unfiltered trajectories for visualization"
                )
            else:
                print("No data in all_particles.csv for unfiltered trajectory generation.")

            # --- Process FILTERED_PARTICLES.CSV for filtered trajectories ---
            print("Loading FILTERED particles for trajectory linking...")
            self.progress_label.setText("Working... Loading filtered particles...")
            QApplication.processEvents()
            # Use FileController to load filtered particles (already loaded above, but reload for clarity)
            filtered_particles_df = self.file_controller.load_particles_data(
                "filtered_particles.csv"
            )
            print(f"Loaded {len(filtered_particles_df)} filtered particles.")

            print(f"Linking filtered particles with search_range={search_range}, memory={memory}")
            self.progress_label.setText("Working... Linking filtered particles...")
            QApplication.processEvents()
            trajectories_filtered = tp.link_df(
                filtered_particles_df, search_range=search_range, memory=memory
            )
            print(f"Created {trajectories_filtered['particle'].nunique()} filtered trajectories")

            print(f"Filtering filtered trajectories shorter than {min_trajectory_length} frames...")
            self.progress_label.setText("Working... Filtering trajectories...")
            QApplication.processEvents()
            trajectories_filtered = tp.filter_stubs(trajectories_filtered, min_trajectory_length)
            print(
                f"After filtering: {trajectories_filtered['particle'].nunique()} filtered trajectories"
            )

            if self.sub_drift.isChecked():
                trajectories_filtered = self.calc_drift(trajectories_filtered)

            # Store the filtered linked trajectories
            self.linked_trajectories = trajectories_filtered

            # Save filtered trajectories.csv
            trajectories_file = self.file_controller.get_data_file_path("trajectories.csv")
            self.file_controller.save_trajectories_data(trajectories_filtered)
            print(f"Saved FILTERED trajectories to: {trajectories_file}")

            # Create trajectory visualization using unfiltered trajectories
            if trajectories_all is not None:
                self.progress_label.setText("Working... Creating trajectory visualization...")
                QApplication.processEvents()
                self.create_trajectory_visualization(
                    trajectories_all, data_folder, "trajectory_visualization.png"
                )

            self.progress_label.setText("Working... Creating RB gallery...")
            QApplication.processEvents()
            self.create_errant_distance_links_gallery(trajectories_file, data_folder)

            self.progress_label.setText("Working... Finding high memory links...")
            QApplication.processEvents()
            ParticleProcessing.find_and_save_high_memory_links(
                trajectories_file, memory, max_links=5
            )

            # Emit signal - this will trigger centralized refresh_linking_ui() function
            # which will update plots, info displays, and refresh all UI elements
            self.trajectoriesLinked.emit()
            self.errantDistanceLinksGalleryCreated.emit()

            # Hide progress indicator and re-enable button
            self.progress_label.setText("Trajectory linking completed!")
            QApplication.processEvents()
            self.progress_bar.setVisible(False)
            self.find_trajectories_button.setEnabled(True)
            # Clear the success message after a moment
            QTimer.singleShot(2000, lambda: self.progress_label.setVisible(False))

        except Exception as e:
            print(f"Error linking trajectories: {e}")
            self.linked_trajectories = None
            # Hide progress indicator and re-enable button on error
            self.progress_label.setText(f"Error: {str(e)}")
            self.progress_bar.setVisible(False)
            self.find_trajectories_button.setEnabled(True)

    def create_trajectory_visualization(
        self, trajectories_df, output_folder, filename="trajectory_visualization.png"
    ):
        """Create a trajectory visualization on white background and save as image."""
        try:
            # Get image dimensions from first frame using FileController
            if self.file_controller:
                original_frames_folder = self.file_controller.original_frames_folder
                # Use FileController to get frame files
                frame_files = self.file_controller.get_all_frame_paths()
                # Filter to just image files and get first one
                frame_files = [
                    f
                    for f in frame_files
                    if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff"))
                ]
                if frame_files:
                    frame_files = [frame_files[0]]  # Just need first frame for dimensions
            else:
                if self.config_manager:
                    original_frames_folder = self.config_manager.get_path("original_frames_folder")
                else:
                    original_frames_folder = "original_frames/"
                # Fallback to os.listdir if no file_controller
                frame_files = []
                for filename in sorted(os.listdir(original_frames_folder)):
                    if filename.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
                        frame_files.append(os.path.join(original_frames_folder, filename))
                        break  # Just need first frame for dimensions

            if frame_files:
                first_frame = cv2.imread(frame_files[0])
                if first_frame is not None:
                    height, width = first_frame.shape[:2]
                else:
                    height, width = 800, 600  # Default dimensions
            else:
                height, width = 800, 600  # Default dimensions

            # Create figure with white background
            fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
            ax.set_facecolor("white")
            fig.patch.set_facecolor("white")

            # Plot trajectories
            unique_particles = trajectories_df["particle"].unique()
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_particles)))

            for i, particle_id in enumerate(unique_particles):
                particle_data = trajectories_df[trajectories_df["particle"] == particle_id]
                x_coords = particle_data["x"].values
                y_coords = particle_data["y"].values

                # Plot trajectory line
                ax.plot(
                    x_coords,
                    y_coords,
                    color=colors[i % len(colors)],
                    linewidth=1.5,
                    alpha=0.7,
                    label=f"Particle {particle_id}",
                )

                # Plot start point
                if len(x_coords) > 0:
                    ax.plot(
                        x_coords[0],
                        y_coords[0],
                        "o",
                        color=colors[i % len(colors)],
                        markersize=4,
                        markeredgecolor="black",
                        markeredgewidth=0.5,
                    )

            # Set axis properties
            ax.set_xlim(0, width)
            ax.set_ylim(height, 0)  # Invert y-axis to match image coordinates
            ax.set_aspect("equal")
            ax.set_xlabel("X (pixels)")
            ax.set_ylabel("Y (pixels)")
            ax.set_title("Particle Trajectories")

            # Remove top and right spines for cleaner look
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            # Save the visualization using FileController if available
            if self.file_controller:
                trajectory_image_path = os.path.join(
                    self.file_controller.data_folder, "trajectory_visualization.png"
                )
            else:
                trajectory_image_path = os.path.join(output_folder, "trajectory_visualization.png")
            plt.savefig(
                trajectory_image_path,
                dpi=150,
                bbox_inches="tight",
                facecolor="white",
                edgecolor="none",
            )
            plt.close(fig)

            print(f"Trajectory visualization saved to: {trajectory_image_path}")

            # Emit signal with image path for display
            self.trajectoryVisualizationCreated.emit(trajectory_image_path)

        except Exception as e:
            print(f"Error creating trajectory visualization: {e}")

    def create_errant_distance_links_gallery(self, trajectories_file, data_folder):
        """Create RB gallery using particle_processing function."""
        try:
            print(f"🔵 Starting RB gallery creation...")
            print(f"🔵 Trajectories file: {trajectories_file}")

            if self.file_controller:
                original_frames_folder = self.file_controller.original_frames_folder
                errant_distance_links_folder = self.file_controller.errant_distance_links_folder
                print(f"🔵 Using file_controller paths:")
                print(f"   Frames folder: {original_frames_folder}")
                print(f"   RB gallery folder: {errant_distance_links_folder}")
            else:
                if self.config_manager:
                    original_frames_folder = self.config_manager.get_path("original_frames_folder")
                    errant_distance_links_folder = self.config_manager.get_path(
                        "errant_distance_links_folder"
                    )
                else:
                    original_frames_folder = "original_frames/"
                    errant_distance_links_folder = "rb_gallery/"
                print(f"⚠️  No file_controller, using config paths:")
                print(f"   Frames folder: {original_frames_folder}")
                print(f"   RB gallery folder: {errant_distance_links_folder}")

            # Verify trajectories file exists using FileController
            trajectories_df = self.file_controller.load_trajectories_data("trajectories.csv")
            if trajectories_df.empty:
                print(
                    f"❌ ERROR: Trajectories file does not exist or is empty: {trajectories_file}"
                )
                return

            # Call the RB gallery creation function
            print(f"🔵 Calling particle_processing.create_rb_gallery...")
            ParticleProcessing.create_errant_distance_links_gallery(
                trajectories_file=trajectories_file,
                frames_folder=original_frames_folder,
                output_folder=errant_distance_links_folder,
            )
            print(f"✅ RB gallery creation completed")

        except Exception as e:
            print(f"❌ Error creating RB gallery: {e}")
            print(f"❌ Traceback:")
            traceback.print_exc()

    def go_back(self):
        """Emit signal to go back to particle detection window."""
        self.goBackToDetection.emit()
