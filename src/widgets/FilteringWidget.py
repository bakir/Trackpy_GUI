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
    QApplication,
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


@dataclass
class CompoundFilter:
    """Data class representing a compound filter with two filters and an operator."""
    filter1: Filter
    filter2: Filter
    operator: str  # "AND", "OR", "XOR"
    filter_id: str = None  # Unique ID for this compound filter

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


class CompoundFilterCreatorDialog(QDialog):
    """Dialog for creating a compound filter with two filters and an operator."""

    def __init__(self, available_parameters: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compound Filter Creator")
        self.setModal(True)
        self.resize(500, 350)
        self.available_parameters = available_parameters
        self.created_compound_filter = None

        layout = QVBoxLayout(self)
        
        # Filter 1
        filter1_label = QLabel("Filter 1:")
        filter1_label_font = QFont()
        filter1_label_font.setBold(True)
        filter1_label.setFont(filter1_label_font)
        layout.addWidget(filter1_label)
        
        param1_layout = QHBoxLayout()
        param1_layout.addWidget(QLabel("Parameter:"))
        self.parameter1_combo = QComboBox()
        self.parameter1_combo.addItems(available_parameters)
        param1_layout.addWidget(self.parameter1_combo)
        layout.addLayout(param1_layout)

        operator1_layout = QHBoxLayout()
        operator1_layout.addWidget(QLabel("Operator:"))
        self.operator1_combo = QComboBox()
        self.operator1_combo.addItems(["<", "<=", ">", ">=", "==", "!="])
        operator1_layout.addWidget(self.operator1_combo)
        layout.addLayout(operator1_layout)

        value1_layout = QHBoxLayout()
        value1_layout.addWidget(QLabel("Value:"))
        self.value1_input = QLineEdit()
        self.value1_input.setPlaceholderText("Enter numeric value")
        value1_layout.addWidget(self.value1_input)
        layout.addLayout(value1_layout)
        
        # Operator between filters
        op_label = QLabel("Compound Operator:")
        op_label_font = QFont()
        op_label_font.setBold(True)
        op_label.setFont(op_label_font)
        layout.addWidget(op_label)
        
        compound_op_layout = QHBoxLayout()
        self.compound_operator_combo = QComboBox()
        self.compound_operator_combo.addItems(["AND", "OR", "XOR"])
        compound_op_layout.addWidget(self.compound_operator_combo)
        layout.addLayout(compound_op_layout)
        
        # Filter 2
        filter2_label = QLabel("Filter 2:")
        filter2_label_font = QFont()
        filter2_label_font.setBold(True)
        filter2_label.setFont(filter2_label_font)
        layout.addWidget(filter2_label)
        
        param2_layout = QHBoxLayout()
        param2_layout.addWidget(QLabel("Parameter:"))
        self.parameter2_combo = QComboBox()
        self.parameter2_combo.addItems(available_parameters)
        param2_layout.addWidget(self.parameter2_combo)
        layout.addLayout(param2_layout)

        operator2_layout = QHBoxLayout()
        operator2_layout.addWidget(QLabel("Operator:"))
        self.operator2_combo = QComboBox()
        self.operator2_combo.addItems(["<", "<=", ">", ">=", "==", "!="])
        operator2_layout.addWidget(self.operator2_combo)
        layout.addLayout(operator2_layout)

        value2_layout = QHBoxLayout()
        value2_layout.addWidget(QLabel("Value:"))
        self.value2_input = QLineEdit()
        self.value2_input.setPlaceholderText("Enter numeric value")
        value2_layout.addWidget(self.value2_input)
        layout.addLayout(value2_layout)

        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create Compound Filter")
        self.create_button.clicked.connect(self.create_compound_filter)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def create_compound_filter(self):
        try:
            value1 = float(self.value1_input.text())
            value2 = float(self.value2_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Value", "Please enter valid numeric values for both filters.")
            return
        
        filter1 = Filter(
            parameter=self.parameter1_combo.currentText(),
            operator=self.operator1_combo.currentText(),
            value=value1
        )
        filter2 = Filter(
            parameter=self.parameter2_combo.currentText(),
            operator=self.operator2_combo.currentText(),
            value=value2
        )
        
        compound_operator = self.compound_operator_combo.currentText()
        self.created_compound_filter = CompoundFilter(
            filter1=filter1,
            filter2=filter2,
            operator=compound_operator
        )
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


class CompoundFilterCard(QFrame):
    """Widget representing a compound filter card."""

    def __init__(self, compound_filter_obj: CompoundFilter, on_delete: Callable, parent=None):
        super().__init__(parent)
        self.compound_filter_obj = compound_filter_obj
        self.on_delete = on_delete
        self.setFrameStyle(QFrame.Box)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        f1 = compound_filter_obj.filter1
        f2 = compound_filter_obj.filter2
        filter_text = f"({f1.parameter} {f1.operator} {f1.value}) {compound_filter_obj.operator} ({f2.parameter} {f2.operator} {f2.value})"
        label = QLabel(filter_text)
        label_font = QFont()
        label_font.setBold(True)
        label.setFont(label_font)
        layout.addWidget(label)
        delete_button = QPushButton("×")
        delete_button.setFixedSize(24, 24)
        delete_button.clicked.connect(lambda: self.on_delete(compound_filter_obj.filter_id))
        layout.addWidget(delete_button)


class FilteringWidget(QWidget):
    """Widget for managing particle data filters."""
    filteredParticlesUpdated = Signal()

    def __init__(self, source_data_file: str = "all_particles.csv", parent=None):
        super().__init__(parent)
        self.project_path = None
        self.filters: List[Filter] = []
        self.compound_filters: List[CompoundFilter] = []
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
        # Use appropriate title based on source data file
        if self.source_data_file == "all_trajectories.csv" or self.source_data_file == "trajectories.csv":
            title_text = "Trajectory Filters"
        else:
            title_text = "Particle Filters"
        title = QLabel(title_text)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)
        
        add_button = QPushButton("+ Add Filter")
        add_button.clicked.connect(self.open_filter_creator)
        
        add_compound_button = QPushButton("+ Add Compound Filter")
        add_compound_button.clicked.connect(self.open_compound_filter_creator)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(add_compound_button)
        layout.addLayout(button_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # Set height based on screen size - use 50% of screen height for longer list
        screen = QApplication.primaryScreen()
        if screen:
            screen_height = screen.availableGeometry().height()
            scroll_area.setMaximumHeight(int(screen_height * 0.5))
        else:
            # Fallback if screen not available
            scroll_area.setMaximumHeight(600)

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

        self.particle_labels = QWidget()
        self.particle_labels_layout = QVBoxLayout(self.particle_labels)
        self.total_particles_label = QLabel()
        self.particles_after_filter_label = QLabel()
        self.particle_labels_layout.addWidget(self.total_particles_label)
        self.particle_labels_layout.addWidget(self.particles_after_filter_label)
        layout.addWidget(self.particle_labels)

    def update_available_parameters(self):
        if not self.file_controller:
            return
        try:
            # Use source_data_file to determine which file to load
            if self.source_data_file == "all_trajectories.csv" or self.source_data_file == "trajectories.csv":
                data = self.file_controller.load_trajectories_data(self.source_data_file)
            else:
                data = self.file_controller.load_particles_data(self.source_data_file)
            
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
    
    def open_compound_filter_creator(self):
        self.update_available_parameters()
        if not self.available_parameters:
            QMessageBox.warning(self, "No Parameters Available", "No numeric parameters found. Please load particle data first.")
            return
        dialog = CompoundFilterCreatorDialog(self.available_parameters, self)
        if dialog.exec() == QDialog.Accepted and dialog.created_compound_filter:
            self.add_compound_filter(dialog.created_compound_filter)

    def add_filter(self, filter_obj: Filter):
        self.filters.append(filter_obj)
        self.update_filter_cards_ui()
        self.save_filters_to_disk()
        self.apply_filters_and_notify()
    
    def add_compound_filter(self, compound_filter_obj: CompoundFilter):
        self.compound_filters.append(compound_filter_obj)
        self.update_filter_cards_ui()
        self.save_filters_to_disk()
        self.apply_filters_and_notify()

    def remove_filter(self, filter_id: str):
        self.filters = [f for f in self.filters if f.filter_id != filter_id]
        self.update_filter_cards_ui()
        self.save_filters_to_disk()
        self.apply_filters_and_notify()
    
    def remove_compound_filter(self, filter_id: str):
        self.compound_filters = [f for f in self.compound_filters if f.filter_id != filter_id]
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
        for compound_filter_obj in self.compound_filters:
            card = CompoundFilterCard(compound_filter_obj, self.remove_compound_filter, self)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        total_filters = len(self.filters) + len(self.compound_filters)
        self.status_label.setText(f"{total_filters} filter(s) active" if total_filters > 0 else "No filters active")

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
        # Create sections for filters and compound filters
        config['filters'] = {}
        for filter_obj in self.filters:
            # Storing as a list of strings, e.g., "mass,>,100.0"
            value_str = f"{filter_obj.parameter},{filter_obj.operator},{filter_obj.value}"
            config['filters'][filter_obj.filter_id] = value_str
        
        config['compound_filters'] = {}
        for compound_filter_obj in self.compound_filters:
            f1 = compound_filter_obj.filter1
            f2 = compound_filter_obj.filter2
            # Store as: "param1,op1,val1|param2,op2,val2|operator"
            value_str = f"{f1.parameter},{f1.operator},{f1.value}|{f2.parameter},{f2.operator},{f2.value}|{compound_filter_obj.operator}"
            config['compound_filters'][compound_filter_obj.filter_id] = value_str
        
        try:
            with open(ini_path, "w") as f:
                config.write(f)
        except Exception as e:
            print(f"Error saving filters to disk: {e}")

    def load_filters_from_disk(self):
        ini_path = self.get_filters_ini_path()
        if not ini_path or not os.path.exists(ini_path):
            self.filters = []
            self.compound_filters = []
            self.update_filter_cards_ui()
            self.apply_filters_and_notify()  # Apply filters after loading (even if empty)
            return
        
        config = configparser.ConfigParser()
        try:
            config.read(ini_path)
            self.filters = []
            self.compound_filters = []
            
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
            
            if 'compound_filters' in config:
                for compound_filter_id, value_str in config['compound_filters'].items():
                    parts = value_str.split('|')
                    if len(parts) == 3:
                        filter1_str, filter2_str, compound_op = parts
                        f1_parts = filter1_str.split(',')
                        f2_parts = filter2_str.split(',')
                        if len(f1_parts) == 3 and len(f2_parts) == 3:
                            f1 = Filter(
                                parameter=f1_parts[0],
                                operator=f1_parts[1],
                                value=float(f1_parts[2])
                            )
                            f2 = Filter(
                                parameter=f2_parts[0],
                                operator=f2_parts[1],
                                value=float(f2_parts[2])
                            )
                            compound_filter_obj = CompoundFilter(
                                filter1=f1,
                                filter2=f2,
                                operator=compound_op,
                                filter_id=compound_filter_id
                            )
                            self.compound_filters.append(compound_filter_obj)
            
            self.update_filter_cards_ui()
            self.apply_filters_and_notify()  # Apply filters after loading
        except Exception as e:
            print(f"Error loading filters from disk: {e}")

    def apply_filters_and_notify(self):
        self.apply_filters()
        self.filteredParticlesUpdated.emit()

    def update_particle_labels(self, all_particle_count, filtered_particle_count):
        self.total_particles_label.setText(f"Particles Found: {all_particle_count}")
        self.particles_after_filter_label.setText(f"Particles After Filter(s): {filtered_particle_count}")


    def apply_filters(self) -> Optional[pd.DataFrame]:
        if not self.file_controller:
            print("File controller not set")
            return None
        # try:
        # Use source_data_file to determine which file to load
        # For trajectories, use load_trajectories_data, for particles use load_particles_data
        if self.source_data_file == "all_trajectories.csv" or self.source_data_file == "trajectories.csv":
            data = self.file_controller.load_trajectories_data(self.source_data_file)
            output_filename = "trajectories.csv"  # Save filtered trajectories to trajectories.csv
        else:
            # Default to particles
            data = self.file_controller.load_particles_data(self.source_data_file)
            output_filename = "filtered_particles.csv"
        
        if data.empty:
            filtered_data = pd.DataFrame()
        else:
            filtered_data = apply_filters(data, self.filters, self.compound_filters)
        
        output_path = os.path.join(self.file_controller.data_folder, output_filename)
        filtered_data.to_csv(output_path, index=False)
        
        original_count = len(data) if not data.empty else 0
        print(f"Saved filtered data to: {output_path}")
        print(f"  Original: {original_count} particles")
        print(f"  Filtered: {len(filtered_data)} particles")
        self.update_particle_labels(original_count, len(filtered_data))
        return filtered_data
        # except Exception as e:
        #     print(f"Error applying filters: {e}")
        #     return None

def apply_single_filter(df: pd.DataFrame, filter_obj: Filter) -> pd.Series:
    """Apply a single filter and return a boolean mask."""
    parameter = filter_obj.parameter
    operator = filter_obj.operator
    value = filter_obj.value
    if parameter not in df.columns:
        print(f"Warning: Parameter '{parameter}' not found in data. Skipping filter.")
        return pd.Series([False] * len(df), index=df.index)
    try:
        if operator == "<":
            return df[parameter] < value
        elif operator == "<=":
            return df[parameter] <= value
        elif operator == ">":
            return df[parameter] > value
        elif operator == ">=":
            return df[parameter] >= value
        elif operator == "==":
            return df[parameter] == value
        elif operator == "!=":
            return df[parameter] != value
        else:
            print(f"Warning: Unknown operator '{operator}'. Skipping filter.")
            return pd.Series([False] * len(df), index=df.index)
    except Exception as e:
        print(f"Error applying filter {parameter} {operator} {value}: {e}")
        return pd.Series([False] * len(df), index=df.index)

def apply_filters(df: pd.DataFrame, filters: List[Filter], compound_filters: List[CompoundFilter] = None) -> pd.DataFrame:
    if not filters and (not compound_filters or len(compound_filters) == 0):
        return df.copy()
    filtered_df = df.copy()
    
    # Apply simple filters (all are ANDed together)
    for filter_obj in filters:
        mask = apply_single_filter(filtered_df, filter_obj)
        filtered_df = filtered_df[mask]
    
    # Apply compound filters (each compound filter is applied independently, ANDed with previous results)
    if compound_filters:
        for compound_filter_obj in compound_filters:
            mask1 = apply_single_filter(filtered_df, compound_filter_obj.filter1)
            mask2 = apply_single_filter(filtered_df, compound_filter_obj.filter2)
            
            if compound_filter_obj.operator == "AND":
                combined_mask = mask1 & mask2
            elif compound_filter_obj.operator == "OR":
                combined_mask = mask1 | mask2
            elif compound_filter_obj.operator == "XOR":
                combined_mask = mask1 ^ mask2
            else:
                print(f"Warning: Unknown compound operator '{compound_filter_obj.operator}'. Skipping compound filter.")
                continue
            
            filtered_df = filtered_df[combined_mask]
    
    return filtered_df
