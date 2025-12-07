"""
Trajectory Player Widget - Memory Link Gallery

Description: Displays a gallery of high-memory links (particles that disappeared
for many frames before reappearing). Allows navigation through links and frames
within each link.
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
import os
import json


class LWErrantMemoryLinksWidget(QWidget):
    """Widget for displaying memory link galleries."""

    def __init__(self, parent=None):
        """Initialize trajectory player widget.

        Parameters
        ----------
        parent : QWidget, optional
            Parent widget
        """
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None
        self.layout = QVBoxLayout(self)

        # Photo display for current frame
        self.photo_label = QLabel("No memory links available")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setMinimumHeight(300)
        self.layout.addWidget(self.photo_label)

        # Legend/key for cross markers (placed right after video frame)
        legend_layout = QHBoxLayout()
        legend_layout.addStretch()
        
        # Helper function to create label with info icon
        def create_legend_item(label_text, color, tooltip_text):
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(4)
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {color};")
            info_icon = QLabel("ⓘ")
            info_icon.setToolTip(tooltip_text)
            font = info_icon.font()
            font.setPointSize(10)
            info_icon.setFont(font)
            info_icon.setStyleSheet("color: #0033cc;")
            item_layout.addWidget(label)
            item_layout.addWidget(info_icon)
            return item_widget
        
        # Create legend items
        disappears_item = create_legend_item(
            "Disappears",
            "yellow",
            "The last location of the particle before it disappears from the linking data for a few frames"
        )
        reappears_item = create_legend_item(
            "Reappears",
            "green",
            "The first location of the particle after it reappears in the linking data after being absent for a few frames"
        )
        
        legend_layout.addWidget(disappears_item)
        legend_layout.addSpacing(20)  # Add spacing between items
        legend_layout.addWidget(reappears_item)
        legend_layout.addStretch()
        
        self.layout.addLayout(legend_layout)

        # Current link and frame display
        self.current_display_label = QLabel("Particle ID: N/A | Memory Link: 0 / 0 | Frame: 0 / 0")
        self.current_display_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.current_display_label)

        # Combined navigation controls
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()

        # Memory Link navigation
        nav_layout.addWidget(QLabel("Memory Link:"))
        self.prev_link_button = QPushButton("◀◀")
        self.prev_link_button.setFixedSize(40, 30)
        self.prev_link_button.clicked.connect(self.previous_link)
        nav_layout.addWidget(self.prev_link_button)

        # Frame navigation
        self.prev_frame_button = QPushButton("◀")
        self.prev_frame_button.setFixedSize(40, 30)
        self.prev_frame_button.clicked.connect(self.previous_frame)
        nav_layout.addWidget(self.prev_frame_button)

        self.frame_display = QLabel("0 / 0")
        self.frame_display.setAlignment(Qt.AlignCenter)
        self.frame_display.setMinimumWidth(60)
        nav_layout.addWidget(self.frame_display)

        self.next_frame_button = QPushButton("▶")
        self.next_frame_button.setFixedSize(40, 30)
        self.next_frame_button.clicked.connect(self.next_frame)
        nav_layout.addWidget(self.next_frame_button)

        self.next_link_button = QPushButton("▶▶")
        self.next_link_button.setFixedSize(40, 30)
        self.next_link_button.clicked.connect(self.next_link)
        nav_layout.addWidget(self.next_link_button)

        nav_layout.addStretch()
        self.layout.addLayout(nav_layout)

        # Store state
        self.errant_memory_links_folder = None
        self.links = []  # This will be a list of dictionaries from the JSON
        self.current_link_idx = 0
        self.current_frame_idx = 0
        self.current_link_frames = []  # List of frame files for current link

    def set_config_manager(self, config_manager):
        self.config_manager = config_manager

    def set_file_controller(self, file_controller):
        self.file_controller = file_controller
        if file_controller:
            self.errant_memory_links_folder = file_controller.errant_memory_links_folder
            self._load_links()

    def _load_links(self):
        """Load available memory links from the new JSON metadata file."""
        if not self.errant_memory_links_folder:
            self.links = []
            self._update_display()
            return
            
        json_path = os.path.join(self.errant_memory_links_folder, "memory_links.json")
        if not os.path.exists(json_path):
            self.links = []
            self.current_link_frames = []
            self.photo_label.setText("No memory links available")
            self._update_display()
            return

        try:
            with open(json_path, 'r') as f:
                self.links = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading memory links metadata: {e}")
            self.links = []

        if len(self.links) > 0:
            self.current_link_idx = 0
            self._load_link_frames()
        else:
            self.current_link_frames = []
            self.photo_label.setText("No memory links available")
        self._update_display()

    def _load_link_frames(self):
        """Load frame files for the current link."""
        if self.current_link_idx < 0 or self.current_link_idx >= len(self.links):
            self.current_link_frames = []
            return

        current_link = self.links[self.current_link_idx]
        link_folder_name = current_link.get("link_folder")
        if not link_folder_name:
            self.current_link_frames = []
            return

        link_folder_path = os.path.join(self.errant_memory_links_folder, link_folder_name)
        
        frame_files = [os.path.join(link_folder_path, f) for f in sorted(os.listdir(link_folder_path)) if f.startswith("frame_") and f.lower().endswith(".jpg")]

        self.current_link_frames = frame_files
        if len(self.current_link_frames) > 0:
            self.current_frame_idx = 0
            self._display_current_frame()
        else:
            self.photo_label.setText(f"No frames in memory link {self.current_link_idx}")

    def _display_current_frame(self):
        """Display the current pre-annotated frame."""
        if (self.current_frame_idx < 0 or 
            self.current_frame_idx >= len(self.current_link_frames)):
            self.photo_label.setPixmap(QPixmap())
            self.photo_label.setText("No Frames")
            return

        frame_path = self.current_link_frames[self.current_frame_idx]
        if not os.path.exists(frame_path):
            self.photo_label.setPixmap(QPixmap())
            self.photo_label.setText("Frame file not found")
            return
        
        pixmap = QPixmap(frame_path)
        
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.photo_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.photo_label.setPixmap(scaled_pixmap)
        else:
            self.photo_label.setPixmap(QPixmap())
            self.photo_label.setText("Failed to load frame")

    def _update_display(self):
        """Update the display labels."""
        total_frames = len(self.current_link_frames)
        total_links = len(self.links)

        # Update frame counter
        if total_frames > 0:
            self.frame_display.setText(f"{self.current_frame_idx + 1} / {total_frames}")
        else:
            self.frame_display.setText("0 / 0")

        # Update main info label
        if total_links > 0 and self.current_link_idx < total_links:
            current_link = self.links[self.current_link_idx]
            particle_id = current_link.get('particle_id', 'N/A')
            
            # Try to get original frame number if available
            frame_num = self.current_frame_idx + 1 # Default to 1-based index
            if self.current_link_frames and self.current_frame_idx < len(self.current_link_frames):
                frame_filename = os.path.basename(self.current_link_frames[self.current_frame_idx])
                try:
                    # Assumes format "frame_#####.jpg"
                    frame_num_original = int(frame_filename.split('_')[1].split('.')[0])
                    frame_num = frame_num_original
                except (ValueError, IndexError):
                    pass # Fallback to index if parsing fails

            self.current_display_label.setText(
                f"Particle ID: {particle_id} | "
                f"Memory Link: {self.current_link_idx + 1} / {total_links} | "
                f"Frame: {self.current_frame_idx + 1} / {total_frames} "
                f"(Original: {frame_num})"
            )
        else:
            self.current_display_label.setText("Particle ID: N/A | Memory Link: 0 / 0 | Frame: 0 / 0")

    def previous_link(self):
        if len(self.links) > 0 and self.current_link_idx > 0:
            self.current_link_idx -= 1
            self._load_link_frames()
            self._update_display()

    def next_link(self):
        if len(self.links) > 0 and self.current_link_idx < len(self.links) - 1:
            self.current_link_idx += 1
            self._load_link_frames()
            self._update_display()

    def previous_frame(self):
        if len(self.current_link_frames) > 0 and self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            self._display_current_frame()
            self._update_display()

    def next_frame(self):
        if len(self.current_link_frames) > 0 and self.current_frame_idx < len(self.current_link_frames) - 1:
            self.current_frame_idx += 1
            self._display_current_frame()
            self._update_display()

    def refresh_links(self):
        self._load_links()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._display_current_frame()

    def reset_state(self):
        self.current_link_idx = 0
        self.current_frame_idx = 0
        self.refresh_links()
