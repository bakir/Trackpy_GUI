"""
Detection Parameters Widget

Description: GUI widget for configuring particle detection parameters and triggering detection workflows.
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton
from PySide6.QtCore import Qt, Signal
import trackpy as tp
import matplotlib.pyplot as plt
from config_parser import *
import cv2
import os
import particle_processing

class DetectionParametersWidget(QWidget):
    particlesUpdated = Signal()
    openTrajectoryLinking = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)

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

        # Buttons
        self.buttons_layout = QVBoxLayout()
        self.save_button = QPushButton("Find Particles")
        self.save_button.clicked.connect(self.find_particles)
        self.buttons_layout.addWidget(self.save_button, alignment=Qt.AlignRight)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_step)
        self.buttons_layout.addWidget(self.next_button, alignment=Qt.AlignRight)
        
        self.layout.addLayout(self.buttons_layout)

        # Load existing values
        self.load_params()

        # Save on Enter / editing finished
        self.feature_size_input.editingFinished.connect(self.save_params)
        self.min_mass_input.editingFinished.connect(self.save_params)
        self.threshold_input.editingFinished.connect(self.save_params)
        # Also catch Return in the embedded line edits
        self.feature_size_input.lineEdit().returnPressed.connect(self.save_params)
        self.min_mass_input.lineEdit().returnPressed.connect(self.save_params)
        self.threshold_input.lineEdit().returnPressed.connect(self.save_params)
        # Save on invert toggle
        self.invert_input.stateChanged.connect(lambda _state: self.save_params())

    def load_params(self):
        params = get_detection_params()
        # Ensure feature_size is odd; if even, bump by 1 for UI consistency
        feature_size = int(params.get('feature_size', 15))
        if feature_size % 2 == 0:
            feature_size += 1
        self.feature_size_input.setValue(feature_size)
        self.min_mass_input.setValue(float(params.get('min_mass', 100.0)))
        self.invert_input.setChecked(bool(params.get('invert', False)))
        self.threshold_input.setValue(float(params.get('threshold', 0.0)))

    def save_params(self):
        feature_size = int(self.feature_size_input.value())
        # enforce odd diameter required by trackpy
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
        # Ensure latest values are saved
        self.save_params()
        params = get_detection_params()
        config = get_config()
        frames_folder = config.get('frames_folder', 'frames/')
        # construct frame path
        idx = int(params.get('frame_idx', 0))
        frame_filename = f"frame_{idx:05d}.jpg"
        frame_path = os.path.join(frames_folder, frame_filename)
        if not os.path.isfile(frame_path):
            return
        # run detection and save particles
        features = particle_processing.find_and_save_particles(frame_path, params=params)
        # emit update so gallery can refresh
        self.particlesUpdated.emit()

        # create an annotated frame. Nothing done with it right now.
        plt.figure(figsize=(10, 10))
        tp.annotate(features, cv2.imread(frame_path))
        plt.savefig('annotated_frame.jpg', dpi=150)
        plt.close()

    def next_step(self):
        """Detect particles in all frames and switch to trajectory linking window."""
        # First, detect particles in all frames
        self.detect_all_frames()
        
        # Then switch to trajectory linking window
        self.openTrajectoryLinking.emit()

    def detect_all_frames(self):
        """Detect particles in all frames using tp.locate and save results."""
        # Ensure latest values are saved
        self.save_params()
        params = get_detection_params()
        config = get_config()
        frames_folder = config.get('frames_folder', 'frames/')
        
        # Check if frames exist
        if not os.path.exists(frames_folder):
            print(f"Frames folder not found: {frames_folder}")
            return
        
        # Get all frame files
        frame_files = []
        for filename in sorted(os.listdir(frames_folder)):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff')):
                frame_files.append(os.path.join(frames_folder, filename))
        
        if not frame_files:
            print("No frame files found in frames folder")
            return
        
        print(f"Detecting particles in {len(frame_files)} frames...")
        
        try:
            import trackpy as tp
            import cv2
            import pandas as pd
            
            # Get detection parameters
            feature_size = int(params.get('feature_size', 15))
            min_mass = float(params.get('min_mass', 100.0))
            invert = bool(params.get('invert', False))
            threshold = float(params.get('threshold', 0.0))
            
            # Ensure odd feature size as required by trackpy
            if feature_size % 2 == 0:
                feature_size += 1
            
            all_particles = []
            
            # Process each frame
            for frame_idx, frame_file in enumerate(frame_files):
                # Read and convert to grayscale
                frame = cv2.imread(frame_file)
                if frame is None:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect particles in this frame
                particles = tp.locate(
                    gray,
                    diameter=feature_size,
                    minmass=min_mass,
                    invert=invert,
                    threshold=threshold
                )
                
                # Add frame number to particles
                particles['frame'] = frame_idx
                all_particles.append(particles)
                
                if frame_idx % 10 == 0:  # Progress indicator
                    print(f"Processed frame {frame_idx + 1}/{len(frame_files)}")
            
            # Combine all particles
            if all_particles:
                combined_particles = pd.concat(all_particles, ignore_index=True)
                
                # Save to particles folder
                particles_folder = config.get('particles_folder', 'particles/')
                os.makedirs(particles_folder, exist_ok=True)
                
                particles_file = os.path.join(particles_folder, 'all_particles.csv')
                combined_particles.to_csv(particles_file, index=False)
                
                print(f"Detected {len(combined_particles)} particles across {len(frame_files)} frames")
                print(f"Saved to: {particles_file}")
                
                # Emit signal that all frames were processed
                self.particlesUpdated.emit()
            else:
                print("No particles detected in any frame")
                
        except Exception as e:
            print(f"Error detecting particles in all frames: {e}")

    def open_trajectory_linking(self):
        """Emit signal to open trajectory linking window."""
        self.openTrajectoryLinking.emit()
