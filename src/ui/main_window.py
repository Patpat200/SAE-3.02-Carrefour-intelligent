from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from .carrefour_widget import CarrefourWidget
from .control_panel import ControlPanel


class MainWindow(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("Simulation Carrefour - SAE (Client)")
        self.resize(900, 620)

        self.carrefour_widget = CarrefourWidget()
        self.control_panel = ControlPanel()

        container = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.carrefour_widget, stretch=3)
        layout.addWidget(self.control_panel, stretch=1)
        container.setLayout(layout)
        self.setCentralWidget(container)
