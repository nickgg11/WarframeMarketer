"""Warframes tab for displaying price information"""
# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget,
                            QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from src.utils.market_analysis import calculate_trimmed_mean

class NumericTableWidgetItem(QTableWidgetItem):
    """Custom QTableWidgetItem that ensures proper numeric sorting."""
    
    def __lt__(self, other):
        """Override the less than operator for correct numeric sorting.
        
        Args:
            other: Another table item to compare with
            
        Returns:
            bool: Result of numeric comparison
        """
        try:
            return float(self.data(Qt.ItemDataRole.EditRole)) < float(other.data(Qt.ItemDataRole.EditRole))
        except (ValueError, TypeError):
            return super().__lt__(other)

class WarframesTab(QWidget):
    """Tab for displaying warframe price information.
    
    Shows a table of all warframes with their average, minimum, and maximum prices.
    """
    def __init__(self, parent=None, db_ops=None):
        """Initialize the warframes tab.
        
        Args:
            parent: Parent widget
            db_ops: Database operations instance
        """
        super().__init__(parent)
        self.db_ops = db_ops
        self.sort_column = 1  # Default sort by average price
        self.sort_order = Qt.SortOrder.DescendingOrder  # Default descending
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        
        # Create table for warframes
        self.warframes_table = QTableWidget()
        self.warframes_table.setColumnCount(4)
        self.warframes_table.setHorizontalHeaderLabels([
            "Warframe", "Average", "Min Price", "Max Price"
        ])
        
        # Make the table columns stretch to fill the width
        header = self.warframes_table.horizontalHeader()
        if header:  # Add null check
            for i in range(4):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            
            # Connect header click to sorting function
            header.sectionClicked.connect(self.header_clicked)
        
        layout.addWidget(self.warframes_table)
        self.load_warframe_data()
    
    def header_clicked(self, logical_index):
        """Handle header click to sort the table.
        
        Args:
            logical_index: Index of the clicked column
        """
        # Only allow sorting on numeric columns (Average, Min, Max)
        if logical_index >= 1:  # Skip sorting on column 0 (Warframe name)
            # If clicking the same column, toggle the sort order
            if self.sort_column == logical_index:
                self.sort_order = (Qt.SortOrder.AscendingOrder 
                                  if self.sort_order == Qt.SortOrder.DescendingOrder 
                                  else Qt.SortOrder.DescendingOrder)
            else:
                # If clicking a different column, use descending order by default
                self.sort_column = logical_index
                self.sort_order = Qt.SortOrder.DescendingOrder
                
            # Apply the sorting
            self.warframes_table.sortItems(self.sort_column, self.sort_order)
    
    def refresh_data(self):
        """Refresh the warframes data in the table with latest prices."""
        self.load_warframe_data()
    
    def load_warframe_data(self):
        """Load and display warframe data from the database."""
        if not self.db_ops:
            return
        
        warframes = self.db_ops.get_all_warframes()
        self.warframes_table.setRowCount(len(warframes))
        
        for row, (warframe_id, name) in enumerate(warframes):
            # Get latest prices from database
            prices = self.db_ops.get_latest_prices(warframe_id)
            
            # Get recent prices for trimmed mean calculation
            recent_prices = self.db_ops.get_recent_sell_prices(warframe_id, hours=24)
            
            # Calculate trimmed mean with proper error handling
            try:
                trimmed_mean = calculate_trimmed_mean(recent_prices, trim_percent=10.0) if recent_prices else 0.0
                # Ensure we have a valid float for trimmed_mean
                trimmed_mean = 0.0 if trimmed_mean is None else float(trimmed_mean)
            except (TypeError, ValueError):
                trimmed_mean = 0.0
                
            # Display data in table
            name_item = QTableWidgetItem(name)
            self.warframes_table.setItem(row, 0, name_item)
            
            # Create numeric items with custom class for proper sorting
            avg_item = NumericTableWidgetItem()
            avg_item.setData(Qt.ItemDataRole.DisplayRole, f"{trimmed_mean:.2f}")
            avg_item.setData(Qt.ItemDataRole.EditRole, trimmed_mean)
            self.warframes_table.setItem(row, 1, avg_item)
            
            # Initialize default values
            min_price = 0.0
            max_price = 0.0
            
            if prices:
                # Handle min price with proper null-checking
                try:
                    min_price_val = prices.get('min')
                    min_price = 0.0 if min_price_val is None else float(min_price_val)
                except (TypeError, ValueError):
                    min_price = 0.0
                
                # Handle max price with proper null-checking
                try:
                    max_price_val = prices.get('max')
                    max_price = 0.0 if max_price_val is None else float(max_price_val)
                except (TypeError, ValueError):
                    max_price = 0.0
            
            # Create items with proper numeric values for sorting using custom class
            min_item = NumericTableWidgetItem()
            min_item.setData(Qt.ItemDataRole.DisplayRole, f"{min_price:.2f}")
            min_item.setData(Qt.ItemDataRole.EditRole, min_price)
            self.warframes_table.setItem(row, 2, min_item)
            
            max_item = NumericTableWidgetItem()
            max_item.setData(Qt.ItemDataRole.DisplayRole, f"{max_price:.2f}")
            max_item.setData(Qt.ItemDataRole.EditRole, max_price)
            self.warframes_table.setItem(row, 3, max_item)
        
        # Apply the current sorting
        self.warframes_table.sortItems(self.sort_column, self.sort_order)
