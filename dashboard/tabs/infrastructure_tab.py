"""
Infrastructure Tab - Modern Builder.io Design
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

class InfrastructureTab:
    """Modern Builder.io Infrastructure Tab - Completely redesigned"""
    
    def __init__(self):
        self.cards = DashboardCards()
        self.charts = DashboardCharts()
    
    def create_tab_layout(self) -> html.Div:
        """Create modern Builder.io infrastructure layout"""
        return html.Div([
            # Modern Section Header
            html.Div([
                html.H2("🏗️ Infrastructure Analysis", className="section-title"),
                html.P("Deep-dive analytics for AWS infrastructure optimization and carbon efficiency", 
                       className="section-description")
            ], className="section-header"),
            
            # KPI Cards Grid (Builder.io style)
            html.Div([
                html.Div(id='infrastructure-active-card', className="metric-card"),
                html.Div(id='infrastructure-efficiency-card', className="metric-card"),
                html.Div(id='infrastructure-cost-hour-card', className="metric-card"),
                html.Div(id='infrastructure-rightsizing-card', className="metric-card")
            ], className="metrics-grid"),
            
            # Cost Analysis Section (Builder.io grid)
            html.Div([
                html.H3("💰 Cost Analysis Deep-Dive", className="subsection-title"),
                html.Div([
                    html.Div([
                        html.H4("🕐 Historical Trends", className="chart-title"),
                        dcc.Graph(id='infrastructure-cost-trends-chart', className="chart-container")
                    ], className="chart-card"),
                    html.Div([
                        html.H4("📊 Instance Distribution", className="chart-title"),
                        dcc.Graph(id='infrastructure-type-distribution-chart', className="chart-container")
                    ], className="chart-card")
                ], className="charts-grid-2")
            ], className="content-section"),
            
            # Performance Section (Builder.io responsive)
            html.Div([
                html.H3("⚡ Performance Analysis", className="subsection-title"),
                html.Div([
                    html.Div([
                        html.H4("🔗 Runtime vs Cost", className="chart-title"),
                        dcc.Graph(id='infrastructure-runtime-correlation-chart', className="chart-container")
                    ], className="chart-card"),
                    html.Div([
                        html.H4("🎯 Efficiency Matrix", className="chart-title"),
                        dcc.Graph(id='infrastructure-efficiency-matrix-chart', className="chart-container")
                    ], className="chart-card")
                ], className="charts-grid-2")
            ], className="content-section"),
            
            # Optimization Section (Builder.io layout)
            html.Div([
                html.H3("🚀 Optimization Opportunities", className="subsection-title"),
                html.Div([
                    html.Div([
                        html.H4("📈 Right-sizing Analysis", className="chart-title"),
                        html.Div(id='infrastructure-rightsizing-analysis', className="analysis-content")
                    ], className="analysis-card"),
                    html.Div([
                        html.H4("❤️ Infrastructure Health", className="chart-title"),
                        html.Div(id='infrastructure-health-matrix', className="health-content")
                    ], className="analysis-card")
                ], className="analysis-grid-2")
            ], className="content-section"),
            
            # Data Sources Section (Builder.io modern)
            html.Div([
                html.H3("🔬 Data Sources & Methodology", className="subsection-title"),
                html.Div([
                    html.Div([
                        html.H4("☁️ AWS Cost Explorer", className="info-title"),
                        html.Div(id='infrastructure-aws-data', className="info-content")
                    ], className="info-card"),
                    html.Div([
                        html.H4("⏱️ Runtime Analytics", className="info-title"),
                        html.Div(id='infrastructure-runtime-data', className="info-content")
                    ], className="info-card"),
                    html.Div([
                        html.H4("⚠️ API Limitations", className="info-title"),
                        html.Div(id='infrastructure-api-limitations', className="info-content")
                    ], className="info-card"),
                    html.Div([
                        html.H4("🎓 Scientific Method", className="info-title"),
                        html.Div(id='infrastructure-methodology', className="info-content")
                    ], className="info-card")
                ], className="info-grid-4")
            ], className="content-section")
        ], className="content-section")
    
    def create_active_infrastructure_card(self, instances: List[Dict]) -> html.Div:
        """Create modern active infrastructure card with Builder.io styling"""
        running_instances = len([i for i in instances if i.get('state') == 'running'])
        total_instances = len(instances)
        
        return html.Div([
            html.Div([
                html.Div("🏗️", className="card-icon"),
                html.Div([
                    html.H3(str(total_instances), className="card-value"),
                    html.P("Active Infrastructure", className="card-label"),
                    html.Span(f"{running_instances} running now", className="card-detail")
                ], className="card-content")
            ], className="card-inner")
        ], className="modern-card infrastructure-card")
    
    def create_efficiency_card(self, instances: List[Dict]) -> html.Div:
        """Create modern efficiency card with Builder.io styling"""
        if not instances:
            return self._create_empty_card("⚡", "Resource Efficiency", "No data", "0%")
        
        # Calculate average utilization
        total_utilization = sum(
            (instance.get('runtime_hours_month', 0) / 720) * 100 
            for instance in instances
        )
        avg_efficiency = total_utilization / len(instances) if instances else 0
        
        return html.Div([
            html.Div([
                html.Div("⚡", className="card-icon"),
                html.Div([
                    html.H3(f"{avg_efficiency:.0f}%", className="card-value"),
                    html.P("Resource Efficiency", className="card-label"),
                    html.Span("average utilization", className="card-detail")
                ], className="card-content")
            ], className="card-inner")
        ], className="modern-card efficiency-card")
    
    def create_cost_hour_card(self, instances: List[Dict]) -> html.Div:
        """Create modern cost per hour card with Builder.io styling"""
        if not instances:
            return self._create_empty_card("💸", "Cost per Hour", "No data", "€0.00")
        
        total_cost = sum(instance.get('monthly_cost_eur', 0) for instance in instances)
        total_hours = sum(instance.get('runtime_hours_month', 0) for instance in instances)
        avg_cost_hour = total_cost / total_hours if total_hours > 0 else 0
        
        return html.Div([
            html.Div([
                html.Div("💸", className="card-icon"),
                html.Div([
                    html.H3(f"€{avg_cost_hour:.3f}", className="card-value"),
                    html.P("Average Cost per Hour", className="card-label"),
                    html.Span("infrastructure average", className="card-detail")
                ], className="card-content")
            ], className="card-inner")
        ], className="modern-card cost-hour-card")
    
    def create_rightsizing_card(self, instances: List[Dict]) -> html.Div:
        """Create modern right-sizing potential card with Builder.io styling"""
        if not instances:
            return self._create_empty_card("🎯", "Right-sizing Potential", "No data", "€0.00")
        
        # Calculate potential savings from right-sizing
        potential_savings = 0
        for instance in instances:
            utilization = instance.get('runtime_hours_month', 0) / 720
            if utilization < 0.3:  # Low utilization
                potential_savings += instance.get('monthly_cost_eur', 0) * 0.4
            elif utilization < 0.5:  # Medium-low utilization
                potential_savings += instance.get('monthly_cost_eur', 0) * 0.2
        
        return html.Div([
            html.Div([
                html.Div("🎯", className="card-icon"),
                html.Div([
                    html.H3(f"€{potential_savings:.0f}", className="card-value"),
                    html.P("Right-sizing Potential", className="card-label"),
                    html.Span("monthly savings", className="card-detail")
                ], className="card-content")
            ], className="card-inner")
        ], className="modern-card rightsizing-card")
    
    def create_cost_trends_chart(self, instances: List[Dict]):
        """Create modern cost trends chart"""
        if not instances:
            return self.charts.create_empty_chart("No cost trend data available")
        
        return self.charts.create_cost_analysis_chart(instances)
    
    def create_type_distribution_chart(self, instances: List[Dict]):
        """Create modern instance type distribution chart"""
        if not instances:
            return self.charts.create_empty_chart("No type distribution data available")
        
        return self.charts.create_instance_type_distribution_chart(instances)
    
    def create_runtime_correlation_chart(self, instances: List[Dict]):
        """Create modern runtime correlation chart"""
        if not instances:
            return self.charts.create_empty_chart("No runtime correlation data available")
        
        return self.charts.create_runtime_cost_correlation_chart(instances)
    
    def create_efficiency_matrix_chart(self, instances: List[Dict]):
        """Create modern efficiency matrix chart"""
        if not instances:
            return self.charts.create_empty_chart("No efficiency matrix data available")
        
        return self.charts.create_efficiency_matrix_chart(instances)
    
    def create_rightsizing_analysis(self, instances: List[Dict]) -> html.Div:
        """Create modern right-sizing analysis with Builder.io styling"""
        if not instances:
            return html.Div([
                html.H5("🎯 Right-sizing Analysis", className="analysis-subtitle"),
                html.P("No instances available for analysis", className="empty-state")
            ], className="analysis-section")
        
        # Analyze instances for right-sizing opportunities
        over_provisioned = []
        under_provisioned = []
        optimal = []
        
        for instance in instances:
            utilization = instance.get('runtime_hours_month', 0) / 720
            cost_per_hour = instance.get('monthly_cost_eur', 0) / instance.get('runtime_hours_month', 1)
            
            if utilization < 0.3:
                over_provisioned.append(instance)
            elif utilization > 0.9 and cost_per_hour > 0.15:
                under_provisioned.append(instance)
            else:
                optimal.append(instance)
        
        total_savings = sum(
            inst.get('monthly_cost_eur', 0) * 0.4 for inst in over_provisioned
        ) + sum(
            inst.get('monthly_cost_eur', 0) * 0.2 for inst in under_provisioned
        )
        
        return html.Div([
            html.H5("🎯 Right-sizing Analysis", className="analysis-subtitle"),
            html.Div([
                html.Div([
                    html.Div([
                        html.Span("⬇️", className="insight-icon"),
                        html.Span(f"{len(over_provisioned)} over-provisioned", className="insight-text")
                    ], className="insight-item"),
                    html.Div([
                        html.Span("⬆️", className="insight-icon"),
                        html.Span(f"{len(under_provisioned)} under-provisioned", className="insight-text")
                    ], className="insight-item"),
                    html.Div([
                        html.Span("✅", className="insight-icon"),
                        html.Span(f"{len(optimal)} optimally sized", className="insight-text")
                    ], className="insight-item")
                ], className="insights-list"),
                html.Div([
                    html.H4(f"€{total_savings:.0f}", className="savings-value"),
                    html.P("potential monthly savings", className="savings-label")
                ], className="savings-summary")
            ], className="analysis-content")
        ], className="analysis-section")
    
    def create_health_matrix(self, instances: List[Dict]) -> html.Div:
        """Create modern infrastructure health matrix with Builder.io styling"""
        if not instances:
            return html.Div([
                html.H5("❤️ Infrastructure Health", className="analysis-subtitle"),
                html.P("No health data available", className="empty-state")
            ], className="analysis-section")
        
        # Calculate health metrics
        healthy = 0
        warning = 0
        critical = 0
        
        for instance in instances:
            utilization = instance.get('runtime_hours_month', 0) / 720
            cost_per_hour = instance.get('monthly_cost_eur', 0) / instance.get('runtime_hours_month', 1)
            
            if utilization > 0.3 and utilization < 0.8 and cost_per_hour < 0.2:
                healthy += 1
            elif utilization < 0.2 or cost_per_hour > 0.3:
                critical += 1
            else:
                warning += 1
        
        total = len(instances)
        health_score = (healthy / total * 100) if total > 0 else 0
        
        return html.Div([
            html.H5("❤️ Infrastructure Health", className="analysis-subtitle"),
            html.Div([
                html.Div([
                    html.Div([
                        html.H4(str(healthy), className="health-value healthy"),
                        html.P("Healthy", className="health-label")
                    ], className="health-metric"),
                    html.Div([
                        html.H4(str(warning), className="health-value warning"),
                        html.P("Warning", className="health-label")
                    ], className="health-metric"),
                    html.Div([
                        html.H4(str(critical), className="health-value critical"),
                        html.P("Critical", className="health-label")
                    ], className="health-metric")
                ], className="health-metrics"),
                html.Div([
                    html.H3(f"{health_score:.0f}%", className="health-score"),
                    html.P("Overall Health Score", className="health-score-label")
                ], className="health-summary")
            ], className="health-content")
        ], className="analysis-section")
    
    def create_aws_data_summary(self, instances: List[Dict]) -> html.Div:
        """Create modern AWS data summary with Builder.io styling"""
        if not instances:
            return html.Div([
                html.P("☁️ AWS Cost Explorer", className="info-subtitle"),
                html.P("No instances deployed", className="info-empty")
            ], className="info-section")
        
        total_cost = sum(instance.get('monthly_cost_eur', 0) for instance in instances)
        instance_types = len(set(instance.get('instance_type', '') for instance in instances))
        
        return html.Div([
            html.P("☁️ AWS Cost Explorer", className="info-subtitle"),
            html.Div([
                html.Div([
                    html.Span("💰", className="info-icon"),
                    html.Span(f"€{total_cost:.2f} total monthly cost", className="info-text")
                ], className="info-item"),
                html.Div([
                    html.Span("🔧", className="info-icon"),
                    html.Span(f"{instance_types} different instance types", className="info-text")
                ], className="info-item"),
                html.Div([
                    html.Span("📊", className="info-icon"),
                    html.Span("Real-time API integration", className="info-text")
                ], className="info-item")
            ], className="info-list")
        ], className="info-section")
    
    def create_runtime_data_summary(self, instances: List[Dict]) -> html.Div:
        """Create modern runtime data summary with Builder.io styling"""
        if not instances:
            return html.Div([
                html.P("⏱️ Runtime Analytics", className="info-subtitle"),
                html.P("No runtime data available", className="info-empty")
            ], className="info-section")
        
        total_runtime = sum(instance.get('runtime_hours_month', 0) for instance in instances)
        avg_runtime = total_runtime / len(instances) if instances else 0
        running_now = len([i for i in instances if i.get('state') == 'running'])
        
        return html.Div([
            html.P("⏱️ Runtime Analytics", className="info-subtitle"),
            html.Div([
                html.Div([
                    html.Span("⏰", className="info-icon"),
                    html.Span(f"{total_runtime:.0f}h total monthly runtime", className="info-text")
                ], className="info-item"),
                html.Div([
                    html.Span("📊", className="info-icon"),
                    html.Span(f"{avg_runtime:.0f}h average per instance", className="info-text")
                ], className="info-item"),
                html.Div([
                    html.Span("🟢", className="info-icon"),
                    html.Span(f"{running_now} currently running", className="info-text")
                ], className="info-item")
            ], className="info-list")
        ], className="info-section")
    
    def create_api_limitations_summary(self) -> html.Div:
        """Create modern API limitations summary with Builder.io styling"""
        return html.Div([
            html.P("⚠️ API Limitations", className="info-subtitle"),
            html.Div([
                html.Div([
                    html.Span("❌", className="info-icon"),
                    html.Span("RESOURCE_ID not supported", className="info-text")
                ], className="info-item"),
                html.Div([
                    html.Span("✅", className="info-icon"),
                    html.Span("Proportional allocation used", className="info-text")
                ], className="info-item"),
                html.Div([
                    html.Span("📚", className="info-icon"),
                    html.Span("Research contribution validated", className="info-text")
                ], className="info-item")
            ], className="info-list")
        ], className="info-section")
    
    def create_methodology_summary(self) -> html.Div:
        """Create modern methodology summary with Builder.io styling"""
        return html.Div([
            html.P("🎓 Scientific Method", className="info-subtitle"),
            html.Div([
                html.Div([
                    html.Span("1️⃣", className="info-icon"),
                    html.Span("Real AWS API data collection", className="info-text")
                ], className="info-item"),
                html.Div([
                    html.Span("2️⃣", className="info-icon"),
                    html.Span("Precision runtime calculation", className="info-text")
                ], className="info-item"),
                html.Div([
                    html.Span("3️⃣", className="info-icon"),
                    html.Span("Validated cost allocation", className="info-text")
                ], className="info-item"),
                html.Div([
                    html.Span("4️⃣", className="info-icon"),
                    html.Span("Carbon-aware optimization", className="info-text")
                ], className="info-item")
            ], className="info-list")
        ], className="info-section")
    
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
infrastructure_tab = InfrastructureTab()