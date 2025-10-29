"""
Trajectory linking plot

Description: Displays trajectory linking plot based on trajectory linking parameters.

"""


from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class TrajectoryPlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None
        self.layout = QVBoxLayout(self)
        
        # Photo display for trajectory visualization
        self.photo_label = QLabel("Trajectory Display")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            "background-color: white; color: #333; border: 1px solid #555;"
        )
        self.photo_label.setMinimumHeight(300)
        self.photo_label.setScaledContents(False)
        self.layout.addWidget(self.photo_label)
        
        # Store current pixmap for resize handling
        self.current_pixmap = None

    def set_config_manager(self, config_manager):
        """Set the config manager for this widget."""
        self.config_manager = config_manager

    def set_file_controller(self, file_controller):
        """Set the file controller for this widget."""
        self.file_controller = file_controller

    def display_trajectory_image(self, image_path):
        """Display a trajectory visualization image."""
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.current_pixmap = pixmap
                # Scale to fit while keeping aspect ratio
                scaled = self.current_pixmap.scaled(
                    self.photo_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.photo_label.setPixmap(scaled)
            else:
                self.photo_label.setText("Failed to load trajectory image")
        except Exception as e:
            self.photo_label.setText(f"Error loading image: {str(e)}")

    def resizeEvent(self, event):
        """Handle widget resize to update image display."""
        super().resizeEvent(event)
        if self.current_pixmap is not None and not self.current_pixmap.isNull():
            scaled = self.current_pixmap.scaled(
                self.photo_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.photo_label.setPixmap(scaled)
