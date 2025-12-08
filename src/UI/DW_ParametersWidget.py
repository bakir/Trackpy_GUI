"""
Detection Parameters Widget

Description: GUI widget for configuring particle detection parameters and triggering detection workflows.

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
    QCheckBox,
    QPushButton,
    QHBoxLayout,
    QProgressBar,
    QApplication,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal, QThread, QTimer
import pandas as pd
from ..utils import ParticleProcessing
from ..utils.UIUtils import create_label_with_info


class FindParticlesThread(QThread):
    """Thread for finding particles in selected frames."""

    processing_frame = Signal(str)
    finished = Signal(object)  # Emits found particles DataFrame

    def __init__(self, frame_paths, params):
        """Initialize particle finding thread."""
        super().__init__()
        self.frame_paths = frame_paths
        self.params = params

    def run(self):
        """Run particle detection on frames and return particles, but do not save."""
        try:
            particles = ParticleProcessing.find_particles_in_frames(
                self.frame_paths,
                self.params,
                progress_callback=self.processing_frame,
            )
            # Always emit finished signal, even if particles is None or empty
            if particles is None:
                particles = pd.DataFrame()
            self.finished.emit(particles)
        except Exception as e:
            print(f"Error in particle detection: {e}")
            # Emit empty DataFrame on error to ensure progress bar stops
            self.finished.emit(pd.DataFrame())


class DWParametersWidget(QWidget):
    allParticlesUpdated = Signal()
    openTrajectoryLinking = Signal()
    parameter_changed = Signal()
    particles_found = Signal()  # Emitted when Find Particles is clicked

    def __init__(self, graphing_panel, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None

        self.total_frames = 0
        self.find_particles_thread = None
        self.layout = QVBoxLayout(self)

        self.graphing_panel = graphing_panel

        # Track previous parameter values to detect actual changes
        self.previous_params = {}

        self.form = QFormLayout()

        # Inputs
        self.feature_size_input = QSpinBox()
        self.feature_size_input.setRange(1, 9999)
        self.feature_size_input.setSingleStep(2)
        self.feature_size_input.setToolTip("Approximate diameter of features (odd integer).")

        self.min_mass_input = QDoubleSpinBox()
        self.min_mass_input.setDecimals(2)
        self.min_mass_input.setRange(0.0, 1e12)
        self.min_mass_input.setSingleStep(10.0)
        self.min_mass_input.setToolTip("Minimum integrated brightness of a feature.")

        self.invert_input = QCheckBox("Invert (detect dark spots)")

        self.threshold_input = QDoubleSpinBox()
        self.threshold_input.setDecimals(2)
        self.threshold_input.setRange(0.0, 1e9)
        self.threshold_input.setSingleStep(1.0)
        self.threshold_input.setToolTip("Clip band-passed data below this value.")

        self.form.addRow(
            create_label_with_info(
                "Feature size", "Approximate diameter of features (odd integer)."
            ),
            self.feature_size_input,
        )
        self.form.addRow(
            create_label_with_info("Min mass", "Minimum integrated brightness of a feature."),
            self.min_mass_input,
        )
        self.form.addRow(
            create_label_with_info(
                "Invert", "Invert the image to detect dark spots instead of bright features."
            ),
            self.invert_input,
        )
        self.form.addRow(
            create_label_with_info("Threshold", "Clip band-passed data below this value."),
            self.threshold_input,
        )

        self.layout.addLayout(self.form)
        self.layout.addStretch()

        # --- Bottom Controls ---
        bottom_controls_layout = QVBoxLayout()
        self.progress_display = QLabel("")
        self.progress_display.setAlignment(Qt.AlignCenter)
        self.progress_display.setWordWrap(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress bar
        self.progress_bar.setVisible(False)
        bottom_controls_layout.addWidget(self.progress_display)
        bottom_controls_layout.addWidget(self.progress_bar)

        frame_inputs_layout = QHBoxLayout()
        self.start_frame_input = QSpinBox()
        self.end_frame_input = QSpinBox()
        self.step_frame_input = QSpinBox()
        self.step_frame_input.setRange(1, 9999)
        self.start_frame_input.valueChanged.connect(self.update_end_range)

        frame_inputs_layout.addWidget(
            create_label_with_info(
                "Start:", "First frame number to process (1-based).", add_stretch=False
            )
        )
        frame_inputs_layout.addWidget(self.start_frame_input)
        frame_inputs_layout.addWidget(
            create_label_with_info(
                "End:", "Last frame number to process (1-based).", add_stretch=False
            )
        )
        frame_inputs_layout.addWidget(self.end_frame_input)
        frame_inputs_layout.addWidget(
            create_label_with_info(
                "Step:", "Frame step size (process every Nth frame).", add_stretch=False
            )
        )
        frame_inputs_layout.addWidget(self.step_frame_input)
        bottom_controls_layout.addLayout(frame_inputs_layout)

        buttons_row_layout = QHBoxLayout()
        self.all_frames_button = QPushButton("All frames")
        self.all_frames_button.clicked.connect(self.set_all_frames)
        self.save_button = QPushButton("Find Particles")
        self.save_button.clicked.connect(self.find_particles)

        buttons_row_layout.addWidget(self.all_frames_button)
        buttons_row_layout.addStretch()
        buttons_row_layout.addWidget(self.save_button)
        # Undo button will be added here by detection window
        # Store reference to layout for detection window to use
        self.buttons_row_layout = buttons_row_layout
        bottom_controls_layout.addLayout(buttons_row_layout)

        # Frame info display (shows which frames particles were detected in)
        self.frame_info_label = QLabel("")
        self.frame_info_label.setAlignment(Qt.AlignCenter)
        self.frame_info_label.setWordWrap(True)
        self.frame_info_label.setStyleSheet(
            """
            QLabel {
                background-color: #f0f0f0;
                padding: 8px;
                border-radius: 4px;
                margin-top: 5px;
            }
        """
        )
        bottom_controls_layout.addWidget(self.frame_info_label)

        self.layout.addLayout(bottom_controls_layout)

        # Next button will be added by parent window below metadata
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_step)
        self.load_params()

        # Parameters are NOT automatically saved to config when edited
        # They are only saved when "Find Particles" is clicked or "Next" is clicked
        # This prevents accidental changes to the config file
        # However, we still emit parameter_changed for visual feedback (e.g., feature size update)
        self.feature_size_input.editingFinished.connect(self._on_parameter_edited)
        self.min_mass_input.editingFinished.connect(self._on_parameter_edited)
        self.threshold_input.editingFinished.connect(self._on_parameter_edited)
        self.invert_input.stateChanged.connect(self._on_parameter_edited)

    def set_config_manager(self, config_manager):
        self.config_manager = config_manager
        self.load_params()

    def set_file_controller(self, file_controller):
        self.file_controller = file_controller
        self.set_total_frames(len(self.file_controller.get_frame_files()))
        self._update_frame_info()

    def set_total_frames(self, num_frames):
        self.total_frames = num_frames
        self.start_frame_input.setRange(1, num_frames if num_frames > 0 else 1)
        self.end_frame_input.setRange(1, num_frames if num_frames > 0 else 1)
        self.set_all_frames()

    def set_all_frames(self):
        if self.total_frames > 0:
            self.start_frame_input.setValue(1)
            self.end_frame_input.setValue(self.total_frames)
            self.step_frame_input.setValue(1)

    def update_end_range(self):
        self.end_frame_input.setMinimum(self.start_frame_input.value())

    def load_params(self):
        if not self.config_manager:
            return
        params = self.config_manager.get_detection_params()
        self.feature_size_input.setValue(int(params.get("feature_size", 15)))
        self.min_mass_input.setValue(float(params.get("min_mass", 100.0)))
        self.invert_input.setChecked(bool(params.get("invert", False)))
        self.threshold_input.setValue(float(params.get("threshold", 0.0)))
        # Initialize previous_params with loaded values
        self.previous_params = {
            "feature_size": int(params.get("feature_size", 15)),
            "min_mass": float(params.get("min_mass", 100.0)),
            "invert": bool(params.get("invert", False)),
            "threshold": float(params.get("threshold", 0.0)),
        }

    def _on_parameter_edited(self):
        """Handle parameter editing - emit signal for visual feedback but don't save to config."""
        # Emit signal for visual feedback (e.g., feature size update in frame player)
        # but do NOT save to config file - that only happens when "Find Particles" is clicked
        self.parameter_changed.emit()

    def save_params(self):
        if not self.config_manager:
            return
        # Get current scaling from config (don't allow editing it here)
        current_scaling = self.config_manager.get_detection_params().get("scaling", 1.0)
        params = {
            "feature_size": self.feature_size_input.value(),
            "min_mass": self.min_mass_input.value(),
            "invert": self.invert_input.isChecked(),
            "threshold": self.threshold_input.value(),
            "scaling": current_scaling,  # Preserve existing scaling value
        }

        # Check if parameters actually changed
        params_changed = False
        if not self.previous_params:
            # First time saving, mark as changed
            params_changed = True
        else:
            # Compare current values with previous values
            for key in ["feature_size", "min_mass", "invert", "threshold"]:
                if params[key] != self.previous_params.get(key):
                    params_changed = True
                    break

        # Save params regardless (to persist current values)
        self.config_manager.save_detection_params(params)

        # Only emit signal if parameters actually changed
        if params_changed:
            self.previous_params = params.copy()
            self.parameter_changed.emit()
        else:
            # Update previous params even if no change (to track current state)
            self.previous_params = params.copy()

    def find_particles(self):
        if not self.file_controller:
            self.progress_display.setText("Project not loaded.")
            return

        # CRITICAL: Save current state for undo BEFORE doing anything else
        # This saves the CURRENT config file (with old parameters) before we update it
        # Get the main window to call save function
        main_window = self.window()
        if main_window and hasattr(main_window, "save_current_state"):
            main_window.save_current_state()

        # NOW save the new parameters to the config file
        # This updates the config with the values from the input widgets
        self.save_params()

        # Emit signal to clear gallery when Find Particles is clicked
        self.particles_found.emit()

        self._backup_and_clear_particles_data()

        # Convert 1-based UI input to 0-based frame indexing
        start_frame_0based = self.start_frame_input.value() - 1
        end_frame_0based = self.end_frame_input.value() - 1

        frame_paths = self.file_controller.get_frame_files(
            start=start_frame_0based,
            end=end_frame_0based,
            step=self.step_frame_input.value(),
        )

        if not frame_paths:
            self.progress_display.setText("No frames found in range.")
            return

        # Show progress indicator and disable buttons
        self.save_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.progress_display.setText("Working... Detecting particles. This may take a moment.")
        self.progress_bar.setVisible(True)
        QApplication.processEvents()  # Update UI immediately

        params = self.config_manager.get_detection_params()
        self.find_particles_thread = FindParticlesThread(frame_paths, params)
        self.find_particles_thread.processing_frame.connect(self.progress_display.setText)
        self.find_particles_thread.finished.connect(self.on_find_finished)
        self.find_particles_thread.start()

    def on_find_finished(self, particles_df):
        # Always re-enable buttons and hide progress bar first
        self.save_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        # Handle None case - convert to empty DataFrame
        if particles_df is None:
            particles_df = pd.DataFrame()

        # Save particles to file
        if not particles_df.empty:
            self.progress_display.setText("Particle detection completed!")
            self._save_all_particles_df(particles_df)
        else:
            # Even if no particles are found, save empty DataFrame
            self.progress_display.setText("Particle detection completed (no particles found).")
            self._save_all_particles_df(pd.DataFrame())

        # Use centralized refresh function to update all UI elements
        # Get the detection window to call refresh function
        detection_window = self.window()
        if detection_window and hasattr(detection_window, "refresh_detection_ui"):
            detection_window.refresh_detection_ui(particles_df, block_signals=False)
        else:
            # Fallback to old method if detection window not available
            self.allParticlesUpdated.emit()
            self.graphing_panel.filtering_widget.apply_filters_and_notify()
            self._update_frame_info()

        # Clear message after a moment
        QTimer.singleShot(2000, lambda: self.progress_display.setText(""))

    def _backup_and_clear_particles_data(self):
        """Backs up all_particles.csv and then clears it using FileController."""
        # Use FileController to backup particles data
        self.file_controller.backup_particles_data("old_all_particles.csv")

        # Clear all_particles.csv by saving an empty DataFrame using FileController
        self.file_controller.save_particles_data(pd.DataFrame(), "all_particles.csv")

    def _save_all_particles_df(self, df):
        self.file_controller.save_particles_data(df)
        self.graphing_panel.set_particles(df)  # Update graph with raw data

    def _update_frame_info(self):
        """Update the frame info display with frames where particles were detected."""
        if not self.file_controller:
            self.frame_info_label.setText("")
            return

        # Use FileController to load particles data
        try:
            particle_data = self.file_controller.load_particles_data("all_particles.csv")
            if not particle_data.empty and "frame" in particle_data.columns:
                frames = sorted(particle_data["frame"].unique())
                if len(frames) > 0:
                    # Convert to 1-indexed
                    frames_1indexed = [f + 1 for f in frames]
                    total_frames_processed = len(frames_1indexed)
                    min_frame = frames_1indexed[0]
                    max_frame = frames_1indexed[-1]
                    total_particles = len(particle_data)

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
                    frame_text = (
                        f"Frames processed: {total_frames_processed} | "
                        f"Range: {frame_range_text} | "
                        f"Total particles: {total_particles}"
                    )
                    self.frame_info_label.setText(frame_text)
                    return
        except Exception as e:
            print(f"Error reading frame info from particles: {e}")

        # No particles detected yet
        self.frame_info_label.setText("")

    def next_step(self):
        self.save_params()
        self.graphing_panel.blank_plot
        self.openTrajectoryLinking.emit()
