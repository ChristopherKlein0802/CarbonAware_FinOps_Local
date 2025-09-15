"""
Thesis Validation Tab - Academic Research Validation
Carbon-Aware FinOps Dashboard - Bachelor Thesis

THESIS VALIDATION WITH CHART.JS:
- Research Question: Integrated vs Separate Tools
- Explores integrated approach potential through data
- Chart.js framework integration supports research methodology
"""

from dash import html
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.components import DashboardCards
from components.chartjs_library import ChartJSFactory


class ThesisValidationTabChartJS:
    """Academic Thesis Exploration - Investigates integrated approach potential"""

    def __init__(self):
        self.cards = DashboardCards()
        self.charts = ChartJSFactory()
    
    def _create_empty_card(self, icon: str, title: str, subtitle: str, value: str) -> html.Div:
        """Create empty card for NO-FALLBACK policy compliance"""
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(icon, className="card-icon"),
                        html.Div(
                            [
                                html.H3(value, className="card-value"),
                                html.P(title, className="card-label"),
                                html.Span(subtitle, className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card thesis-card",
        )

    def create_tab_layout(self) -> html.Div:
        """Create thesis validation layout with modern charts"""
        return html.Div(
            [
                html.Div(
                    [
                        html.H2("🎓 Thesis Validation", className="section-title"),
                        html.P(
                            "Academic exploration: Integrated Carbon-aware FinOps approach investigates potential efficiency gains",
                            className="section-description",
                        ),
                    ],
                    className="section-header",
                ),
                html.Div(
                    [
                        html.Div(id="thesis-cost-advantage-card", className="carbon-card"),
                        html.Div(id="thesis-carbon-advantage-card", className="carbon-card"),
                        html.Div(id="thesis-integration-card", className="carbon-card"),
                        html.Div(id="thesis-research-card", className="carbon-card"),
                    ],
                    className="carbon-grid",
                ),
                html.Div(
                    [
                        html.H3("📊 Academic Research Validation", className="subsection-title"),
                        html.P(
                            "These visualizations explore our thesis hypothesis: integrated approaches show theoretical advantages",
                            className="subsection-description",
                        ),
                    ],
                    className="section-header",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4("💰 Cost Optimization Comparison", className="chart-title"),
                                html.Div(id="chartjs-cost-comparison", className="chartjs-container"),
                            ],
                            className="chart-card",
                        ),
                        html.Div(
                            [
                                html.H4("🌍 Carbon Optimization Comparison", className="chart-title"),
                                html.Div(id="chartjs-carbon-comparison", className="chartjs-container"),
                            ],
                            className="chart-card",
                        ),
                        html.Div(
                            [
                                html.H4("🚀 Integrated Approach Exploration", className="chart-title"),
                                html.Div(id="chartjs-integration-exploration", className="chartjs-container"),
                            ],
                            className="chart-card wide",
                        ),
                    ],
                    className="charts-grid",
                ),
            ],
            className="content-section",
        )

    # Chart Methods for Thesis Validation
    def create_cost_comparison_chart(self, instances: List[Dict]) -> html.Div:
        """Cost optimization comparison using modern charts"""
        return ChartJSFactory.create_cost_comparison_chart(instances)

    def create_carbon_comparison_chart(self, instances: List[Dict]) -> html.Div:
        """Carbon optimization comparison using modern charts"""
        return ChartJSFactory.create_carbon_comparison_chart(instances)

    def create_integration_exploration_chart(self, instances: List[Dict]) -> html.Div:
        """Integrated approach theoretical exploration"""
        return ChartJSFactory.create_integration_exploration_chart(instances)

    def create_comparison_analysis_chart(self, instances: List[Dict]) -> html.Div:
        """Integrated approach comparison analysis"""
        return ChartJSFactory.create_comparison_analysis_chart(instances)

    # Card methods
    def create_cost_advantage_card(self, instances: List[Dict]) -> html.Div:
        """Cost advantage card with REAL data (per CLAUDE.md NO-FALLBACK Policy)"""
        if not instances:
            return self._create_empty_card("💰", "Cost Potential", "No API Data", "N/A")
        
        # Calculate theoretical potential from optimization scenarios (academic modeling)
        total_potential_savings = sum(inst.get("potential_cost_savings", 0) or 0 for inst in instances)
        total_cost = sum(inst.get("monthly_cost_eur", 0) or 0 for inst in instances)
        
        if total_cost > 0 and total_potential_savings > 0:
            savings_percentage = (total_potential_savings / total_cost) * 100
            display_value = f"{savings_percentage:.0f}% theoretical*"
        elif total_cost > 0:
            display_value = "0% (no optimization scenarios)"
        else:
            display_value = "N/A (no cost data)"
        
        return html.Div(
            [
                html.Div(
                    [
                        html.Div("💰", className="card-icon"),
                        html.Div(
                            [
                                html.H3(display_value, className="card-value"),
                                html.P("Cost Optimization", className="card-label"),
                                html.Span("scheduling scenarios only", className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card thesis-card",
        )

    def create_carbon_advantage_card(self, instances: List[Dict]) -> html.Div:
        """Carbon advantage card with REAL data (per CLAUDE.md NO-FALLBACK Policy)"""
        if not instances:
            return self._create_empty_card("🌍", "Carbon Potential", "No API Data", "N/A")
        
        # Calculate theoretical CO2 reduction from optimization scenarios (academic modeling)
        total_co2_potential = sum(inst.get("potential_co2_savings", 0) or 0 for inst in instances if inst.get("potential_co2_savings") is not None)
        total_co2 = sum(inst.get("monthly_co2_kg", 0) or 0 for inst in instances if inst.get("monthly_co2_kg") is not None)
        
        if total_co2 > 0 and total_co2_potential > 0:
            potential_percentage = (total_co2_potential / total_co2) * 100
            display_value = f"{potential_percentage:.0f}% theoretical*"
        elif total_co2 > 0:
            display_value = "0% (no optimization scenarios)"
        else:
            display_value = "N/A (no carbon data)"
        
        return html.Div(
            [
                html.Div(
                    [
                        html.Div("🌍", className="card-icon"),
                        html.Div(
                            [
                                html.H3(display_value, className="card-value"),
                                html.P("Carbon Optimization", className="card-label"),
                                html.Span("scheduling scenarios only", className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card thesis-card",
        )

    def create_integration_card(self, instances: List[Dict]) -> html.Div:
        """Integration benefits card with REAL API integration status"""
        if not instances:
            return self._create_empty_card("🔧", "Integration Score", "No API Data", "N/A")
        
        # Calculate REAL integration score based on API availability
        from utils.data_processing import data_processor
        api_sources_available = 0
        total_api_sources = 3  # ElectricityMaps, Boavizta, AWS
        
        # Check ElectricityMaps
        if data_processor.get_german_carbon_intensity() > 0:
            api_sources_available += 1
            
        # Check if instances have power data (Boavizta)
        if any(inst.get("power_watts") for inst in instances):
            api_sources_available += 1
            
        # Check if instances have cost data (AWS)
        if any(inst.get("monthly_cost_eur") for inst in instances):
            api_sources_available += 1
            
        integration_percentage = (api_sources_available / total_api_sources) * 100
        
        return html.Div(
            [
                html.Div(
                    [
                        html.Div("🔧", className="card-icon"),
                        html.Div(
                            [
                                html.H3(f"{integration_percentage:.0f}%", className="card-value"),
                                html.P("API Integration", className="card-label"),
                                html.Span(f"{api_sources_available}/3 APIs Active", className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card thesis-card",
        )

    def create_research_card(self, instances: List[Dict]) -> html.Div:
        """Research validation card"""
        return html.Div(
            [
                html.Div(
                    [
                        html.Div("🎓", className="card-icon"),
                        html.Div(
                            [
                                html.H3("Bachelor", className="card-value"),
                                html.P("Thesis 2025", className="card-label"),
                                html.Span("Data-driven validation", className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card thesis-card",
        )

    def create_business_case_analysis(self, instances: List[Dict]) -> html.Div:
        """Business case analysis with REAL framework metrics (per CLAUDE.md)"""
        # Calculate REAL integration metrics from instances
        if not instances:
            integration_status = "No data for integration analysis"
            api_coverage = "0%"
        else:
            # Check API integration completeness
            has_cost_data = any(inst.get("monthly_cost_eur") for inst in instances)
            has_carbon_data = any(inst.get("monthly_co2_kg") for inst in instances)  
            has_power_data = any(inst.get("power_watts") for inst in instances)
            
            active_apis = sum([has_cost_data, has_carbon_data, has_power_data])
            api_coverage = f"{(active_apis/3)*100:.0f}%"
            
            if active_apis >= 2:
                integration_status = "Integrated approach demonstrable"
            else:
                integration_status = "Limited integration - requires API improvements"
        
        return html.Div(
            [
                html.H4("💼 Integrated Approach Analysis", className="analysis-title"),
                html.P("Framework integration assessment for thesis validation:"),
                html.Ul(
                    [
                        html.Li(f"API Integration Status: {integration_status}"),
                        html.Li(f"Data Coverage: {api_coverage} (Cost+Carbon+Power APIs)"),
                        html.Li("Implementation: Analysis-first approach (conservative)"),
                        html.Li("Academic Contribution: Methodological exploration framework"),
                    ],
                    className="analysis-list",
                ),
            ]
        )

    def create_german_grid_analysis(self, instances: List[Dict]) -> html.Div:
        """German grid analysis with REAL data (per CLAUDE.md NO-FALLBACK)"""
        # Get REAL German grid data and instance count
        from utils.data_processing import data_processor
        current_intensity = data_processor.get_german_carbon_intensity()
        instance_count = len(instances) if instances else 0
        
        # Calculate REAL monitoring scope vs SME target
        sme_target = 100  # Per CLAUDE.md thesis scope
        scope_percentage = min(100, (instance_count / sme_target) * 100) if instance_count > 0 else 0
        
        grid_status = f"{current_intensity:.0f}g CO2/kWh (ElectricityMaps)" if current_intensity > 0 else "Grid data unavailable"
        monitoring_status = f"{instance_count} instances ({scope_percentage:.0f}% of SME target)"
        
        return html.Div(
            [
                html.H4("🇩🇪 German Grid Context Analysis", className="analysis-title"),
                html.P("Real-time German market analysis for thesis validation:"),
                html.Ul(
                    [
                        html.Li(f"SME Market Scope: ≤{sme_target} instances (thesis boundary)"),
                        html.Li(f"Current Monitoring: {monitoring_status}"),
                        html.Li(f"Real Grid Intensity: {grid_status}"),
                        html.Li("Regional Focus: EU-Central-1 (Frankfurt) alignment"),
                    ],
                    className="analysis-list",
                ),
            ]
        )

    def create_academic_summary(self, instances: List[Dict]) -> html.Div:
        """Academic research summary with REAL validation metrics (per CLAUDE.md)"""
        # Calculate REAL research validation metrics from instances
        if not instances:
            methodology_status = "Insufficient data for validation"
            evidence_strength = "0% - No API data available"
        else:
            # Check methodological completeness
            has_cost_integration = any(inst.get("monthly_cost_eur") for inst in instances)
            has_carbon_integration = any(inst.get("monthly_co2_kg") for inst in instances)
            has_power_integration = any(inst.get("power_watts") for inst in instances)
            
            integration_score = sum([has_cost_integration, has_carbon_integration, has_power_integration])
            evidence_strength = f"{(integration_score/3)*100:.0f}% - {integration_score}/3 APIs integrated"
            
            if integration_score >= 2:
                methodology_status = "Integrated approach methodology demonstrable"
            else:
                methodology_status = "Limited methodology validation - requires API improvements"
        
        return html.Div(
            [
                html.H4("🔬 Academic Research Validation", className="analysis-title"),
                html.P("Methodological validation status for Bachelor thesis:"),
                html.Ul(
                    [
                        html.Li("Research Question: Integrated vs Separate Carbon-aware FinOps Tools"),
                        html.Li("Method: Comparative analysis through implementation"),
                        html.Li(f"Evidence Quality: {evidence_strength}"),
                        html.Li(f"Validation Status: {methodology_status}"),
                    ],
                    className="analysis-list",
                ),
            ]
        )


# Create instance
thesis_validation_tab_chartjs = ThesisValidationTabChartJS()
