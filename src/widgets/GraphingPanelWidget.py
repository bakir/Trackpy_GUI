"""
Graphing Panel showing subpixel bias

Description: Graphing panel showing the subpixel bias of all particles based on current tracking parameters.

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

class GraphingPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None
        self.particles = None
        
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

        self.mass_size_button = QPushButton(text = "Plot Mass", parent = self)
        self.mass_size_button.clicked.connect(self.plot_mass)
        self.button_layout.addWidget(self.mass_size_button, alignment=Qt.AlignLeft)

        self.mass_size_button = QPushButton(text = "Plot Mass vs Size", parent = self)
        self.mass_size_button.clicked.connect(self.plot_mass_size)
        self.button_layout.addWidget(self.mass_size_button, alignment=Qt.AlignLeft)

        self.layout.addWidget(self.graphing_buttons)
        # Add stretch below the buttons
        self.layout.addStretch(1) 
     
    def set_config_manager(self, config_manager):
        """Set the config manager for this widget."""
        self.config_manager = config_manager
    
    def set_file_controller(self, file_controller):
        """Set the file controller for this widget."""
        self.file_controller = file_controller

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

    def plot_mass(self):
        # 1. Get the new sized figure
        new_fig = self.get_mass_count()

        # 2. Close the old figure 
        if self.fig and self.fig is not new_fig:
             plt.close(self.fig)
        
        if new_fig is None:
            # Handle error/no particles case
            self.blank_plot("error")
            self.canvas.draw()
            return

        # 3. Assign the new figure
        self.fig = new_fig
        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)

        # 4. Redraw the canvas with the new figure
        self.canvas.figure = self.fig
        self.canvas.draw()

    def get_mass_count(self):
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Return None if nothing was found
            if self.particles is None or self.particles.empty:
                print("No particles detected in the selected frame.")
                return None 

            # Create the plot 
            fig, ax = plt.subplots()
            ax.hist(self.particles['mass'], bins=20)

            # Label the axes
            ax.set_xlabel("Mass", fontsize = 20)
            ax.set_ylabel("Count", fontsize = 20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)

            temp_fig.suptitle("Mass (Brightness)", fontsize = 24)

            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def plot_sb(self, particles):
        # 1. Get the new sized figure
        self.particles = particles
        new_fig = self.get_subpixel_bias(particles)

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

    def get_subpixel_bias(self, particles):
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Return None if nothing was found
            if particles.empty:
                print("No particles detected in the selected frame.")
                return None 

            # Create the plot 
            tp.subpx_bias(particles)

            temp_fig = plt.gcf()
            temp_fig.subplots_adjust(top = 0.900, bottom = 0.100, left = 0.075, right = 0.950, wspace = 0.250)
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)
            temp_fig.suptitle("Subpixel Bias", fontsize = 24)
            
            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

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
            if self.particles is None or self.particles.empty:
                print("No particles detected in the selected frame.")
                return None # Return None if nothing was found

            # Create the plot 
            fig, ax = plt.subplots()
            tp.mass_size(self.particles, ax = ax)

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
