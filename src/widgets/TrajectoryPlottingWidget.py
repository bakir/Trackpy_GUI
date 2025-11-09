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
    QPushButton
)
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from .. import particle_processing
from ..config_parser import *
import os
from copy import copy

from .GraphingUtils import *

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
        self.trajectory_layout.addWidget(self.trajectory_label, alignment=Qt.AlignTop)

        self.trajectory_button = GraphingButton(
            text="Plot Trajectories", parent=self
        )
        self.trajectory_button.clicked.connect(lambda: self.self_plot(self.get_trajectories, self.trajectory_button))
        self.trajectory_layout.addWidget(self.trajectory_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.trajectories)
        self.trajectory_layout.addStretch(1)

        # Filtering
        self.filtering_buttons(self.button_layout, "trajectory")

        # Drift
        self.drift = QWidget()
        self.drift_layout = QVBoxLayout(self.drift)
        self.drift_label = QLabel("Drift")
        self.drift_layout.addWidget(self.drift_label, alignment=Qt.AlignTop)

        self.drift_button = GraphingButton(
            text="Plot Drift", parent=self
        )
        self.drift_button.clicked.connect(lambda: self.self_plot(self.get_drift, self.drift_button))
        self.drift_layout.addWidget(self.drift_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.drift)
        self.drift_layout.addStretch(1)

        self.layout.addWidget(self.graphing_buttons)
        # Add stretch below the buttons
        self.layout.addStretch(1)

    def get_linked_particles(self, linked_particles):
        """Sets linking data and plots trajectories."""
        self.data = linked_particles
        self.self_plot(self.get_trajectories, self.trajectory_button)

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

            ax.set_xlabel("Frame", fontsize=20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)
            temp_fig.suptitle("Drift", fontsize=24)

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

            ax.set_xlabel("X [px]", fontsize=20)
            ax.set_ylabel("Y [px]", fontsize=20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)
            temp_fig.suptitle("Trajectories", fontsize=24)

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None
