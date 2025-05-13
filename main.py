import sys
import json
import requests
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QComboBox, QPushButton, 
                              QTableWidget, QTableWidgetItem, QTabWidget, 
                              QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, 
                              QScrollArea, QSplitter, QGroupBox, QMessageBox,
                              QTextEdit, QHeaderView, QFrame)
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
        
        summary_layout.addRow("Status:", self.status_label)
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
        layout.addWidget(messages_group)
        
    def display_results(self, result_data: Dict[str, Any]):
        """Display optimization results in the UI"""
        # Update summary fields
        self.status_label.setText(result_data.get("status", "Unknown"))
        
        if result_data.get("status") == "optimal":
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        elif result_data.get("status") == "infeasible":
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            
        self.objective_value_label.setText(f"{result_data.get('objective_value', 0):.2f}")
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
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Product", "Profit", "Labor Hours", "Material Cost", "Min Demand"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.setAlternatingRowColors(True)
        
        # Controls for adding products
        input_layout = QHBoxLayout()
        
        self.product_name = QLineEdit()
        self.product_name.setPlaceholderText("Product Name")
        
        self.profit = QDoubleSpinBox()
        self.profit.setRange(0, 10000)
        self.profit.setPrefix("$")
        self.profit.setValue(10)
        
        self.labor_hours = QDoubleSpinBox()
        self.labor_hours.setRange(0, 1000)
        self.labor_hours.setValue(1)
        
        self.material_cost = QDoubleSpinBox()
        self.material_cost.setRange(0, 10000)
        self.material_cost.setPrefix("$")
        self.material_cost.setValue(5)
        
        self.min_demand = QSpinBox()
        self.min_demand.setRange(0, 10000)
        
        add_button = QPushButton("Add Product")
        add_button.clicked.connect(self.add_product)
        
        input_layout.addWidget(self.product_name)
        input_layout.addWidget(self.profit)
        input_layout.addWidget(self.labor_hours)
        input_layout.addWidget(self.material_cost)
        input_layout.addWidget(self.min_demand)
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
        
    def add_sample_products(self):
        """Add some sample products to get started"""
        sample_products = [
            {"name": "Table", "profit": 120, "labor_hours": 8, "material_cost": 50, "min_demand": 5},
            {"name": "Chair", "profit": 45, "labor_hours": 5, "material_cost": 20, "min_demand": 10},
            {"name": "Bookshelf", "profit": 80, "labor_hours": 7, "material_cost": 35, "min_demand": 3},
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
            "profit": self.profit.value(),
            "labor_hours": self.labor_hours.value(),
            "material_cost": self.material_cost.value(),
            "min_demand": self.min_demand.value()
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
        self.products_table.setRowCount(len(self.products))
        
        for row, product in enumerate(self.products):
            self.products_table.setItem(row, 0, QTableWidgetItem(product["name"]))
            
            profit_item = QTableWidgetItem(f"${product['profit']:.2f}")
            profit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 1, profit_item)
            
            labor_item = QTableWidgetItem(f"{product['labor_hours']:.2f}")
            labor_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 2, labor_item)
            
            material_item = QTableWidgetItem(f"${product['material_cost']:.2f}")
            material_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 3, material_item)
            
            demand_item = QTableWidgetItem(f"{product['min_demand']}")
            demand_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 4, demand_item)
    
    def get_products_data(self) -> List[Dict[str, Any]]:
        """Get the products data in a format suitable for the API"""
        return self.products


class ConstraintsInputForm(QWidget):
    """Form for entering constraint values"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # Available labor hours
        self.labor_hours = QDoubleSpinBox()
        self.labor_hours.setRange(0, 100000)
        self.labor_hours.setValue(200)
        self.labor_hours.setSuffix(" hours")
        layout.addRow("Available Labor Hours:", self.labor_hours)
        
        # Maximum material budget
        self.material_budget = QDoubleSpinBox()
        self.material_budget.setRange(0, 1000000)
        self.material_budget.setValue(2000)
        self.material_budget.setPrefix("$")
        layout.addRow("Material Budget:", self.material_budget)
        
        # Maximum total production
        self.max_production = QSpinBox()
        self.max_production.setRange(0, 10000)
        self.max_production.setValue(500)
        self.max_production.setSuffix(" units")
        layout.addRow("Maximum Total Production:", self.max_production)
    
    def get_constraints_data(self) -> Dict[str, float]:
        """Get the constraints data in a format suitable for the API"""
        return {
            "available_labor_hours": self.labor_hours.value(),
            "material_budget": self.material_budget.value(),
            "max_total_production": self.max_production.value()
        }


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
        
        input_layout.addLayout(optimizer_layout)
        
        # Tabs for products and constraints
        input_tabs = QTabWidget()
        
        # Products tab
        self.product_form = ProductInputForm()
        input_tabs.addTab(self.product_form, "Products")
        
        # Constraints tab
        self.constraints_form = ConstraintsInputForm()
        input_tabs.addTab(self.constraints_form, "Constraints")
        
        input_layout.addWidget(input_tabs)
        
        # Results section
        self.results_widget = OptimizationResultWidget()
        
        # Add widgets to splitter
        splitter.addWidget(input_widget)
        splitter.addWidget(self.results_widget)
        
        # Set initial sizes
        splitter.setSizes([400, 400])
        
        main_layout.addWidget(splitter)
    
    def fetch_optimizer_types(self):
        """Fetch available optimizer types from the API"""
        try:
            response = requests.get(f"{API_BASE_URL}/optimizers")
            data = response.json()
            
            self.optimizer_types = data.get("optimizers", [])
            
            # Update combo box
            self.optimizer_combo.clear()
            for optimizer in self.optimizer_types:
                self.optimizer_combo.addItem(optimizer)
                
            if self.optimizer_types:
                self.optimizer_combo.setCurrentIndex(0)
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
        
        # Get selected optimizer
        optimizer_type = self.optimizer_combo.currentText()
        if optimizer_type in ["API connection failed", "Loading optimizers..."]:
            QMessageBox.warning(self, "Connection Error", "Cannot connect to optimization API")
            return
        
        # Prepare request data
        constraints = self.constraints_form.get_constraints_data()
        
        # Format product data - ensure name field is present as API requires it
        formatted_products = []
        for p in products:
            formatted_products.append({
                "product_name": p["name"],
                "name": p["name"],  # Keep both name and product_name to satisfy requirements
                "profit_per_unit": p["profit"],
                "labor_hours": p["labor_hours"],
                "cost_per_unit": p["material_cost"],
                "min_demand": p["min_demand"]
            })
        
        # Format resource data - use available_capacity instead of available
        formatted_resources = [
            {"name": "labor", "available_capacity": constraints["available_labor_hours"]},
            {"name": "material_budget", "available_capacity": constraints["material_budget"]},
            {"name": "production_capacity", "available_capacity": constraints["max_total_production"]}
        ]
        
        # Format resource usage for each product - update structure to match API requirements
        resource_usage = []
        for p in products:
            # Add each resource usage separately with the required fields
            resource_usage.append({
                "product_name": p["name"],
                "resource_name": "labor",
                "usage_per_unit": p["labor_hours"]
            })
            resource_usage.append({
                "product_name": p["name"],
                "resource_name": "material_budget",
                "usage_per_unit": p["material_cost"]
            })
            resource_usage.append({
                "product_name": p["name"],
                "resource_name": "production_capacity",
                "usage_per_unit": 1  # Each product uses 1 unit of production capacity
            })
        
        # Create request data
        request_data = {
            "objective": "maximize_profit",
            "products": formatted_products,
            "resources": formatted_resources,
            "resource_usage": resource_usage
        }
        
        # Show loading state
        self.run_button.setEnabled(False)
        self.run_button.setText("Running...")
        QApplication.processEvents()
        
        try:
            # Debug output
            print(f"Sending request to: {API_BASE_URL}/optimize/{optimizer_type}")
            print(f"Request payload: {json.dumps(request_data, indent=2)}")
            
            # Make API request
            response = requests.post(f"{API_BASE_URL}/optimize/{optimizer_type}", 
                                json=request_data)
            
            # Process response
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text}")
            
            if response.status_code == 200:
                result_data = response.json()
                self.results_widget.display_results(result_data)
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("solver_message", "Unknown error")
                    validation_errors = error_data.get("validation_errors", [])
                    
                    error_text = f"Error: {error_message}\n\n"
                    if validation_errors:
                        error_text += "Validation errors:\n" + "\n".join(f"- {err}" for err in validation_errors)
                except Exception:
                    error_text = f"Error: {response.text}"
                
                QMessageBox.critical(self, "Optimization Error", error_text)
                
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
            with open("main.qss", "r") as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
        except FileNotFoundError:
            print("Style file not found. Using default style.")
    
    def show_help(self):
        """Show help information"""
        help_text = """
        <h3>How to Use Production Optimizer</h3>
        
        <p><b>Step 1:</b> Add products with their properties:</p>
        <ul>
            <li>Enter product name, profit, labor hours, material cost, and minimum demand</li>
            <li>Click "Add Product" to add it to the list</li>
        </ul>
        
        <p><b>Step 2:</b> Set constraints:</p>
        <ul>
            <li>Go to the Constraints tab</li>
            <li>Enter available labor hours, material budget, and maximum production</li>
        </ul>
        
        <p><b>Step 3:</b> Run the optimization:</p>
        <ul>
            <li>Select an optimizer type from the dropdown</li>
            <li>Click "Run Optimization"</li>
        </ul>
        
        <p><b>Step 4:</b> Review results:</p>
        <ul>
            <li>Check the optimization status and objective value</li>
            <li>Review the production plan</li>
            <li>Check for any warnings or messages</li>
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
        
        <p>The Production Optimizer helps businesses maximize profits while respecting production constraints.</p>
        
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