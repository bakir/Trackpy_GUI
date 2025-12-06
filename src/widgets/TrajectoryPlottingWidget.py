"""
Trajectory Plotting Widget

Description: GUI widget for displaying trajectory plots, filtering plots, and 
             drift for all trajectories found.

"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import os
from copy import copy
from .. import particle_processing
import pandas as pd

from ..utils import GraphingUtils
from .FilteringWidget import FilteringWidget


class TrajectoryPlottingWidget(GraphingUtils.GraphingPanelWidget):
    filteredTrajectoriesUpdated = Signal()

    def __init__(self, parent=None):
        super(GraphingUtils.GraphingPanelWidget, self).__init__()

        self.setup_plot_display()

        # Buttons
        self.graphing_buttons = QWidget()
        self.button_layout = QHBoxLayout(self.graphing_buttons)

        # Trajectories
        self.trajectories = QWidget()
        self.trajectory_layout = QVBoxLayout(self.trajectories)
        self.trajectory_label = QLabel("Trajectories")
        self.trajectory_layout.addWidget(
            self.trajectory_label, alignment=Qt.AlignTop
        )

        self.trajectory_button = GraphingUtils.GraphingButton(
            text="Trajectories", parent=self
        )
        self.trajectory_button.clicked.connect(
            lambda: self.self_plot(
                self.get_trajectories, self.trajectory_button
            )
        )
        self.trajectory_layout.addWidget(
            self.trajectory_button, alignment=Qt.AlignTop
        )

        self.button_layout.addWidget(self.trajectories)
        self.trajectory_layout.addStretch(1)

        # Filtering
        self.filtering_buttons(self.button_layout, "trajectory")

        # Drift
        self.drift = QWidget()
        self.drift_layout = QVBoxLayout(self.drift)
        self.drift_label = QLabel("Drift")
        self.drift_layout.addWidget(self.drift_label, alignment=Qt.AlignTop)

        self.drift_button = GraphingUtils.GraphingButton(text="Drift", parent=self)
        self.drift_button.clicked.connect(
            lambda: self.self_plot(self.get_drift, self.drift_button)
        )
        self.drift_layout.addWidget(self.drift_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.drift)
        self.drift_layout.addStretch(1)

        self.layout.addWidget(self.graphing_buttons)
        
        # Add filtering widget below the graphs
        self.filtering_widget = FilteringWidget(source_data_file="trajectories.csv")
        self.filtering_widget.filteredParticlesUpdated.connect(self.filteredTrajectoriesUpdated.emit)
        self.layout.addWidget(self.filtering_widget)
        
        # Add stretch below the buttons
        self.layout.addStretch(1)

    def get_linked_particles(self, linked_particles):
        """Sets linking data and plots trajectories."""
        self.data = linked_particles
        self.self_plot(self.get_trajectories, self.trajectory_button)
    
    # def refresh_plots(self):
    #     """Reload data from all_trajectories.csv and refresh plots."""
    #     if self.file_controller:
    #         try:
    #             self.data = self.file_controller.load_trajectories_data("all_trajectories.csv")
    #             if not self.data.empty:
    #                 self.self_plot(self.get_trajectories, self.trajectory_button)
    #             else:
    #                 self.blank_plot()
    #         except pd.errors.EmptyDataError:
    #             self.data = pd.DataFrame()
    #             self.blank_plot()

    def set_file_controller(self, file_controller):
        """Override to also set file controller for filtering widget."""
        super().set_file_controller(file_controller)
        if hasattr(self, 'filtering_widget'):
            self.filtering_widget.set_file_controller(file_controller)
            if file_controller and hasattr(file_controller, 'project_path'):
                self.filtering_widget.project_path = file_controller.project_path
        # Load trajectory data when file controller is set
        self.load_trajectory_data()
    
    def load_trajectory_data(self):
        """Load trajectory data from file controller if available."""
        if self.file_controller:
            try:
                self.data = self.file_controller.load_trajectories_data("all_trajectories.csv")
            except (pd.errors.EmptyDataError, FileNotFoundError):
                self.data = pd.DataFrame()

    def get_drift(self, page=None):
        """Creates a plot of all particles drift"""
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            scaling = self.config_manager.get_detection_params().get("scaling", 1.0)
            drift = tp.compute_drift(self.data, smoothing=15)*scaling
            ax = drift.plot()

            ax.set_xlabel("Frame")

            temp_fig = plt.gcf()
            temp_fig.suptitle("Drift")

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def get_trajectories(self, page=None):
        """Creates a plot of all particle trajectories."""
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            self.check_for_empty_data()

            params = self.config_manager.get_detection_params()
            scaling = params.get("scaling")

            # Create the plot
            fig, ax = plt.subplots()
            tp.plot_traj(self.data, mpp = scaling, ax=ax)

            ax.set_xlabel("X [microns per px]")
            ax.set_ylabel("Y [microns per px]")

            temp_fig = plt.gcf()
            temp_fig.suptitle("Trajectories")

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None
