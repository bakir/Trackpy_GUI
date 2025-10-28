"""
Detection Parameters Widget

Description: GUI widget for configuring particle detection parameters and triggering detection workflows.
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QThread
import trackpy as tp
import matplotlib.pyplot as plt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ..config_parser import *
import cv2
from .. import particle_processing

class FindParticlesThread(QThread):
    processing_frame = Signal(str)
    finished = Signal()

    def __init__(self, frame_paths, params):
        super().__init__()
        self.frame_paths = frame_paths
        self.params = params

    def run(self):
        particle_processing.find_and_save_errant_particles(
            self.frame_paths,
            self.params,
            progress_callback=self.processing_frame
        )
        self.finished.emit()

class DetectAllFramesThread(QThread):
    processing_frame = Signal(str)
    finished = Signal()

    def __init__(self, frame_paths, params, config_manager=None, file_controller=None):
        super().__init__()
        self.frame_paths = frame_paths
        self.params = params
        self.config_manager = config_manager
        self.file_controller = file_controller

    def run(self):
        try:
            import pandas as pd
            
            # Use injected file controller if available
            if self.file_controller:
                annotated_frames_folder = self.file_controller.annotated_frames_folder
                data_folder = self.file_controller.data_folder
            else:
                # Fall back to config manager
                if self.config_manager:
                    annotated_frames_folder = self.config_manager.get_path('annotated_frames_folder')
                    data_folder = self.config_manager.get_path('data_folder')
                else:
                    # Fall back to global config
                    config = get_config()
                    annotated_frames_folder = config.get('annotated_frames_folder', 'annotated_frames/')
                    data_folder = config.get('data_folder', 'data/')

            feature_size = int(self.params.get('feature_size', 15))
            min_mass = float(self.params.get('min_mass', 100.0))
            invert = bool(self.params.get('invert', False))
            threshold = float(self.params.get('threshold', 0.0))

            if feature_size % 2 == 0:
                feature_size += 1

            all_particles = []
            for frame_idx, frame_file in enumerate(self.frame_paths):
                frame_num = int(os.path.splitext(os.path.basename(frame_file))[0].split('_')[-1])
                self.processing_frame.emit(f"Processing remaining frame {frame_num}")
                
                frame = cv2.imread(frame_file)
                if frame is None:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                particles = tp.locate(gray, diameter=feature_size, minmass=min_mass, invert=invert, threshold=threshold)
                particles['frame'] = frame_num
                all_particles.append(particles)

                if not particles.empty:
                    annotated_image = frame.copy()
                    for index, particle in particles.iterrows():
                        cv2.circle(annotated_image, (int(particle.x), int(particle.y)), int(feature_size/2) + 2, (0, 255, 255), 2)
                    annotated_frame_path = os.path.join(annotated_frames_folder, f"frame_{frame_num:05d}.jpg")
                    cv2.imwrite(annotated_frame_path, annotated_image)

            if all_particles:
                combined_particles = pd.concat(all_particles, ignore_index=True)
                os.makedirs(data_folder, exist_ok=True)
                particles_file = os.path.join(data_folder, 'all_particles.csv')
                
                if os.path.exists(particles_file):
                    existing_df = pd.read_csv(particles_file)
                    combined_particles = pd.concat([existing_df, combined_particles], ignore_index=True)
                
                combined_particles.to_csv(particles_file, index=False)

        except Exception as e:
            print(f"Error in DetectAllFramesThread: {e}")
        finally:
            self.finished.emit()

class DetectionParametersWidget(QWidget):
    particlesUpdated = Signal()
    openTrajectoryLinking = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None

        self.total_frames = 0
        self.find_particles_thread = None
        self.detect_all_thread = None
        self.processed_frames = set()
        self._last_find_range = None
        self.layout = QVBoxLayout(self)

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

        self.form.addRow("Feature size", self.feature_size_input)
        self.form.addRow("Min mass", self.min_mass_input)
        self.form.addRow("Invert", self.invert_input)
        self.form.addRow("Threshold", self.threshold_input)

        self.layout.addLayout(self.form)
        self.layout.addStretch()

        # --- Bottom Controls ---
        bottom_controls_layout = QVBoxLayout()

        self.progress_display = QLabel("")
        self.progress_display.setAlignment(Qt.AlignCenter)
        bottom_controls_layout.addWidget(self.progress_display)

        # Frame selection inputs
        frame_inputs_layout = QHBoxLayout()
        self.start_frame_input = QSpinBox()
        self.start_frame_input.setRange(1, 1)
        self.start_frame_input.valueChanged.connect(self.update_end_range)
        self.end_frame_input = QSpinBox()
        self.end_frame_input.setRange(1, 1)
        self.step_frame_input = QSpinBox()
        self.step_frame_input.setRange(1, 9999)
        
        frame_inputs_layout.addWidget(QLabel("Start:"))
        frame_inputs_layout.addWidget(self.start_frame_input)
        frame_inputs_layout.addWidget(QLabel("End:"))
        frame_inputs_layout.addWidget(self.end_frame_input)
        frame_inputs_layout.addWidget(QLabel("Step:"))
        frame_inputs_layout.addWidget(self.step_frame_input)
        
        bottom_controls_layout.addLayout(frame_inputs_layout)

        # Buttons layout
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

        # Load existing values
        self.load_params()

        # Save on Enter / editing finished
        self.feature_size_input.editingFinished.connect(self.save_params)
        self.min_mass_input.editingFinished.connect(self.save_params)
        self.threshold_input.editingFinished.connect(self.save_params)
        self.feature_size_input.lineEdit().returnPressed.connect(self.save_params)
        self.min_mass_input.lineEdit().returnPressed.connect(self.save_params)
        self.threshold_input.lineEdit().returnPressed.connect(self.save_params)
        self.invert_input.stateChanged.connect(lambda _state: self.save_params())

    def set_config_manager(self, config_manager):
        """Set the config manager for this widget."""
        self.config_manager = config_manager
    
    def set_file_controller(self, file_controller):
        """Set the file controller for this widget."""
        self.file_controller = file_controller

    def clear_processed_frames(self):
        self.processed_frames.clear()

    def set_total_frames(self, num_frames):
        self.total_frames = num_frames
        self.start_frame_input.setRange(1, num_frames if num_frames > 0 else 1)
        self.end_frame_input.setRange(1, num_frames if num_frames > 0 else 1)
        self.set_all_frames()

    def set_all_frames(self):
        self.start_frame_input.setValue(1)
        self.end_frame_input.setValue(self.total_frames)
        self.step_frame_input.setValue(1)

    def update_end_range(self):
        self.end_frame_input.setMinimum(self.start_frame_input.value())

    def load_params(self):
        params = get_detection_params()
        feature_size = int(params.get('feature_size', 15))
        if feature_size % 2 == 0:
            feature_size += 1
        self.feature_size_input.setValue(feature_size)
        self.min_mass_input.setValue(float(params.get('min_mass', 100.0)))
        self.invert_input.setChecked(bool(params.get('invert', False)))
        self.threshold_input.setValue(float(params.get('threshold', 0.0)))

    def save_params(self):
        feature_size = int(self.feature_size_input.value())
        if feature_size % 2 == 0:
            feature_size += 1
        params = {
            'feature_size': feature_size,
            'min_mass': float(self.min_mass_input.value()),
            'invert': bool(self.invert_input.isChecked()),
            'threshold': float(self.threshold_input.value()),
        }
        save_detection_params(params)

    def find_particles(self):
        self.save_params()
        params = get_detection_params()
        
        # Use injected file controller if available
        if self.file_controller:
            original_frames_folder = self.file_controller.original_frames_folder
        else:
            # Fall back to config manager
            if self.config_manager:
                original_frames_folder = self.config_manager.get_path('original_frames_folder')
            else:
                # Fall back to global config
                from ..config_parser import get_config
                config = get_config()
                original_frames_folder = config.get('original_frames_folder', 'original_frames/')

        start = self.start_frame_input.value()
        end = self.end_frame_input.value()
        step = self.step_frame_input.value()
        self._last_find_range = (start, end, step)

        frame_paths = []
        for i in range(start - 1, end, step):
            frame_filename = f"frame_{i:05d}.jpg"
            frame_path = os.path.join(original_frames_folder, frame_filename)
            if os.path.isfile(frame_path):
                frame_paths.append(frame_path)
        
        if not frame_paths:
            self.progress_display.setText("No frames found in range.")
            return

        self.save_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.progress_display.setText("Starting...")

        self.find_particles_thread = FindParticlesThread(frame_paths, params)
        self.find_particles_thread.processing_frame.connect(self.progress_display.setText)
        self.find_particles_thread.finished.connect(self.on_find_finished)
        self.find_particles_thread.start()

    def on_find_finished(self):
        self.save_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.particlesUpdated.emit()
        
        # Update processed frames set
        if self._last_find_range:
            start, end, step = self._last_find_range
            for i in range(start - 1, end, step):
                self.processed_frames.add(i)

    def next_step(self):
        self.detect_all_frames()

    def detect_all_frames(self):
        self.save_params()
        params = get_detection_params()
        
        # Use injected file controller if available
        if self.file_controller:
            original_frames_folder = self.file_controller.original_frames_folder
        else:
            # Fall back to config manager
            if self.config_manager:
                original_frames_folder = self.config_manager.get_path('original_frames_folder')
            else:
                # Fall back to global config
                from ..config_parser import get_config
                config = get_config()
                original_frames_folder = config.get('original_frames_folder', 'original_frames/')
        
        if not os.path.exists(original_frames_folder):
            print(f"Frames folder not found: {original_frames_folder}")
            return
        
        all_frame_files = []
        for filename in sorted(os.listdir(original_frames_folder)):
            if filename.startswith("frame_") and filename.lower().endswith('.jpg'):
                all_frame_files.append(os.path.join(original_frames_folder, filename))
        
        if not all_frame_files:
            print("No frame files found in frames folder")
            return

        frames_to_process = []
        for frame_file in all_frame_files:
            try:
                frame_num = int(os.path.splitext(os.path.basename(frame_file))[0].split('_')[-1])
                if frame_num not in self.processed_frames:
                    frames_to_process.append(frame_file)
            except (ValueError, IndexError):
                continue

        if not frames_to_process:
            self.progress_display.setText("All frames already processed.")
            self.openTrajectoryLinking.emit()
            return

        self.save_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.progress_display.setText("Processing remaining frames...")

        self.detect_all_thread = DetectAllFramesThread(frames_to_process, params, self.config_manager, self.file_controller)
        self.detect_all_thread.processing_frame.connect(self.progress_display.setText)
        self.detect_all_thread.finished.connect(self.on_detect_all_finished)
        self.detect_all_thread.start()

    def on_detect_all_finished(self):
        self.save_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.progress_display.setText("Finished processing all frames.")
        
        # Update processed frames set
        # This is a bit redundant if we only ever add to it, but good practice
        for frame_file in self.detect_all_thread.frame_paths:
             try:
                frame_num = int(os.path.splitext(os.path.basename(frame_file))[0].split('_')[-1])
                self.processed_frames.add(frame_num)
             except (ValueError, IndexError):
                continue

        self.openTrajectoryLinking.emit()

    def open_trajectory_linking(self):
        self.openTrajectoryLinking.emit()