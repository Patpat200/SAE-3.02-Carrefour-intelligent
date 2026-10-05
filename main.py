import sys

from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.utils.config_loader import load_settings

def main():
    settings = load_settings()

    app = QApplication(sys.argv)
    window = MainWindow(settings)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
