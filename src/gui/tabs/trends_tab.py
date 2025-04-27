"""Trends tab for market analysis visualization"""
# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget,
                           QTableWidgetItem, QPushButton, QHeaderView)

from src.models.data_models import TimeRange
from src.utils.market_analysis import analyze_market_data

class TrendsTab(QWidget):
    """Tab for displaying market trend analysis and trading recommendations.
    
    Visualizes price trends, volume trends, and generates trading recommendations
    based on market analysis data.
    """
    def __init__(self, parent=None, db_ops=None):
        """Initialize the trends tab.
        
        Args:
            parent: Parent widget
            db_ops: Database operations instance
        """
        super().__init__(parent)
        self.db_ops = db_ops
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        
        # Create table for trends
        self.trends_table = QTableWidget()
        self.trends_table.setColumnCount(4)
        self.trends_table.setHorizontalHeaderLabels([
            "Warframe", "Price Trend", "Volume Trend", "Recommendation"
        ])
        
        # Make the table columns stretch to fill the width
        header = self.trends_table.horizontalHeader()
        if header:  # Add null check
            for i in range(4):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        
        refresh_btn = QPushButton("Refresh Trends")
        refresh_btn.clicked.connect(self.refresh_trends)
        
        layout.addWidget(refresh_btn)
        layout.addWidget(self.trends_table)
        
    def load_trend_data(self):
        """Load and display trend data for all warframes."""
        if not self.db_ops:
            return
        
        warframes = self.db_ops.get_all_warframes()
        self.trends_table.setRowCount(len(warframes))
        
        for row, (warframe_id, name) in enumerate(warframes):
            self.trends_table.setItem(row, 0, QTableWidgetItem(name))
            
            # Get market analysis data
            try:
                analysis = analyze_market_data(warframe_id, TimeRange.MONTH)
                if analysis:
                    price_trend = f"{analysis.price_trends:.2f}%" if hasattr(analysis, 'price_trends') else "N/A"
                    volume_trend = f"{analysis.avg_daily_volume:.1f}" if hasattr(analysis, 'avg_daily_volume') else "N/A"
                    recommendation = self._get_recommendation(analysis)
                    
                    self.trends_table.setItem(row, 1, QTableWidgetItem(price_trend))
                    self.trends_table.setItem(row, 2, QTableWidgetItem(volume_trend))
                    self.trends_table.setItem(row, 3, QTableWidgetItem(recommendation))
            except (AttributeError, TypeError, ValueError):
                # If there's an error with the analysis, just show N/A values
                self.trends_table.setItem(row, 1, QTableWidgetItem("N/A"))
                self.trends_table.setItem(row, 2, QTableWidgetItem("N/A"))
                self.trends_table.setItem(row, 3, QTableWidgetItem("N/A"))
    
    def refresh_trends(self):
        """Refresh the trends data."""
        self.load_trend_data()
        
    def _get_recommendation(self, analysis):
        """Generate a trading recommendation based on analysis data.
        
        Args:
            analysis: MarketAnalysis object containing trend data
            
        Returns:
            String recommendation for trading the item
        """
        if not analysis:
            return "Insufficient Data"
        
        # This is a simple recommendation algorithm that can be expanded
        if hasattr(analysis, 'price_trends') and hasattr(analysis, 'price_volatility'):
            if analysis.price_trends > 5 and analysis.price_volatility < 10:
                return "Buy"
            elif analysis.price_trends < -5 and analysis.price_volatility < 10:
                return "Sell"
            elif analysis.price_volatility > 20:
                return "Volatile - Caution"
        
        return "Hold"