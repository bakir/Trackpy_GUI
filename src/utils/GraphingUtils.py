"""
Graphing Utilities Module

Description: Base classes and utilities for graphing widgets used in both
             ParticleDetectionWindow and TrajectoryLinkingWindow.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
import numpy as np
import pandas as pd
import pyqtgraph as pg


pg.setConfigOptions(antialias=True, background="w", foreground="k")


class GraphingButton(QPushButton):
    """Button for graphing controls with highlight state management."""

    highlighted_button = None

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

    def switch_button_color(self):
        if GraphingButton.highlighted_button is not None:
            prev_button = GraphingButton.highlighted_button
            prev_button.setDown(False)
            prev_button.setChecked(False)

        GraphingButton.highlighted_button = self
        self.setChecked(True)


class GraphingPanelWidget(QWidget):
    """Base widget for graphing panels with interactive PyQtGraph plots."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def set_config_manager(self, config_manager):
        self.config_manager = config_manager

    def set_file_controller(self, file_controller):
        self.file_controller = file_controller

    def setup_plot_display(self):
        self.config_manager = None
        self.file_controller = None
        self.data = None

        self.layout = QVBoxLayout(self)
        self.plot_container = pg.GraphicsLayoutWidget()
        self.plot_container.setBackground("w")
        self.layout.addWidget(self.plot_container, 20)
        self.blank_plot()

    def blank_plot(self):
        if hasattr(self, "plot_container"):
            self.plot_container.clear()
            label = pg.LabelItem("No plot to display.", color="k", size="14pt")
            self.plot_container.addItem(label, row=0, col=0)

    def has_plot_data(self):
        return self.data is not None and not self.data.empty

    def check_for_empty_data(self):
        if not self.has_plot_data():
            print("No particles detected in the selected frame.")
            return False
        return True

    def self_plot(self, plotting_function, button, page=None):
        success = plotting_function(page)
        if not success:
            self.blank_plot()
            return
        button.switch_button_color()

    def _clear_plot(self):
        self.plot_container.clear()

    def _style_plot(self, plot, xlabel=None, ylabel=None):
        plot.showGrid(x=True, y=True, alpha=0.25)
        plot.getAxis("bottom").setPen(pg.mkPen("k"))
        plot.getAxis("left").setPen(pg.mkPen("k"))
        plot.getAxis("bottom").setTextPen(pg.mkPen("k"))
        plot.getAxis("left").setTextPen(pg.mkPen("k"))
        if xlabel:
            plot.setLabel("bottom", xlabel, color="k")
        if ylabel:
            plot.setLabel("left", ylabel, color="k")

    def _add_histogram(self, plot, values, bins, xlabel=None, ylabel="Count"):
        self._style_plot(plot, xlabel=xlabel, ylabel=ylabel)
        counts, edges = np.histogram(values, bins=bins)
        if len(counts) == 0:
            return
        bar_width = (edges[1] - edges[0]) * 0.9
        x = (edges[:-1] + edges[1:]) / 2
        plot.addItem(
            pg.BarGraphItem(
                x=x,
                height=counts,
                width=bar_width,
                brush=pg.mkBrush(0, 0, 0, 180),
            )
        )

    def _plot_scatter_panel(self, x, y, title, xlabel, ylabel):
        self._clear_plot()
        plot = self.plot_container.addPlot(row=0, col=0, title=title)
        self._style_plot(plot, xlabel=xlabel, ylabel=ylabel)
        plot.addItem(
            pg.ScatterPlotItem(
                x=np.asarray(x),
                y=np.asarray(y),
                pen=None,
                brush=pg.mkBrush(0, 0, 0, 30),
                size=6,
            )
        )
        return True

    def _plot_dataframe(self, df, page):
        if page == "detection":
            return df
        return df.groupby(["particle"]).mean()

    def filtering_buttons(self, button_layout, page):
        self.filter = QWidget()
        self.filter_layout = QVBoxLayout(self.filter)
        self.filter_label = QLabel("Filtering")
        self.filter_layout.addWidget(self.filter_label, alignment=Qt.AlignTop)

        self.mass_ecc_button = GraphingButton(text="Mass vs Eccentricity", parent=self)
        self.mass_ecc_button.clicked.connect(
            lambda: self.self_plot(self.get_mass_ecc, self.mass_ecc_button, page)
        )
        self.filter_layout.addWidget(self.mass_ecc_button, alignment=Qt.AlignTop)

        self.mass_size_button = GraphingButton(text="Mass vs Size", parent=self)
        self.mass_size_button.clicked.connect(
            lambda: self.self_plot(self.get_mass_size, self.mass_size_button, page)
        )
        self.filter_layout.addWidget(self.mass_size_button, alignment=Qt.AlignTop)

        self.size_ecc_button = GraphingButton(text="Size vs Eccentricity", parent=self)
        self.size_ecc_button.clicked.connect(
            lambda: self.self_plot(self.get_size_ecc, self.size_ecc_button, page)
        )
        self.filter_layout.addWidget(self.size_ecc_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.filter)
        self.filter_layout.addStretch(1)

    def get_mass_size(self, page):
        try:
            if not self.check_for_empty_data():
                return False
            plot_df = self._plot_dataframe(self.data, page)
            return self._plot_scatter_panel(
                plot_df["mass"],
                plot_df["size"],
                "Mass vs Size",
                "Mass",
                "Size",
            )
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False

    def get_mass_ecc(self, page):
        try:
            if not self.check_for_empty_data():
                return False
            plot_df = self._plot_dataframe(self.data, page)
            return self._plot_scatter_panel(
                plot_df["mass"],
                plot_df["ecc"],
                "Mass vs Eccentricity",
                "Mass",
                "Eccentricity",
            )
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False

    def get_size_ecc(self, page):
        try:
            if not self.check_for_empty_data():
                return False
            plot_df = self._plot_dataframe(self.data, page)
            return self._plot_scatter_panel(
                plot_df["size"],
                plot_df["ecc"],
                "Size vs Eccentricity",
                "Size",
                "Eccentricity",
            )
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False
