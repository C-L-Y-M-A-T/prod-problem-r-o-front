import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QComboBox, QTableWidget, 
                            QTableWidgetItem, QPushButton, QGroupBox, QFormLayout, 
                            QSpinBox, QDoubleSpinBox, QMessageBox, QFileDialog, QSplitter,
                            QTextEdit, QHeaderView, QFrame, QStackedWidget, QInputDialog,
                            QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QSize, pyqtSlot, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QLinearGradient, QGradient, QPainter, QPen, QBrush
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import sys
import os

# Set API base URL
API_BASE_URL = "http://localhost:5000"

# Define allowed optimizer types
ALLOWED_OPTIMIZERS = ["demand-constrained-production", "basic-production"]

class OptimizationThread(QThread):
    """Thread for running optimization requests without blocking the UI"""
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, optimizer_type, data):
        super().__init__()
        self.optimizer_type = optimizer_type
        self.data = data
        
    def run(self):
        try:
            url = f"{API_BASE_URL}/production/optimize/{self.optimizer_type}"
            response = requests.post(url, json=self.data)
            
            if response.status_code == 200:
                self.result_ready.emit(response.json())
            else:
                self.error_occurred.emit(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")

class ModernFigureCanvas(FigureCanvas):
    """Base class for modern-looking charts"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use('default')
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('#ffffff')
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('#f8f9fa')
        
        super().__init__(self.fig)
        self.setParent(parent)
        self.fig.tight_layout()

class ResourceUsageChart(ModernFigureCanvas):
    """Widget for displaying resource utilization charts"""
    def update_chart(self, resource_utilization):
        self.axes.clear()
        if not resource_utilization:
            return
            
        resources = []
        used_values = []
        available_values = []
        
        for resource, details in resource_utilization.items():
            resources.append(resource)
            used_values.append(details['used'])
            available_values.append(details['available'])
            
        x = np.arange(len(resources))
        width = 0.35
        
        # Use modern colors
        self.axes.bar(x - width/2, used_values, width, label='Used', color='#3b82f6')
        self.axes.bar(x + width/2, available_values, width, label='Available', color='#8b5cf6')
        
        self.axes.set_ylabel('Capacity', color='#1e293b')
        self.axes.set_title('Resource Utilization', color='#1e293b', fontweight='bold')
        self.axes.set_xticks(x)
        self.axes.set_xticklabels(resources, rotation=45, ha='right', color='#1e293b')
        self.axes.tick_params(axis='y', colors='#1e293b')
        self.axes.spines['bottom'].set_color('#cbd5e1')
        self.axes.spines['top'].set_color('#cbd5e1')
        self.axes.spines['left'].set_color('#cbd5e1')
        self.axes.spines['right'].set_color('#cbd5e1')
        self.axes.legend(facecolor='#ffffff', edgecolor='#cbd5e1')
        
        self.fig.tight_layout()
        self.draw()

class ProductionChart(ModernFigureCanvas):
    """Widget for displaying production plan charts"""
    def update_chart(self, production_plan):
        self.axes.clear()
        if not production_plan:
            return
            
        products = list(production_plan.keys())
        quantities = list(production_plan.values())
        
        # Sort by quantity for better visualization
        sorted_data = sorted(zip(products, quantities), key=lambda x: x[1], reverse=True)
        products = [x[0] for x in sorted_data]
        quantities = [x[1] for x in sorted_data]
        
        y_pos = np.arange(len(products))
        
        # Create a gradient of colors
        colors = plt.cm.viridis(np.linspace(0, 0.8, len(products)))
        
        self.axes.barh(y_pos, quantities, align='center', color='#3b82f6')
        self.axes.set_yticks(y_pos)
        self.axes.set_yticklabels(products, color='#1e293b')
        self.axes.invert_yaxis()  # labels read top-to-bottom
        self.axes.set_xlabel('Production Quantity', color='#1e293b')
        self.axes.set_title('Production Plan', color='#1e293b', fontweight='bold')
        self.axes.tick_params(axis='x', colors='#1e293b')
        self.axes.spines['bottom'].set_color('#cbd5e1')
        self.axes.spines['top'].set_color('#cbd5e1')
        self.axes.spines['left'].set_color('#cbd5e1')
        self.axes.spines['right'].set_color('#cbd5e1')
        
        self.fig.tight_layout()
        self.draw()

class StyleHelper:
    """Helper class for styling the application"""
    @staticmethod
    def apply_futuristic_light_theme(app):
        app.setStyle("Fusion")
        
        # Light futuristic palette
        light_palette = QPalette()
        light_palette.setColor(QPalette.Window, QColor(248, 250, 252))
        light_palette.setColor(QPalette.WindowText, QColor(15, 23, 42))
        light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
        light_palette.setColor(QPalette.AlternateBase, QColor(241, 245, 249))
        light_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        light_palette.setColor(QPalette.ToolTipText, QColor(15, 23, 42))
        light_palette.setColor(QPalette.Text, QColor(15, 23, 42))
        light_palette.setColor(QPalette.Button, QColor(226, 232, 240))
        light_palette.setColor(QPalette.ButtonText, QColor(15, 23, 42))
        light_palette.setColor(QPalette.BrightText, QColor(59, 130, 246))
        light_palette.setColor(QPalette.Link, QColor(59, 130, 246))
        light_palette.setColor(QPalette.Highlight, QColor(59, 130, 246))
        light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(light_palette)
        
    @staticmethod
    def get_accent_color():
        return QColor(59, 130, 246)  # Blue accent color
        
    @staticmethod
    def get_success_color():
        return QColor(34, 197, 94)  # Green
        
    @staticmethod
    def get_warning_color():
        return QColor(234, 179, 8)  # Yellow
        
    @staticmethod
    def get_error_color():
        return QColor(239, 68, 68)  # Red
        
    @staticmethod
    def style_button(button, primary=False):
        if primary:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: #ffffff;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
                QPushButton:pressed {
                    background-color: #1d4ed8;
                    padding: 11px 19px 9px 21px;
                }
                QPushButton:disabled {
                    background-color: #cbd5e1;
                    color: #64748b;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #e2e8f0;
                    color: #1e293b;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #cbd5e1;
                }
                QPushButton:pressed {
                    background-color: #94a3b8;
                    padding: 11px 19px 9px 21px;
                }
                QPushButton:disabled {
                    background-color: #f1f5f9;
                    color: #94a3b8;
                }
            """)
            
    @staticmethod
    def style_table(table):
        table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #1e293b;
                gridline-color: #e2e8f0;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                selection-background-color: #3b82f6;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                color: #1e293b;
                padding: 6px;
                border: none;
                border-right: 1px solid #e2e8f0;
                border-bottom: 1px solid #e2e8f0;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f1f5f9;
            }
            QTableWidget::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
        """)
        
    @staticmethod
    def style_group_box(group_box):
        group_box.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 20px;
                font-weight: bold;
                color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #3b82f6;
                color: #ffffff;
                border-radius: 4px;
            }
        """)
        
    @staticmethod
    def style_combo_box(combo_box):
        combo_box.setStyleSheet("""
            QComboBox {
                background-color: #f1f5f9;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 6em;
            }
            QComboBox:hover {
                background-color: #e2e8f0;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                selection-background-color: #3b82f6;
                selection-color: #ffffff;
                outline: none;
            }
        """)
        
    @staticmethod
    def style_spin_box(spin_box):
        spin_box.setStyleSheet("""
            QDoubleSpinBox, QSpinBox {
                background-color: #f1f5f9;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QDoubleSpinBox:hover, QSpinBox:hover {
                background-color: #e2e8f0;
            }
            QDoubleSpinBox::up-button, QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border: none;
            }
            QDoubleSpinBox::down-button, QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border: none;
            }
        """)
        
    @staticmethod
    def style_text_edit(text_edit):
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        
    @staticmethod
    def add_shadow(widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 5)
        widget.setGraphicsEffect(shadow)

class ModernTableWidget(QTableWidget):
    """Base class for modern styled table widgets"""
    def __init__(self, parent=None):
        super().__init__(parent)
        StyleHelper.style_table(self)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        
    def add_empty_row(self):
        row = self.rowCount()
        self.insertRow(row)

class ProductsTableWidget(ModernTableWidget):
    """Custom table widget for products data"""
    product_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Product Name", "Profit per Unit", "Cost per Unit"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.itemChanged.connect(self.on_item_changed)
        
    def on_item_changed(self, item):
        # Validate numeric inputs for profit and cost columns
        if item.column() in [1, 2]:  # Profit or Cost column
            try:
                # Try to convert to float
                value = float(item.text())
                # Format to 2 decimal places
                item.setText(f"{value:.2f}")
            except ValueError:
                # If not a valid number, reset to 0
                item.setText("0.00")
                QMessageBox.warning(None, "Invalid Input", "Please enter a valid number.")
        
        self.product_changed.emit()
        
    def get_products_data(self):
        products = []
        for row in range(self.rowCount()):
            name = self.item(row, 0).text() if self.item(row, 0) else ""
            profit = float(self.item(row, 1).text()) if self.item(row, 1) and self.item(row, 1).text() else 0
            cost = float(self.item(row, 2).text()) if self.item(row, 2) and self.item(row, 2).text() else 0
            
            if name:
                products.append({
                    "name": name,
                    "profit_per_unit": profit,
                    "cost_per_unit": cost
                })
        return products
    
    def get_product_names(self):
        """Get list of all product names"""
        names = []
        for row in range(self.rowCount()):
            name = self.item(row, 0).text() if self.item(row, 0) else ""
            if name:
                names.append(name)
        return names
        
    def set_products_data(self, products):
        self.setRowCount(0)
        for product in products:
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(product["name"]))
            self.setItem(row, 1, QTableWidgetItem(str(product["profit_per_unit"])))
            self.setItem(row, 2, QTableWidgetItem(str(product["cost_per_unit"])))

class ResourcesTableWidget(ModernTableWidget):
    """Custom table widget for resources data"""
    resource_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Resource Name", "Available Capacity"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.itemChanged.connect(self.on_item_changed)
        
    def on_item_changed(self, item):
        # Validate numeric input for capacity column
        if item.column() == 1:  # Capacity column
            try:
                # Try to convert to float
                value = float(item.text())
                # Format to 2 decimal places
                item.setText(f"{value:.2f}")
            except ValueError:
                # If not a valid number, reset to 0
                item.setText("0.00")
                QMessageBox.warning(None, "Invalid Input", "Please enter a valid number.")
        
        self.resource_changed.emit()
        
    def get_resources_data(self):
        resources = []
        for row in range(self.rowCount()):
            name = self.item(row, 0).text() if self.item(row, 0) else ""
            capacity = float(self.item(row, 1).text()) if self.item(row, 1) and self.item(row, 1).text() else 0
            
            if name:
                resources.append({
                    "name": name,
                    "available_capacity": capacity
                })
        return resources
    
    def get_resource_names(self):
        """Get list of all resource names"""
        names = []
        for row in range(self.rowCount()):
            name = self.item(row, 0).text() if self.item(row, 0) else ""
            if name:
                names.append(name)
        return names
        
    def set_resources_data(self, resources):
        self.setRowCount(0)
        for resource in resources:
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(resource["name"]))
            self.setItem(row, 1, QTableWidgetItem(str(resource["available_capacity"])))

class ResourceUsageTableWidget(QTableWidget):
    """Custom table widget for resource usage data with dropdown selection"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Product", "Resource", "Usage per Unit"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        StyleHelper.style_table(self)
        
        # Set row height to accommodate dropdowns
        self.verticalHeader().setDefaultSectionSize(40)
        
        # Initially disable the table
        self.setEnabled(False)
        
        # Product and resource names
        self.product_names = []
        self.resource_names = []
        
        # Connect itemChanged signal for validation
        self.itemChanged.connect(self.validate_numeric_input)
        
    def validate_numeric_input(self, item):
        # Validate numeric input for usage column
        if item.column() == 2:  # Usage column
            try:
                # Try to convert to float
                value = float(item.text())
                # Format to 2 decimal places
                item.setText(f"{value:.2f}")
            except ValueError:
                # If not a valid number, reset to 0
                item.setText("0.00")
                QMessageBox.warning(None, "Invalid Input", "Please enter a valid number.")
    
    def update_product_names(self, names):
        """Update the list of available product names"""
        self.product_names = names
        self.update_dropdowns()
        
    def update_resource_names(self, names):
        """Update the list of available resource names"""
        self.resource_names = names
        self.update_dropdowns()
        
    def update_dropdowns(self):
        """Update all dropdown cells with current product and resource names"""
        for row in range(self.rowCount()):
            # Update product dropdown
            product_combo = self.cellWidget(row, 0)
            if product_combo:
                current_text = product_combo.currentText()
                product_combo.clear()
                product_combo.addItems(self.product_names)
                if current_text in self.product_names:
                    product_combo.setCurrentText(current_text)
            
            # Update resource dropdown
            resource_combo = self.cellWidget(row, 1)
            if resource_combo:
                current_text = resource_combo.currentText()
                resource_combo.clear()
                resource_combo.addItems(self.resource_names)
                if current_text in self.resource_names:
                    resource_combo.setCurrentText(current_text)
        
    def add_empty_row(self):
        """Add a new row with dropdown cells"""
        row = self.rowCount()
        self.insertRow(row)
        
        # Add product dropdown with improved visibility
        product_combo = QComboBox()
        product_combo.addItems(self.product_names)
        product_combo.setMinimumWidth(150)  # Set minimum width
        product_combo.setMaximumWidth(300)  # Set maximum width
        product_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)  # Adjust to content
        StyleHelper.style_combo_box(product_combo)
        self.setCellWidget(row, 0, product_combo)
        
        # Add resource dropdown with improved visibility
        resource_combo = QComboBox()
        resource_combo.addItems(self.resource_names)
        resource_combo.setMinimumWidth(150)  # Set minimum width
        resource_combo.setMaximumWidth(300)  # Set maximum width
        resource_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)  # Adjust to content
        StyleHelper.style_combo_box(resource_combo)
        self.setCellWidget(row, 1, resource_combo)
        
        # Add usage cell
        self.setItem(row, 2, QTableWidgetItem("0.00"))
        
    def get_resource_usage_data(self):
        """Get resource usage data from the table"""
        resource_usage = []
        for row in range(self.rowCount()):
            product_combo = self.cellWidget(row, 0)
            resource_combo = self.cellWidget(row, 1)
            
            if not product_combo or not resource_combo:
                continue
                
            product = product_combo.currentText()
            resource = resource_combo.currentText()
            usage = float(self.item(row, 2).text()) if self.item(row, 2) and self.item(row, 2).text() else 0
            
            if product and resource:
                resource_usage.append({
                    "product_name": product,
                    "resource_name": resource,
                    "usage_per_unit": usage
                })
        return resource_usage
        
    def set_resource_usage_data(self, resource_usage):
        """Set resource usage data in the table"""
        self.setRowCount(0)
        for ru in resource_usage:
            row = self.rowCount()
            self.insertRow(row)
            
            # Add product dropdown with improved visibility
            product_combo = QComboBox()
            product_combo.addItems(self.product_names)
            product_combo.setMinimumWidth(150)  # Set minimum width
            product_combo.setMaximumWidth(300)  # Set maximum width
            product_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)  # Adjust to content
            if ru["product_name"] in self.product_names:
                product_combo.setCurrentText(ru["product_name"])
            StyleHelper.style_combo_box(product_combo)
            self.setCellWidget(row, 0, product_combo)
        
            # Add resource dropdown with improved visibility
            resource_combo = QComboBox()
            resource_combo.addItems(self.resource_names)
            resource_combo.setMinimumWidth(150)  # Set minimum width
            resource_combo.setMaximumWidth(300)  # Set maximum width
            resource_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)  # Adjust to content
            if ru["resource_name"] in self.resource_names:
                resource_combo.setCurrentText(ru["resource_name"])
            StyleHelper.style_combo_box(resource_combo)
            self.setCellWidget(row, 1, resource_combo)
        
            # Add usage cell
            self.setItem(row, 2, QTableWidgetItem(f"{ru['usage_per_unit']:.2f}"))
            
    def check_enable_state(self):
        """Check if the table should be enabled based on product and resource names"""
        should_enable = len(self.product_names) > 0 and len(self.resource_names) > 0
        self.setEnabled(should_enable)
        return should_enable

class DemandConstraintsTableWidget(QTableWidget):
    """Custom table widget for demand constraints data with dropdown selection for products"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Product", "Min Demand", "Max Demand"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        StyleHelper.style_table(self)
        
        # Set row height to accommodate dropdowns
        self.verticalHeader().setDefaultSectionSize(40)
        
        # Initially disable the table
        self.setEnabled(False)
        
        # Product names
        self.product_names = []
        
        # Connect itemChanged signal for validation
        self.itemChanged.connect(self.validate_numeric_input)
        
    def validate_numeric_input(self, item):
        # Validate numeric inputs for min and max demand columns
        if item.column() in [1, 2]:  # Min or Max demand column
            if item.text():  # Only validate if not empty
                try:
                    # Try to convert to float
                    value = float(item.text())
                    # Format to 2 decimal places
                    item.setText(f"{value:.2f}")
                except ValueError:
                    # If not a valid number, reset to empty
                    item.setText("")
                    QMessageBox.warning(None, "Invalid Input", "Please enter a valid number.")
    
    def update_product_names(self, names):
        """Update the list of available product names"""
        self.product_names = names
        self.update_dropdowns()
        
    def update_dropdowns(self):
        """Update all dropdown cells with current product names"""
        for row in range(self.rowCount()):
            # Update product dropdown
            product_combo = self.cellWidget(row, 0)
            if product_combo:
                current_text = product_combo.currentText()
                product_combo.clear()
                product_combo.addItems(self.product_names)
                if current_text in self.product_names:
                    product_combo.setCurrentText(current_text)
        
    def add_empty_row(self):
        """Add a new row with dropdown cells"""
        row = self.rowCount()
        self.insertRow(row)
        
        # Add product dropdown with improved visibility
        product_combo = QComboBox()
        product_combo.addItems(self.product_names)
        product_combo.setMinimumWidth(150)  # Set minimum width
        product_combo.setMaximumWidth(300)  # Set maximum width
        product_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)  # Adjust to content
        StyleHelper.style_combo_box(product_combo)
        self.setCellWidget(row, 0, product_combo)
        
        # Add min demand cell
        self.setItem(row, 1, QTableWidgetItem(""))
        
        # Add max demand cell
        self.setItem(row, 2, QTableWidgetItem(""))
        
    def get_demand_constraints_data(self):
        """Get demand constraints data from the table"""
        demand_constraints = []
        for row in range(self.rowCount()):
            product_combo = self.cellWidget(row, 0)
            
            if not product_combo:
                continue
                
            product = product_combo.currentText()
            min_demand = self.item(row, 1).text() if self.item(row, 1) else ""
            max_demand = self.item(row, 2).text() if self.item(row, 2) else ""
            
            if product:
                constraint = {"product_name": product}
                if min_demand:
                    constraint["min_demand"] = float(min_demand)
                if max_demand:
                    constraint["max_demand"] = float(max_demand)
                demand_constraints.append(constraint)
        return demand_constraints
        
    def set_demand_constraints_data(self, demand_constraints):
        """Set demand constraints data in the table"""
        self.setRowCount(0)
        for dc in demand_constraints:
            row = self.rowCount()
            self.insertRow(row)
            
            # Add product dropdown with improved visibility
            product_combo = QComboBox()
            product_combo.addItems(self.product_names)
            product_combo.setMinimumWidth(150)  # Set minimum width
            product_combo.setMaximumWidth(300)  # Set maximum width
            product_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)  # Adjust to content
            if dc["product_name"] in self.product_names:
                product_combo.setCurrentText(dc["product_name"])
            StyleHelper.style_combo_box(product_combo)
            self.setCellWidget(row, 0, product_combo)
            
            # Add min demand cell
            if "min_demand" in dc:
                self.setItem(row, 1, QTableWidgetItem(f"{dc['min_demand']:.2f}"))
            else:
                self.setItem(row, 1, QTableWidgetItem(""))
                
            # Add max demand cell
            if "max_demand" in dc:
                self.setItem(row, 2, QTableWidgetItem(f"{dc['max_demand']:.2f}"))
            else:
                self.setItem(row, 2, QTableWidgetItem(""))
                
    def check_enable_state(self):
        """Check if the table should be enabled based on product names"""
        should_enable = len(self.product_names) > 0
        self.setEnabled(should_enable)
        return should_enable

class ModernGroupBox(QGroupBox):
    """Custom styled group box"""
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        StyleHelper.style_group_box(self)
        StyleHelper.add_shadow(self)

class ModernButton(QPushButton):
    """Custom styled button"""
    def __init__(self, text, parent=None, primary=False):
        super().__init__(text, parent)
        StyleHelper.style_button(self, primary)
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Production Optimization")
        self.setMinimumSize(1200, 800)
        self.from_launcher = "--from-launcher" in sys.argv
        
        # Initialize UI components
        self.init_ui()
        
        # Initialize data
        self.current_result = None
        self.optimization_thread = None
        
    def init_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #f8f9fa;")
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create header
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #ffffff; border-radius: 10px;")
        StyleHelper.add_shadow(header_widget)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # App title
        header_label = QLabel("Production Optimization")
        header_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        header_label.setStyleSheet("color: #3b82f6;")
        header_layout.addWidget(header_label)
        
        # Add optimizer type selector
        self.optimizer_combo = QComboBox()
        self.optimizer_combo.setMinimumWidth(200)
        StyleHelper.style_combo_box(self.optimizer_combo)
        header_layout.addWidget(QLabel("Optimizer:"))
        header_layout.addWidget(self.optimizer_combo)
        
        # Add objective selector
        self.objective_combo = QComboBox()
        self.objective_combo.addItems(["maximize_profit", "minimize_cost"])
        StyleHelper.style_combo_box(self.objective_combo)
        header_layout.addWidget(QLabel("Objective:"))
        header_layout.addWidget(self.objective_combo)
        
        # Add spacer and buttons
        header_layout.addStretch()
        
        self.load_button = ModernButton("Load Example")
        self.load_button.clicked.connect(self.load_example)
        header_layout.addWidget(self.load_button)
        
        self.save_button = ModernButton("Save")
        self.save_button.clicked.connect(self.save_data)
        header_layout.addWidget(self.save_button)
        
        self.optimize_button = ModernButton("Optimize", primary=True)
        self.optimize_button.clicked.connect(self.run_optimization)
        header_layout.addWidget(self.optimize_button)
        
        if self.from_launcher:
          self.return_button = ModernButton("Return to Launcher")
          self.return_button.clicked.connect(self.return_to_launcher)
          header_layout.addWidget(self.return_button)
        
        main_layout.addWidget(header_widget)
        
        # Create tab widget for input and results
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f1f5f9;
                color: #1e293b;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3b82f6;
                color: #ffffff;
                font-weight: bold;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)
        StyleHelper.add_shadow(self.tab_widget)
        
        # Input tab
        input_tab = QWidget()
        input_layout = QVBoxLayout(input_tab)
        input_layout.setContentsMargins(15, 15, 15, 15)
        input_layout.setSpacing(15)
        
        # Create splitter for input sections
        input_splitter = QSplitter(Qt.Vertical)
        input_splitter.setStyleSheet("QSplitter::handle { background-color: #e2e8f0; }")
        
        # Products and Resources section
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(15)
        
        # Products group
        products_group = ModernGroupBox("Products")
        products_layout = QVBoxLayout(products_group)
        products_layout.setContentsMargins(15, 25, 15, 15)
        products_layout.setSpacing(10)
        
        self.products_table = ProductsTableWidget()
        products_layout.addWidget(self.products_table)
        
        products_buttons_layout = QHBoxLayout()
        add_product_button = ModernButton("Add Product")
        add_product_button.clicked.connect(self.products_table.add_empty_row)
        products_buttons_layout.addWidget(add_product_button)
        
        remove_product_button = ModernButton("Remove Selected")
        remove_product_button.clicked.connect(lambda: self.products_table.removeRow(self.products_table.currentRow()))
        products_buttons_layout.addWidget(remove_product_button)
        
        products_layout.addLayout(products_buttons_layout)
        top_layout.addWidget(products_group)
        
        # Resources group
        resources_group = ModernGroupBox("Resources")
        resources_layout = QVBoxLayout(resources_group)
        resources_layout.setContentsMargins(15, 25, 15, 15)
        resources_layout.setSpacing(10)
        
        self.resources_table = ResourcesTableWidget()
        resources_layout.addWidget(self.resources_table)
        
        resources_buttons_layout = QHBoxLayout()
        add_resource_button = ModernButton("Add Resource")
        add_resource_button.clicked.connect(self.resources_table.add_empty_row)
        resources_buttons_layout.addWidget(add_resource_button)
        
        remove_resource_button = ModernButton("Remove Selected")
        remove_resource_button.clicked.connect(lambda: self.resources_table.removeRow(self.resources_table.currentRow()))
        resources_buttons_layout.addWidget(remove_resource_button)
        
        resources_layout.addLayout(resources_buttons_layout)
        top_layout.addWidget(resources_group)
        
        input_splitter.addWidget(top_widget)
        
        # Resource Usage section
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        resource_usage_group = ModernGroupBox("Resource Usage")
        resource_usage_layout = QVBoxLayout(resource_usage_group)
        resource_usage_layout.setContentsMargins(15, 25, 15, 15)
        resource_usage_layout.setSpacing(10)
        
        self.resource_usage_table = ResourceUsageTableWidget()
        resource_usage_layout.addWidget(self.resource_usage_table)
        
        resource_usage_buttons_layout = QHBoxLayout()
        self.add_usage_button = ModernButton("Add Resource Usage")
        self.add_usage_button.clicked.connect(self.resource_usage_table.add_empty_row)
        self.add_usage_button.setEnabled(False)  # Initially disabled
        resource_usage_buttons_layout.addWidget(self.add_usage_button)
        
        self.remove_usage_button = ModernButton("Remove Selected")
        self.remove_usage_button.clicked.connect(lambda: self.resource_usage_table.removeRow(self.resource_usage_table.currentRow()))
        self.remove_usage_button.setEnabled(False)  # Initially disabled
        resource_usage_buttons_layout.addWidget(self.remove_usage_button)
        
        resource_usage_layout.addLayout(resource_usage_buttons_layout)
        middle_layout.addWidget(resource_usage_group)
        
        input_splitter.addWidget(middle_widget)
        
        # Constraints section
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        constraints_group = ModernGroupBox("Constraints")
        constraints_layout = QVBoxLayout(constraints_group)
        constraints_layout.setContentsMargins(15, 25, 15, 15)
        constraints_layout.setSpacing(10)
        
        # Demand constraints
        demand_constraints_label = QLabel("Demand Constraints")
        demand_constraints_label.setStyleSheet("color: #1e293b; font-weight: bold;")
        constraints_layout.addWidget(demand_constraints_label)
        
        self.demand_constraints_table = DemandConstraintsTableWidget()

        # Add buttons for demand constraints with initial disabled state
        self.add_demand_button = ModernButton("Add Demand Constraint")
        self.add_demand_button.clicked.connect(self.demand_constraints_table.add_empty_row)
        self.add_demand_button.setEnabled(False)  # Initially disabled
        demand_buttons_layout = QHBoxLayout()
        demand_buttons_layout.addWidget(self.add_demand_button)

        self.remove_demand_button = ModernButton("Remove Selected")
        self.remove_demand_button.clicked.connect(lambda: self.demand_constraints_table.removeRow(self.demand_constraints_table.currentRow()))
        self.remove_demand_button.setEnabled(False)  # Initially disabled
        demand_buttons_layout.addWidget(self.remove_demand_button)

        constraints_layout.addWidget(self.demand_constraints_table)
        
        constraints_layout.addLayout(demand_buttons_layout)
        
        # Total constraints
        total_constraints_group = QGroupBox("Total Production Constraints")
        total_constraints_group.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                margin-top: 15px;
                color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
        """)
        total_constraints_layout = QFormLayout(total_constraints_group)
        total_constraints_layout.setContentsMargins(15, 15, 15, 15)
        total_constraints_layout.setSpacing(10)
        
        self.min_total_spin = QDoubleSpinBox()
        self.min_total_spin.setRange(0, 1000000)
        self.min_total_spin.setSpecialValueText("None")
        StyleHelper.style_spin_box(self.min_total_spin)
        total_constraints_layout.addRow("Minimum Total:", self.min_total_spin)
        
        self.max_total_spin = QDoubleSpinBox()
        self.max_total_spin.setRange(0, 1000000)
        self.max_total_spin.setSpecialValueText("None")
        StyleHelper.style_spin_box(self.max_total_spin)
        total_constraints_layout.addRow("Maximum Total:", self.max_total_spin)
        
        constraints_layout.addWidget(total_constraints_group)
        
        bottom_layout.addWidget(constraints_group)
        input_splitter.addWidget(bottom_widget)
        
        input_layout.addWidget(input_splitter)
        self.tab_widget.addTab(input_tab, "Input Data")
        
        # Results tab
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        results_layout.setContentsMargins(15, 15, 15, 15)
        results_layout.setSpacing(15)
        
        results_splitter = QSplitter(Qt.Vertical)
        results_splitter.setStyleSheet("QSplitter::handle { background-color: #e2e8f0; }")
        
        # Status section
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(15)
        
        status_group = ModernGroupBox("Optimization Status")
        status_group_layout = QFormLayout(status_group)
        status_group_layout.setContentsMargins(15, 25, 15, 15)
        status_group_layout.setSpacing(10)
        
        self.status_label = QLabel("Not optimized")
        self.status_label.setStyleSheet("color: #1e293b; font-weight: bold;")
        status_group_layout.addRow("Status:", self.status_label)
        
        self.objective_value_label = QLabel("-")
        self.objective_value_label.setStyleSheet("color: #1e293b;")
        status_group_layout.addRow("Objective Value:", self.objective_value_label)
        
        self.total_production_label = QLabel("-")
        self.total_production_label.setStyleSheet("color: #1e293b;")
        status_group_layout.addRow("Total Production:", self.total_production_label)
        
        status_layout.addWidget(status_group)
        
        # Messages section
        messages_group = ModernGroupBox("Messages")
        messages_layout = QVBoxLayout(messages_group)
        messages_layout.setContentsMargins(15, 25, 15, 15)
        
        self.messages_text = QTextEdit()
        self.messages_text.setReadOnly(True)
        StyleHelper.style_text_edit(self.messages_text)
        messages_layout.addWidget(self.messages_text)
        
        status_layout.addWidget(messages_group)
        
        results_splitter.addWidget(status_widget)
        
        # Charts section
        charts_widget = QWidget()
        charts_layout = QHBoxLayout(charts_widget)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        charts_layout.setSpacing(15)
        
        # Production plan chart
        production_chart_group = ModernGroupBox("Production Plan")
        production_chart_layout = QVBoxLayout(production_chart_group)
        production_chart_layout.setContentsMargins(15, 25, 15, 15)
        
        self.production_chart = ProductionChart()
        production_chart_layout.addWidget(self.production_chart)
        
        charts_layout.addWidget(production_chart_group)
        
        # Resource utilization chart
        resource_chart_group = ModernGroupBox("Resource Utilization")
        resource_chart_layout = QVBoxLayout(resource_chart_group)
        resource_chart_layout.setContentsMargins(15, 25, 15, 15)
        
        self.resource_chart = ResourceUsageChart()
        resource_chart_layout.addWidget(self.resource_chart)
        
        charts_layout.addWidget(resource_chart_group)
        
        results_splitter.addWidget(charts_widget)
        
        # Detailed results section
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        details_group = ModernGroupBox("Detailed Results")
        details_group_layout = QVBoxLayout(details_group)
        details_group_layout.setContentsMargins(15, 25, 15, 15)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        StyleHelper.style_text_edit(self.results_text)
        details_group_layout.addWidget(self.results_text)
        
        details_layout.addWidget(details_group)
        results_splitter.addWidget(details_widget)
        
        results_layout.addWidget(results_splitter)
        self.tab_widget.addTab(results_tab, "Results")
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #ffffff;
                color: #1e293b;
                border-top: 1px solid #e2e8f0;
            }
        """)
        
        # Connect signals for updating resource usage table
        self.products_table.product_changed.connect(self.update_resource_usage_dropdowns)
        self.resources_table.resource_changed.connect(self.update_resource_usage_dropdowns)
        
        # Connect demand constraints table to check for optimizer type
        self.demand_constraints_table.itemChanged.connect(self.check_optimizer_type)
        
        # Fetch available optimizers
        self.fetch_optimizers()
    
    def return_to_launcher(self):
      """Return to the application launcher"""
      self.close()
      # Try to bring the launcher window back to the foreground
      try:
          # This is a simple approach - in a real app, you might want to use
          # inter-process communication to signal the launcher
          if os.name == 'nt':  # Windows
              os.system('python app_launcher.py &')
          else:  # Linux/Mac
              os.system('python3 app_launcher.py &')
      except Exception as e:
          print(f"Error returning to launcher: {e}")

    def update_resource_usage_dropdowns(self):
        """Update the resource usage and demand constraints tables with current product and resource names"""
        product_names = self.products_table.get_product_names()
        resource_names = self.resources_table.get_resource_names()
        
        # Update resource usage table
        self.resource_usage_table.update_product_names(product_names)
        self.resource_usage_table.update_resource_names(resource_names)
        
        # Enable/disable the resource usage table and buttons based on available products and resources
        resource_usage_enabled = self.resource_usage_table.check_enable_state()
        self.add_usage_button.setEnabled(resource_usage_enabled)
        self.remove_usage_button.setEnabled(resource_usage_enabled)
        
        # Update demand constraints table
        self.demand_constraints_table.update_product_names(product_names)
        
        # Enable/disable the demand constraints table and buttons based on available products
        demand_constraints_enabled = self.demand_constraints_table.check_enable_state()
        self.add_demand_button.setEnabled(demand_constraints_enabled)
        self.remove_demand_button.setEnabled(demand_constraints_enabled)
        
        if resource_usage_enabled:
            self.statusBar().showMessage("Resource usage table enabled", 3000)
        if demand_constraints_enabled:
            self.statusBar().showMessage("Demand constraints table enabled", 3000)
        
    def fetch_optimizers(self):
        """Fetch available optimizers from the API"""
        try:
            response = requests.get(f"{API_BASE_URL}/production/optimizers")
            if response.status_code == 200:
                optimizers = response.json().get('optimizers', [])
                # Filter to only allowed optimizers
                filtered_optimizers = [opt for opt in optimizers if opt in ALLOWED_OPTIMIZERS]
                self.optimizer_combo.addItems(filtered_optimizers)
                
                # Default to basic-production
                index = self.optimizer_combo.findText("basic-production")
                if index >= 0:
                    self.optimizer_combo.setCurrentIndex(index)
            else:
                QMessageBox.warning(self, "API Error", f"Failed to fetch optimizers: {response.status_code}")
        except Exception as e:
            QMessageBox.warning(self, "Connection Error", f"Failed to connect to API: {str(e)}")
            
    def check_optimizer_type(self, item=None):
        """Check if demand constraints are defined and switch optimizer type if needed"""
        demand_constraints = self.demand_constraints_table.get_demand_constraints_data()
        if demand_constraints:
            # Switch to demand-constrained-production
            index = self.optimizer_combo.findText("demand-constrained-production")
            if index >= 0 and self.optimizer_combo.currentText() == "basic-production":
                self.optimizer_combo.setCurrentIndex(index)
                self.statusBar().showMessage("Switched to demand-constrained optimizer due to demand constraints", 5000)
            
    def get_input_data(self):
        """Collect all input data from UI components"""
        data = {
            "objective": self.objective_combo.currentText(),
            "products": self.products_table.get_products_data(),
            "resources": self.resources_table.get_resources_data(),
            "resource_usage": self.resource_usage_table.get_resource_usage_data()
        }
        
        # Add demand constraints if any
        demand_constraints = self.demand_constraints_table.get_demand_constraints_data()
        if demand_constraints:
            data["demand_constraints"] = demand_constraints
            
        # Add total constraints if any
        min_total = self.min_total_spin.value() if self.min_total_spin.value() > 0 else None
        max_total = self.max_total_spin.value() if self.max_total_spin.value() > 0 else None
        
        if min_total is not None or max_total is not None:
            data["total_constraints"] = {}
            if min_total is not None:
                data["total_constraints"]["min_total"] = min_total
            if max_total is not None:
                data["total_constraints"]["max_total"] = max_total
                
        return data
        
    def set_input_data(self, data):
        """Set input data to UI components"""
        # Set objective
        index = self.objective_combo.findText(data.get("objective", "maximize_profit"))
        if index >= 0:
            self.objective_combo.setCurrentIndex(index)
            
        # Set products
        self.products_table.set_products_data(data.get("products", []))
        
        # Set resources
        self.resources_table.set_resources_data(data.get("resources", []))
        
        # Update resource usage dropdowns before setting data
        self.update_resource_usage_dropdowns()
        
        # Set resource usage
        self.resource_usage_table.set_resource_usage_data(data.get("resource_usage", []))
        
        # Update demand constraints dropdowns before setting data
        self.demand_constraints_table.update_product_names(self.products_table.get_product_names())
        self.demand_constraints_table.set_demand_constraints_data(data.get("demand_constraints", []))
        
        # Set total constraints
        total_constraints = data.get("total_constraints", {})
        
        min_total = total_constraints.get("min_total", 0)
        if min_total is not None:
            self.min_total_spin.setValue(min_total)
        else:
            self.min_total_spin.setValue(0)
            
        max_total = total_constraints.get("max_total", 0)
        if max_total is not None:
            self.max_total_spin.setValue(max_total)
        else:
            self.max_total_spin.setValue(0)
            
        # Check if we need to switch optimizer type
        self.check_optimizer_type(None)
            
    def load_example(self):
        """Load example data"""
        options = ["Demand Constrained"]
        selected, ok = QInputDialog.getItem(self, "Select Example", 
                                          "Choose an example:", options, 0, False)
        if ok and selected:
            try:
                with open("example_demand_constrained.json", "r") as f:
                    data = json.load(f)
                        
                self.set_input_data(data)
                self.statusBar().showMessage(f"Loaded {selected} example")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load example: {str(e)}")
                
    def save_data(self):
        """Save current input data to file"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "JSON Files (*.json)")
        if file_path:
            try:
                data = self.get_input_data()
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)
                self.statusBar().showMessage(f"Data saved to {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save data: {str(e)}")
                
    def run_optimization(self):
        """Run optimization with current input data"""
        try:
            # Validate input data
            data = self.get_input_data()
            
            if not data["products"]:
                QMessageBox.warning(self, "Validation Error", "No products defined")
                return
                
            if not data["resources"]:
                QMessageBox.warning(self, "Validation Error", "No resources defined")
                return
                
            if not data["resource_usage"]:
                QMessageBox.warning(self, "Validation Error", "No resource usage defined")
                return
                
            # Get optimizer type
            optimizer_type = self.optimizer_combo.currentText()
            if not optimizer_type:
                QMessageBox.warning(self, "Validation Error", "No optimizer selected")
                return
                
            # Check if we need to switch optimizer type
            if "demand_constraints" in data and optimizer_type == "basic-production":
                optimizer_type = "demand-constrained-production"
                index = self.optimizer_combo.findText(optimizer_type)
                if index >= 0:
                    self.optimizer_combo.setCurrentIndex(index)
                    self.statusBar().showMessage("Switched to demand-constrained optimizer due to demand constraints", 5000)
                
            # Disable optimize button and show status
            self.optimize_button.setEnabled(False)
            self.statusBar().showMessage("Optimizing...")
            
            # Switch to results tab
            self.tab_widget.setCurrentIndex(1)
            
            # Clear previous results
            self.status_label.setText("Running...")
            self.objective_value_label.setText("-")
            self.total_production_label.setText("-")
            self.messages_text.clear()
            self.results_text.clear()
            
            # Run optimization in a separate thread
            self.optimization_thread = OptimizationThread(optimizer_type, data)
            self.optimization_thread.result_ready.connect(self.handle_optimization_result)
            self.optimization_thread.error_occurred.connect(self.handle_optimization_error)
            self.optimization_thread.start()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to run optimization: {str(e)}")
            self.optimize_button.setEnabled(True)
            
    def handle_optimization_result(self, result):
        """Handle optimization result"""
        self.current_result = result
        self.optimize_button.setEnabled(True)
        self.statusBar().showMessage("Optimization completed")
        
        # Update status
        status = result.get("status", "unknown")
        self.status_label.setText(status)
        
        # Set status label color based on result
        if status == "optimal":
            self.status_label.setStyleSheet(f"color: {StyleHelper.get_success_color().name()}; font-weight: bold;")
        elif status == "solution_warning":
            self.status_label.setStyleSheet(f"color: {StyleHelper.get_warning_color().name()}; font-weight: bold;")
        elif status in ["infeasible", "error", "validation_error"]:
            self.status_label.setStyleSheet(f"color: {StyleHelper.get_error_color().name()}; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #1e293b; font-weight: bold;")
            
        # Update objective value
        if "objective_value" in result:
            self.objective_value_label.setText(f"{result['objective_value']:.4f}")
        else:
            self.objective_value_label.setText("-")
            
        # Update total production
        if "total_production" in result:
            self.total_production_label.setText(f"{result['total_production']:.4f}")
        elif "production_plan" in result:
            total = sum(result["production_plan"].values())
            self.total_production_label.setText(f"{total:.4f}")
        else:
            self.total_production_label.setText("-")
            
        # Update messages
        self.messages_text.clear()
        
        if status == "validation_error" and "validation_errors" in result:
            self.messages_text.append("<span style='color: #ef4444; font-weight: bold;'>Validation Errors:</span>")
            for error in result["validation_errors"]:
                self.messages_text.append(f"• <span style='color: #ef4444;'>{error}</span>")
                
        if "solver_message" in result:
            self.messages_text.append(f"<span style='color: #3b82f6; font-weight: bold;'>Solver Message:</span> {result['solver_message']}")
            
        if "feasibility_warnings" in result and result["feasibility_warnings"]:
            self.messages_text.append("<span style='color: #eab308; font-weight: bold;'>Feasibility Warnings:</span>")
            for warning in result["feasibility_warnings"]:
                self.messages_text.append(f"• <span style='color: #eab308;'>{warning}</span>")
                
        # Update charts
        if "production_plan" in result:
            self.production_chart.update_chart(result["production_plan"])
            
        if "resource_utilization" in result:
            self.resource_chart.update_chart(result["resource_utilization"])
            
        # Update detailed results
        self.results_text.clear()
        self.results_text.append(json.dumps(result, indent=2))
        
    def handle_optimization_error(self, error_message):
        """Handle optimization error"""
        self.optimize_button.setEnabled(True)
        self.statusBar().showMessage("Optimization failed")
        
        self.status_label.setText("Error")
        self.status_label.setStyleSheet(f"color: {StyleHelper.get_error_color().name()}; font-weight: bold;")
        
        self.messages_text.clear()
        self.messages_text.append(f"<span style='color: #ef4444; font-weight: bold;'>Error:</span> {error_message}")
        
        QMessageBox.critical(self, "Optimization Error", error_message)

def main():
    app = QApplication(sys.argv)
    StyleHelper.apply_futuristic_light_theme(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
