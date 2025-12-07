"""
New Project Window

Description: Dialog window for creating new projects.
             Allows users to select project folder and set project name.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QFileDialog,
    QMessageBox,
    QDateEdit,
    QDoubleSpinBox,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from ..utils import SizingUtils
import os


class NPWNewProjectWindow(QDialog):
    """Dialog for creating a new project."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = None
        self.project_name = None
        self.movie_taker = ""
        self.person_doing_analysis = ""
        self.video_path = ""
        self.scaling = 1.0
        self.movie_taken_date = None
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Create New Project")
        self.setModal(True)
        
        # Set window geometry
        x_left, y_up, start_screen_width, start_screen_height = SizingUtils.get_start_screen_geometry()
        self.setGeometry(x_left, y_up, start_screen_width, start_screen_height)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_label = QLabel("Create New Project")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Project name field
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText(
            "Enter project name (e.g., 'My Particle Analysis')"
        )
        form_layout.addRow("Project Name:", self.project_name_edit)

        # Movie Taker field
        self.movie_taker_edit = QLineEdit()
        self.movie_taker_edit.setPlaceholderText(
            "Enter name of person who took the movie (optional)"
        )
        form_layout.addRow("Movie Taker:", self.movie_taker_edit)

        # Person Doing Analysis field
        self.person_doing_analysis_edit = QLineEdit()
        self.person_doing_analysis_edit.setPlaceholderText(
            "Enter name of person doing analysis (optional)"
        )
        form_layout.addRow("Person Doing Analysis:", self.person_doing_analysis_edit)

        # Movie Taken Date field
        self.movie_taken_date_edit = QDateEdit()
        self.movie_taken_date_edit.setDate(QDate.currentDate())
        self.movie_taken_date_edit.setCalendarPopup(True)
        form_layout.addRow("Movie Taken Date:", self.movie_taken_date_edit)

        # Video File selection
        video_layout = QHBoxLayout()
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("Select video file...")
        self.video_path_edit.setReadOnly(True)

        self.browse_video_btn = QPushButton("Browse...")
        self.browse_video_btn.clicked.connect(self.browse_video)

        video_layout.addWidget(self.video_path_edit)
        video_layout.addWidget(self.browse_video_btn)
        form_layout.addRow("Video File:", video_layout)

        # Scaling field
        self.scaling_edit = QDoubleSpinBox()
        self.scaling_edit.setRange(0.000001, 1000.0)
        self.scaling_edit.setDecimals(6)
        self.scaling_edit.setSingleStep(0.1)
        self.scaling_edit.setValue(1.0)
        self.scaling_edit.setToolTip("Microns per pixel (calibration).")
        form_layout.addRow("Scaling (μm/pixel):", self.scaling_edit)

        # Project folder selection
        folder_layout = QHBoxLayout()
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setPlaceholderText(
            "Select parent folder for project..."
        )
        self.folder_path_edit.setReadOnly(True)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_folder)

        folder_layout.addWidget(self.folder_path_edit)
        folder_layout.addWidget(self.browse_btn)
        form_layout.addRow("Parent Folder:", folder_layout)

        main_layout.addLayout(form_layout)

        # Info text
        info_label = QLabel(
            "A new project folder will be created inside the selected parent folder:\n"
            "• Project folder name: [Project Name]\n"
            "• Project structure:\n"
            "  - particles/ - Particle images\n"
            "  - original_frames/ - Video frames\n"
            "  - annotated_frames/ - Annotated frames\n"
            "  - rb_gallery/ - Red-blue overlays\n"
            "  - data/ - CSV and pickle files\n"
            "  - videos/ - Video files\n"
            "  - config.ini - Project configuration"
        )
        info_font = QFont()
        info_font.setPointSize(12)
        info_label.setFont(info_font)
        main_layout.addWidget(info_label)

        # Add stretch
        main_layout.addStretch()

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        # Create button
        self.create_btn = QPushButton("Create Project")
        self.create_btn.clicked.connect(self.create_project)
        self.create_btn.setEnabled(False)
        button_layout.addWidget(self.create_btn)

        main_layout.addLayout(button_layout)

        # Connect signals
        self.project_name_edit.textChanged.connect(self.validate_input)
        self.folder_path_edit.textChanged.connect(self.validate_input)
        self.video_path_edit.textChanged.connect(self.validate_input)
        self.scaling_edit.valueChanged.connect(self.validate_input)

    def browse_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if folder:
            self.folder_path_edit.setText(folder)
            # Auto-fill project name if empty
            if not self.project_name_edit.text():
                folder_name = os.path.basename(folder)
                self.project_name_edit.setText(folder_name)

    def browse_video(self):
        """Open video file selection dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.avi *.mp4 *.mov *.mkv);;All Files (*)",
        )
        if file_path:
            self.video_path_edit.setText(file_path)

    def validate_input(self):
        """Validate input fields and enable/disable create button."""
        has_name = bool(self.project_name_edit.text().strip())
        has_folder = bool(self.folder_path_edit.text().strip())
        has_video = bool(self.video_path_edit.text().strip())
        has_scaling = self.scaling_edit.value() > 0

        self.create_btn.setEnabled(has_name and has_folder and has_video and has_scaling)

    def create_project(self):
        """Create the project and accept the dialog."""
        project_name = self.project_name_edit.text().strip()
        parent_folder = self.folder_path_edit.text().strip()

        # Validate inputs
        if not project_name:
            QMessageBox.warning(
                self, "Invalid Input", "Please enter a project name."
            )
            return

        if not parent_folder:
            QMessageBox.warning(
                self, "Invalid Input", "Please select a parent folder."
            )
            return

        # Validate video file
        video_path = self.video_path_edit.text().strip()
        if not video_path:
            QMessageBox.warning(
                self, "Invalid Input", "Please select a video file."
            )
            return

        if not os.path.exists(video_path):
            QMessageBox.warning(
                self, "Invalid Video File", "The selected video file does not exist."
            )
            return

        # Validate scaling
        scaling = self.scaling_edit.value()
        if scaling <= 0:
            QMessageBox.warning(
                self, "Invalid Input", "Scaling must be greater than 0."
            )
            return

        # Check if parent folder exists and is writable
        if not os.path.exists(parent_folder):
            QMessageBox.warning(
                self, "Invalid Folder", "The selected folder does not exist."
            )
            return

        if not os.access(parent_folder, os.W_OK):
            QMessageBox.warning(
                self,
                "Permission Error",
                "You don't have write permission to the selected folder.",
            )
            return

        # Create the actual project folder path (subfolder with project name)
        # Clean the project name to be filesystem-safe
        safe_project_name = self._make_filesystem_safe(project_name)
        project_folder = os.path.join(parent_folder, safe_project_name)

        # Check if project folder already exists
        if os.path.exists(project_folder):
            reply = QMessageBox.question(
                self,
                "Project Already Exists",
                f"A project folder named '{safe_project_name}' already exists.\n\nDo you want to overwrite it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        # Set project details
        self.project_name = project_name
        self.project_path = project_folder
        self.movie_taker = self.movie_taker_edit.text().strip()
        self.person_doing_analysis = self.person_doing_analysis_edit.text().strip()
        self.video_path = video_path
        self.scaling = scaling
        self.movie_taken_date = self.movie_taken_date_edit.date().toString("yyyy-MM-dd")

        # Accept the dialog
        self.accept()

    def _make_filesystem_safe(self, name):
        """Make a project name safe for filesystem use."""
        import re

        # Replace invalid characters with underscores
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", name)
        # Remove leading/trailing spaces and dots
        safe_name = safe_name.strip(" .")
        # Ensure it's not empty
        if not safe_name:
            safe_name = "Untitled_Project"
        # Limit length
        if len(safe_name) > 50:
            safe_name = safe_name[:50]
        return safe_name

    def get_project_name(self):
        """Get the project name."""
        return self.project_name

    def get_project_path(self):
        """Get the project path."""
        return self.project_path

    def get_movie_taker(self):
        """Get the movie taker name."""
        return self.movie_taker

    def get_person_doing_analysis(self):
        """Get the person doing analysis name."""
        return self.person_doing_analysis

    def get_video_path(self):
        """Get the video file path."""
        return self.video_path

    def get_scaling(self):
        """Get the scaling value."""
        return self.scaling

    def get_movie_taken_date(self):
        """Get the movie taken date."""
        return self.movie_taken_date
