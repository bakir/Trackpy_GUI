"""
Graphing Utilities Module

Description: Base classes and utilities for graphing widgets used in both
             ParticleDetectionWindow and TrajectoryLinkingWindow.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal
import numpy as np
import pandas as pd
import pyqtgraph as pg

from .SizingUtils import get_plot_font_sizes, scaled_length


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

    pointSelected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scatter_plot_df = None
        self._scatter_item = None
        self._scatter_x_col = None
        self._scatter_y_col = None
        self._selected_scatter_index = None

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

        self.selection_info_label = QLabel("Click a point to inspect particle coordinates.")
        self.selection_info_label.setWordWrap(True)
        self.selection_info_label.setAlignment(Qt.AlignCenter)
        self.selection_info_label.setStyleSheet(
            """
            QLabel {
                background-color: #f0f0f0;
                padding: 6px;
                border-radius: 4px;
            }
        """
        )
        self.layout.addWidget(self.selection_info_label)

        self.blank_plot()

    def _get_plot_font_sizes(self):
        return get_plot_font_sizes()

    def _get_scaled_scatter_size(self):
        fonts = self._get_plot_font_sizes()
        return scaled_length(6, fonts["scale"])

    def _get_scaled_pen_width(self, base=1.5):
        fonts = self._get_plot_font_sizes()
        return scaled_length(base, fonts["scale"], minimum=1.0)

    def _add_scaled_plot(self, row=0, col=0, colspan=1, title=None):
        fonts = self._get_plot_font_sizes()
        plot = self.plot_container.addPlot(row=row, col=col, colspan=colspan)
        if title:
            plot.setTitle(title, color="k", size=fonts["title_pt"])
        return plot, fonts

    def blank_plot(self):
        if hasattr(self, "plot_container"):
            self._scatter_plot_df = None
            self._scatter_item = None
            self._selected_scatter_index = None
            self.plot_container.clear()
            fonts = self._get_plot_font_sizes()
            label = pg.LabelItem(
                "No plot to display.", color="k", size=fonts["subtitle_pt"]
            )
            self.plot_container.addItem(label, row=0, col=0)
            self._reset_selection_label()

    def _reset_selection_label(self):
        if hasattr(self, "selection_info_label"):
            self.selection_info_label.setText("Click a point to inspect particle coordinates.")

    def _format_particle_info(self, row, x_col=None, y_col=None, prefix="Selected"):
        parts = []
        if x_col is not None and y_col is not None and x_col in row and y_col in row:
            parts.append(f"plot {x_col}={row[x_col]:.3f}")
            parts.append(f"{y_col}={row[y_col]:.3f}")
        if "frame" in row:
            parts.append(f"frame={int(row['frame']) + 1}")
        if "x" in row:
            parts.append(f"x={row['x']:.2f}")
        if "y" in row:
            parts.append(f"y={row['y']:.2f}")
        if "particle" in row:
            parts.append(f"particle={int(row['particle'])}")
        if "mass" in row:
            parts.append(f"mass={row['mass']:.2f}")
        if "size" in row:
            parts.append(f"size={row['size']:.2f}")
        if "ecc" in row:
            parts.append(f"ecc={row['ecc']:.3f}")
        return f"{prefix}: " + " | ".join(parts)

    def _build_scatter_spots(self, plot_df, x_col, y_col, selected_index=None):
        size = self._get_scaled_scatter_size()
        selected_size = size * 1.6
        default_brush = pg.mkBrush(0, 0, 0, 30)
        selected_brush = pg.mkBrush(220, 40, 40, 220)
        spots = []
        for index, row in plot_df.iterrows():
            is_selected = selected_index is not None and index == selected_index
            spots.append(
                {
                    "pos": (float(row[x_col]), float(row[y_col])),
                    "data": int(index),
                    "brush": selected_brush if is_selected else default_brush,
                    "size": selected_size if is_selected else size,
                    "pen": pg.mkPen(220, 40, 40, width=2) if is_selected else None,
                }
            )
        return spots

    def _update_scatter_highlight(self):
        if self._scatter_item is None or self._scatter_plot_df is None:
            return
        if self._scatter_x_col is None or self._scatter_y_col is None:
            return
        spots = self._build_scatter_spots(
            self._scatter_plot_df,
            self._scatter_x_col,
            self._scatter_y_col,
            self._selected_scatter_index,
        )
        self._scatter_item.setData(spots=spots)

    def _on_scatter_clicked(self, _plot, points):
        if not points or self._scatter_plot_df is None:
            return
        row_index = points[0].data()
        if row_index is None:
            return
        self._select_scatter_point(int(row_index))

    def _on_scatter_hovered(self, _plot, points):
        if self._scatter_plot_df is None:
            return
        if points:
            row = self._scatter_plot_df.iloc[int(points[0].data())]
            self.selection_info_label.setText(
                self._format_particle_info(
                    row, self._scatter_x_col, self._scatter_y_col, prefix="Hover"
                )
            )
        elif self._selected_scatter_index is None:
            self._reset_selection_label()
        else:
            row = self._scatter_plot_df.iloc[self._selected_scatter_index]
            self.selection_info_label.setText(
                self._format_particle_info(row, self._scatter_x_col, self._scatter_y_col)
            )

    def _select_scatter_point(self, row_index):
        if self._scatter_plot_df is None or row_index not in self._scatter_plot_df.index:
            return
        self._selected_scatter_index = row_index
        self._update_scatter_highlight()
        row = self._scatter_plot_df.iloc[row_index]
        self.selection_info_label.setText(
            self._format_particle_info(row, self._scatter_x_col, self._scatter_y_col)
        )
        self.pointSelected.emit(row.to_dict())

    def _clear_plot(self):
        self._scatter_plot_df = None
        self._scatter_item = None
        self._scatter_x_col = None
        self._scatter_y_col = None
        self._selected_scatter_index = None
        self.plot_container.clear()

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

    def _style_plot(self, plot, xlabel=None, ylabel=None, fonts=None):
        if fonts is None:
            fonts = self._get_plot_font_sizes()

        plot.showGrid(x=True, y=True, alpha=0.25)
        tick_font = QFont()
        tick_font.setPointSizeF(fonts["tick"])

        for axis_name in ("bottom", "left"):
            axis = plot.getAxis(axis_name)
            axis.setPen(pg.mkPen("k"))
            axis.setTextPen(pg.mkPen("k"))
            axis.setStyle(tickFont=tick_font)

        if xlabel:
            plot.setLabel("bottom", xlabel, color="k", size=fonts["label_pt"])
        if ylabel:
            plot.setLabel("left", ylabel, color="k", size=fonts["label_pt"])

    def _add_histogram(self, plot, values, bins, xlabel=None, ylabel="Count", fonts=None):
        self._style_plot(plot, xlabel=xlabel, ylabel=ylabel, fonts=fonts)
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

    def _plot_scatter_panel(self, plot_df, x_col, y_col, title, xlabel, ylabel):
        self._clear_plot()
        self._reset_selection_label()
        plot_df = plot_df.reset_index(drop=True)
        self._scatter_plot_df = plot_df
        self._scatter_x_col = x_col
        self._scatter_y_col = y_col
        self._selected_scatter_index = None

        plot, fonts = self._add_scaled_plot(title=title)
        self._style_plot(plot, xlabel=xlabel, ylabel=ylabel, fonts=fonts)

        scatter = pg.ScatterPlotItem(
            spots=self._build_scatter_spots(plot_df, x_col, y_col),
            hoverable=True,
            tip=None,
        )
        scatter.sigClicked.connect(self._on_scatter_clicked)
        scatter.sigHovered.connect(self._on_scatter_hovered)
        plot.addItem(scatter)
        self._scatter_item = scatter
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
                plot_df,
                "mass",
                "size",
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
                plot_df,
                "mass",
                "ecc",
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
                plot_df,
                "size",
                "ecc",
                "Size vs Eccentricity",
                "Size",
                "Eccentricity",
            )
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False
