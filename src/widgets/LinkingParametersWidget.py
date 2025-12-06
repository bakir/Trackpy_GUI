"""
Linking Parameters Widget

Description: GUI widget for configuring trajectory linking parameters.
             Boiler plate code generated with Cursor.

This widget provides user interface controls for adjusting trackpy linking
parameters and managing the trajectory linking and visualization workflow.
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
)
from PySide6.QtCore import Qt, Signal
import os
from .. import particle_processing
import pandas as pd


class LinkingParametersWidget(QWidget):
    particlesDetected = Signal()
    trajectoriesLinked = Signal()
    trajectoryVisualizationCreated = Signal(str)  # Emits image path
    rbGalleryCreated = Signal()  # Signal that RB gallery was created
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

        self.form.addRow("Search range", self.search_range_input)
        self.form.addRow("Memory", self.memory_input)
        self.form.addRow(
            "Min trajectory length", self.min_trajectory_length_input
        )
        self.form.addRow("Subtract Drift", self.sub_drift)

        self.layout.addLayout(self.form)

        # Buttons
        self.buttons_layout = QVBoxLayout()

        self.find_trajectories_button = QPushButton("Find Trajectories")
        self.find_trajectories_button.clicked.connect(self.find_trajectories)
        self.buttons_layout.addWidget(
            self.find_trajectories_button, alignment=Qt.AlignRight
        )

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)
        self.buttons_layout.addWidget(
            self.back_button, alignment=Qt.AlignRight
        )

        self.export_close_button = QPushButton("Export & Close")
        self.export_close_button.clicked.connect(self.export_and_close.emit)
        self.buttons_layout.addWidget(
            self.export_close_button, alignment=Qt.AlignRight
        )

        self.layout.addLayout(self.buttons_layout)

        # Load existing values
        self.load_params()

        # Save on Enter / editing finished
        self.search_range_input.editingFinished.connect(self.save_params)
        self.memory_input.editingFinished.connect(self.save_params)
        self.min_trajectory_length_input.editingFinished.connect(
            self.save_params
        )
        self.sub_drift.stateChanged.connect(self.save_params)
        # Also catch Return in the embedded line edits
        self.search_range_input.lineEdit().returnPressed.connect(
            self.save_params
        )
        self.memory_input.lineEdit().returnPressed.connect(self.save_params)
        self.min_trajectory_length_input.lineEdit().returnPressed.connect(
            self.save_params
        )

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
        self.min_trajectory_length_input.setValue(
            int(params.get("min_trajectory_length", 10))
        )
        self.sub_drift.setChecked(bool(params.get("drift", False)))

    def save_params(self):
        if not self.config_manager:
            return
        params = {
            "search_range": int(self.search_range_input.value()),
            "memory": int(self.memory_input.value()),
            "min_trajectory_length": int(self.min_trajectory_length_input.value()),
            "drift": bool(self.sub_drift.isChecked())
        }
        self.config_manager.save_linking_params(params)

    def calc_drift(self, particle_data):
        try:
            import trackpy as tp
            scaling = self.config_manager.get_detection_params().get("scaling", 1.0)
            particle_data = particle_data.copy()
            
            # ⭐️ FIX: Check if the index is a simple RangeIndex (meaning structure was lost).
            # If so, reset the index to the required MultiIndex.
            if isinstance(particle_data.index, pd.RangeIndex):
                if 'particle' in particle_data.columns and 'frame' in particle_data.columns:
                    particle_data = particle_data.set_index(['frame', 'particle'])
            # if 'particle' in particle_data.columns and 'frame' in particle_data.columns:
            #     particle_data = particle_data.copy().set_index(['frame', 'particle'], drop=False)
            # else:
            #      # Should not happen with linked data, but a safeguard
            #     particle_data = particle_data.copy().set_index('frame', drop=False)
            drift = tp.compute_drift(particle_data, smoothing=15)*scaling
            # if 'particle' in particle_data.columns and 'frame' in particle_data.columns:
            #     particle_data = particle_data.set_index(['frame', 'particle'], drop=False)
            print(drift)
            print(particle_data.head())
            particle_data = tp.subtract_drift(particle_data, drift)
            print(particle_data.head())
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

        all_particles_file = os.path.join(data_folder, "all_particles.csv")
        filtered_particles_file = os.path.join(data_folder, "filtered_particles.csv")

        if not os.path.exists(filtered_particles_file):
            print(f"Filtered particles file not found: {filtered_particles_file}")
            print("Please run 'Find Particles' and 'Apply Filters' first.")
            return
        
        try:
            import trackpy as tp
            import pandas as pd

            search_range = int(linking_params.get("search_range", 10))
            memory = int(linking_params.get("memory", 10))
            min_trajectory_length = int(linking_params.get("min_trajectory_length", 10))

            # --- Process ALL_PARTICLES.CSV for unfiltered trajectories ---
            if os.path.exists(all_particles_file):
                all_particles_df = pd.read_csv(all_particles_file)
                if not all_particles_df.empty:
                    print("Linking ALL particles for unfiltered view...")
                    trajectories_all = tp.link_df(all_particles_df, search_range=search_range, memory=memory)
                    print(trajectories_all)
                    
                    trajectories_all = tp.filter_stubs(trajectories_all, min_trajectory_length)
                    print(trajectories_all)
                    if self.sub_drift.isChecked():
                        self.calc_drift(trajectories_all)
                        # scaling = self.config_manager.get_detection_params().get("scaling", 1.0)
                        # # scaling = float(params.get("scaling", 1.0))
                        # drift = tp.compute_drift(trajectories_all, smoothing=15)*scaling
                        # # drift_all = tp.compute_drift(trajectories_all)
                        # trajectories_all = tp.subtract_drift(trajectories_all, drift)
                        # trajectories_all = trajectories_all.reset_index(drop=True)
                        # if "particle" in trajectories_all.columns:
                        #     trajectories_all = trajectories_all.drop(columns=["particle"])
                        # if "frame" in trajectories_all.columns:
                        #     trajectories_all = trajectories_all.drop(columns=["frame"])
                        # trajectories_all = trajectories_all.reset_index(drop=False)

                    # Save all_trajectories.csv
                    all_trajectories_file = os.path.join(data_folder, "all_trajectories.csv")
                    trajectories_all.to_csv(all_trajectories_file, index=False)
                    print(f"Saved ALL trajectories to: {all_trajectories_file}")
                    self.trajectory_plotting.get_linked_particles(trajectories_all) # Pass unfiltered data to plotting
                else:
                    print("No data in all_particles.csv for unfiltered trajectory generation.")
            else:
                print("all_particles.csv not found, skipping unfiltered trajectory generation.")

            # --- Process FILTERED_PARTICLES.CSV for filtered trajectories ---
            print("Loading FILTERED particles for trajectory linking...")
            filtered_particles_df = pd.read_csv(filtered_particles_file)
            print(f"Loaded {len(filtered_particles_df)} filtered particles.")

            print(f"Linking filtered particles with search_range={search_range}, memory={memory}")
            trajectories_filtered = tp.link_df(filtered_particles_df, search_range=search_range, memory=memory)
            print(f"Created {trajectories_filtered['particle'].nunique()} filtered trajectories")

            print(f"Filtering filtered trajectories shorter than {min_trajectory_length} frames...")
            trajectories_filtered = tp.filter_stubs(trajectories_filtered, min_trajectory_length)
            print(f"After filtering: {trajectories_filtered['particle'].nunique()} filtered trajectories")

            if self.sub_drift.isChecked():
                self.calc_drift(trajectories_filtered)

            self.linked_trajectories = trajectories_filtered # Store the filtered linked trajectories
            print(trajectories_all.head())
            print(trajectories_filtered.head())
            # Save filtered trajectories.csv
            trajectories_file = os.path.join(data_folder, "trajectories.csv")
            trajectories_filtered.to_csv(trajectories_file, index=False)
            print(f"Saved FILTERED trajectories to: {trajectories_file}")

            # Create trajectory visualization (using filtered trajectories for this part)
            # The requirement is to visualize all_particles.csv, which is done above.
            # Here we can simply re-use the all_trajectories_file visualization name.
            # I will pass trajectories_all for this part.
            if 'trajectories_all' in locals():
                self.create_trajectory_visualization(trajectories_all, data_folder, "trajectory_visualization.png")

            self.create_rb_gallery(trajectories_file, data_folder) # RB gallery from filtered trajectories
            particle_processing.find_and_save_high_memory_links(trajectories_file, memory, max_links=5)

            self.trajectoriesLinked.emit()
            self.rbGalleryCreated.emit()

        except Exception as e:
            print(f"Error linking trajectories: {e}")
            self.linked_trajectories = None

    def create_trajectory_visualization(self, trajectories_df, output_folder, filename="trajectory_visualization.png"):
        """Create a trajectory visualization on white background and save as image."""
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            # Get image dimensions from first frame
            if self.file_controller:
                original_frames_folder = (
                    self.file_controller.original_frames_folder
                )
            else:
                if self.config_manager:
                    original_frames_folder = self.config_manager.get_path(
                        "original_frames_folder"
                    )
                else:
                    original_frames_folder = "original_frames/"

            frame_files = []
            for filename in sorted(os.listdir(original_frames_folder)):
                if filename.lower().endswith(
                    (".jpg", ".jpeg", ".png", ".tif", ".tiff")
                ):
                    frame_files.append(
                        os.path.join(original_frames_folder, filename)
                    )
                    break  # Just need first frame for dimensions

            if frame_files:
                import cv2

                first_frame = cv2.imread(frame_files[0])
                if first_frame is not None:
                    height, width = first_frame.shape[:2]
                else:
                    height, width = 800, 600  # Default dimensions
            else:
                height, width = 800, 600  # Default dimensions

            # Create figure with white background
            fig, ax = plt.subplots(
                figsize=(width / 100, height / 100), dpi=100
            )
            ax.set_facecolor("white")
            fig.patch.set_facecolor("white")

            # Plot trajectories
            unique_particles = trajectories_df["particle"].unique()
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_particles)))

            for i, particle_id in enumerate(unique_particles):
                particle_data = trajectories_df[
                    trajectories_df["particle"] == particle_id
                ]
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

            # Save the visualization
            trajectory_image_path = os.path.join(
                output_folder, "trajectory_visualization.png"
            )
            plt.savefig(
                trajectory_image_path,
                dpi=150,
                bbox_inches="tight",
                facecolor="white",
                edgecolor="none",
            )
            plt.close(fig)

            print(
                f"Trajectory visualization saved to: {trajectory_image_path}"
            )

            # Emit signal with image path for display
            self.trajectoryVisualizationCreated.emit(trajectory_image_path)

        except Exception as e:
            print(f"Error creating trajectory visualization: {e}")

    def create_rb_gallery(self, trajectories_file, data_folder):
        """Create RB gallery using particle_processing function."""
        try:
            print(f"🔵 Starting RB gallery creation...")
            print(f"🔵 Trajectories file: {trajectories_file}")

            if self.file_controller:
                original_frames_folder = (
                    self.file_controller.original_frames_folder
                )
                rb_gallery_folder = self.file_controller.rb_gallery_folder
                print(f"🔵 Using file_controller paths:")
                print(f"   Frames folder: {original_frames_folder}")
                print(f"   RB gallery folder: {rb_gallery_folder}")
            else:
                if self.config_manager:
                    original_frames_folder = self.config_manager.get_path(
                        "original_frames_folder"
                    )
                    rb_gallery_folder = self.config_manager.get_path(
                        "rb_gallery_folder"
                    )
                else:
                    original_frames_folder = "original_frames/"
                    rb_gallery_folder = "rb_gallery/"
                print(f"⚠️  No file_controller, using config paths:")
                print(f"   Frames folder: {original_frames_folder}")
                print(f"   RB gallery folder: {rb_gallery_folder}")

            # Verify trajectories file exists
            if not os.path.exists(trajectories_file):
                print(
                    f"❌ ERROR: Trajectories file does not exist: {trajectories_file}"
                )
                return

            # Call the RB gallery creation function
            print(f"🔵 Calling particle_processing.create_rb_gallery...")
            particle_processing.create_rb_gallery(
                trajectories_file=trajectories_file,
                frames_folder=original_frames_folder,
                output_folder=rb_gallery_folder,
            )
            print(f"✅ RB gallery creation completed")

        except Exception as e:
            import traceback

            print(f"❌ Error creating RB gallery: {e}")
            print(f"❌ Traceback:")
            traceback.print_exc()

    def refresh_trajectories(self):
        """Re-run the trajectory finding process."""
        self.find_trajectories()

    def go_back(self):
        """Emit signal to go back to particle detection window."""
        self.goBackToDetection.emit()
