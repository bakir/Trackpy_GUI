"""
Detection Parameters Widget

Description: GUI widget for configuring particle detection parameters and triggering detection workflows.
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
import os
import shutil
from ..utils import ParticleProcessing


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
        particles = ParticleProcessing.find_particles_in_frames(
            self.frame_paths,
            self.params,
            progress_callback=self.processing_frame,
        )
        self.finished.emit(particles)


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

        # Helper function to create label with info icon
        def create_label_with_info(label_text, tooltip_text):
            label_widget = QWidget()
            label_layout = QHBoxLayout(label_widget)
            label_layout.setContentsMargins(0, 0, 0, 0)
            label_layout.setSpacing(4)
            label = QLabel(label_text)
            info_icon = QLabel("ⓘ")
            info_icon.setToolTip(tooltip_text)
            font = info_icon.font()
            font.setPointSize(10)
            info_icon.setFont(font)
            info_icon.setStyleSheet("color: #0033cc;")
            label_layout.addWidget(label)
            label_layout.addWidget(info_icon)
            label_layout.addStretch()
            return label_widget

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

        self.form.addRow(create_label_with_info("Feature size", "Approximate diameter of features (odd integer)."), self.feature_size_input)
        self.form.addRow(create_label_with_info("Min mass", "Minimum integrated brightness of a feature."), self.min_mass_input)
        self.form.addRow(create_label_with_info("Invert", "Invert the image to detect dark spots instead of bright features."), self.invert_input)
        self.form.addRow(create_label_with_info("Threshold", "Clip band-passed data below this value."), self.threshold_input)

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
        
        # Helper function to create simple label with info icon (no stretch for horizontal layout)
        def create_simple_label_with_info(label_text, tooltip_text):
            label_widget = QWidget()
            label_layout = QHBoxLayout(label_widget)
            label_layout.setContentsMargins(0, 0, 0, 0)
            label_layout.setSpacing(4)
            label = QLabel(label_text)
            info_icon = QLabel("ⓘ")
            info_icon.setToolTip(tooltip_text)
            font = info_icon.font()
            font.setPointSize(10)
            info_icon.setFont(font)
            info_icon.setStyleSheet("color: #0033cc;")
            label_layout.addWidget(label)
            label_layout.addWidget(info_icon)
            return label_widget
        
        frame_inputs_layout.addWidget(create_simple_label_with_info("Start:", "First frame number to process (1-based)."))
        frame_inputs_layout.addWidget(self.start_frame_input)
        frame_inputs_layout.addWidget(create_simple_label_with_info("End:", "Last frame number to process (1-based)."))
        frame_inputs_layout.addWidget(self.end_frame_input)
        frame_inputs_layout.addWidget(create_simple_label_with_info("Step:", "Frame step size (process every Nth frame)."))
        frame_inputs_layout.addWidget(self.step_frame_input)
        bottom_controls_layout.addLayout(frame_inputs_layout)

        buttons_row_layout = QHBoxLayout()
        self.all_frames_button = QPushButton("All frames")
        self.all_frames_button.clicked.connect(self.set_all_frames)
        self.save_button = QPushButton("Find Particles")
        self.save_button.clicked.connect(self.find_particles)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_step)
        
        buttons_row_layout.addWidget(self.all_frames_button)
        buttons_row_layout.addStretch()
        buttons_row_layout.addWidget(self.save_button)
        buttons_row_layout.addWidget(self.next_button)
        bottom_controls_layout.addLayout(buttons_row_layout)
        
        self.layout.addLayout(bottom_controls_layout)
        self.load_params()

        # Connect signals for saving parameters
        self.feature_size_input.editingFinished.connect(self.save_params)
        self.min_mass_input.editingFinished.connect(self.save_params)
        self.threshold_input.editingFinished.connect(self.save_params)
        self.invert_input.stateChanged.connect(self.save_params)

    def set_config_manager(self, config_manager):
        self.config_manager = config_manager
        self.load_params()

    def set_file_controller(self, file_controller):
        self.file_controller = file_controller
        self.set_total_frames(len(self.file_controller.get_frame_files()))

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
        self.save_params()
        if not self.file_controller:
            self.progress_display.setText("Project not loaded.")
            return

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
        self.save_button.setEnabled(True)
        self.next_button.setEnabled(True)
        
        if particles_df is not None and not particles_df.empty:
            self.progress_display.setText("Particle detection completed!")
            self._save_all_particles_df(particles_df)
            self.allParticlesUpdated.emit()
            self.graphing_panel.filtering_widget.apply_filters_and_notify() # Trigger filter application
        else:
            # Even if no particles are found, clear existing data and refresh
            self.progress_display.setText("Particle detection completed (no particles found).")
            self._save_all_particles_df(pd.DataFrame())
            self.allParticlesUpdated.emit()
            self.graphing_panel.filtering_widget.apply_filters_and_notify()
        
        # Hide progress bar and clear message after a moment
        self.progress_bar.setVisible(False)
        QTimer.singleShot(2000, lambda: self.progress_display.setText(""))

    def _backup_and_clear_particles_data(self):
        """Backs up all_particles.csv and then clears it."""
        data_folder = self.file_controller.data_folder
        all_particles_path = os.path.join(data_folder, "all_particles.csv")
        old_all_particles_path = os.path.join(data_folder, "old_all_particles.csv")

        if os.path.exists(all_particles_path):
            shutil.copyfile(all_particles_path, old_all_particles_path)

        # Clear all_particles.csv by writing an empty DataFrame
        pd.DataFrame().to_csv(all_particles_path, index=False)

    def _save_all_particles_df(self, df):
        all_particles_path = os.path.join(self.file_controller.data_folder, "all_particles.csv")
        df.to_csv(all_particles_path, index=False)
        self.graphing_panel.set_particles(df) # Update graph with raw data

    def _apply_filters_and_refresh(self):
        """Applies filters to generate filtered_particles.csv and notifies UI."""
        # This method is now effectively replaced by calling graphing_panel.filtering_widget.apply_filters_and_notify()
        # The logic is handled by the FilteringWidget itself.
        pass

    def next_step(self):
        self.save_params()
        self.graphing_panel.blank_plot
        self.openTrajectoryLinking.emit()
