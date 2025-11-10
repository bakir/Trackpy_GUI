"""
Graphing Panel for the ParticleDetectionWindow

Description: Graphing panel showing the subpixel bias, filtering parameters, 
             and histograms of all particles based on current tracking parameters.

"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMenu,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
import os
from copy import copy
from .. import particle_processing

from .GraphingUtils import *


class DectectionPlottingWidget(GraphingPanelWidget):
    def __init__(self, parent=None):
        super(GraphingPanelWidget, self).__init__()

        self.set_up_canvas()

        # Buttons
        self.graphing_buttons = QWidget()
        self.button_layout = QHBoxLayout(self.graphing_buttons)

        # Subpixel bias
        self.sb = QWidget()
        self.sb_layout = QVBoxLayout(self.sb)
        self.sb_label = QLabel("Subpixel Bias")
        self.sb_layout.addWidget(self.sb_label, alignment=Qt.AlignTop)

        self.sb_button = GraphingButton(text="Plot Subpixel Bias", parent=self)
        self.sb_button.clicked.connect(
            lambda: self.self_plot(self.get_subpixel_bias, self.sb_button)
        )
        self.sb_layout.addWidget(self.sb_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.sb)
        self.sb_layout.addStretch(1)

        # Filtering
        self.filtering_buttons(self.button_layout, "detection")

        # Histograms
        self.hist = QWidget()
        self.hist_layout = QVBoxLayout(self.hist)
        self.hist_label = QLabel("Histograms")
        self.hist_layout.addWidget(self.hist_label, alignment=Qt.AlignTop)

        self.ecc_button = GraphingButton(text="Plot Eccentricity", parent=self)
        self.ecc_button.clicked.connect(
            lambda: self.self_plot(
                self.get_eccentricity_count, self.ecc_button
            )
        )
        self.hist_layout.addWidget(self.ecc_button, alignment=Qt.AlignTop)

        self.mass_button = GraphingButton(text="Plot Mass", parent=self)
        self.mass_button.clicked.connect(
            lambda: self.self_plot(self.get_mass_count, self.mass_button)
        )
        self.hist_layout.addWidget(self.mass_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.hist)
        self.hist_layout.addStretch(1)

        self.layout.addWidget(self.graphing_buttons)
        # Add stretch below the buttons
        self.layout.addStretch(1)

    def set_particles(self, particles):
        """Sets paritcle data and plots subpixel bias."""
        self.data = particles
        self.self_plot(self.get_subpixel_bias, self.sb_button)

    def get_mass_count(self, page=None):
        """Creates a histogram of all current particles mass."""
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            fig, ax = plt.subplots()
            ax.hist(self.data["mass"], bins=20)

            # Label the axes
            ax.set_xlabel("Mass", fontsize=20)
            ax.set_ylabel("Count", fontsize=20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)

            temp_fig.suptitle("Mass (Brightness)", fontsize=24)

            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def get_eccentricity_count(self, page=None):
        """Creates a histogram of all current particles eccentricity."""
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            fig, ax = plt.subplots()
            ax.hist(self.data["ecc"], bins=20)

            # Label the axes
            ax.set_xlabel("Eccentricity", fontsize=20)
            ax.set_ylabel("Count", fontsize=20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)

            temp_fig.suptitle("Eccentricity", fontsize=24)

            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def get_subpixel_bias(self, page=None):
        """Creates a plot of the subpixel bias of all current particles."""
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            tp.subpx_bias(self.data)

            temp_fig = plt.gcf()
            temp_fig.subplots_adjust(
                top=0.900, bottom=0.100, left=0.075, right=0.950, wspace=0.250
            )
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)
            temp_fig.suptitle("Subpixel Bias", fontsize=24)

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None
