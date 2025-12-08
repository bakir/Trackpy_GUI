"""
Errant particle gallery widget

Description: Widget displaying errant particles to inform user if particle tracking parameters need adjustment.
             Generated boiler plate code using Cursor AI.
"""

import json
import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..utils.ScaledLabel import ScaledLabel


class DWErrantParticleWidget(QWidget):
    """Widget for displaying errant particles."""

    update_required = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None

        self.layout = QVBoxLayout(self)

        # photo - fixed 200x200 size, centered
        self.photo_label = ScaledLabel("Photo display")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.photo_label, 1)  # Add with stretch factor

        # Store particle data from JSON
        self.particle_data = []
        self.current_frame_number = -1

        # info
        self.info_label = QLabel("Info")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.info_label)

        # --- Frame Navigation ---
        self.frame_nav_layout = QHBoxLayout()
        self.prev_frame_button = QPushButton("◀")
        self.frame_number_display = QLineEdit("0 / 0")
        self.curr_particle_idx = 0
        self.frame_number_display.setReadOnly(False)
        self.frame_number_display.setAlignment(Qt.AlignCenter)
        self.next_frame_button = QPushButton("▶")
        self.prev_frame_button.clicked.connect(self.prev_particle)
        self.next_frame_button.clicked.connect(self.next_particle)
        self.frame_number_display.returnPressed.connect(
            self._jump_to_input_particle
        )
        self.frame_number_display.editingFinished.connect(
            self._jump_to_input_particle
        )
        self.frame_nav_layout.addWidget(self.prev_frame_button)
        self.frame_nav_layout.addWidget(self.frame_number_display)
        self.frame_nav_layout.addWidget(self.next_frame_button)

        # Add "Show particle on frame" checkbox
        self.show_particle_checkbox = QCheckBox("Show particle on frame")
        self.show_particle_checkbox.stateChanged.connect(
            self._on_show_particle_checkbox_changed
        )
        self.frame_nav_layout.addWidget(self.show_particle_checkbox)

        self.layout.addLayout(self.frame_nav_layout)

        # particles directory and files
        self.particles_dir = ""
        self.current_pixmap = None

        # show initial particle if available
        self._display_particle(self.curr_particle_idx)

    def is_show_on_frame_checked(self):
        """Returns the state of the 'Show particle on frame' checkbox."""
        return self.show_particle_checkbox.isChecked()

    def get_current_particle_info(self):
        """Returns a dict with info of the currently displayed particle."""
        if 0 <= self.curr_particle_idx < len(self.particle_data):
            particle_info = self.particle_data[self.curr_particle_idx]
            return {
                "frame": particle_info.get("frame"),
                "x": particle_info.get("x"),
                "y": particle_info.get("y"),
            }
        return None

    def regenerate_errant_particles(self):
        """Regenerate errant particle crops based on the latest filtered data."""
        if not self.file_controller or not self.config_manager:
            return

        params = self.config_manager.get_detection_params()

        # This function now uses filtered_particles.csv internally
        from ..utils import ParticleProcessing

        ParticleProcessing.save_errant_particle_crops_for_frame(params)

        self.refresh_particles()

    def set_config_manager(self, config_manager):
        """Set the config manager for this widget."""
        self.config_manager = config_manager

    def set_file_controller(self, file_controller):
        """Set the file controller for this widget."""
        self.file_controller = file_controller
        if self.file_controller:
            self.particles_dir = self.file_controller.errant_particles_folder
            self.refresh_particles()

    def refresh_particles(self):
        """Reload the list of particle image files and refresh display."""
        if not self.particles_dir:
            return

        json_path = os.path.join(self.particles_dir, "errant_particles.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as f:
                    self.particle_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.particle_data = []
        else:
            self.particle_data = []

        # clamp current index within bounds
        if self.particle_data:
            self.curr_particle_idx = min(
                self.curr_particle_idx, len(self.particle_data) - 1
            )
        else:
            self.curr_particle_idx = 0
        self._display_particle(self.curr_particle_idx)

    def clear_gallery(self):
        """Clears all displayed errant particles and deletes the corresponding files."""
        if self.file_controller:
            try:
                self.file_controller.delete_all_files_in_folder(
                    self.particles_dir
                )
                self.particle_data = []
                self.curr_particle_idx = 0
                self._display_particle(self.curr_particle_idx)
                print(
                    f"Cleared errant particle gallery and deleted files in {self.particles_dir}"
                )
            except Exception as e:
                print(f"Error clearing errant particle gallery: {e}")

    def reset_state(self):
        """Reset gallery state and reload particles from disk."""
        self.current_frame_number = -1
        self.curr_particle_idx = 0
        self.particle_data = []
        self.refresh_particles()


    def _display_particle(self, index):
        """Update UI to display particle image and index if within bounds."""
        if 0 <= index < len(self.particle_data):

            particle_info = self.particle_data[index]
            image_file = particle_info.get("image_file")
            if not image_file:
                self.photo_label.setText("Image not found in metadata")
                self._update_display_text()
                return

            file_path = os.path.join(self.particles_dir, image_file)

            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.current_pixmap = pixmap
                self.photo_label.setPixmap(self.current_pixmap)
            else:
                self.photo_label.setText("Failed to load image")

            # Display info from the loaded JSON data
            display_text = ""
            mass = particle_info.get("mass")
            min_mass = particle_info.get("min_mass")
            size = particle_info.get("size")
            min_size = particle_info.get("min_size")

            if mass is not None and min_mass is not None:
                display_text = f"Mass: {mass:.2f}\nMin mass: {min_mass:.2f}"
            elif size is not None and min_size is not None:
                display_text = f"Size: {size:.2f}\nMin size: {min_size:.2f}"

            self.info_label.setText(display_text)

            self._update_display_text()

            # If checkbox is checked, notify the main window to update the view
            if self.is_show_on_frame_checked():
                self.update_required.emit()
        else:
            # out of bounds or no files
            if not self.particle_data:
                self.photo_label.setText("No particle images found")
            self.info_label.setText("")
            self._update_display_text()

    def _on_show_particle_checkbox_changed(self, state):
        """Handle state change of 'Show particle on frame' checkbox."""
        self.update_required.emit()

    def next_particle(self):
        """Advance to the next particle and update display."""
        if not self.particle_data:
            return
        if self.curr_particle_idx < len(self.particle_data) - 1:
            self.curr_particle_idx += 1
            self._display_particle(self.curr_particle_idx)
        else:
            # already at last image; do nothing
            pass

    def prev_particle(self):
        """Go to the previous particle and update display."""
        if not self.particle_data:
            return
        if self.curr_particle_idx > 0:
            self.curr_particle_idx -= 1
            self._display_particle(self.curr_particle_idx)
        else:
            # already at first image; do nothing
            pass

    def _update_display_text(self):
        total = len(self.particle_data)
        current_display = self.curr_particle_idx + 1 if total > 0 else 0
        text = f"{current_display} / {total}"
        # avoid recursive signals while editing
        old_block = self.frame_number_display.blockSignals(True)
        self.frame_number_display.setText(text)
        self.frame_number_display.blockSignals(old_block)

    def _jump_to_input_particle(self):
        """Parse the input and jump to the requested particle index if valid."""
        text = self.frame_number_display.text().strip()
        # Accept formats like "12" or "12 / 200"
        if "/" in text:
            first = text.split("/", 1)[0].strip()
        else:
            first = text
        try:
            requested = int(first) - 1
        except ValueError:
            # restore correct text
            self._update_display_text()
            return
        total = len(self.particle_data)
        if total == 0:
            self._update_display_text()
            return
        # clamp to valid range
        requested = max(0, min(requested, total - 1))
        if requested != self.curr_particle_idx:
            self.curr_particle_idx = requested
            self._display_particle(self.curr_particle_idx)
        else:
            # even if unchanged, ensure text format is correct
            self._update_display_text()
