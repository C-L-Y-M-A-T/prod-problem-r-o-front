import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                              QFormLayout, QComboBox, QGroupBox, QTabWidget, QLineEdit,
                              QTableWidget, QTableWidgetItem, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

class ResultsVisualizer(QWidget):
    """Widget for visualizing optimization results with charts"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget for different visualizations
        viz_tabs = QTabWidget()
        
        # Production chart tab
        self.production_chart_widget = QWidget()
        chart_layout = QVBoxLayout(self.production_chart_widget)
        
        # Create chart
        self.chart = QChart()
        self.chart.setTitle("Production Plan")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)
        
        # Create chart view
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(self.chart_view.Antialiasing)
        
        chart_layout.addWidget(self.chart_view)
        viz_tabs.addTab(self.production_chart_widget, "Production Chart")
        
        # Resource utilization tab
        self.resource_widget = QWidget()
        resource_layout = QVBoxLayout(self.resource_widget)
        
        # Create resource utilization chart
        self.resource_chart = QChart()
        self.resource_chart.setTitle("Resource Utilization")
        self.resource_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.resource_chart.legend().setVisible(True)
        self.resource_chart.legend().setAlignment(Qt.AlignBottom)
        
        # Create chart view for resources
        self.resource_chart_view = QChartView(self.resource_chart)
        self.resource_chart_view.setRenderHint(self.resource_chart_view.Antialiasing)
        
        resource_layout.addWidget(self.resource_chart_view)
        viz_tabs.addTab(self.resource_widget, "Resource Utilization")
        
        # Add the tabs to the layout
        layout.addWidget(viz_tabs)
    
    def update_charts(self, result_data, constraints_data):
        """Update charts with optimization results"""
        self._update_production_chart(result_data)
        self._update_resource_chart(result_data, constraints_data)
    
    def _update_production_chart(self, result_data):
        """Update the production plan chart"""
        # Clear previous series
        self.chart.removeAllSeries()
        
        production_plan = result_data.get("production_plan", {})
        if not production_plan:
            return
            
        # Create bar set
        bar_set = QBarSet("Production Quantity")
        bar_set.setColor(QColor("#3498db"))
        
        # Add values and categories
        categories = []
        for product, quantity in production_plan.items():
            bar_set.append(quantity)
            categories.append(product)
            
        # Create series
        series = QBarSeries()
        series.append(bar_set)
        self.chart.addSeries(series)
        
        # Create axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, max(bar_set) * 1.1)  # Add 10% headroom
        axis_y.setLabelFormat("%d")
        axis_y.setTitleText("Units")
        
        # Set axes
        self.chart.setAxisX(axis_x, series)
        self.chart.setAxisY(axis_y, series)
        
        # Refresh the chart
        self.chart.update()
        
    def _update_resource_chart(self, result_data, constraints_data):
        """Update the resource utilization chart"""
        # Clear previous series
        self.resource_chart.removeAllSeries()
        
        # Get utilized resources
        production_plan = result_data.get("production_plan", {})
        if not production_plan:
            return
            
        # Calculate resource utilization
        resource_data = {
            "Labor Hours": {
                "used": result_data.get("resource_usage", {}).get("labor_hours", 0),
                "total": constraints_data.get("available_labor_hours", 0)
            },
            "Material Budget": {
                "used": result_data.get("resource_usage", {}).get("material_cost", 0),
                "total": constraints_data.get("material_budget", 0)
            }
        }
        
        # Create series for utilized resources
        utilized_set = QBarSet("Utilized")
        utilized_set.setColor(QColor("#2ecc71"))
        
        # Create series for remaining resources
        remaining_set = QBarSet("Remaining")
        remaining_set.setColor(QColor("#e74c3c"))
        
        # Add values and categories
        categories = []
        for resource, data in resource_data.items():
            utilized = data["used"]
            total = data["total"]
            remaining = max(0, total - utilized)
            
            utilized_set.append(utilized)
            remaining_set.append(remaining)
            categories.append(resource)
            
        # Create series
        series = QBarSeries()
        series.append(utilized_set)
        series.append(remaining_set)
        self.resource_chart.addSeries(series)
        
        # Create axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        
        axis_y = QValueAxis()
        max_value = max([data["total"] for data in resource_data.values()])
        axis_y.setRange(0, max_value * 1.1)  # Add 10% headroom
        
        # Set axes
        self.resource_chart.setAxisX(axis_x, series)
        self.resource_chart.setAxisY(axis_y, series)
        
        # Refresh the chart
        self.resource_chart.update()


class SolutionSummary(QWidget):
    """Widget for displaying a summary of the optimization solution"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Create summary groupbox
        summary_group = QGroupBox("Optimization Summary")
        summary_layout = QFormLayout()
        
        # Create labels for summary information
        self.objective_label = QLabel("--")
        self.objective_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        
        self.status_label = QLabel("--")
        self.status_label.setProperty("class", "result-status")
        
        self.solve_time_label = QLabel("--")
        
        self.products_count_label = QLabel("--")
        self.active_constraints_label = QLabel("--")
        
        # Add labels to form layout
        summary_layout.addRow("Total Profit:", self.objective_label)
        summary_layout.addRow("Status:", self.status_label)
        summary_layout.addRow("Solution Time:", self.solve_time_label)
        summary_layout.addRow("Products Produced:", self.products_count_label)
        summary_layout.addRow("Active Constraints:", self.active_constraints_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Add a separator
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #bdc3c7;")
        layout.addWidget(separator)
        
        # Add buttons for exporting or sharing
        buttons_layout = QHBoxLayout()
        
        export_button = QPushButton("Export Results")
        export_button.setProperty("class", "action-button")
        export_button.clicked.connect(self.export_results)
        
        share_button = QPushButton("Share Solution")
        share_button.setProperty("class", "action-button")
        share_button.clicked.connect(self.share_solution)
        
        buttons_layout.addWidget(export_button)
        buttons_layout.addWidget(share_button)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
    
    def update_summary(self, result_data):
        """Update the summary with optimization results"""
        # Update status with appropriate styling
        status = result_data.get("status", "Unknown")
        self.status_label.setText(status)
        
        if status == "optimal":
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        elif status == "infeasible":
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        # Update other summary information
        objective_value = result_data.get("objective_value", 0)
        self.objective_label.setText(f"${objective_value:.2f}")
        
        solve_time = result_data.get("solve_time", 0)
        self.solve_time_label.setText(f"{solve_time:.4f} seconds")
        
        # Count number of products actually produced
        production_plan = result_data.get("production_plan", {})
        products_produced = sum(1 for qty in production_plan.values() if qty > 0.001)
        self.products_count_label.setText(f"{products_produced}")
        
        # Determine active constraints
        active_constraints = []
        resource_usage = result_data.get("resource_usage", {})
        
        if resource_usage.get("labor_hours_constraint_active", False):
            active_constraints.append("Labor Hours")
        
        if resource_usage.get("material_budget_constraint_active", False):
            active_constraints.append("Material Budget")
            
        if resource_usage.get("max_production_constraint_active", False):
            active_constraints.append("Maximum Production")
            
        if active_constraints:
            self.active_constraints_label.setText(", ".join(active_constraints))
        else:
            self.active_constraints_label.setText("None")
    
    def export_results(self):
        """Export optimization results"""
        QMessageBox.information(
            self,
            "Export Results",
            "This would export the optimization results to a file.\n"
            "Feature to be implemented in future versions."
        )
    
    def share_solution(self):
        """Share optimization solution"""
        QMessageBox.information(
            self,
            "Share Solution",
            "This would share the optimization solution.\n"
            "Feature to be implemented in future versions."
        )


class SensitivityAnalysis(QWidget):
    """Widget for basic sensitivity analysis"""
    
    analysis_requested = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Parameter selection
        param_group = QGroupBox("Analysis Parameters")
        param_layout = QFormLayout()
        
        self.param_type_combo = QComboBox()
        self.param_type_combo.addItems([
            "Product Profit", 
            "Labor Hours", 
            "Material Cost",
            "Available Labor",
            "Material Budget"
        ])
        
        self.param_product_combo = QComboBox()
        self.param_product_combo.setEnabled(False)  # Will be enabled when products are loaded
        
        self.variation_combo = QComboBox()
        self.variation_combo.addItems([
            "±10%", "±20%", "±30%", "±50%"
        ])
        
        param_layout.addRow("Parameter Type:", self.param_type_combo)
        param_layout.addRow("Product:", self.param_product_combo)
        param_layout.addRow("Variation Range:", self.variation_combo)
        
        param_group.setLayout(param_layout)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.analyze_button = QPushButton("Run Analysis")
        self.analyze_button.setProperty("class", "primary-button")
        self.analyze_button.clicked.connect(self.request_analysis)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.analyze_button)
        
        # Description
        description_label = QLabel(
            "Sensitivity analysis helps understand how changes in parameters\n"
            "affect the optimal solution and objective value."
        )
        description_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        layout.addWidget(description_label)
        layout.addWidget(param_group)
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        # Connect signals
        self.param_type_combo.currentTextChanged.connect(self.on_param_type_changed)
    
    def on_param_type_changed(self, param_type):
        """Enable/disable product selection based on parameter type"""
        is_product_param = param_type in ["Product Profit", "Labor Hours", "Material Cost"]
        self.param_product_combo.setEnabled(is_product_param)
    
    def update_products(self, products):
        """Update the products combo box"""
        self.param_product_combo.clear()
        for product in products:
            self.param_product_combo.addItem(product["name"])
            
    def request_analysis(self):
        """Request sensitivity analysis with current parameters"""
        param_type = self.param_type_combo.currentText()
        product = self.param_product_combo.currentText() if self.param_product_combo.isEnabled() else None
        variation = self.variation_combo.currentText()
        
        # Parse variation percentage
        variation_pct = int(variation.strip("±%"))
        
        analysis_params = {
            "param_type": param_type,
            "product": product,
            "variation_pct": variation_pct
        }
        
        self.analysis_requested.emit(analysis_params)
        
        # For now, show a placeholder message
        QMessageBox.information(
            self,
            "Sensitivity Analysis",
            f"This would run sensitivity analysis for {param_type} "
            f"{'for ' + product if product else ''} with {variation} variation.\n\n"
            "Feature to be implemented in future versions."
        )