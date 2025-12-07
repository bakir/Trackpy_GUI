"""
Main Application Controller with Project Management

Description: Main application controller that manages the start screen and project-based workflow.
             Handles switching between start screen and main application windows.
"""

import sys
import os
import platform
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtGui import QGuiApplication
from PySide6 import QtWidgets
from src.UI.SSW_StartScreenWindow import SSWStartScreenWindow
from src.UI.DW_DetectionWindow import DWDetectionWindow
from src.UI.LW_LinkingWindow import LWLinkingWindow
from src.utils.ProjectManager import ProjectManager
from src.utils.FileController import FileController
from src.utils.ConfigManager import ConfigManager


class ParticleTrackingAppController(QMainWindow):
    """Main application controller that manages project workflow and window switching."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Particle Tracking GUI")

        # Initialize configuration and managers
        self.project_config = None  # Will be set when project is loaded
        self.project_manager = ProjectManager()
        self.file_controller = (
            None  # Will be initialized when project is loaded
        )

        # Initialize windows
        self.ssw_start_screen_window = None
        self.dw_detection_window = None
        self.lw_linking_window = None

        # Initialize window sizes
        self.win_width = None
        self.win_height = None

        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Show start screen
        self.show_start_screen()

    def show_start_screen(self):
        """Show the start screen for project selection."""
        # Clean up any existing windows
        self.cleanup_windows()

        # Create start screen
        self.ssw_start_screen_window = SSWStartScreenWindow()
        self.ssw_start_screen_window.project_selected.connect(self.on_project_selected)

        self.stacked_widget.addWidget(self.ssw_start_screen_window)
        self.stacked_widget.setCurrentWidget(self.ssw_start_screen_window)

        # Resize the main window to fit the start screen
        self.ssw_start_screen_window.adjustSize()
        self.resize(self.ssw_start_screen_window.size())
        self.center()
        
    def center(self):
        """Center the window on the screen."""
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) / 2
        y = (screen.height() - self.height()) / 2
        self.move(int(x), int(y))

    def on_project_selected(self, project_path):
        """Handle project selection from start screen."""
        # Load the project
        if self.project_manager.load_project(project_path):
            # Initialize project-specific config and file controller
            project_config_path = os.path.join(project_path, "config.ini")
            self.project_config = ConfigManager(project_config_path)
            self.file_controller = FileController(
                self.project_config, project_path
            )

            # Set file controller in particle processing module
            from src.utils import ParticleProcessing

            ParticleProcessing.set_file_controller(self.file_controller)

            # Start the main application workflow
            self.show_particle_detection_window()

            # Check for existing frames
            num_frames = self.file_controller.get_total_frames_count()
            if num_frames > 0:
                self.dw_detection_window.load_existing_frames(num_frames)
            else:
                # If no frames exist, check if video file exists and auto-extract frames
                metadata = self.project_config.get_metadata()
                video_filename = metadata.get("movie_filename", "")
                if video_filename:
                    videos_folder = self.file_controller.videos_folder
                    video_path = os.path.join(videos_folder, video_filename)
                    if os.path.exists(video_path):
                        # Auto-extract frames from video
                        self.dw_detection_window.frame_player.save_video_frames(video_path)
        else:
            print(f"Failed to load project: {project_path}")

    def show_particle_detection_window(self):
        """Show the particle detection window and hide others."""
        # Clean up any existing windows
        self.cleanup_windows(clear_rb_gallery=False)

        # Create particle detection window
        self.dw_detection_window = DWDetectionWindow()
        self.dw_detection_window.set_config_manager(self.project_config)
        self.dw_detection_window.set_file_controller(
            self.file_controller
        )

        # Connect signals from particle detection window
        self.dw_detection_window.right_panel.openTrajectoryLinking.connect(
            self.on_next_to_trajectory_linking
        )

        # Add to stacked widget
        self.stacked_widget.addWidget(self.dw_detection_window)
        self.stacked_widget.setCurrentWidget(self.dw_detection_window)

        # Resize the main window to a fraction of the screen
        available_geometry = QGuiApplication.primaryScreen().availableGeometry()
        self.resize(available_geometry.width() * 0.8, available_geometry.height() * 0.8)
        self.center()

    def show_trajectory_linking_window(self):
        """Show the trajectory linking window and hide others."""
        # Save the current window size and position before switching
        current_size = self.size()
        current_pos = self.pos()
        
        # Clean up any existing windows
        self.cleanup_windows(clear_rb_gallery=False)

        # Create trajectory linking window
        self.lw_linking_window = LWLinkingWindow()
        self.lw_linking_window.set_config_manager(self.project_config)
        self.lw_linking_window.set_file_controller(
            self.file_controller
        )

        # Connect signals from trajectory linking window
        self.lw_linking_window.right_panel.goBackToDetection.connect(
            self.on_back_to_particle_detection
        )

        # Add to stacked widget
        self.stacked_widget.addWidget(self.lw_linking_window)
        self.stacked_widget.setCurrentWidget(self.lw_linking_window)

        # Preserve the window size and position from the previous window
        self.resize(current_size)
        self.move(current_pos)

    def on_next_to_trajectory_linking(self):
        """Handle signal to switch from particle detection to trajectory linking."""
        # The particle detection window will handle the "Next" button logic
        # (detecting particles in all frames), then we switch windows
        self.show_trajectory_linking_window()

    def on_back_to_particle_detection(self):
        """Handle signal to switch from trajectory linking back to particle detection."""
        # Save the current window size and position before switching
        current_size = self.size()
        current_pos = self.pos()
        
        # Show particle detection window
        self.show_particle_detection_window()
        
        # Preserve the window size and position
        self.resize(current_size)
        self.move(current_pos)

    def cleanup_windows(self, clear_rb_gallery: bool = True):
        """Clean up existing windows and optionally RB gallery."""
        if clear_rb_gallery:
            self.cleanup_rb_gallery()

        # Close existing windows
        if self.dw_detection_window:
            self.dw_detection_window.close()
            self.dw_detection_window = None

        if self.lw_linking_window:
            self.lw_linking_window.close()
            self.lw_linking_window = None

    def cleanup_rb_gallery(self):
        """Delete all files in the rb_gallery folder."""
        if self.file_controller:
            self.file_controller.cleanup_rb_gallery()

    def closeEvent(self, event):
        """Handle application close event."""
        # Close any open windows but keep generated data on disk
        self.cleanup_windows(clear_rb_gallery=False)
        super().closeEvent(event)


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)

    # Set the application style based on operating system
    system = platform.system()
    available_styles = QtWidgets.QStyleFactory.keys()
    
    if system == "Darwin":  # macOS
        # Don't set a style - let Qt use native macOS styling
        pass
    elif system == "Windows":
        if "Windows" in available_styles:
            app.setStyle(QtWidgets.QStyleFactory.create("Windows"))
        else:
            app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    else:
        # Linux or other
        app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))

    # Create and show the main controller
    controller = ParticleTrackingAppController()
    controller.show()

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
