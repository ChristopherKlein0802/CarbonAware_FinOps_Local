"""
Overview Tab - Infrastructure Monitoring Dashboard
Carbon-Aware FinOps Dashboard - Bachelor Thesis

DASHBOARD FEATURES:
- Modern lightweight charting framework (50kb)
- Optimized Builder.io Integration
- Consistent 400px chart dimensions
- Seamless CSS styling without conflicts
"""

from dash import html
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.components import DashboardCards
from components.chartjs_library import ChartJSFactory


class OverviewTabChartJS:
    """Modern Builder.io Overview Tab - Infrastructure Dashboard"""

    def __init__(self):
        self.cards = DashboardCards()
        self.charts = ChartJSFactory()

    def create_tab_layout(self) -> html.Div:
        """Create modern Builder.io overview layout with optimized charts"""
        return html.Div(
            [
                # Modern Section Header
                html.Div(
                    [
                        html.H2("📊 Infrastructure Overview", className="section-title"),
                        html.P(
                            "Real-time AWS infrastructure monitoring with modern analytics framework",
                            className="section-description",
                        ),
                    ],
                    className="section-header",
                ),
                # KPI Cards Grid (Builder.io style)
                html.Div(
                    [
                        html.Div(id="overview-cost-card", className="carbon-card"),
                        html.Div(id="overview-co2-card", className="carbon-card"),
                        html.Div(id="overview-instances-card", className="carbon-card"),
                        html.Div(id="overview-savings-card", className="carbon-card"),
                    ],
                    className="carbon-grid",
                ),
                # Analysis Section (Unified grid)
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(id="overview-insights", className="content-card"),
                                html.Div(id="overview-business-case", className="content-card"),
                            ],
                            className="content-column",
                        ),
                        html.Div(
                            [html.Div(id="overview-data-quality", className="content-card")],
                            className="content-column",
                        ),
                    ],
                    className="content-grid",
                ),
                # Charts Section Header
                html.Div(
                    [
                        html.H3("📊 Modern Analytics Dashboard", className="subsection-title"),
                        html.P(
                            "Modern Chart.js visualization with Builder.io design system",
                            className="subsection-description",
                        ),
                    ],
                    className="section-header",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4("💰 Cost Analysis", className="chart-title"),
                                html.Div(id="chartjs-overview-costs", className="chartjs-container"),
                            ],
                            className="chart-card",
                        ),
                        html.Div(
                            [
                                html.H4("⏱️ Runtime Patterns", className="chart-title"),
                                html.Div(id="chartjs-overview-runtime", className="chartjs-container"),
                            ],
                            className="chart-card",
                        ),
                        html.Div(
                            [
                                html.H4("🌍 Carbon Emissions", className="chart-title"),
                                html.Div(id="chartjs-overview-co2", className="chartjs-container"),
                            ],
                            className="chart-card",
                        ),
                        html.Div(
                            [
                                html.H4("📈 Efficiency Matrix", className="chart-title"),
                                html.Div(id="chartjs-overview-efficiency", className="chartjs-container"),
                            ],
                            className="chart-card",
                        ),
                    ],
                    className="charts-grid",
                ),
            ],
            className="content-section",
        )

    # Modern Chart Methods - Lightweight Implementation
    def create_costs_chart(self, instances: List[Dict]) -> html.Div:
        """Modern Cost Chart with optimized rendering"""
        return ChartJSFactory.create_cost_breakdown_chart(instances)

    def create_runtime_chart(self, instances: List[Dict]) -> html.Div:
        """Modern Runtime Chart with optimized rendering"""
        return ChartJSFactory.create_runtime_line_chart(instances)

    def create_co2_chart(self, instances: List[Dict]) -> html.Div:
        """Modern CO2 Chart with optimized rendering"""
        return ChartJSFactory.create_co2_donut_chart(instances)

    def create_efficiency_chart(self, instances: List[Dict]) -> html.Div:
        """Modern Efficiency Chart with optimized rendering"""
        return ChartJSFactory.create_efficiency_scatter_chart(instances)

    # Keep existing card methods unchanged
    def create_cost_card(self, instances: List[Dict]) -> html.Div:
        """Create modern cost card with Builder.io styling"""
        if not instances:
            return self._create_empty_card("💰", "Total Monthly Cost", "No data", "€0.00")

        total_cost = sum(instance.get("monthly_cost_eur", 0) for instance in instances)

        return html.Div(
            [
                html.Div(
                    [
                        html.Div("💰", className="card-icon"),
                        html.Div(
                            [
                                html.H3(f"€{total_cost:.2f}", className="card-value"),
                                html.P("Monthly Cost", className="card-label"),
                                html.Span(f"{len(instances)} instances monitored", className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card cost-card",
        )

    def create_co2_card(self, instances: List[Dict]) -> html.Div:
        """Create modern CO2 card with Builder.io styling"""
        if not instances:
            return self._create_empty_card("🌍", "Carbon Emissions", "No data", "0kg CO₂")

        total_co2 = sum(instance.get("monthly_co2_kg", 0) for instance in instances)

        return html.Div(
            [
                html.Div(
                    [
                        html.Div("🌍", className="card-icon"),
                        html.Div(
                            [
                                html.H3(f"{total_co2:.1f}kg", className="card-value"),
                                html.P("CO₂ Emissions", className="card-label"),
                                html.Span("Monthly carbon footprint", className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card co2-card",
        )

    def create_instances_card(self, instances: List[Dict]) -> html.Div:
        """Create modern instances card with Builder.io styling"""
        if not instances:
            return self._create_empty_card("🖥️", "Active Instances", "No data", "0")

        running_instances = len([inst for inst in instances if inst.get("state") == "running"])

        return html.Div(
            [
                html.Div(
                    [
                        html.Div("🖥️", className="card-icon"),
                        html.Div(
                            [
                                html.H3(str(len(instances)), className="card-value"),
                                html.P("Active Instances", className="card-label"),
                                html.Span(f"{running_instances} running", className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card instances-card",
        )

    def create_savings_card(self, instances: List[Dict]) -> html.Div:
        """Create modern savings card with REAL calculated potential (per CLAUDE.md)"""
        if not instances:
            return self._create_empty_card("💡", "Potential Savings", "No data", "N/A")

        # Calculate REAL savings potential from instance data
        total_cost = sum(instance.get("monthly_cost_eur", 0) or 0 for instance in instances)
        instances_with_cost = len([inst for inst in instances if inst.get("monthly_cost_eur", 0) > 0])
        
        if total_cost > 0 and instances_with_cost > 0:
            # Use REAL potential_cost_savings if available, otherwise conservative estimate
            total_potential_savings = sum(inst.get("potential_cost_savings", 0) or 0 for inst in instances)
            
            if total_potential_savings > 0:
                # Use REAL calculated savings from optimization scenarios
                estimated_savings = total_potential_savings
                savings_detail = "From optimization scenarios"
            else:
                # Literature-based estimate: 20% of monthly cost (McKinsey 2024)
                estimated_savings = total_cost * 0.20  # 20% of total monthly cost
                savings_detail = "Literature-based estimate*"
                
            savings_display = f"€{estimated_savings:.2f}"
        else:
            savings_display = "N/A"
            savings_detail = "Insufficient cost data"

        return html.Div(
            [
                html.Div(
                    [
                        html.Div("💡", className="card-icon"),
                        html.Div(
                            [
                                html.H3(savings_display, className="card-value"),
                                html.P("Theoretical Savings", className="card-label"),
                                html.Span(savings_detail, className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card savings-card",
        )

    def create_insights(self, instances: List[Dict]) -> html.Div:
        """Create insights content with REAL calculated metrics (per CLAUDE.md)"""
        if not instances:
            return html.Div("No insights available - no instance data (NO-FALLBACK policy)", className="insight-text")

        # Calculate REAL metrics from instances
        total_cost = sum(instance.get("monthly_cost_eur", 0) or 0 for instance in instances)
        total_co2 = sum(instance.get("monthly_co2_kg", 0) or 0 for instance in instances) 
        avg_cost = total_cost / len(instances) if instances and total_cost > 0 else 0
        running_instances = len([inst for inst in instances if inst.get("state") == "running"])
        
        # Calculate optimization potential from real data
        instances_with_power = len([inst for inst in instances if inst.get("power_watts", 0) > 0])
        data_completeness = (instances_with_power / len(instances)) * 100 if instances else 0

        return html.Div(
            [
                html.H4("📊 Research Insights", className="insights-title"),
                html.Ul(
                    [
                        html.Li(f"Average cost per instance: €{avg_cost:.2f}/month" if avg_cost > 0 else "Cost data incomplete"),
                        html.Li(f"Infrastructure scope: {len(instances)} instances ({running_instances} active)"),
                        html.Li(f"Data completeness: {data_completeness:.0f}% (power consumption available)"),
                        html.Li("Analysis framework: Conservative methodology applied"),
                    ],
                    className="insights-list",
                ),
            ]
        )

    def create_business_case_summary(self, instances: List[Dict]) -> html.Div:
        """Create business case summary with REAL calculated data"""        
        if not instances:
            potential_savings = "N/A"
            carbon_potential = "N/A"
            roi_estimate = "Insufficient data"
        else:
            # Calculate REAL potential from instance data
            total_cost = sum(inst.get("monthly_cost_eur", 0) or 0 for inst in instances)
            total_co2 = sum(inst.get("monthly_co2_kg", 0) or 0 for inst in instances)
            
            # Calculate theoretical savings based on literature percentages
            if total_cost > 0:
                # McKinsey 2024: 20-30% cost reduction potential through optimization
                theoretical_cost_savings = total_cost * 0.25  # 25% of total cost
                cost_percentage = 25  # Fixed percentage from literature
                potential_savings = f"{cost_percentage}% theoretical potential (€{theoretical_cost_savings:.2f})*"
            else:
                potential_savings = "No cost data available"
                
            if total_co2 > 0:
                # MIT 2023: 15-25% CO2 reduction through temporal shifting
                theoretical_co2_savings = total_co2 * 0.20  # 20% of total CO2
                carbon_percentage = 20  # Fixed percentage from literature
                carbon_potential = f"{carbon_percentage}% theoretical potential ({theoretical_co2_savings:.2f}kg)*"
            else:
                carbon_potential = "No carbon data available"
                
            roi_estimate = "Requires empirical validation" if total_cost > 0 else "Insufficient data"
        
        return html.Div(
            [
                html.H4("💼 Business Case Analysis", className="business-title"),
                html.P("Theoretical integrated Carbon-aware FinOps potential (literature-based):"),
                html.Ul(
                    [
                        html.Li(f"Cost optimization: {potential_savings}"),
                        html.Li(f"Carbon reduction: {carbon_potential}"),
                        html.Li(f"ROI validation: {roi_estimate}"),
                        html.Li("Framework integration: Analysis-ready implementation"),
                    ],
                    className="business-list",
                ),
            ]
        )

    def create_data_quality_summary(self, instances: List[Dict]) -> html.Div:
        """Create data quality summary with REAL API status monitoring"""
        # Check REAL API integration status from instances data
        from utils.data_processing import data_processor
        
        # ElectricityMaps API status
        current_carbon = data_processor.get_german_carbon_intensity()
        electricity_status = f"✅ ElectricityMap API: {current_carbon:.0f}g CO2/kWh live" if current_carbon > 0 else "❌ ElectricityMap API: Unavailable"
        
        # Boavizta API status (check if instances have power data)
        instances_with_power = len([inst for inst in instances if inst.get("power_watts", 0) > 0]) if instances else 0
        total_instances = len(instances) if instances else 0
        boavizta_coverage = (instances_with_power / total_instances * 100) if total_instances > 0 else 0
        boavizta_status = f"✅ Boavizta API: {instances_with_power}/{total_instances} instances ({boavizta_coverage:.0f}%)" if instances_with_power > 0 else "❌ Boavizta API: No power data"
        
        # AWS Cost Explorer status (check if instances have cost data)
        instances_with_cost = len([inst for inst in instances if inst.get("monthly_cost_eur", 0) > 0]) if instances else 0
        aws_coverage = (instances_with_cost / total_instances * 100) if total_instances > 0 else 0
        aws_status = f"✅ AWS Cost Explorer: {instances_with_cost}/{total_instances} instances ({aws_coverage:.0f}%)" if instances_with_cost > 0 else "❌ AWS Cost Explorer: No cost data"
        
        # Framework performance calculation
        total_data_points = instances_with_power + instances_with_cost + (1 if current_carbon > 0 else 0)
        framework_efficiency = (total_data_points / 3) * 100 if total_instances > 0 else 0
        framework_status = f"📊 Framework: {framework_efficiency:.0f}% integration ({total_data_points}/3 APIs active)"
        
        return html.Div(
            [
                html.H4("🎯 Data Quality Assessment", className="quality-title"),
                html.P("Live API integration status:"),
                html.Ul(
                    [
                        html.Li(electricity_status),
                        html.Li(boavizta_status),
                        html.Li(aws_status),
                        html.Li(framework_status),
                    ],
                    className="quality-list",
                ),
            ]
        )

    def _create_empty_card(self, icon: str, title: str, subtitle: str, value: str) -> html.Div:
        """Create empty state card"""
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(icon, className="card-icon"),
                        html.Div(
                            [
                                html.H3(value, className="card-value empty"),
                                html.P(title, className="card-label"),
                                html.Span(subtitle, className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card empty-card",
        )


# Create instance
overview_tab_chartjs = OverviewTabChartJS()
