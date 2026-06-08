"""
Interactive Frame Viewer

Description: Zoomable, pannable video frame display using PyQtGraph (same interaction
             model as the particle plot panels).

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget


class InteractiveFrameViewer(QWidget):
    """Displays a single frame with pan/zoom via PyQtGraph."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._has_image = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.placeholder_label = QLabel("Loading video...")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet(
            """
            QLabel {
                background-color: #1a1a1a;
                color: #cccccc;
                padding: 16px;
            }
        """
        )
        self.stack.addWidget(self.placeholder_label)

        self.graphics = pg.GraphicsLayoutWidget()
        self.graphics.setBackground("#1a1a1a")
        self.stack.addWidget(self.graphics)

        self.plot = self.graphics.addPlot(row=0, col=0)
        self.plot.hideAxis("left")
        self.plot.hideAxis("bottom")
        self.plot.setAspectLocked(True)
        self.plot.invertY(True)
        self.plot.setMenuEnabled(False)

        self.image_item = pg.ImageItem()
        self.plot.addItem(self.image_item)

        self.stack.setCurrentWidget(self.placeholder_label)

    def set_message(self, message):
        """Show a text placeholder instead of a frame."""
        self._has_image = False
        self.placeholder_label.setText(message)
        self.stack.setCurrentWidget(self.placeholder_label)

    def set_frame_image(self, rgb_image, reset_view=True):
        """
        Display an RGB frame (HxWx3 uint8).

        Parameters
        ----------
        rgb_image : np.ndarray or None
            Image in row-major RGB order.
        reset_view : bool
            If True, fit the full frame in view (used when changing frames).
        """
        if rgb_image is None or rgb_image.size == 0:
            self.set_message("Frame not found")
            return

        self._has_image = True
        self.stack.setCurrentWidget(self.graphics)
        self.image_item.setImage(np.ascontiguousarray(rgb_image), axisOrder="row-major")
        if reset_view:
            self.reset_view()

    def reset_view(self):
        """Fit the entire frame in the viewer."""
        if not self._has_image:
            return
        self.plot.autoRange(padding=0.02)

    def clear(self):
        self._has_image = False
        self.image_item.clear()
        self.set_message("")
