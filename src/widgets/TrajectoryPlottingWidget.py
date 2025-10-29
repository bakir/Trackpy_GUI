"""
Trajectory Plotting Widget

Description: GUI widget for displaying trajectory plots and analysis visualizations.

"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from .. import particle_processing
from ..config_parser import *
import os
from copy import copy

TARGET_WIDTH_PX = 500
TARGET_HEIGHT_PX = 400
STANDARD_DPI = 100

class TrajectoryPlottingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.linked_particles = None

        # Graph area
        self.layout = QVBoxLayout(self)
        self.fig = None 
        self.blank_plot("beginning")

        self.canvas = FigureCanvas(self.fig)

        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX) 
        
        # Add stretch above the canvas for vertical centering
        self.layout.addStretch(1) 
        # Center the canvas in the layout
        self.layout.addWidget(self.canvas, alignment = Qt.AlignCenter) 

        # buttons
        self.graphing_buttons = QWidget()
        self.button_layout = QHBoxLayout(self.graphing_buttons)

        self.mass_size_button = QPushButton(text = "Plot Mass vs Size", parent = self)
        self.mass_size_button.clicked.connect(self.plot_mass_size)
        self.button_layout.addWidget(self.mass_size_button, alignment=Qt.AlignLeft)

        self.drift_button = QPushButton(text = "Plot Drift", parent = self)
        self.drift_button.clicked.connect(self.plot_drift)
        self.button_layout.addWidget(self.drift_button, alignment=Qt.AlignLeft)

        self.layout.addWidget(self.graphing_buttons)
        # Add stretch below the buttons
        self.layout.addStretch(1) 

    def get_linked_particles(self, particles):
        self.linked_particles = particles
    
    def _get_figure_size_inches(self):
        """Calculates the necessary figsize in inches."""
        width_in = TARGET_WIDTH_PX / STANDARD_DPI 
        height_in = TARGET_HEIGHT_PX / STANDARD_DPI
        return (width_in, height_in)

    def blank_plot(self, state):
        """Creates a new blank figure with the correct size."""
        fig_size = self._get_figure_size_inches()
        if self.fig:
             plt.close(self.fig)
             
        # Ensure the blank figure is created with the target size properties
        self.fig = Figure(figsize=fig_size, dpi=STANDARD_DPI)
        ax = self.fig.add_subplot(111)
        if state == "error":
            print("error")
            ax.set_axis_on()
            self.fig.suptitle("Error: No particles detected.")
        else:
            ax.set_axis_off()

    def plot_mass_size(self):
        # 1. Get the new sized figure
        new_fig = self.get_mass_size()

        # 2. Close the old figure 
        if self.fig and self.fig is not new_fig:
             plt.close(self.fig)
        
        if new_fig is None:
            # Handle error/no particles case
            return

        # 3. Assign the new figure
        self.fig = new_fig
        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)

        # 4. Redraw the canvas with the new figure
        self.canvas.figure = self.fig
        self.canvas.draw()

    def get_mass_size(self):
        try:
            import trackpy as tp
            import cv2
            import pandas as pd
                    
            # Check if particles were found before plotting
            if self.linked_particles is None or self.linked_particles.empty:
                print("No particles detected in the selected frame.")
                return None # Return None if nothing was found

            # Create the plot 
            fig, ax = plt.subplots()
            tp.mass_size(self.linked_particles.groupby('particle').mean(), ax = ax)

            ax.set_xlabel("Mass", fontsize = 20)
            ax.set_ylabel("Size", fontsize = 20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)
            temp_fig.suptitle("Mass vs Size", fontsize = 24)
            
            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def plot_drift(self):
        # 1. Get the new sized figure
        new_fig = self.get_drift()

        # 2. Close the old figure 
        if self.fig and self.fig is not new_fig:
             plt.close(self.fig)
        
        if new_fig is None:
            # Handle error/no particles case
            return

        # 3. Assign the new figure
        self.fig = new_fig
        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)

        # 4. Redraw the canvas with the new figure
        self.canvas.figure = self.fig
        self.canvas.draw()

    def get_drift(self):
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            if self.linked_particles is None or self.linked_particles.empty:
                print("No particles detected in the selected frame.")
                return None # Return None if nothing was found

            # Create the plot 
            d = tp.compute_drift(self.linked_particles)
            ax = d.plot()

            ax.set_xlabel("Frame", fontsize = 20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)
            temp_fig.suptitle("Drift", fontsize = 24)
            
            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None