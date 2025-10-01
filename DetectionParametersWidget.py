from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton
from PySide6.QtCore import Qt, Signal
from config_parser import *
import os
import particle_processing

class DetectionParametersWidget(QWidget):
    particlesUpdated = Signal()
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
        particle_processing.find_and_save_particles(frame_path, params=params)
        # emit update so gallery can refresh
        self.particlesUpdated.emit()
