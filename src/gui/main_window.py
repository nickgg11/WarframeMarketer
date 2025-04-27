"""Main window for the Warframe Market GUI application"""
# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget

from src.database.operations import DatabaseOperations
from .tabs import WarframesTab, UpdateTab, TrendsTab

class WarframeMarketGUI(QMainWindow):
    """Main application window for the Warframe Market GUI"""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warframe Market Analyzer")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize database operations
        self.db_ops = DatabaseOperations()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create and add tabs
        self.warframes_tab = WarframesTab(parent=self, db_ops=self.db_ops)
        self.update_tab = UpdateTab(parent=self, db_ops=self.db_ops)
        self.trends_tab = TrendsTab(parent=self, db_ops=self.db_ops)
        
        self.tabs.addTab(self.warframes_tab, "Warframes")
        self.tabs.addTab(self.update_tab, "Update Data")
        self.tabs.addTab(self.trends_tab, "Trends")
        
        layout.addWidget(self.tabs)
        
    def refresh_data(self):
        """Refresh all data in tabs"""
        self.warframes_tab.load_warframe_data()
        self.trends_tab.load_trend_data()