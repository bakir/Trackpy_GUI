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
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
import os
from copy import copy
from .. import particle_processing

from .GraphingUtils import *
from .FilteringWidget import FilteringWidget


class TrajectoryPlottingWidget(GraphingPanelWidget):
    def __init__(self, parent=None):
        super(GraphingPanelWidget, self).__init__()

        self.set_up_canvas()

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

        self.trajectory_button = GraphingButton(
            text="Plot Trajectories", parent=self
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

        self.drift_button = GraphingButton(text="Plot Drift", parent=self)
        self.drift_button.clicked.connect(
            lambda: self.self_plot(self.get_drift, self.drift_button)
        )
        self.drift_layout.addWidget(self.drift_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.drift)
        self.drift_layout.addStretch(1)

        self.layout.addWidget(self.graphing_buttons)
        
        # Add filtering widget below the graphs
        self.filtering_widget = FilteringWidget()
        self.filtering_widget.set_source_data_file("trajectories.csv")
        self.layout.addWidget(self.filtering_widget)
        
        # Add stretch below the buttons
        self.layout.addStretch(1)

    def get_linked_particles(self, linked_particles):
        """Sets linking data and plots trajectories."""
        self.data = linked_particles
        self.self_plot(self.get_trajectories, self.trajectory_button)
    
    def set_file_controller(self, file_controller):
        """Override to also set file controller for filtering widget."""
        super().set_file_controller(file_controller)
        if hasattr(self, 'filtering_widget'):
            self.filtering_widget.set_file_controller(file_controller)
            if file_controller and hasattr(file_controller, 'project_path'):
                self.filtering_widget.set_project_path(file_controller.project_path)

    def get_drift(self, page=None):
        """Creates a plot of all particles drift"""
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            d = tp.compute_drift(self.data)
            ax = d.plot()

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

            # Create the plot
            fig, ax = plt.subplots()
            tp.plot_traj(self.data, ax=ax)

            ax.set_xlabel("X [px]")
            ax.set_ylabel("Y [px]")

            temp_fig = plt.gcf()
            temp_fig.suptitle("Trajectories")

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None
