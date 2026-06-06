"""
Trajectory Plotting Widget

Description: GUI widget for displaying trajectory plots, filtering plots, and
             drift for all trajectories found.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal
import numpy as np
import pandas as pd
import pyqtgraph as pg
import trackpy as tp

from ..utils import GraphingUtils
from .DW_LW_FilteringWidget import DWLWFilteringWidget


class LWPlottingWidget(GraphingUtils.GraphingPanelWidget):
    filteredTrajectoriesUpdated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setup_plot_display()

        self.graphing_buttons = QWidget()
        self.button_layout = QHBoxLayout(self.graphing_buttons)

        self.trajectories = QWidget()
        self.trajectory_layout = QVBoxLayout(self.trajectories)
        self.trajectory_label = QLabel("Trajectories")
        self.trajectory_layout.addWidget(self.trajectory_label, alignment=Qt.AlignTop)

        self.trajectory_button = GraphingUtils.GraphingButton(text="Trajectories", parent=self)
        self.trajectory_button.clicked.connect(
            lambda: self.self_plot(self.get_trajectories, self.trajectory_button)
        )
        self.trajectory_layout.addWidget(self.trajectory_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.trajectories)
        self.trajectory_layout.addStretch(1)

        self.filtering_buttons(self.button_layout, "detection")

        self.drift = QWidget()
        self.drift_layout = QVBoxLayout(self.drift)
        self.drift_label = QLabel("Drift")
        self.drift_layout.addWidget(self.drift_label, alignment=Qt.AlignTop)

        self.drift_button = GraphingUtils.GraphingButton(text="Drift", parent=self)
        self.drift_button.clicked.connect(lambda: self.self_plot(self.get_drift, self.drift_button))
        self.drift_layout.addWidget(self.drift_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.drift)
        self.drift_layout.addStretch(1)

        self.layout.addWidget(self.graphing_buttons)

        self.filtering_widget = DWLWFilteringWidget(source_data_file="all_particles.csv")
        self.filtering_widget.filteredParticlesUpdated.connect(
            self.filteredTrajectoriesUpdated.emit
        )
        self.layout.addWidget(self.filtering_widget)
        self.layout.addStretch(1)

    def get_linked_particles(self, linked_particles):
        self.data = linked_particles
        self.self_plot(self.get_trajectories, self.trajectory_button)

    def set_file_controller(self, file_controller):
        super().set_file_controller(file_controller)
        if hasattr(self, "filtering_widget"):
            self.filtering_widget.set_file_controller(file_controller)
            if file_controller and hasattr(file_controller, "project_path"):
                self.filtering_widget.project_path = file_controller.project_path
        self.load_particle_data()

    def load_particle_data(self):
        if self.file_controller:
            try:
                self.data = self.file_controller.load_particles_data("all_particles.csv")
            except (pd.errors.EmptyDataError, FileNotFoundError):
                self.data = pd.DataFrame()

    def get_drift(self, page=None):
        try:
            if not self.check_for_empty_data():
                return False

            scaling = self.config_manager.get_detection_params().get("scaling", 1.0)
            drift = tp.compute_drift(self.data, smoothing=15) * scaling

            self._clear_plot()
            plot, fonts = self._add_scaled_plot(title="Drift")
            self._style_plot(plot, xlabel="Frame", ylabel="Drift", fonts=fonts)
            line_width = self._get_scaled_pen_width(2.0)

            frames = drift.index.values.astype(float)
            plot.plot(
                frames,
                drift["x"].values,
                pen=pg.mkPen(color=(0, 0, 200), width=line_width),
                name="x",
            )
            plot.plot(
                frames,
                drift["y"].values,
                pen=pg.mkPen(color=(200, 0, 0), width=line_width),
                name="y",
            )
            plot.addLegend(offset=(10, 10), labelTextSize=fonts["label_pt"])
            return True
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False

    def get_trajectories(self, page=None):
        try:
            if not self.check_for_empty_data():
                return False

            scaling = self.config_manager.get_detection_params().get("scaling", 1.0) or 1.0

            self._clear_plot()
            plot, fonts = self._add_scaled_plot(title="Trajectories")
            self._style_plot(
                plot,
                xlabel="X [microns per px]",
                ylabel="Y [microns per px]",
                fonts=fonts,
            )
            line_width = self._get_scaled_pen_width(1.5)

            particle_count = self.data["particle"].nunique()
            for index, (_, particle_data) in enumerate(self.data.groupby("particle")):
                sorted_data = particle_data.sort_values("frame")
                color = pg.intColor(index, hues=max(10, particle_count))
                plot.plot(
                    sorted_data["x"].values * scaling,
                    sorted_data["y"].values * scaling,
                    pen=pg.mkPen(color, width=line_width),
                )
            return True
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False
