"""
Scaled Label Module

Description: A QLabel subclass that automatically scales its pixmap to fit the label's
             size while maintaining aspect ratio.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

from PySide6.QtWidgets import QLabel, QStyle, QStyleOption
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt


class ScaledLabel(QLabel):
    """
    A QLabel subclass that automatically scales its pixmap to fit the label's
    size while preserving the original aspect ratio. The scaled image is
    always centered.
    """

    def __init__(self, parent=None):
        """
        Initialize the ScaledLabel.

        Parameters
        ----------
        parent : QWidget, optional
            Parent widget. Defaults to None.

        Returns
        -------
        None
        """
        super().__init__(parent)
        self._pixmap = QPixmap()

    def setPixmap(self, pixmap):
        """
        Sets the pixmap for the label.

        Parameters
        ----------
        pixmap : QPixmap
            The pixmap to display.

        Returns
        -------
        None
        """
        self._pixmap = pixmap
        self.update()  # Trigger a repaint

    def paintEvent(self, event):
        """
        Overrides the paint event to draw the scaled pixmap.

        Parameters
        ----------
        event : QPaintEvent
            The paint event.

        Returns
        -------
        None
        """
        if self._pixmap.isNull():
            # If no pixmap is set, draw the default QLabel content
            super().paintEvent(event)
            return

        painter = QPainter(self)
        pixmap_size = self._pixmap.size()
        label_size = self.size()

        # Scale pixmap to fit the label, maintaining aspect ratio
        scaled_pixmap = self._pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Calculate coordinates to center the pixmap
        x = (label_size.width() - scaled_pixmap.width()) / 2
        y = (label_size.height() - scaled_pixmap.height()) / 2

        painter.drawPixmap(x, y, scaled_pixmap)
