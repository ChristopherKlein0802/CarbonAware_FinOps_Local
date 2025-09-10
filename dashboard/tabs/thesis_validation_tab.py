"""
Thesis Validation Tab for Carbon-Aware FinOps Dashboard

This module handles the thesis validation functionality including:
- Research question validation through competitive analysis
- Cost optimization vs Carbon optimization comparison charts  
- Integrated approach superiority demonstration
- Business case analysis with EU ETS pricing
- German grid analysis integration
- Academic summary with research novelty
"""

from dash import html, dcc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.components.components import DashboardCards, DashboardCharts

class ThesisValidationTab:
    """Handles thesis validation tab functionality with research focus"""
    
    def __init__(self):
        self.cards = DashboardCards()
        self.charts = DashboardCharts()
    
    def create_layout(self) -> html.Div:
        """
        Create the complete Thesis Validation tab layout
        
        Returns:
            html.Div: Complete thesis validation tab layout
        """
        return html.Div([
            html.Div([
                # Research Question Header
                html.Div([
                    html.H2("🎓 Research Question Validation", style={'color': '#2E8B57', 'marginBottom': '20px'}),
                    html.P("Integrierte Carbon-aware FinOps Optimierung vs. separate Cost-only und Carbon-only Tools",
                          style={'fontSize': '16px', 'color': '#666', 'fontStyle': 'italic'})
                ], style={'textAlign': 'center', 'marginBottom': '30px'}),
                
                # Key Business Metrics Cards
                html.Div([
                    html.Div(id='thesis-cost-advantage-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                    html.Div(id='thesis-carbon-advantage-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                    html.Div(id='thesis-roi-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                    html.Div(id='thesis-novelty-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'})
                ], style={'marginBottom': '30px'}),
                
                # Competitive Analysis Charts (Two Column Layout)
                html.Div([
                    html.H3("📊 Competitive Advantage Demonstration", style={'color': '#333', 'marginBottom': '20px'}),
                    
                    # Row 1: Cost vs Carbon Optimization
                    html.Div([
                        html.Div([
                            dcc.Graph(id='cost-optimization-comparison-chart')
                        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                        
                        html.Div([
                            dcc.Graph(id='carbon-optimization-comparison-chart') 
                        ], style={'width': '48%', 'display': 'inline-block'})
                    ], style={'marginBottom': '20px'}),
                    
                    # Row 2: Integrated Superiority Chart (Full Width)
                    html.Div([
                        dcc.Graph(id='integrated-superiority-chart')
                    ], style={'marginBottom': '30px'})
                ]),
                
                # Business Case & German Grid Analysis
                html.Div([
                    html.Div([
                        html.H4("💼 Conservative Business Case", style={'color': '#333'}),
                        html.Div(id='business-case-analysis')
                    ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                    
                    html.Div([
                        html.H4("🇩🇪 German Grid Integration", style={'color': '#333'}),
                        html.Div(id='german-grid-analysis')
                    ], style={'width': '48%', 'display': 'inline-block'})
                ], style={'marginBottom': '30px'}),
                
                # Academic Summary
                html.Div([
                    html.H4("📚 Academic Research Summary", style={'color': '#333'}),
                    html.Div(id='academic-research-summary')
                ])
                
            ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px', 'margin': '20px'})
        ])
    
    def create_cost_advantage_card(self, data: Dict) -> html.Div:
        """Create office hours advantage card showing scheduling-based optimization"""
        if 'competitive_advantage' not in data or 'scheduling_scenarios' not in data['competitive_advantage']:
            return self.cards.create_empty_state_card("Office Hours Advantage", "No scheduling data available", "🕘")
        
        office_hours = data['competitive_advantage']['scheduling_scenarios']['office_hours_only']
        runtime_reduction = office_hours.get('runtime_reduction_pct', 0)
        
        return self.cards.create_metric_card(
            title="Office Hours Advantage",
            value=f"{runtime_reduction:.1f}%",
            subtitle="Runtime reduction (Mo-Fr 9-17h scheduling)",
            icon="🕘"
        )
    
    def create_carbon_advantage_card(self, data: Dict) -> html.Div:
        """Create carbon-aware advantage card showing grid-based optimization"""
        if 'competitive_advantage' not in data or 'scheduling_scenarios' not in data['competitive_advantage']:
            return self.cards.create_empty_state_card("Carbon-aware Advantage", "No scheduling data available", "🌱")
        
        carbon_aware = data['competitive_advantage']['scheduling_scenarios']['carbon_aware_only']
        grid_threshold = carbon_aware.get('grid_threshold', '<350g CO2/kWh')
        
        return self.cards.create_metric_card(
            title="Carbon-aware Advantage", 
            value=grid_threshold,
            subtitle="Grid-based scheduling threshold",
            icon="🌱"
        )
    
    def create_roi_card(self, data: Dict) -> html.Div:
        """Create ROI payback card with Proof-of-Concept disclaimer"""
        if 'business_case' not in data:
            return self.cards.create_empty_state_card("ROI Payback", "No business case data available", "📈")
        
        business_case = data['business_case']
        roi_months = business_case.get('roi_payback_months', 999)
        proof_of_concept_status = business_case.get('proof_of_concept_status', 'Proof-of-Concept')
        
        # Show Proof-of-Concept status instead of unrealistic ROI
        if roi_months > 240:  # More than 20 years
            display_value = "Proof-of-Concept"
            subtitle = "Test infrastructure - Production scaling required"
        else:
            display_value = f"{roi_months:.1f} months"
            subtitle = "Conservative estimate ±15% uncertainty"
        
        return self.cards.create_metric_card(
            title="ROI Status",
            value=display_value,
            subtitle=subtitle,
            icon="🎓"
        )
    
    def create_novelty_card(self, data: Dict) -> html.Div:
        """Create integration value card showing unique combined optimization"""
        if 'competitive_advantage' not in data or 'scheduling_scenarios' not in data['competitive_advantage']:
            return self.cards.create_empty_state_card("Integration Value", "No scheduling data available", "🔗")
        
        integrated = data['competitive_advantage']['scheduling_scenarios']['integrated_approach']
        combined_efficiency = integrated.get('combined_efficiency_factor', 0.85)
        
        return self.cards.create_metric_card(
            title="Integration Value",
            value=f"{combined_efficiency:.1%}",
            subtitle="Combined scheduling efficiency (Office Hours + Carbon-aware)",
            icon="🔗"
        )
    
    def create_cost_optimization_comparison_chart(self, data: Dict) -> go.Figure:
        """Create cost optimization comparison chart"""
        if 'competitive_advantage' not in data:
            return self.charts.create_empty_chart("Cost Optimization Comparison")
        
        comp_data = data['competitive_advantage']
        
        # Prepare data for comparison using scheduling scenarios
        tools = ['Office Hours Only\n(Mo-Fr 9-17h)', 'Carbon-aware Only\n(<350g CO2/kWh)', 'Integrated Approach\n(Office Hours + Carbon-aware)']
        
        scheduling = comp_data.get('scheduling_scenarios', {})
        cost_savings = [
            scheduling.get('office_hours_only', {}).get('monthly_cost_savings', 0),
            scheduling.get('carbon_aware_only', {}).get('monthly_cost_savings', 0),
            scheduling.get('integrated_approach', {}).get('monthly_cost_savings', 0)
        ]
        
        fig = go.Figure([
            go.Bar(
                x=tools,
                y=cost_savings,
                text=[f'€{val:.0f}' for val in cost_savings],
                textposition='outside',
                marker_color=['#ff7f0e', '#d62728', '#2E8B57'],
                name='Monthly Cost Savings (EUR)'
            )
        ])
        
        fig.update_layout(
            title="Cost Optimization: Scheduling-Based Approaches Comparison",
            xaxis_title="Scheduling Strategy",
            yaxis_title="Monthly Cost Savings (EUR)",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_carbon_optimization_comparison_chart(self, data: Dict) -> go.Figure:
        """Create carbon optimization comparison chart"""
        if 'competitive_advantage' not in data:
            return self.charts.create_empty_chart("Carbon Optimization Comparison")
        
        comp_data = data['competitive_advantage']
        
        # Prepare data for comparison using scheduling scenarios
        tools = ['Office Hours Only\n(Runtime Reduction)', 'Carbon-aware Only\n(Grid-based Timing)', 'Integrated Approach\n(Combined Strategy)']
        
        scheduling = comp_data.get('scheduling_scenarios', {})
        co2_reduction = [
            scheduling.get('office_hours_only', {}).get('monthly_co2_reduction_kg', 0),
            scheduling.get('carbon_aware_only', {}).get('monthly_co2_reduction_kg', 0),
            scheduling.get('integrated_approach', {}).get('monthly_co2_reduction_kg', 0)
        ]
        
        fig = go.Figure([
            go.Bar(
                x=tools,
                y=co2_reduction,
                text=[f'{val:.1f} kg' for val in co2_reduction],
                textposition='outside',
                marker_color=['#ff7f0e', '#d62728', '#2E8B57'],
                name='Monthly CO2 Reduction (kg)'
            )
        ])
        
        fig.update_layout(
            title="Carbon Optimization: Scheduling-Based Approaches Comparison",
            xaxis_title="Scheduling Strategy",
            yaxis_title="Monthly CO2 Reduction (kg)",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_integrated_superiority_chart(self, data: Dict) -> go.Figure:
        """Create integrated approach superiority chart (thesis novelty demonstration)"""
        if 'competitive_advantage' not in data:
            return self.charts.create_empty_chart("Integrated Approach Superiority")
        
        comp_data = data['competitive_advantage']
        
        # Three-way comparison showing both dimensions using scheduling scenarios
        tools = ['Office Hours Only', 'Carbon-aware Only', 'Integrated Approach']
        
        scheduling = comp_data.get('scheduling_scenarios', {})
        cost_savings = [
            scheduling.get('office_hours_only', {}).get('monthly_cost_savings', 0),
            scheduling.get('carbon_aware_only', {}).get('monthly_cost_savings', 0),
            scheduling.get('integrated_approach', {}).get('monthly_cost_savings', 0)
        ]
        co2_reduction = [
            scheduling.get('office_hours_only', {}).get('monthly_co2_reduction_kg', 0),
            scheduling.get('carbon_aware_only', {}).get('monthly_co2_reduction_kg', 0),
            scheduling.get('integrated_approach', {}).get('monthly_co2_reduction_kg', 0)
        ]
        
        fig = go.Figure()
        
        # Add cost savings bars
        fig.add_trace(go.Bar(
            name='Cost Savings (EUR/month)',
            x=tools,
            y=cost_savings,
            text=[f'€{val:.0f}' for val in cost_savings],
            textposition='outside',
            marker_color='#1f77b4'
        ))
        
        # Add CO2 reduction bars (scaled for visibility)
        fig.add_trace(go.Bar(
            name='CO2 Reduction (kg/month × 10)',
            x=tools,
            y=[val * 10 for val in co2_reduction],  # Scale for visibility
            text=[f'{val:.1f} kg' for val in co2_reduction],
            textposition='outside',
            marker_color='#2E8B57'
        ))
        
        fig.update_layout(
            title="Scheduling-Based Optimization: Integrated Approach Superiority",
            xaxis_title="Scheduling Strategy",
            yaxis_title="Value (EUR for cost, kg×10 for CO2)",
            barmode='group',
            height=500,
            annotations=[
                dict(
                    text="🎓 Research Contribution: Combined scheduling strategies optimize both dimensions",
                    x=0.5, y=1.1,
                    xref='paper', yref='paper',
                    showarrow=False,
                    font=dict(size=14, color='#2E8B57')
                )
            ]
        )
        
        return fig

# Create global instance for use across dashboard
thesis_validation_tab = ThesisValidationTab()