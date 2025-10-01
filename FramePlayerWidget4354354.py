from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class FramePlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.label = QLabel("Frame Player Widget")
        self.layout.addWidget(self.label)
