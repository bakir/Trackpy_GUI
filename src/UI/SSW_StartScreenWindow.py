"""
Start Screen Widget

Description: Main start screen with project management options.
             Allows users to create new projects or open existing ones.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon
import os
from ..utils.ProjectManager import ProjectManager


class SSWStartScreenWindow(QWidget):
    """Main start screen widget for project management."""

    project_selected = Signal(
        str
    )  # Emits project path when project is selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_manager = ProjectManager()
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_label = QLabel("Particle Tracking GUI")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel(
            "Select a project to begin particle tracking analysis"
        )
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)

        # Project management section
        project_frame = QWidget()
        project_layout = QVBoxLayout(project_frame)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        # New Project button
        self.new_project_btn = QPushButton("Create New Project")
        self.new_project_btn.setMinimumHeight(50)
        self.new_project_btn.clicked.connect(self.create_new_project)
        button_layout.addWidget(self.new_project_btn)

        # Open Project button
        self.open_project_btn = QPushButton("Open Existing Project")
        self.open_project_btn.setMinimumHeight(50)
        self.open_project_btn.clicked.connect(self.open_existing_project)
        button_layout.addWidget(self.open_project_btn)

        project_layout.addLayout(button_layout)
        main_layout.addWidget(project_frame)

        # Add some stretch to center everything
        main_layout.addStretch()

    def create_new_project(self):
        """Open dialog to create a new project."""
        from .NPW_NewProjectWindow import NPWNewProjectWindow

        dialog = NPWNewProjectWindow(parent=self.window())
        if dialog.exec() == NPWNewProjectWindow.Accepted:
            project_path = dialog.get_project_path()
            project_name = dialog.get_project_name()
            movie_taker = dialog.get_movie_taker()
            person_doing_analysis = dialog.get_person_doing_analysis()
            video_path = dialog.get_video_path()
            scaling = dialog.get_scaling()
            movie_taken_date = dialog.get_movie_taken_date()

            if self.project_manager.create_new_project(
                project_path,
                project_name,
                movie_taker=movie_taker,
                person_doing_analysis=person_doing_analysis,
                video_path=video_path,
                scaling=scaling,
                movie_taken_date=movie_taken_date,
            ):
                self.project_selected.emit(project_path)
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to create project. Please check the folder path and try again.",
                )

    def open_existing_project(self):
        """Open dialog to select an existing project."""
        project_folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if project_folder:
            # Check if it's a valid project folder
            config_path = os.path.join(project_folder, "config.ini")
            if os.path.exists(config_path):
                if self.project_manager.load_project(project_folder):
                    self.project_selected.emit(project_folder)
                else:
                    QMessageBox.critical(
                        self,
                        "Error",
                        "Failed to load project. Please check the project folder.",
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Project",
                    "The selected folder does not appear to be a valid project folder.\n\nA project folder should contain a 'config.ini' file.",
                )
