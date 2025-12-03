"""
Filtering Widget Module

Description: Interactive UI for defining filters on particle data and automatically
             generating filtered_particles.csv whenever filters are changed.
"""

import os
import configparser
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Callable
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QDialog,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


@dataclass
class Filter:
    """Data class representing a single filter."""
    parameter: str
    operator: str
    value: float
    filter_id: str = None  # Unique ID for this filter

    def __post_init__(self):
        if self.filter_id is None:
            import uuid
            self.filter_id = str(uuid.uuid4())[:8]


class FilterCreatorDialog(QDialog):
    """Dialog for creating a new filter."""

    def __init__(self, available_parameters: List[str], parent=None):
        """
        Initialize the filter creator dialog.

        Parameters
        ----------
        available_parameters : List[str]
            List of available parameter names to filter on
        parent : QWidget, optional
            Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Filter Creator")
        self.setModal(True)
        self.resize(400, 200)

        self.available_parameters = available_parameters
        self.created_filter = None  # Will be set if filter is created

        # Main layout
        layout = QVBoxLayout(self)

        # Parameter selection
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("Parameter:"))
        self.parameter_combo = QComboBox()
        self.parameter_combo.addItems(available_parameters)
        param_layout.addWidget(self.parameter_combo)
        layout.addLayout(param_layout)

        # Operator selection
        operator_layout = QHBoxLayout()
        operator_layout.addWidget(QLabel("Operator:"))
        self.operator_combo = QComboBox()
        self.operator_combo.addItems(["<", "<=", ">", ">=", "==", "!="])
        operator_layout.addWidget(self.operator_combo)
        layout.addLayout(operator_layout)

        # Value input
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Enter numeric value")
        value_layout.addWidget(self.value_input)
        layout.addLayout(value_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create Filter")
        self.create_button.clicked.connect(self.create_filter)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def create_filter(self):
        """Validate and create the filter."""
        parameter = self.parameter_combo.currentText()
        operator = self.operator_combo.currentText()

        # Validate value
        try:
            value = float(self.value_input.text())
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Value", "Please enter a valid numeric value."
            )
            return

        # Create filter
        self.created_filter = Filter(
            parameter=parameter, operator=operator, value=value
        )
        self.accept()


class FilterCard(QFrame):
    """Widget representing a single filter card."""

    def __init__(self, filter_obj: Filter, on_delete: Callable, parent=None):
        """
        Initialize a filter card.

        Parameters
        ----------
        filter_obj : Filter
            The filter object to display
        on_delete : Callable
            Callback function when delete button is clicked
        parent : QWidget, optional
            Parent widget
        """
        super().__init__(parent)
        self.filter_obj = filter_obj
        self.on_delete = on_delete

        # Set card style
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(
            """
            QFrame {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f5f5f5;
                padding: 5px;
            }
        """
        )

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Filter text
        filter_text = f"{filter_obj.parameter} {filter_obj.operator} {filter_obj.value}"
        label = QLabel(filter_text)
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        # Delete button
        delete_button = QPushButton("×")
        delete_button.setFixedSize(24, 24)
        delete_button.setStyleSheet(
            """
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """
        )
        delete_button.clicked.connect(lambda: self.on_delete(filter_obj.filter_id))
        layout.addWidget(delete_button)


class FilteringWidget(QWidget):
    """Widget for managing particle data filters."""

    def __init__(self, project_path: str = None, parent=None):
        """
        Initialize the filtering widget.

        Parameters
        ----------
        project_path : str, optional
            Path to the project directory
        parent : QWidget, optional
            Parent widget
        """
        super().__init__(parent)
        self.project_path = project_path
        self.filters: List[Filter] = []
        self.file_controller = None
        self.source_data_file = "all_particles.csv"  # Default source file

        # Available parameters (will be updated based on actual data)
        self.available_parameters = [
            "mass",
            "size",
            "ecc",
            "x",
            "y",
            "frame",
            "signal",
            "raw_mass",
            "ep",
        ]

        self.setup_ui()
        self.load_filters_from_disk()

    def set_file_controller(self, file_controller):
        """Set the file controller for data access."""
        self.file_controller = file_controller
        if file_controller and hasattr(file_controller, "project_path") and file_controller.project_path:
            self.project_path = file_controller.project_path
            # Reload filters when file controller is set
            self.load_filters_from_disk()
        # Update available parameters based on actual data
        self.update_available_parameters()

    def set_project_path(self, project_path: str):
        """Set the project path."""
        self.project_path = project_path
        self.load_filters_from_disk()

    def set_source_data_file(self, filename: str):
        """Set the source data file to filter (e.g., 'all_particles.csv')."""
        self.source_data_file = filename

    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Title
        title = QLabel("Particle Filters")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)

        # Add filter button
        add_button = QPushButton("+ Add Filter")
        add_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        add_button.clicked.connect(self.open_filter_creator)
        layout.addWidget(add_button)

        # Scroll area for filter cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        scroll_area.setStyleSheet("QScrollArea { border: 1px solid #ddd; }")

        # Container for filter cards
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        self.cards_layout.setSpacing(5)
        self.cards_layout.addStretch()

        scroll_area.setWidget(self.cards_container)
        layout.addWidget(scroll_area)

        # Status label
        self.status_label = QLabel("No filters active")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)

    def update_available_parameters(self):
        """Update available parameters based on actual data columns."""
        if not self.file_controller:
            return

        try:
            # Try to load the source data to get column names
            if self.source_data_file == "trajectories.csv":
                data = self.file_controller.load_trajectories_data(self.source_data_file)
            else:
                data = self.file_controller.load_particles_data(self.source_data_file)
            if not data.empty:
                # Get numeric columns only
                numeric_cols = data.select_dtypes(include=["number"]).columns.tolist()
                if numeric_cols:
                    self.available_parameters = numeric_cols
        except Exception as e:
            print(f"Error updating available parameters: {e}")

    def open_filter_creator(self):
        """Open the filter creator dialog."""
        # Update available parameters first
        self.update_available_parameters()

        if not self.available_parameters:
            QMessageBox.warning(
                self,
                "No Parameters Available",
                "No numeric parameters found in the data. Please load particle data first.",
            )
            return

        dialog = FilterCreatorDialog(self.available_parameters, self)
        if dialog.exec() == QDialog.Accepted and dialog.created_filter:
            self.add_filter(dialog.created_filter)

    def add_filter(self, filter_obj: Filter):
        """Add a filter to the list and update UI."""
        self.filters.append(filter_obj)
        self.update_filter_cards_ui()
        self.save_filters_to_disk()
        self.apply_filters()

    def remove_filter(self, filter_id: str):
        """Remove a filter by ID."""
        self.filters = [f for f in self.filters if f.filter_id != filter_id]
        self.update_filter_cards_ui()
        self.save_filters_to_disk()
        self.apply_filters()

    def update_filter_cards_ui(self):
        """Update the filter cards display."""
        # Clear existing cards
        while self.cards_layout.count() > 1:  # Keep the stretch
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add cards for each filter
        for filter_obj in self.filters:
            card = FilterCard(filter_obj, self.remove_filter, self)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        # Update status
        if self.filters:
            self.status_label.setText(f"{len(self.filters)} filter(s) active")
        else:
            self.status_label.setText("No filters active")

    def get_filters_folder(self) -> str:
        """Get the path to the filters folder."""
        if not self.project_path:
            return None
        filters_folder = os.path.join(self.project_path, "filters")
        os.makedirs(filters_folder, exist_ok=True)
        return filters_folder

    def get_filters_ini_path(self) -> str:
        """Get the path to the filters.ini file."""
        filters_folder = self.get_filters_folder()
        if not filters_folder:
            return None
        return os.path.join(filters_folder, "filters.ini")

    def save_filters_to_disk(self):
        """Save filters to filters.ini file."""
        ini_path = self.get_filters_ini_path()
        if not ini_path:
            return

        config = configparser.ConfigParser()

        # Clear existing filters
        for i, filter_obj in enumerate(self.filters, 1):
            section_name = f"filter_{i}"
            config[section_name] = {
                "parameter": filter_obj.parameter,
                "operator": filter_obj.operator,
                "value": str(filter_obj.value),
                "filter_id": filter_obj.filter_id,
            }

        # Write to file
        try:
            with open(ini_path, "w") as f:
                config.write(f)
        except Exception as e:
            print(f"Error saving filters to disk: {e}")

    def load_filters_from_disk(self):
        """Load filters from filters.ini file."""
        ini_path = self.get_filters_ini_path()
        if not ini_path or not os.path.exists(ini_path):
            return

        config = configparser.ConfigParser()
        try:
            config.read(ini_path)
            self.filters = []

            for section_name in config.sections():
                if section_name.startswith("filter_"):
                    section = config[section_name]
                    filter_obj = Filter(
                        parameter=section.get("parameter", ""),
                        operator=section.get("operator", ""),
                        value=float(section.get("value", "0")),
                        filter_id=section.get("filter_id", None),
                    )
                    self.filters.append(filter_obj)

            self.update_filter_cards_ui()
            # Apply loaded filters
            self.apply_filters()
        except Exception as e:
            print(f"Error loading filters from disk: {e}")

    def apply_filters(self) -> Optional[pd.DataFrame]:
        """
        Apply all active filters to the particle data and save to filtered_particles.csv.

        Returns
        -------
        pd.DataFrame or None
            Filtered DataFrame, or None if error
        """
        if not self.file_controller:
            print("File controller not set")
            return None

        # Load source data - use appropriate method based on file type
        try:
            if self.source_data_file == "trajectories.csv":
                data = self.file_controller.load_trajectories_data(self.source_data_file)
            else:
                data = self.file_controller.load_particles_data(self.source_data_file)
            if data.empty:
                print(f"No data found in {self.source_data_file}")
                return None
        except Exception as e:
            print(f"Error loading source data: {e}")
            return None

        # Apply filters
        filtered_data = apply_filters(data, self.filters)

        # Save filtered data
        if filtered_data is not None:
            try:
                output_path = os.path.join(
                    self.file_controller.data_folder, "filtered_particles.csv"
                )
                filtered_data.to_csv(output_path, index=False)
                print(f"Saved filtered data to: {output_path}")
                print(f"  Original: {len(data)} particles")
                print(f"  Filtered: {len(filtered_data)} particles")
            except Exception as e:
                print(f"Error saving filtered data: {e}")

        return filtered_data


def apply_filters(df: pd.DataFrame, filters: List[Filter]) -> pd.DataFrame:
    """
    Apply a list of filters to a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame
    filters : List[Filter]
        List of Filter objects to apply

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame
    """
    if not filters:
        # If no filters, return original data (or empty if we want to require filters)
        return df.copy()

    filtered_df = df.copy()

    for filter_obj in filters:
        parameter = filter_obj.parameter
        operator = filter_obj.operator
        value = filter_obj.value

        # Check if parameter exists
        if parameter not in filtered_df.columns:
            print(f"Warning: Parameter '{parameter}' not found in data. Skipping filter.")
            continue

        # Apply filter based on operator
        try:
            if operator == "<":
                mask = filtered_df[parameter] < value
            elif operator == "<=":
                mask = filtered_df[parameter] <= value
            elif operator == ">":
                mask = filtered_df[parameter] > value
            elif operator == ">=":
                mask = filtered_df[parameter] >= value
            elif operator == "==":
                mask = filtered_df[parameter] == value
            elif operator == "!=":
                mask = filtered_df[parameter] != value
            else:
                print(f"Warning: Unknown operator '{operator}'. Skipping filter.")
                continue

            filtered_df = filtered_df[mask]
        except Exception as e:
            print(f"Error applying filter {parameter} {operator} {value}: {e}")
            continue

    return filtered_df

