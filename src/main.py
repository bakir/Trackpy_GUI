"""
Main Application Controller with Project Management

Description: Main application controller that manages the start screen and project-based workflow.
             Handles switching between start screen and main application windows.
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6 import QtWidgets
from src.widgets.StartScreen import StartScreen
from src.widgets.ParticleDetectionWindow import ParticleDetectionWindow
from src.widgets.TrajectoryLinkingWindow import TrajectoryLinkingWindow
from src.project_manager import ProjectManager
from src.file_controller import FileController
from src.config_manager import ConfigManager


class ParticleTrackingAppController(QMainWindow):
    """Main application controller that manages project workflow and window switching."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Particle Tracking GUI")

        # Initialize configuration and managers
        self.project_config = None  # Will be set when project is loaded
        self.project_manager = ProjectManager()
        self.file_controller = None  # Will be initialized when project is loaded

        # Initialize windows
        self.start_screen = None
        self.particle_detection_window = None
        self.trajectory_linking_window = None

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
        self.start_screen = StartScreen()
        self.start_screen.project_selected.connect(self.on_project_selected)

        # Add to stacked widget
        self.stacked_widget.addWidget(self.start_screen)
        self.stacked_widget.setCurrentWidget(self.start_screen)

        # Resize the main window to fit the start screen
        self.resize(600, 400)

    def on_project_selected(self, project_path):
        """Handle project selection from start screen."""
        # Load the project
        if self.project_manager.load_project(project_path):
            # Initialize project-specific config and file controller
            project_config_path = os.path.join(project_path, "config.ini")
            self.project_config = ConfigManager(project_config_path)
            self.file_controller = FileController(self.project_config, project_path)

            # Set file controller in particle processing module
            from src import particle_processing

            particle_processing.set_file_controller(self.file_controller)

            # Start the main application workflow
            self.show_particle_detection_window()

            # Check for existing frames
            num_frames = self.file_controller.get_total_frames_count()
            if num_frames > 0:
                self.particle_detection_window.load_existing_frames(num_frames)
        else:
            print(f"Failed to load project: {project_path}")

    def show_particle_detection_window(self):
        """Show the particle detection window and hide others."""
        # Clean up any existing windows
        self.cleanup_windows(clear_rb_gallery=False)

        # Create particle detection window
        self.particle_detection_window = ParticleDetectionWindow()
        self.particle_detection_window.set_config_manager(self.project_config)
        self.particle_detection_window.set_file_controller(self.file_controller)

        # Connect signals from particle detection window
        self.particle_detection_window.main_layout.right_panel.openTrajectoryLinking.connect(
            self.on_next_to_trajectory_linking
        )

        # Add to stacked widget
        self.stacked_widget.addWidget(self.particle_detection_window)
        self.stacked_widget.setCurrentWidget(self.particle_detection_window)

        # Resize the main window to fit the detection window
        self.resize(1200, 500)

    def show_trajectory_linking_window(self):
        """Show the trajectory linking window and hide others."""
        # Clean up any existing windows
        self.cleanup_windows(clear_rb_gallery=False)

        # Create trajectory linking window
        self.trajectory_linking_window = TrajectoryLinkingWindow()
        self.trajectory_linking_window.set_config_manager(self.project_config)
        self.trajectory_linking_window.set_file_controller(self.file_controller)

        # Connect signals from trajectory linking window
        self.trajectory_linking_window.main_layout.right_panel.goBackToDetection.connect(
            self.on_back_to_particle_detection
        )

        # Add to stacked widget
        self.stacked_widget.addWidget(self.trajectory_linking_window)
        self.stacked_widget.setCurrentWidget(self.trajectory_linking_window)

        # Resize the main window to fit the linking window
        self.resize(1200, 500)

    def on_next_to_trajectory_linking(self):
        """Handle signal to switch from particle detection to trajectory linking."""
        # The particle detection window will handle the "Next" button logic
        # (detecting particles in all frames), then we switch windows
        self.show_trajectory_linking_window()

    def on_back_to_particle_detection(self):
        """Handle signal to switch from trajectory linking back to particle detection."""
        self.show_particle_detection_window()

    def cleanup_windows(self, clear_rb_gallery: bool = True):
        """Clean up existing windows and optionally RB gallery."""
        if clear_rb_gallery:
            self.cleanup_rb_gallery()

        # Close existing windows
        if self.particle_detection_window:
            self.particle_detection_window.close()
            self.particle_detection_window = None

        if self.trajectory_linking_window:
            self.trajectory_linking_window.close()
            self.trajectory_linking_window = None

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

    # Set the application style
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))

    # Create and show the main controller
    controller = ParticleTrackingAppController()
    controller.show()


    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
