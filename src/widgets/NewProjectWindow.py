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
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import os


class NewProjectWindow(QDialog):
    """Dialog for creating a new project."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = None
        self.project_name = None
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Create New Project")
        self.setModal(True)
        self.resize(500, 300)

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
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        main_layout.addWidget(title_label)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Project name field
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText(
            "Enter project name (e.g., 'My Particle Analysis')"
        )
        self.project_name_edit.setStyleSheet(
            """
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """
        )
        form_layout.addRow("Project Name:", self.project_name_edit)

        # Project folder selection
        folder_layout = QHBoxLayout()
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setPlaceholderText(
            "Select parent folder for project..."
        )
        self.folder_path_edit.setReadOnly(True)
        self.folder_path_edit.setStyleSheet(
            """
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
                background-color: #f8f9fa;
            }
        """
        )

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """
        )
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
        info_label.setStyleSheet(
            """
            QLabel {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 15px;
                font-size: 12px;
                color: #2c3e50;
            }
        """
        )
        main_layout.addWidget(info_label)

        # Add stretch
        main_layout.addStretch()

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """
        )
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        # Create button
        self.create_btn = QPushButton("Create Project")
        self.create_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """
        )
        self.create_btn.clicked.connect(self.create_project)
        self.create_btn.setEnabled(False)
        button_layout.addWidget(self.create_btn)

        main_layout.addLayout(button_layout)

        # Connect signals
        self.project_name_edit.textChanged.connect(self.validate_input)
        self.folder_path_edit.textChanged.connect(self.validate_input)

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

    def validate_input(self):
        """Validate input fields and enable/disable create button."""
        has_name = bool(self.project_name_edit.text().strip())
        has_folder = bool(self.folder_path_edit.text().strip())

        self.create_btn.setEnabled(has_name and has_folder)

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
