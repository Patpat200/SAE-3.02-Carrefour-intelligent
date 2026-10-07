from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from .carrefour_widget import CarrefourWidget
from .control_panel import ControlPanel


class MainWindow(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("Simulation Carrefour - Colmar")
        options = settings.get("interface", {})
        self.resize(options.get("largeur", 960), options.get("hauteur", 700))

        self.carrefour_widget = CarrefourWidget()
        self.control_panel = ControlPanel()

        container = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.carrefour_widget, stretch=3)
        layout.addWidget(self.control_panel, stretch=1)
        container.setLayout(layout)
        self.setCentralWidget(container)

    def afficher_etat(self, state):
        self.carrefour_widget.set_state(state)
        self.control_panel.set_density(state.get("densite", {}))
        self.control_panel.set_emergency(state.get("urgence"))
