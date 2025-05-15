import os
import sys
import json
import requests
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QComboBox, QPushButton, 
                              QTableWidget, QTableWidgetItem, QTabWidget, 
                              QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, 
                              QScrollArea, QSplitter, QGroupBox, QMessageBox,
                              QTextEdit, QHeaderView, QFrame, QCheckBox,
                              QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor

# Base URL for API endpoints
API_BASE_URL = "http://localhost:5000/production"

class OptimizationResultWidget(QWidget):
    """Widget to display optimization results"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Summary section
        summary_group = QGroupBox("Optimization Summary")
        summary_layout = QFormLayout()
        
        self.status_label = QLabel("--")
        self.status_label.setProperty("class", "result-status")
        self.objective_value_label = QLabel("--")
        self.solve_time_label = QLabel("--")
        self.objective_type_label = QLabel("--")
        
        summary_layout.addRow("Status:", self.status_label)
        summary_layout.addRow("Objective Type:", self.objective_type_label)
        summary_layout.addRow("Objective Value:", self.objective_value_label)
        summary_layout.addRow("Solve Time:", self.solve_time_label)
        summary_group.setLayout(summary_layout)
        
        # Production plan table
        plan_group = QGroupBox("Production Plan")
        plan_layout = QVBoxLayout()
        
        self.production_table = QTableWidget()
        self.production_table.setAlternatingRowColors(True)
        self.production_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        plan_layout.addWidget(self.production_table)
        plan_group.setLayout(plan_layout)
        
        # Resource utilization table
        resource_group = QGroupBox("Resource Utilization")
        resource_layout = QVBoxLayout()
        
        self.resource_table = QTableWidget()
        self.resource_table.setAlternatingRowColors(True)
        self.resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        resource_layout.addWidget(self.resource_table)
        resource_group.setLayout(resource_layout)
        
        # Messages and warnings
        messages_group = QGroupBox("Messages & Warnings")
        messages_layout = QVBoxLayout()
        
        self.messages_text = QTextEdit()
        self.messages_text.setReadOnly(True)
        
        messages_layout.addWidget(self.messages_text)
        messages_group.setLayout(messages_layout)
        
        # Add all sections to main layout
        layout.addWidget(summary_group)
        layout.addWidget(plan_group)
        layout.addWidget(resource_group)
        layout.addWidget(messages_group)
        
    def display_results(self, result_data: Dict[str, Any], objective_type: str):
        """Display optimization results in the UI"""
        # Update summary fields
        self.status_label.setText(result_data.get("status", "Unknown"))
        
        if result_data.get("status") == "optimal":
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        elif result_data.get("status") == "infeasible":
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        self.objective_type_label.setText(objective_type.replace("_", " ").title())
        value_prefix = "$" if objective_type == "maximize_profit" or objective_type == "minimize_cost" else ""
        self.objective_value_label.setText(f"{value_prefix}{result_data.get('objective_value', 0):.2f}")
        self.solve_time_label.setText(f"{result_data.get('solve_time', 0):.4f} seconds")
        
        # Update production plan table
        production_plan = result_data.get("production_plan", {})
        self.production_table.clear()
        
        if production_plan:
            self.production_table.setColumnCount(2)
            self.production_table.setHorizontalHeaderLabels(["Product", "Quantity"])
            self.production_table.setRowCount(len(production_plan))
            
            for row, (product, quantity) in enumerate(production_plan.items()):
                self.production_table.setItem(row, 0, QTableWidgetItem(product))
                quantity_item = QTableWidgetItem(f"{quantity:.2f}")
                quantity_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.production_table.setItem(row, 1, quantity_item)
        
        # Update resource utilization table
        resource_usage = result_data.get("resource_utilization", {})
        self.resource_table.clear()
        
        if resource_usage:
            self.resource_table.setColumnCount(3)
            self.resource_table.setHorizontalHeaderLabels(["Resource", "Used", "Available"])
            self.resource_table.setRowCount(len(resource_usage))
            
            for row, (resource, usage) in enumerate(resource_usage.items()):
                self.resource_table.setItem(row, 0, QTableWidgetItem(resource))
                
                used_item = QTableWidgetItem(f"{usage.get('used', 0):.2f}")
                used_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.resource_table.setItem(row, 1, used_item)
                
                available_item = QTableWidgetItem(f"{usage.get('available', 0):.2f}")
                available_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.resource_table.setItem(row, 2, available_item)
        
        # Update messages
        messages = []
        
        # Add solver message if present
        if "solver_message" in result_data:
            messages.append(f"🔍 Solver Message: {result_data['solver_message']}")
        
        # Add any feasibility warnings
        if "feasibility_warnings" in result_data and result_data["feasibility_warnings"]:
            messages.append("\n⚠️ Feasibility Warnings:")
            for warning in result_data["feasibility_warnings"]:
                messages.append(f"  • {warning}")
        
        # Add infeasible constraints if present
        if "infeasible_constraints" in result_data and result_data["infeasible_constraints"]:
            messages.append("\n❌ Infeasible Constraints:")
            for constraint, info in result_data["infeasible_constraints"].items():
                messages.append(f"  • {constraint}: {info}")
        
        self.messages_text.setText("\n".join(messages))


class ResourceInputForm(QWidget):
    """Form for entering resources and their available capacities"""
    
    resource_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resources = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Resources table
        self.resources_table = QTableWidget()
        self.resources_table.setColumnCount(2)
        self.resources_table.setHorizontalHeaderLabels([
            "Resource Name", "Available Capacity"
        ])
        self.resources_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resources_table.setAlternatingRowColors(True)
        
        # Controls for adding resources
        input_layout = QHBoxLayout()
        
        self.resource_name = QLineEdit()
        self.resource_name.setPlaceholderText("Resource Name")
        
        self.available_capacity = QDoubleSpinBox()
        self.available_capacity.setRange(0, 1000000)
        self.available_capacity.setValue(100)
        
        add_button = QPushButton("Add Resource")
        add_button.clicked.connect(self.add_resource)
        
        input_layout.addWidget(self.resource_name)
        input_layout.addWidget(self.available_capacity)
        input_layout.addWidget(add_button)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected_resource)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(remove_button)
        buttons_layout.addStretch()
        
        layout.addLayout(input_layout)
        layout.addWidget(self.resources_table)
        layout.addLayout(buttons_layout)
        
        # Add some sample resources
        self.add_sample_resources()
        
        # Connect table item changed signal to update resources list
        self.setup_table_connections()
        
    def setup_table_connections(self):
        """Setup connections to capture table edits"""
        self.resources_table.itemChanged.connect(self.on_table_item_changed)
    
    def on_table_item_changed(self, item):
        """Update the resources list when a table item is edited"""
        row = item.row()
        col = item.column()
        
        if row >= len(self.resources):
            return
            
        resource = self.resources[row]
        
        # Based on which column was edited, update the correct field
        if col == 0:  # Resource name
            resource["name"] = item.text()
        elif col == 1:  # Available capacity
            try:
                resource["available_capacity"] = float(item.text())
            except ValueError:
                pass
        
        self.resource_changed.emit()
                
    def add_sample_resources(self):
        """Add some sample resources to get started"""
        sample_resources = [
            {"name": "Machine Time", "available_capacity": 200},
            {"name": "Raw Material", "available_capacity": 150},
        ]
        
        for resource in sample_resources:
            self.resources.append(resource)
            
        self.update_table()
        self.resource_changed.emit()
    
    def add_resource(self):
        """Add a resource to the table"""
        resource_name = self.resource_name.text().strip()
        if not resource_name:
            QMessageBox.warning(self, "Input Error", "Resource name cannot be empty")
            return
            
        # Check for duplicate resource names
        names = [r["name"] for r in self.resources]
        if resource_name in names:
            QMessageBox.warning(self, "Input Error", f"Resource '{resource_name}' already exists")
            return
            
        resource = {
            "name": resource_name,
            "available_capacity": self.available_capacity.value()
        }
        
        self.resources.append(resource)
        self.update_table()
        self.resource_changed.emit()
        
        # Clear inputs for next resource
        self.resource_name.clear()
        
    def remove_selected_resource(self):
        """Remove the selected resource from the table"""
        selected_rows = self.resources_table.selectedIndexes()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        if 0 <= row < len(self.resources):
            del self.resources[row]
            self.update_table()
            self.resource_changed.emit()
    
    def update_table(self):
        """Update the resources table with current data"""
        # Temporarily disconnect the itemChanged signal to avoid recursion
        try:
            self.resources_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass
        self.resources_table.setRowCount(len(self.resources))
        
        for row, resource in enumerate(self.resources):
            self.resources_table.setItem(row, 0, QTableWidgetItem(resource["name"]))
            
            capacity_item = QTableWidgetItem(f"{resource['available_capacity']:.2f}")
            capacity_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.resources_table.setItem(row, 1, capacity_item)
        
        # Reconnect the signal
        self.resources_table.itemChanged.connect(self.on_table_item_changed)
    
    def get_resources_data(self) -> List[Dict[str, Any]]:
        """Get the resources data in a format suitable for the API"""
        return self.resources


class ProductInputForm(QWidget):
    """Form for entering products and their properties"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.products = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(3)
        self.products_table.setHorizontalHeaderLabels([
            "Product", "Price Per Unit", "Cost Per Unit"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.setAlternatingRowColors(True)
        
        # Controls for adding products
        input_layout = QHBoxLayout()
        
        self.product_name = QLineEdit()
        self.product_name.setPlaceholderText("Product Name")
        
        self.profit_per_unit = QDoubleSpinBox()
        self.profit_per_unit.setRange(0, 10000)
        self.profit_per_unit.setPrefix("$")
        self.profit_per_unit.setValue(10)
        
        self.cost_per_unit = QDoubleSpinBox()
        self.cost_per_unit.setRange(0, 10000)
        self.cost_per_unit.setPrefix("$")
        self.cost_per_unit.setValue(5)
        
        add_button = QPushButton("Add Product")
        add_button.clicked.connect(self.add_product)
        
        input_layout.addWidget(self.product_name)
        input_layout.addWidget(self.profit_per_unit)
        input_layout.addWidget(self.cost_per_unit)
        input_layout.addWidget(add_button)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected_product)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(remove_button)
        buttons_layout.addStretch()
        
        layout.addLayout(input_layout)
        layout.addWidget(self.products_table)
        layout.addLayout(buttons_layout)
        
        # Add some sample products
        self.add_sample_products()
        
        # Connect table item changed signal to update products list
        self.setup_table_connections()
        
    def setup_table_connections(self):
        """Setup connections to capture table edits"""
        self.products_table.itemChanged.connect(self.on_table_item_changed)
    
    def on_table_item_changed(self, item):
        """Update the products list when a table item is edited"""
        row = item.row()
        col = item.column()
        
        if row >= len(self.products):
            return
            
        product = self.products[row]
        
        # Based on which column was edited, update the correct field
        if col == 0:  # Product name
            product["name"] = item.text()
        elif col == 1:  # Profit per unit
            try:
                # Strip the "$" and convert to float
                profit_text = item.text().replace("$", "").strip()
                product["profit_per_unit"] = float(profit_text)
            except ValueError:
                pass
        elif col == 2:  # Cost per unit
            try:
                # Strip the "$" and convert to float
                cost_text = item.text().replace("$", "").strip()
                product["cost_per_unit"] = float(cost_text)
            except ValueError:
                pass
                
    def add_sample_products(self):
        """Add some sample products to get started"""
        sample_products = [
            {"name": "Product A", "profit_per_unit": 10.0, "cost_per_unit": 5.0},
            {"name": "Product B", "profit_per_unit": 8.0, "cost_per_unit": 3.0},
            {"name": "Product C", "profit_per_unit": 12.0, "cost_per_unit": 7.0},
        ]
        
        for product in sample_products:
            self.products.append(product)
            
        self.update_table()
    
    def add_product(self):
        """Add a product to the table"""
        product_name = self.product_name.text().strip()
        if not product_name:
            QMessageBox.warning(self, "Input Error", "Product name cannot be empty")
            return
            
        # Check for duplicate product names
        names = [p["name"] for p in self.products]
        if product_name in names:
            QMessageBox.warning(self, "Input Error", f"Product '{product_name}' already exists")
            return
            
        product = {
            "name": product_name,
            "profit_per_unit": self.profit_per_unit.value(),
            "cost_per_unit": self.cost_per_unit.value()
        }
        
        self.products.append(product)
        self.update_table()
        
        # Clear inputs for next product
        self.product_name.clear()
        
    def remove_selected_product(self):
        """Remove the selected product from the table"""
        selected_rows = self.products_table.selectedIndexes()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        if 0 <= row < len(self.products):
            del self.products[row]
            self.update_table()
    
    def update_table(self):
        """Update the products table with current data"""
        # Temporarily disconnect the itemChanged signal to avoid recursion
        try:
            self.products_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass
        self.products_table.setRowCount(len(self.products))
        
        for row, product in enumerate(self.products):
            self.products_table.setItem(row, 0, QTableWidgetItem(product["name"]))
            
            profit_item = QTableWidgetItem(f"${product['profit_per_unit']:.2f}")
            profit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 1, profit_item)
            
            cost_item = QTableWidgetItem(f"${product['cost_per_unit']:.2f}")
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 2, cost_item)
        
        # Reconnect the signal
        self.products_table.itemChanged.connect(self.on_table_item_changed)
    
    def get_products_data(self) -> List[Dict[str, Any]]:
        """Get the products data in a format suitable for the API"""
        return self.products


class ResourceUsageForm(QWidget):
    """Form for defining which resources each product uses and how much"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.products = []
        self.resources = []
        self.resource_usage = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Resource usage table
        self.usage_table = QTableWidget()
        self.usage_table.setAlternatingRowColors(True)
        
        # Controls for adding resource usage
        form_layout = QFormLayout()
        
        self.product_combo = QComboBox()
        self.product_combo.setPlaceholderText("Select Product")
        
        self.resource_combo = QComboBox()
        self.resource_combo.setPlaceholderText("Select Resource")
        
        self.usage_per_unit = QDoubleSpinBox()
        self.usage_per_unit.setRange(0, 1000)
        self.usage_per_unit.setValue(1)
        
        form_layout.addRow("Product:", self.product_combo)
        form_layout.addRow("Resource:", self.resource_combo)
        form_layout.addRow("Usage Per Unit:", self.usage_per_unit)
        
        add_button = QPushButton("Add Usage")
        add_button.clicked.connect(self.add_resource_usage)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected_usage)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(remove_button)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.usage_table)
        
        # Connect table item changed signal
        self.setup_table_connections()
        
    def setup_table_connections(self):
        """Setup connections to capture table edits"""
        self.usage_table.itemChanged.connect(self.on_table_item_changed)
    
    def on_table_item_changed(self, item):
        """Update the resource usage when a table item is edited"""
        row = item.row()
        col = item.column()
        
        if row >= len(self.resource_usage):
            return
            
        usage = self.resource_usage[row]
        
        # Only usage per unit is editable (column 2)
        if col == 2:  # Usage per unit
            try:
                usage["usage_per_unit"] = float(item.text())
            except ValueError:
                pass
    
    def update_products_and_resources(self, products, resources):
        """Update the available products and resources"""
        self.products = products
        self.resources = resources
        
        # Update combo boxes
        self.product_combo.clear()
        self.resource_combo.clear()
        
        for product in products:
            self.product_combo.addItem(product["name"])
            
        for resource in resources:
            self.resource_combo.addItem(resource["name"])
        
        # Update table headers
        self.update_table()
    
    def add_resource_usage(self):
        """Add a resource usage entry"""
        if self.product_combo.currentIndex() < 0 or self.resource_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Input Error", "Please select both a product and a resource")
            return
            
        product_name = self.product_combo.currentText()
        resource_name = self.resource_combo.currentText()
        
        # Check if this product-resource combination already exists
        for usage in self.resource_usage:
            if usage["product_name"] == product_name and usage["resource_name"] == resource_name:
                QMessageBox.warning(
                    self, 
                    "Input Error", 
                    f"Resource usage for {product_name} - {resource_name} already exists"
                )
                return
                
        usage = {
            "product_name": product_name,
            "resource_name": resource_name,
            "usage_per_unit": self.usage_per_unit.value()
        }
        
        self.resource_usage.append(usage)
        self.update_table()
        
    def remove_selected_usage(self):
        """Remove the selected resource usage entry"""
        selected_rows = self.usage_table.selectedIndexes()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        if 0 <= row < len(self.resource_usage):
            del self.resource_usage[row]
            self.update_table()
    
    def add_sample_data(self):
        """Add sample resource usage data"""
        # Clear existing data
        self.resource_usage = []
        
        # Get product and resource names
        product_names = [p["name"] for p in self.products]
        resource_names = [r["name"] for r in self.resources]
        
        if not product_names or not resource_names:
            return
        
        # Create sample usage data for each product-resource combination
        sample_data = [
            {"product_name": "Product A", "resource_name": "Machine Time", "usage_per_unit": 2.0},
            {"product_name": "Product A", "resource_name": "Raw Material", "usage_per_unit": 3.0},
            {"product_name": "Product B", "resource_name": "Machine Time", "usage_per_unit": 1.5},
            {"product_name": "Product B", "resource_name": "Raw Material", "usage_per_unit": 2.0},
            {"product_name": "Product C", "resource_name": "Machine Time", "usage_per_unit": 3.0},
            {"product_name": "Product C", "resource_name": "Raw Material", "usage_per_unit": 4.0},
        ]
        
        # Only add entries if both product and resource exist
        for entry in sample_data:
            if entry["product_name"] in product_names and entry["resource_name"] in resource_names:
                self.resource_usage.append(entry)
        
        self.update_table()
    
    def update_table(self):
        """Update the resource usage table"""
        # Temporarily disconnect the itemChanged signal
        self.usage_table.itemChanged.disconnect(self.on_table_item_changed)
        
        # Setup table columns
        self.usage_table.setColumnCount(3)
        self.usage_table.setHorizontalHeaderLabels([
            "Product", "Resource", "Usage Per Unit"
        ])
        self.usage_table.setRowCount(len(self.resource_usage))
        
        # Fill in the table
        for row, usage in enumerate(self.resource_usage):
            self.usage_table.setItem(row, 0, QTableWidgetItem(usage["product_name"]))
            self.usage_table.setItem(row, 1, QTableWidgetItem(usage["resource_name"]))
            
            usage_item = QTableWidgetItem(f"{usage['usage_per_unit']:.2f}")
            usage_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.usage_table.setItem(row, 2, usage_item)
        
        # Make product and resource columns read-only
        for row in range(len(self.resource_usage)):
            product_item = self.usage_table.item(row, 0)
            resource_item = self.usage_table.item(row, 1)
            if product_item:
                product_item.setFlags(product_item.flags() & ~Qt.ItemIsEditable)
            if resource_item:
                resource_item.setFlags(resource_item.flags() & ~Qt.ItemIsEditable)
        
        # Adjust column widths
        self.usage_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Reconnect the signal
        self.usage_table.itemChanged.connect(self.on_table_item_changed)
    
    def get_resource_usage_data(self) -> List[Dict[str, Any]]:
        """Get the resource usage data in a format suitable for the API"""
        return self.resource_usage


class DemandConstraintsForm(QWidget):
    """Form for entering demand constraints for products"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.products = []
        self.demand_constraints = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Add a descriptive label
        info_label = QLabel(
            "Optional: Add specific demand constraints for products. "
            "If any constraints are added, the demand-constrained optimization will be used."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Demand constraints table
        self.constraints_table = QTableWidget()
        self.constraints_table.setColumnCount(3)
        self.constraints_table.setHorizontalHeaderLabels([
            "Product", "Min Demand", "Max Demand"
        ])
        self.constraints_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.constraints_table.setAlternatingRowColors(True)
        
        # Controls for adding constraints
        form_layout = QFormLayout()
        
        self.product_combo = QComboBox()
        self.product_combo.setPlaceholderText("Select Product")
        
        self.min_demand = QDoubleSpinBox()
        self.min_demand.setRange(0, 10000)
        self.min_demand.setValue(0)
        self.min_demand.setSpecialValueText("No minimum")  # Indicate no min constraint when value is 0
        
        self.max_demand = QDoubleSpinBox()
        self.max_demand.setRange(0, 10000)
        self.max_demand.setValue(0)
        self.max_demand.setSpecialValueText("No maximum")  # Indicate no max constraint when value is 0
        
        form_layout.addRow("Product:", self.product_combo)
        form_layout.addRow("Minimum Demand:", self.min_demand)
        form_layout.addRow("Maximum Demand:", self.max_demand)
        
        add_button = QPushButton("Add Constraint")
        add_button.clicked.connect(self.add_constraint)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected_constraint)
        
        clear_all_button = QPushButton("Clear All Constraints")
        clear_all_button.clicked.connect(self.clear_all_constraints)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(remove_button)
        buttons_layout.addWidget(clear_all_button)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.constraints_table)
        
        # Connect table item changed signal
        self.setup_table_connections()
        
    def setup_table_connections(self):
        """Setup connections to capture table edits"""
        self.constraints_table.itemChanged.connect(self.on_table_item_changed)
    
    def on_table_item_changed(self, item):
        """Update the demand constraints when a table item is edited"""
        row = item.row()
        col = item.column()
        
        if row >= len(self.demand_constraints):
            return
            
        constraint = self.demand_constraints[row]
        
        # Based on which column was edited, update the correct field
        if col == 1:  # Min demand
            try:
                constraint["min_demand"] = float(item.text())
            except ValueError:
                pass
        elif col == 2:  # Max demand
            try:
                text = item.text()
                if text == "No maximum":
                    constraint["max_demand"] = 0
                else:
                    constraint["max_demand"] = float(text)
            except ValueError:
                pass
    
    def clear_all_constraints(self):
        """Clear all demand constraints"""
        if self.demand_constraints:
            reply = QMessageBox.question(
                self, 
                "Confirm Clear", 
                "Are you sure you want to clear all demand constraints?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.demand_constraints = []
                self.update_table()
    
    def update_products(self, products):
        """Update the available products"""
        self.products = products
        
        # Update combo box
        self.product_combo.clear()
        for product in products:
            self.product_combo.addItem(product["name"])
        
        # Update table headers
        self.update_table()
    
    def add_constraint(self):
        """Add a demand constraint entry"""
        if self.product_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Input Error", "Please select a product")
            return
            
        product_name = self.product_combo.currentText()
        
        # Check if this product already has constraints
        for constraint in self.demand_constraints:
            if constraint["product_name"] == product_name:
                QMessageBox.warning(
                    self, 
                    "Input Error", 
                    f"Demand constraints for {product_name} already exist"
                )
                return
        
        # Only add if at least one constraint is non-zero
        min_demand = self.min_demand.value()
        max_demand = self.max_demand.value()
        
        if min_demand == 0 and max_demand == 0:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please set at least one constraint (min or max demand)"
            )
            return
                
        constraint = {
            "product_name": product_name,
            "min_demand": min_demand,
            "max_demand": max_demand
        }
        
        self.demand_constraints.append(constraint)
        self.update_table()
        
    def remove_selected_constraint(self):
        """Remove the selected demand constraint entry"""
        selected_rows = self.constraints_table.selectedIndexes()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        if 0 <= row < len(self.demand_constraints):
            del self.demand_constraints[row]
            self.update_table()
    
    def add_sample_data(self):
        """Add sample demand constraints"""
        # Clear existing data
        self.demand_constraints = []
        
        # Get product names
        product_names = [p["name"] for p in self.products]
        
        if not product_names:
            return
        
        # Create sample constraints
        sample_data = [
            {"product_name": "Product A", "min_demand": 5.0, "max_demand": 25.0},
            {"product_name": "Product B", "min_demand": 10.0, "max_demand": 0},
        ]
        
        # Only add entries if product exists
        for entry in sample_data:
            if entry["product_name"] in product_names:
                self.demand_constraints.append(entry)
        
        self.update_table()
    
    def update_table(self):
        """Update the demand constraints table"""
        # Temporarily disconnect the itemChanged signal
        self.constraints_table.itemChanged.disconnect(self.on_table_item_changed)
        
        # Setup table columns
        self.constraints_table.setColumnCount(3)
        self.constraints_table.setHorizontalHeaderLabels([
            "Product", "Min Demand", "Max Demand"
        ])
        self.constraints_table.setRowCount(len(self.demand_constraints))
        
        # Fill in the table
        for row, constraint in enumerate(self.demand_constraints):
            self.constraints_table.setItem(row, 0, QTableWidgetItem(constraint["product_name"]))
            
            min_value = constraint["min_demand"]
            min_item = QTableWidgetItem("No minimum" if min_value == 0 else f"{min_value:.2f}")
            min_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.constraints_table.setItem(row, 1, min_item)
            
            max_value = constraint["max_demand"]
            max_item = QTableWidgetItem("No maximum" if max_value == 0 else f"{max_value:.2f}")
            max_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.constraints_table.setItem(row, 2, max_item)
        
        # Make product column read-only
        for row in range(len(self.demand_constraints)):
            product_item = self.constraints_table.item(row, 0)
            if product_item:
                product_item.setFlags(product_item.flags() & ~Qt.ItemIsEditable)
        
        # Adjust column widths
        self.constraints_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Reconnect the signal
        self.constraints_table.itemChanged.connect(self.on_table_item_changed)
    
    def get_demand_constraints(self) -> List[Dict[str, Any]]:
        """Get the demand constraints data in a format suitable for the API"""
        # Filter constraints to remove any with both min and max as 0
        return [
            constraint for constraint in self.demand_constraints
            if constraint["min_demand"] > 0 or constraint["max_demand"] > 0
        ]


class TotalConstraintsForm(QWidget):
    """Form for entering optional total production constraints"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QFormLayout(self)
        
        # Add a descriptive label
        info_label = QLabel(
            "Optional: Set minimum and/or maximum total production across all products. "
            "Leave at zero if no constraint is needed."
        )
        info_label.setWordWrap(True)
        layout.addRow(info_label)
        
        # Min total production
        self.min_total = QDoubleSpinBox()
        self.min_total.setRange(0, 100000)
        self.min_total.setValue(0)
        self.min_total.setSpecialValueText("No minimum")  # Indicate no constraint when value is 0
        
        # Max total production
        self.max_total = QDoubleSpinBox()
        self.max_total.setRange(0, 100000)
        self.max_total.setValue(0)
        self.max_total.setSpecialValueText("No maximum")  # Indicate no constraint when value is 0
        
        layout.addRow("Minimum Total Production:", self.min_total)
        layout.addRow("Maximum Total Production:", self.max_total)
    
    def get_total_constraints(self) -> Dict[str, float]:
        """Get the total constraints data, only returning values > 0"""
        constraints = {}
        
        if self.min_total.value() > 0:
            constraints["min_total"] = self.min_total.value()
            
        if self.max_total.value() > 0:
            constraints["max_total"] = self.max_total.value()
            
        return constraints

class OptimizationPanel(QWidget):
    """Main panel for setting up and running optimizations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.optimizer_types = []
        self.init_ui()
        self.fetch_optimizer_types()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)
        
        # Input section
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        # Objective selection
        objective_group = QGroupBox("Optimization Objective")
        objective_layout = QHBoxLayout(objective_group)
        
        self.objective_group = QButtonGroup(self)
        self.max_profit_radio = QRadioButton("Maximize Profit")
        self.min_cost_radio = QRadioButton("Minimize Cost")
        self.max_profit_radio.setChecked(True)
        
        self.objective_group.addButton(self.max_profit_radio)
        self.objective_group.addButton(self.min_cost_radio)
        
        objective_layout.addWidget(self.max_profit_radio)
        objective_layout.addWidget(self.min_cost_radio)
        objective_layout.addStretch()
        
        # Optimizer selection
        optimizer_layout = QHBoxLayout()
        optimizer_layout.addWidget(QLabel("Optimizer Type:"))
        self.optimizer_combo = QComboBox()
        self.optimizer_combo.addItem("Loading optimizers...")
        optimizer_layout.addWidget(self.optimizer_combo)
        
        # Run button
        self.run_button = QPushButton("Run Optimization")
        self.run_button.setProperty("class", "primary-button")
        self.run_button.clicked.connect(self.run_optimization)
        optimizer_layout.addWidget(self.run_button)
        
        input_layout.addWidget(objective_group)
        input_layout.addLayout(optimizer_layout)
        
        # Tabs for input forms
        input_tabs = QTabWidget()
        
        # Products tab
        self.product_form = ProductInputForm()
        input_tabs.addTab(self.product_form, "Products")
        
        # Resources tab
        self.resource_form = ResourceInputForm()
        input_tabs.addTab(self.resource_form, "Resources")
        
        # Resource Usage tab
        self.usage_form = ResourceUsageForm()
        input_tabs.addTab(self.usage_form, "Resource Usage")
        
    # Constraints tab
        constraints_widget = QWidget()
        constraints_layout = QVBoxLayout(constraints_widget)
        
        # Add explanatory header
        constraints_header = QLabel(
            "<h3>Optimization Constraints</h3>"
            "<p>Configure product-specific and total production constraints below.</p>"

        )
        constraints_header.setWordWrap(True)
        constraints_layout.addWidget(constraints_header)
        
        # Demand constraints group
        demand_constraints_group = QGroupBox("Product Demand Constraints")
        demand_constraints_layout = QVBoxLayout(demand_constraints_group)
        self.demand_constraints_form = DemandConstraintsForm()
        demand_constraints_layout.addWidget(self.demand_constraints_form)
        constraints_layout.addWidget(demand_constraints_group)
        
        # Total constraints group
        total_constraints_group = QGroupBox("Total Production Constraints")
        total_constraints_layout = QVBoxLayout(total_constraints_group)
        self.total_constraints_form = TotalConstraintsForm()
        total_constraints_layout.addWidget(self.total_constraints_form)
        constraints_layout.addWidget(total_constraints_group)
        
        constraints_layout.addStretch()
        input_tabs.addTab(constraints_widget, "Constraints")
        
        input_layout.addWidget(input_tabs)
        
        # Results section
        self.results_widget = OptimizationResultWidget()
        
        # Add widgets to splitter
        splitter.addWidget(input_widget)
        splitter.addWidget(self.results_widget)
        
        # Set initial sizes
        splitter.setSizes([400, 400])
        
        main_layout.addWidget(splitter)
        
        # Connect signals to update forms when products/resources change
        self.product_form.products_table.itemChanged.connect(self.update_forms)
        self.resource_form.resource_changed.connect(self.update_forms)
        
        # Add sample data after initial setup
        self.add_sample_data()
        # Status indicator for which endpoint will be used
        self.endpoint_indicator = QLabel("Using basic production model")
        self.endpoint_indicator.setStyleSheet("color: blue; font-style: italic;")
        optimizer_layout.addWidget(self.endpoint_indicator)
        
        # Connect demand constraints form to update endpoint indicator
        self.demand_constraints_form.constraints_table.model().rowsInserted.connect(self.update_endpoint_indicator)
        self.demand_constraints_form.constraints_table.model().rowsRemoved.connect(self.update_endpoint_indicator)
        
    def update_endpoint_indicator(self):
        """Update the indicator showing which endpoint will be used"""
        has_demand_constraints = len(self.demand_constraints_form.get_demand_constraints()) > 0
        
        if has_demand_constraints:
            self.endpoint_indicator.setText("Using demand-constrained model")
            self.endpoint_indicator.setStyleSheet("color: green; font-style: italic;")
        else:
            self.endpoint_indicator.setText("Using basic production model")
            self.endpoint_indicator.setStyleSheet("color: blue; font-style: italic;")        
    
    def update_forms(self):
        """Update dependent forms when products or resources change"""
        products = self.product_form.get_products_data()
        resources = self.resource_form.get_resources_data()
        
        # Update resource usage form
        self.usage_form.update_products_and_resources(products, resources)
        
        # Update demand constraints form
        self.demand_constraints_form.update_products(products)
    
    def add_sample_data(self):
        """Add sample data to all forms"""
        # Get current products and resources
        products = self.product_form.get_products_data()
        resources = self.resource_form.get_resources_data()
        
        # Update forms with current data
        self.usage_form.update_products_and_resources(products, resources)
        self.demand_constraints_form.update_products(products)
        
        # Add sample resource usage
        self.usage_form.add_sample_data()
        
        # Add sample demand constraints
        self.demand_constraints_form.add_sample_data()
    
    def fetch_optimizer_types(self):
        """Fetch available optimizer types from the API"""
        try:
            response = requests.get(f"{API_BASE_URL}/optimizers")
            if response.status_code == 200:
                data = response.json()
                self.optimizer_types = data.get("optimizers", [])[1:]
                
                # Update combo box
                self.optimizer_combo.clear()
                for optimizer in self.optimizer_types:
                    self.optimizer_combo.addItem(optimizer)
                    
                if self.optimizer_types:
                    self.optimizer_combo.setCurrentIndex(0)
            else:
                raise Exception(f"API returned status code {response.status_code}")
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Connection Error", 
                f"Failed to fetch optimizer types: {str(e)}\n\n"
                "Make sure the backend API is running."
            )
            self.optimizer_combo.clear()
            self.optimizer_combo.addItem("API connection failed")

    def run_optimization(self):
        """Run the optimization with current inputs"""
        # Check if we have products
        products = self.product_form.get_products_data()
        if not products:
            QMessageBox.warning(self, "Input Error", "Please add at least one product")
            return
        
        # Check if we have resources
        resources = self.resource_form.get_resources_data()
        if not resources:
            QMessageBox.warning(self, "Input Error", "Please add at least one resource")
            return
        
        # Check if we have resource usage defined
        resource_usage = self.usage_form.get_resource_usage_data()
        if not resource_usage:
            QMessageBox.warning(self, "Input Error", "Please define resource usage for products")
            return
        
        # Get selected optimizer
        optimizer_type = self.optimizer_combo.currentText()
        if optimizer_type in ["API connection failed", "Loading optimizers..."]:
            QMessageBox.warning(self, "Connection Error", "Cannot connect to optimization API")
            return
        
        # Determine objective
        objective = "maximize_profit" if self.max_profit_radio.isChecked() else "minimize_cost"
        
        # Get demand constraints and determine which endpoint to use
        demand_constraints = self.demand_constraints_form.get_demand_constraints()
        total_constraints = {}
        
        # Only include total constraints if they're set to non-zero values
        min_total = self.total_constraints_form.min_total.value()
        max_total = self.total_constraints_form.max_total.value()
        
        if min_total > 0:
            total_constraints["min_total"] = min_total
        
        if max_total > 0:
            total_constraints["max_total"] = max_total
        
        # Choose the appropriate endpoint based on constraints
        endpoint_suffix = "/demand-constrained" if demand_constraints else "/basic-production"
        
        # Prepare request data
        request_data = {
            "objective": objective,
            "products": products,
            "resources": resources,
            "resource_usage": resource_usage
        }
        
        # Only include constraints if they exist
        if demand_constraints:
            request_data["demand_constraints"] = demand_constraints
            
        if total_constraints:
            request_data["total_constraints"] = total_constraints
        
        # Show loading state
        self.run_button.setEnabled(False)
        self.run_button.setText("Running...")
        QApplication.processEvents()
        
        try:
            # Debug output
            print("Sending optimization request with data:")
            print(json.dumps(request_data, indent=2))
            
            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/optimize/{optimizer_type}{endpoint_suffix}", 
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result_data = response.json()
                print("Received optimization results:")
                print(json.dumps(result_data, indent=2))
                self.results_widget.display_results(result_data, objective)
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", "Unknown error")
                    validation_errors = error_data.get("validation_errors", [])
                    
                    error_text = f"Error {response.status_code}: {error_message}\n\n"
                    if validation_errors:
                        error_text += "Validation errors:\n" + "\n".join(f"- {err}" for err in validation_errors)
                    
                    QMessageBox.critical(self, "Optimization Error", error_text)
                except Exception:
                    QMessageBox.critical(self, "Optimization Error", response.text)
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to run optimization: {str(e)}\n\n"
                "Make sure the backend API is running."
            )
        finally:
            # Restore button state
            self.run_button.setEnabled(True)
            self.run_button.setText("Run Optimization")


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Production Optimizer")
        self.setMinimumSize(900, 700)
        self.init_ui()
        
    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Header with title
        header = QWidget()
        header.setProperty("class", "header")
        header_layout = QHBoxLayout(header)
        
        title_label = QLabel("Production Optimizer")
        title_label.setProperty("class", "app-title")
        header_layout.addWidget(title_label)
        
        # Help and About buttons
        help_button = QPushButton("Help")
        help_button.clicked.connect(self.show_help)
        
        about_button = QPushButton("About")
        about_button.clicked.connect(self.show_about)
        
        header_layout.addStretch()
        header_layout.addWidget(help_button)
        header_layout.addWidget(about_button)
        
        # Main optimization panel
        self.optimization_panel = OptimizationPanel()
        
        # Status bar at bottom
        self.statusBar().showMessage("Ready")
        
        # Add widgets to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(self.optimization_panel)
        
        # Load stylesheet
        self.load_stylesheet()
    
    def load_stylesheet(self):
        """Load the application stylesheet"""
        try:
            # Option 1: Absolute path
            stylesheet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.qss")
            
            # Option 2: Look in different locations
            if not os.path.exists(stylesheet_path):
                alternative_paths = ["./styles/main.qss", "./resources/main.qss", "./paste.txt"]
                for path in alternative_paths:
                    if os.path.exists(path):
                        stylesheet_path = path
                        break
            
            # Load and apply the stylesheet
            if os.path.exists(stylesheet_path):
                with open(stylesheet_path, "r") as f:
                    stylesheet = f.read()
                    try:
                        self.setStyleSheet(stylesheet)
                        print(f"Successfully loaded stylesheet from {stylesheet_path}")
                    except Exception as e:
                        print(f"Failed to parse stylesheet: {e}")
                        # Try to identify problematic lines
                        self.debug_stylesheet(stylesheet_path)
            else:
                print(f"Style file not found at {stylesheet_path}. Using default style.")
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
    
    def show_help(self):
        """Show help information"""
        help_text = """
        <h3>How to Use Production Optimizer</h3>
        
        <p><b>Step 1:</b> Add products with their properties:</p>
        <ul>
            <li>Enter product name, price per unit, cost per unit, and minimum demand</li>
            <li>Click "Add Product" to add it to the list</li>
        </ul>
        
        <p><b>Step 2:</b> Add resources and their capacities:</p>
        <ul>
            <li>Go to the Resources tab</li>
            <li>Enter resource name and available capacity</li>
            <li>Click "Add Resource" to add it to the list</li>
        </ul>
        
        <p><b>Step 3:</b> Define resource usage for each product:</p>
        <ul>
            <li>Go to the Resource Usage tab</li>
            <li>Select a product and resource</li>
            <li>Enter how much of the resource each unit of product consumes</li>
            <li>Click "Add Usage" to add the relationship</li>
        </ul>
        
        <p><b>Step 4:</b> Set constraints:</p>
        <ul>
            <li>Go to the Constraints tab</li>
            <li>Set minimum and maximum demand for each product</li>
            <li>Set total production constraints (minimum and maximum total production)</li>
        </ul>
        
        <p><b>Step 5:</b> Run the optimization:</p>
        <ul>
            <li>Select an objective (maximize profit or minimize cost)</li>
            <li>Select an optimizer type from the dropdown</li>
            <li>Click "Run Optimization"</li>
        </ul>
        
        <p><b>Step 6:</b> Review results:</p>
        <ul>
            <li>Check the optimization status and objective value</li>
            <li>Review the production plan</li>
            <li>Check resource utilization</li>
            <li>Review any warnings or messages</li>
        </ul>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Help")
        msg_box.setText(help_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h3>About Production Optimizer</h3>
        
        <p>This application was developed by <b>CLYMAT</b> as part of Operations Research project.</p>
        
        <h4>Development Team (GL3 G1):</h4>
        <ul>
            <li>Chadha Grami</li>
            <li>Louey Sioua</li>
            <li>Yassine Sallemi</li>
            <li>Mariem El Fouzi</li>
            <li>Mohamed Amine Haddad</li>
            <li>Mohamed Taher Ben Hassine</li>
        </ul>
        
        <p>The Production Optimizer helps businesses optimize their production plans while respecting constraints.</p>
        
        <p>For assistance, please refer to the Help section or contact the development team.</p>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("About Production Optimizer")
        msg_box.setText(about_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())