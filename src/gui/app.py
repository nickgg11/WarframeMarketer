"""Application entry point for the Warframe Market GUI"""
import sys
from PyQt6.QtWidgets import QApplication
from .main_window import WarframeMarketGUI

def main():
    """Initialize and run the GUI application"""
    app = QApplication(sys.argv)
    window = WarframeMarketGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
