"""
Errant particle gallery widget

Description: Widget displaying errant particles to inform user if particle tracking parameters need adjustment.
             Generated boiler plate code using Cursor AI.
"""

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ErrantParticleGalleryWidget(QWidget):
    errant_particle_selected = Signal(int)
    show_particle_on_frame = Signal(int, float, float)  # frame_number, x, y

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None

        self.layout = QVBoxLayout(self)

        # photo - fixed 200x200 size, centered
        self.photo_label = QLabel("Photo display")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            "background-color: #222; color: #ccc; border: 2px solid blue;"
        )
        self.photo_label.setFixedSize(200, 200)
        self.photo_label.setScaledContents(False)
        # Center the widget horizontally
        self.layout.addStretch()
        self.layout.addWidget(self.photo_label, alignment=Qt.AlignCenter)
        self.layout.addStretch()

        # Store frame numbers for each particle
        self.particle_frames = {}  # index -> frame_number
        self.particle_positions = {}  # index -> (x, y)
        self.current_frame_number = -1
        self.highlighted_frame = (
            -1
        )  # Frame that was highlighted via button press

        # info
        self.info_label = QLabel("Info")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.info_label)

        # --- Frame Navigation ---
        self.frame_nav_layout = QHBoxLayout()
        self.prev_frame_button = QPushButton("<")
        self.frame_number_display = QLineEdit("0 / 0")
        self.curr_particle_idx = 0
        self.frame_number_display.setReadOnly(False)
        self.frame_number_display.setAlignment(Qt.AlignCenter)
        self.next_frame_button = QPushButton("->")
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

        # Add "Show particle on frame" button
        self.show_particle_button = QPushButton("Show particle on frame")
        self.show_particle_button.clicked.connect(
            self._on_show_particle_clicked
        )
        self.frame_nav_layout.addWidget(self.show_particle_button)

        self.layout.addLayout(self.frame_nav_layout)

        # particles directory and files
        self.particles_dir = ""
        self.particle_files = []
        self.current_pixmap = None

        # show initial particle if available
        self._display_particle(self.curr_particle_idx)

    def set_config_manager(self, config_manager):
        """Set the config manager for this widget."""
        self.config_manager = config_manager

    def set_file_controller(self, file_controller):
        """Set the file controller for this widget."""
        self.file_controller = file_controller
        if self.file_controller:
            self.particles_dir = self.file_controller.particles_folder
            self.refresh_particles()

    def refresh_particles(self):
        """Reload the list of particle image files and refresh display."""
        if not self.particles_dir:
            return
        self.particle_files = self._load_particle_files(self.particles_dir)
        # clamp current index within bounds
        if self.particle_files:
            self.curr_particle_idx = min(
                self.curr_particle_idx, len(self.particle_files) - 1
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
                self.particle_files = []
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
        self.highlighted_frame = -1
        self.curr_particle_idx = 0
        self.particle_frames.clear()
        self.particle_positions.clear()
        self.refresh_particles()

    def _load_particle_files(self, directory_path):
        """Return a sorted list of image file paths in the particles directory."""
        if not os.path.isdir(directory_path):
            return []
        valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
        files = []
        try:
            for name in os.listdir(directory_path):
                if os.path.splitext(name)[1].lower() in valid_exts:
                    files.append(os.path.join(directory_path, name))
        except Exception:
            return []
        files.sort()
        return files

    def _display_particle(self, index):
        """Update UI to display particle image and index if within bounds."""
        if 0 <= index < len(self.particle_files):
            file_path = self.particle_files[index]

            try:
                basename = os.path.basename(file_path)
                particle_index = int(basename.split("_")[-1].split(".")[0])
                self.errant_particle_selected.emit(particle_index)
            except (ValueError, IndexError):
                self.errant_particle_selected.emit(-1)

            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.current_pixmap = pixmap
                # Fixed 200x200 size - scale to fit
                scaled = self.current_pixmap.scaled(
                    200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.photo_label.setPixmap(scaled)
            else:
                self.photo_label.setText("Failed to load image")

            # Load and display info, extract frame number and position
            info_path = os.path.splitext(file_path)[0] + ".txt"
            frame_num = -1
            particle_x = None
            particle_y = None
            display_text = ""
            if os.path.exists(info_path):
                with open(info_path, "r") as f:
                    info_text = f.read()
                    # Parse frame number and position from metadata (needed for functionality)
                    # But only display mass/min_mass or feature_size/parameter_feature_size
                    mass = None
                    min_mass = None
                    feature_size = None
                    parameter_feature_size = None

                    for line in info_text.split("\n"):
                        if line.startswith("frame:"):
                            try:
                                frame_num = int(line.split(":")[1].strip())
                            except (ValueError, IndexError):
                                pass
                        elif line.startswith("x:"):
                            try:
                                particle_x = float(line.split(":")[1].strip())
                            except (ValueError, IndexError):
                                pass
                        elif line.startswith("y:"):
                            try:
                                particle_y = float(line.split(":")[1].strip())
                            except (ValueError, IndexError):
                                pass
                        elif line.startswith("mass:"):
                            try:
                                mass = float(line.split(":")[1].strip())
                            except (ValueError, IndexError):
                                pass
                        elif line.startswith("min_mass:"):
                            try:
                                min_mass = float(line.split(":")[1].strip())
                            except (ValueError, IndexError):
                                pass
                        elif line.startswith("feature_size:"):
                            try:
                                feature_size = float(
                                    line.split(":")[1].strip()
                                )
                            except (ValueError, IndexError):
                                pass
                        elif line.startswith("parameter_feature_size:"):
                            try:
                                parameter_feature_size = float(
                                    line.split(":")[1].strip()
                                )
                            except (ValueError, IndexError):
                                pass

                    # Build display text - only show mass/min_mass or feature_size/parameter_feature_size
                    if mass is not None and min_mass is not None:
                        display_text = (
                            f"mass: {mass:.2f}\nmin_mass: {min_mass:.2f}"
                        )
                    elif (
                        feature_size is not None
                        and parameter_feature_size is not None
                    ):
                        display_text = f"feature_size: {feature_size:.2f}\nparameter_feature_size: {parameter_feature_size:.2f}"

                    self.info_label.setText(display_text)
            else:
                self.info_label.setText("")

            # Store frame number and position for this particle
            self.particle_frames[index] = frame_num
            if particle_x is not None and particle_y is not None:
                self.particle_positions[index] = (particle_x, particle_y)

            # Update background highlighting based on current frame
            self._update_background_highlighting()

            self._update_display_text()
        else:
            self.errant_particle_selected.emit(-1)
            # out of bounds or no files
            if not self.particle_files:
                self.photo_label.setText("No particle images found")
            self.info_label.setText("")
            self._update_display_text()

    def _on_show_particle_clicked(self):
        """Handle click on 'Show particle on frame' button."""
        if 0 <= self.curr_particle_idx < len(self.particle_files):
            frame_num = self.particle_frames.get(self.curr_particle_idx, -1)
            position = self.particle_positions.get(
                self.curr_particle_idx, None
            )
            if frame_num >= 0 and position is not None:
                particle_x, particle_y = position
                # Set the highlighted frame to trigger background color change
                self.highlighted_frame = frame_num
                self.show_particle_on_frame.emit(
                    frame_num, particle_x, particle_y
                )
                # Update background highlighting
                self._update_background_highlighting()

    def set_current_frame(self, frame_number):
        """Set the current frame number for background highlighting."""
        old_frame = self.current_frame_number
        self.current_frame_number = frame_number

        # If frame changed (and it wasn't changed by the button), clear highlighted frame
        if (
            old_frame != frame_number
            and frame_number != self.highlighted_frame
        ):
            self.highlighted_frame = -1

        self._update_background_highlighting()

    def _update_background_highlighting(self):
        """Update background color based on whether current frame contains an errant particle."""
        # Background should be blue only if:
        # 1. We have a highlighted frame (set by button press)
        # 2. The current frame matches the highlighted frame
        # 3. The displayed particle is from that frame
        if (
            self.highlighted_frame >= 0
            and self.current_frame_number == self.highlighted_frame
            and 0 <= self.curr_particle_idx < len(self.particle_files)
        ):
            particle_frame = self.particle_frames.get(
                self.curr_particle_idx, -1
            )
            if particle_frame == self.highlighted_frame:
                # Current frame has this errant particle and was highlighted - blue background
                self.photo_label.setStyleSheet(
                    "background-color: #0066ff; color: #ccc; border: 2px solid blue;"
                )
            else:
                # Default background
                self.photo_label.setStyleSheet(
                    "background-color: #222; color: #ccc; border: 2px solid blue;"
                )
        else:
            # Default background
            self.photo_label.setStyleSheet(
                "background-color: #222; color: #ccc; border: 2px solid blue;"
            )

    def resizeEvent(self, event):
        """Ensure the currently shown image keeps aspect ratio on resize."""
        super().resizeEvent(event)
        if (
            self.current_pixmap is not None
            and not self.current_pixmap.isNull()
        ):
            # Fixed 200x200 size
            scaled = self.current_pixmap.scaled(
                200,
                200,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.photo_label.setPixmap(scaled)

    def next_particle(self):
        """Advance to the next particle and update display."""
        if not self.particle_files:
            return
        if self.curr_particle_idx < len(self.particle_files) - 1:
            self.curr_particle_idx += 1
            self._display_particle(self.curr_particle_idx)
        else:
            # already at last image; do nothing
            pass

    def prev_particle(self):
        """Go to the previous particle and update display."""
        if not self.particle_files:
            return
        if self.curr_particle_idx > 0:
            self.curr_particle_idx -= 1
            self._display_particle(self.curr_particle_idx)
        else:
            # already at first image; do nothing
            pass

    def _update_display_text(self):
        total = len(self.particle_files)
        text = f"{self.curr_particle_idx} / {total}"
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
            requested = int(first)
        except ValueError:
            # restore correct text
            self._update_display_text()
            return
        total = len(self.particle_files)
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
