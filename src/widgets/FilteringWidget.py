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
        super().__init__(parent)
        self.setWindowTitle("Filter Creator")
        self.setModal(True)
        self.resize(400, 200)
        self.available_parameters = available_parameters
        self.created_filter = None
        layout = QVBoxLayout(self)
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("Parameter:"))
        self.parameter_combo = QComboBox()
        self.parameter_combo.addItems(available_parameters)
        param_layout.addWidget(self.parameter_combo)
        layout.addLayout(param_layout)
        operator_layout = QHBoxLayout()
        operator_layout.addWidget(QLabel("Operator:"))
        self.operator_combo = QComboBox()
        self.operator_combo.addItems(["<", "<=", ">", ">=", "==", "!="])
        operator_layout.addWidget(self.operator_combo)
        layout.addLayout(operator_layout)
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Enter numeric value")
        value_layout.addWidget(self.value_input)
        layout.addLayout(value_layout)
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create Filter")
        self.create_button.clicked.connect(self.create_filter)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def create_filter(self):
        parameter = self.parameter_combo.currentText()
        operator = self.operator_combo.currentText()
        try:
            value = float(self.value_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Value", "Please enter a valid numeric value.")
            return
        self.created_filter = Filter(parameter=parameter, operator=operator, value=value)
        self.accept()


class FilterCard(QFrame):
    """Widget representing a single filter card."""

    def __init__(self, filter_obj: Filter, on_delete: Callable, parent=None):
        super().__init__(parent)
        self.filter_obj = filter_obj
        self.on_delete = on_delete
        self.setFrameStyle(QFrame.Box)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        filter_text = f"{filter_obj.parameter} {filter_obj.operator} {filter_obj.value}"
        label = QLabel(filter_text)
        label_font = QFont()
        label_font.setBold(True)
        label.setFont(label_font)
        layout.addWidget(label)
        delete_button = QPushButton("×")
        delete_button.setFixedSize(24, 24)
        delete_button.clicked.connect(lambda: self.on_delete(filter_obj.filter_id))
        layout.addWidget(delete_button)


class FilteringWidget(QWidget):
    """Widget for managing particle data filters."""
    filteredParticlesUpdated = Signal()

    def __init__(self, source_data_file: str = "all_particles.csv", parent=None):
        super().__init__(parent)
        self.project_path = None
        self.filters: List[Filter] = []
        self.file_controller = None
        self.source_data_file = source_data_file
        self.available_parameters = ["mass", "size", "ecc", "x", "y", "frame", "signal", "raw_mass", "ep"]
        self.setup_ui()

    def set_file_controller(self, file_controller):
        self.file_controller = file_controller
        if file_controller:
            self.project_path = file_controller.project_path
            self.load_filters_from_disk()
            self.update_available_parameters()
    
    def set_source_data_file(self, filename: str):
        """Set the source data file to filter (e.g., 'all_particles.csv')."""
        self.source_data_file = filename

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        title = QLabel("Particle Filters")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)
        
        add_button = QPushButton("+ Add Filter")
        add_button.clicked.connect(self.open_filter_creator)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        layout.addLayout(button_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        self.cards_layout.setSpacing(5)
        self.cards_layout.addStretch()
        scroll_area.setWidget(self.cards_container)
        layout.addWidget(scroll_area)
        self.status_label = QLabel("No filters active")
        status_font = QFont()
        status_font.setItalic(True)
        self.status_label.setFont(status_font)
        layout.addWidget(self.status_label)

    def update_available_parameters(self):
        if not self.file_controller:
            return
        try:
            data = self.file_controller.load_particles_data("all_particles.csv")
            if not data.empty:
                numeric_cols = data.select_dtypes(include=["number"]).columns.tolist()
                if numeric_cols:
                    self.available_parameters = numeric_cols
                else:
                    self.available_parameters = [] # No numeric columns found
            else:
                self.available_parameters = [] # Empty DataFrame
        except pd.errors.EmptyDataError:
            self.available_parameters = [] # Handle empty file
            print(f"Error updating available parameters: No columns to parse from file (empty data).")
        except Exception as e:
            print(f"Error updating available parameters: {e}")

    def open_filter_creator(self):
        self.update_available_parameters()
        if not self.available_parameters:
            QMessageBox.warning(self, "No Parameters Available", "No numeric parameters found. Please load particle data first.")
            return
        dialog = FilterCreatorDialog(self.available_parameters, self)
        if dialog.exec() == QDialog.Accepted and dialog.created_filter:
            self.add_filter(dialog.created_filter)

    def add_filter(self, filter_obj: Filter):
        self.filters.append(filter_obj)
        self.update_filter_cards_ui()
        self.save_filters_to_disk()
        self.apply_filters_and_notify()

    def remove_filter(self, filter_id: str):
        self.filters = [f for f in self.filters if f.filter_id != filter_id]
        self.update_filter_cards_ui()
        self.save_filters_to_disk()
        self.apply_filters_and_notify()

    def update_filter_cards_ui(self):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for filter_obj in self.filters:
            card = FilterCard(filter_obj, self.remove_filter, self)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        self.status_label.setText(f"{len(self.filters)} filter(s) active" if self.filters else "No filters active")

    def get_filters_ini_path(self) -> str:
        """Get the path to the filters.ini file in the project root."""
        if not self.project_path:
            return None
        return os.path.join(self.project_path, "filters.ini")

    def save_filters_to_disk(self):
        ini_path = self.get_filters_ini_path()
        if not ini_path:
            return
        config = configparser.ConfigParser()
        # Create a single section for all filters
        config['filters'] = {}
        for filter_obj in self.filters:
            # Storing as a list of strings, e.g., "mass,>,100.0"
            value_str = f"{filter_obj.parameter},{filter_obj.operator},{filter_obj.value}"
            config['filters'][filter_obj.filter_id] = value_str
        
        try:
            with open(ini_path, "w") as f:
                config.write(f)
        except Exception as e:
            print(f"Error saving filters to disk: {e}")

    def load_filters_from_disk(self):
        ini_path = self.get_filters_ini_path()
        if not ini_path or not os.path.exists(ini_path):
            self.filters = []
            self.update_filter_cards_ui()
            self.apply_filters_and_notify()  # Apply filters after loading (even if empty)
            return
        
        config = configparser.ConfigParser()
        try:
            config.read(ini_path)
            self.filters = []
            if 'filters' in config:
                for filter_id, value_str in config['filters'].items():
                    parts = value_str.split(',')
                    if len(parts) == 3:
                        param, op, val = parts
                        filter_obj = Filter(
                            parameter=param,
                            operator=op,
                            value=float(val),
                            filter_id=filter_id
                        )
                        self.filters.append(filter_obj)
            self.update_filter_cards_ui()
            self.apply_filters_and_notify()  # Apply filters after loading
        except Exception as e:
            print(f"Error loading filters from disk: {e}")

    def apply_filters_and_notify(self):
        self.apply_filters()
        self.filteredParticlesUpdated.emit()

    def apply_filters(self) -> Optional[pd.DataFrame]:
        if not self.file_controller:
            print("File controller not set")
            return None
        try:
            data = self.file_controller.load_particles_data("all_particles.csv")
            if data.empty:
                filtered_data = pd.DataFrame()
            else:
                filtered_data = apply_filters(data, self.filters)
            
            output_path = os.path.join(self.file_controller.data_folder, "filtered_particles.csv")
            filtered_data.to_csv(output_path, index=False)
            
            original_count = len(data) if not data.empty else 0
            print(f"Saved filtered data to: {output_path}")
            print(f"  Original: {original_count} particles")
            print(f"  Filtered: {len(filtered_data)} particles")
            return filtered_data
        except Exception as e:
            print(f"Error applying filters: {e}")
            return None

def apply_filters(df: pd.DataFrame, filters: List[Filter]) -> pd.DataFrame:
    if not filters:
        return df.copy()
    filtered_df = df.copy()
    for filter_obj in filters:
        parameter = filter_obj.parameter
        operator = filter_obj.operator
        value = filter_obj.value
        if parameter not in filtered_df.columns:
            print(f"Warning: Parameter '{parameter}' not found in data. Skipping filter.")
            continue
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
