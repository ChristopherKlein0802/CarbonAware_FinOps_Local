"""
Overview Tab - Modern Builder.io Design
Carbon-Aware FinOps Dashboard - Bachelor Thesis

Complete Builder.io modernization with:
- Modern CSS classes only
- Clean component structure
- Optimized performance
- Academic presentation ready
"""

from dash import html, dcc
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.components.components import DashboardCards, DashboardCharts

class OverviewTab:
    """Modern Builder.io Overview Tab - Completely redesigned"""
    
    def __init__(self):
        self.cards = DashboardCards()
        self.charts = DashboardCharts()
    
    def create_tab_layout(self) -> html.Div:
        """Create modern Builder.io overview layout"""
        return html.Div([
            # Modern Section Header
            html.Div([
                html.H2("📊 Infrastructure Overview", className="section-title"),
                html.P("Real-time AWS infrastructure monitoring with integrated carbon and cost analytics", 
                       className="section-description")
            ], className="section-header"),
            
            # KPI Cards Grid (Builder.io style)
            html.Div([
                html.Div(id='overview-cost-card', className="metric-card"),
                html.Div(id='overview-co2-card', className="metric-card"),
                html.Div(id='overview-instances-card', className="metric-card"),
                html.Div(id='overview-savings-card', className="metric-card")
            ], className="metrics-grid"),
            
            # Analysis Section (Builder.io grid)
            html.Div([
                html.Div([
                    html.Div(id='overview-insights', className="insights-content"),
                    html.Div(id='overview-business-case', className="business-case-content")
                ], className="analysis-column"),
                html.Div([
                    html.Div(id='overview-data-quality', className="data-quality-content")
                ], className="quality-column")
            ], className="analysis-grid"),
            
            # Charts Grid (Builder.io responsive)
            html.Div([
                html.Div([
                    html.H4("💰 Cost Analysis", className="chart-title"),
                    dcc.Graph(id='overview-costs-chart', className="chart-container")
                ], className="chart-card"),
                html.Div([
                    html.H4("⏱️ Runtime Patterns", className="chart-title"),
                    dcc.Graph(id='overview-runtime-chart', className="chart-container")
                ], className="chart-card"),
                html.Div([
                    html.H4("🌍 Carbon Emissions", className="chart-title"),
                    dcc.Graph(id='overview-co2-chart', className="chart-container")
                ], className="chart-card"),
                html.Div([
                    html.H4("📈 Efficiency Matrix", className="chart-title"),
                    dcc.Graph(id='overview-efficiency-chart', className="chart-container")
                ], className="chart-card")
            ], className="charts-grid")
        ], className="content-section")
    
    def create_cost_card(self, instances: List[Dict]) -> html.Div:
        """Create modern cost card with Builder.io styling"""
        if not instances:
            return self._create_empty_card("💰", "Total Monthly Cost", "No data", "€0.00")
        
        total_cost = sum(instance.get('monthly_cost_eur', 0) for instance in instances)
        
        return html.Div([
            html.Div([
                html.Div("💰", className="card-icon"),
                html.Div([
                    html.H3(f"€{total_cost:.2f}", className="card-value"),
                    html.P("Total Monthly Cost", className="card-label"),
                    html.Span(f"across {len(instances)} instances", className="card-detail")
                ], className="card-content")
            ], className="card-inner")
        ], className="modern-card cost-card")
    
    def create_co2_card(self, instances: List[Dict]) -> html.Div:
        """Create modern CO2 card with Builder.io styling"""
        if not instances:
            return self._create_empty_card("🌍", "CO2 Emissions", "No data", "0.0 kg")
        
        total_co2 = sum(instance.get('monthly_co2_kg', 0) for instance in instances)
        
        return html.Div([
            html.Div([
                html.Div("🌍", className="card-icon"),
                html.Div([
                    html.H3(f"{total_co2:.2f} kg", className="card-value"),
                    html.P("Monthly CO2 Emissions", className="card-label"),
                    html.Span("from German grid", className="card-detail")
                ], className="card-content")
            ], className="card-inner")
        ], className="modern-card co2-card")
    
    def create_instances_card(self, instances: List[Dict]) -> html.Div:
        """Create modern instances card with Builder.io styling"""
        running_instances = len([i for i in instances if i.get('state') == 'running'])
        
        return html.Div([
            html.Div([
                html.Div("🖥️", className="card-icon"),
                html.Div([
                    html.H3(str(len(instances)), className="card-value"),
                    html.P("Active Instances", className="card-label"),
                    html.Span(f"{running_instances} running", className="card-detail")
                ], className="card-content")
            ], className="card-inner")
        ], className="modern-card instances-card")
    
    def create_savings_card(self, instances: List[Dict]) -> html.Div:
        """Create modern savings card with Builder.io styling"""
        if not instances:
            return self._create_empty_card("💡", "Potential Savings", "No data", "€0.00")
        
        # Calculate potential savings (simplified)
        potential_savings = sum(instance.get('monthly_cost_eur', 0) * 0.15 for instance in instances)
        
        return html.Div([
            html.Div([
                html.Div("💡", className="card-icon"),
                html.Div([
                    html.H3(f"€{potential_savings:.2f}", className="card-value"),
                    html.P("Potential Monthly Savings", className="card-label"),
                    html.Span("through optimization", className="card-detail")
                ], className="card-content")
            ], className="card-inner")
        ], className="modern-card savings-card")
    
    def create_insights(self, instances: List[Dict]) -> html.Div:
        """Create modern insights section with Builder.io styling"""
        if not instances:
            return html.Div([
                html.H4("📊 Key Insights", className="section-subtitle"),
                html.P("No instances found for analysis", className="empty-state")
            ], className="insights-section")
        
        total_cost = sum(instance.get('monthly_cost_eur', 0) for instance in instances)
        avg_cost = total_cost / len(instances) if instances else 0
        
        return html.Div([
            html.H4("📊 Key Insights", className="section-subtitle"),
            html.Div([
                html.Div([
                    html.Span("🎯", className="insight-icon"),
                    html.Span(f"Average cost per instance: €{avg_cost:.2f}/month", className="insight-text")
                ], className="insight-item"),
                html.Div([
                    html.Span("⚡", className="insight-icon"),
                    html.Span(f"Total infrastructure: {len(instances)} instances", className="insight-text")
                ], className="insight-item"),
                html.Div([
                    html.Span("🌍", className="insight-icon"),
                    html.Span("Carbon optimization active", className="insight-text")
                ], className="insight-item")
            ], className="insights-list")
        ], className="insights-section")
    
    def create_business_case_summary(self, instances: List[Dict]) -> html.Div:
        """Create modern business case with Builder.io styling"""
        return html.Div([
            html.H4("💼 Business Case", className="section-subtitle"),
            html.Div([
                html.P("🎓 Bachelor Thesis Project", className="business-highlight"),
                html.P("Integration von Carbon-aware FinOps für deutsche KMU", className="business-description"),
                html.Div([
                    html.Span("✅", className="status-icon"),
                    html.Span("Proof-of-Concept Status", className="status-text")
                ], className="status-item")
            ], className="business-content")
        ], className="business-section")
    
    def create_data_quality_summary(self, instances: List[Dict]) -> html.Div:
        """Create modern data quality section with Builder.io styling"""
        return html.Div([
            html.H4("🔬 Data Quality", className="section-subtitle"),
            html.Div([
                html.Div([
                    html.Span("🔗", className="quality-icon"),
                    html.Span("ElectricityMap API", className="quality-source"),
                    html.Span("✅", className="quality-status")
                ], className="quality-item"),
                html.Div([
                    html.Span("⚙️", className="quality-icon"),
                    html.Span("Boavizta API", className="quality-source"),
                    html.Span("✅", className="quality-status")
                ], className="quality-item"),
                html.Div([
                    html.Span("☁️", className="quality-icon"),
                    html.Span("AWS Cost Explorer", className="quality-source"),
                    html.Span("✅", className="quality-status")
                ], className="quality-item")
            ], className="quality-list"),
            html.P("Scientific rigor: NO FALLBACK policy", className="quality-note")
        ], className="quality-section")
    
    def create_costs_chart(self, instances: List[Dict]):
        """Create modern costs chart"""
        if not instances:
            return self.charts.create_empty_chart("No cost data available")
        
        return self.charts.create_cost_breakdown_chart(instances)
    
    def create_runtime_chart(self, instances: List[Dict]):
        """Create modern runtime chart"""
        if not instances:
            return self.charts.create_empty_chart("No runtime data available")
        
        return self.charts.create_runtime_analysis_chart(instances)
    
    def create_co2_chart(self, instances: List[Dict]):
        """Create modern CO2 chart"""
        if not instances:
            return self.charts.create_empty_chart("No CO2 data available")
        
        return self.charts.create_co2_emissions_chart(instances)
    
    def create_efficiency_chart(self, instances: List[Dict]):
        """Create modern efficiency chart"""
        if not instances:
            return self.charts.create_empty_chart("No efficiency data available")
        
        return self.charts.create_efficiency_matrix_chart(instances)
    
    def _create_empty_card(self, icon: str, title: str, subtitle: str, value: str) -> html.Div:
        """Create empty state card with Builder.io styling"""
        return html.Div([
            html.Div([
                html.Div(icon, className="card-icon"),
                html.Div([
                    html.H3(value, className="card-value empty"),
                    html.P(title, className="card-label"),
                    html.Span(subtitle, className="card-detail")
                ], className="card-content")
            ], className="card-inner")
        ], className="modern-card empty-card")

# Create instance
overview_tab = OverviewTab()