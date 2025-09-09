"""
Overview Tab for Carbon-Aware FinOps Dashboard

This module handles the Overview tab functionality including:
- Key metric cards
- 4 separate overview charts (costs, runtime, CO2, efficiency) 
- Key insights and quick actions
"""

from dash import html, dcc
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.components import DashboardCards, DashboardCharts

class OverviewTab:
    """Handles all Overview tab functionality"""
    
    def __init__(self):
        self.cards = DashboardCards()
        self.charts = DashboardCharts()
    
    def create_layout(self) -> html.Div:
        """
        Create the complete Overview tab layout
        
        Returns:
            html.Div: Complete overview tab layout
        """
        return html.Div([
            html.Div([
                # Key metrics cards (same as infrastructure tab)
                html.Div([
                    html.Div(id='overview-cost-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                    html.Div(id='overview-co2-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                    html.Div(id='overview-instances-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                    html.Div(id='overview-savings-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'})
                ]),
                
                html.Br(),
                
                # Summary charts - 4 separate charts for better visibility
                html.Div([
                    html.H4("📈 Infrastructure Overview", style={'color': '#333'}),
                    
                    # Row 1: Costs and Runtime
                    html.Div([
                        html.Div([
                            dcc.Graph(id='overview-costs-chart')
                        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                        
                        html.Div([
                            dcc.Graph(id='overview-runtime-chart')
                        ], style={'width': '48%', 'display': 'inline-block'})
                    ]),
                    
                    # Row 2: CO2 and Efficiency
                    html.Div([
                        html.Div([
                            dcc.Graph(id='overview-co2-chart')
                        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                        
                        html.Div([
                            dcc.Graph(id='overview-efficiency-chart')
                        ], style={'width': '48%', 'display': 'inline-block'})
                    ])
                ]),
                
                html.Br(),
                
                # Quick insights (moved below chart)
                html.Div([
                    html.Div([
                        html.H4("💡 Key Insights", style={'color': '#333'}),
                        html.Div(id='overview-insights')
                    ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                    
                    html.Div([
                        html.H4("🚀 Quick Actions", style={'color': '#333'}),
                        html.Div(id='overview-quick-actions')
                    ], style={'width': '48%', 'display': 'inline-block'})
                ])
                
            ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px', 'margin': '20px'})
        ])
    
    def create_cost_card(self, data: List[Dict]) -> html.Div:
        """Create cost overview card for overview tab"""
        return self.cards.create_cost_overview_card(data)
    
    def create_co2_card(self, data: List[Dict]) -> html.Div:
        """Create CO2 overview card for overview tab"""
        return self.cards.create_co2_overview_card(data)
    
    def create_instances_card(self, data: List[Dict]) -> html.Div:
        """Create instances overview card for overview tab"""
        return self.cards.create_instances_overview_card(data)
    
    def create_savings_card(self, data: List[Dict]) -> html.Div:
        """Create savings potential card for overview tab"""
        return self.cards.create_savings_overview_card(data)
    
    def create_costs_chart(self, data: List[Dict]):
        """Create individual cost chart for Overview tab"""
        return self.charts.create_costs_chart(data, height=300)
    
    def create_runtime_chart(self, data: List[Dict]):
        """Create individual runtime chart for Overview tab"""
        return self.charts.create_runtime_chart(data, height=300)
    
    def create_co2_chart(self, data: List[Dict]):
        """Create individual CO2 chart for Overview tab"""
        return self.charts.create_co2_chart(data, height=300)
    
    def create_efficiency_chart(self, data: List[Dict]):
        """Create individual efficiency chart for Overview tab"""
        return self.charts.create_efficiency_chart(data, height=300)
    
    def create_insights(self, data: List[Dict]) -> html.Div:
        """Create key insights section"""
        if not data:
            insights = [
                "No AWS infrastructure currently deployed",
                "Dashboard ready for real-time analysis",
                "Deploy infrastructure to see optimization potential",
                "ElectricityMap and Boavizta APIs ready for carbon analysis"
            ]
        else:
            # Calculate meaningful insights from real data
            total_cost = sum(item['monthly_cost_eur'] for item in data)
            total_co2 = sum(item['monthly_co2_kg'] for item in data)
            avg_runtime = sum(item['runtime_hours_month'] for item in data) / len(data)
            
            # Find highest cost instance
            highest_cost_instance = max(data, key=lambda x: x['monthly_cost_eur'])
            
            # Calculate total potential savings
            total_savings = 0
            for instance in data:
                if 'optimization_potential' in instance:
                    best_savings = max(
                        instance['optimization_potential']['office_hours']['cost_savings'],
                        instance['optimization_potential']['weekdays_only']['cost_savings'],
                        instance['optimization_potential']['carbon_aware']['cost_savings']
                    )
                    total_savings += best_savings
            
            insights = [
                f"Current monthly infrastructure cost: €{total_cost:.0f}",
                f"Monthly carbon footprint: {total_co2:.1f} kg CO2",
                f"Average runtime: {avg_runtime:.0f} hours/month per instance",
                f"Highest cost instance: {highest_cost_instance['name']} (€{highest_cost_instance['monthly_cost_eur']:.0f})",
                f"Total optimization potential: €{total_savings:.0f}/month savings available"
            ]
        
        return html.Div([html.P(insight, style={'margin': '10px 0'}) for insight in insights])

    def create_quick_actions(self, data: List[Dict]) -> html.Div:
        """Create quick actions section"""
        if not data:
            actions = [
                "• Explore Carbon & Power Data for API details",
                "• Review Academic Value for methodology", 
                "• Deploy infrastructure to see optimization potential",
                "• Check Optimization tab for scheduling strategies"
            ]
        else:
            # Calculate actionable recommendations based on data
            total_potential_savings = 0
            high_cost_instances = []
            
            for instance in data:
                # Calculate best potential savings for this instance
                if 'optimization_potential' in instance:
                    best_savings = max(
                        instance['optimization_potential']['office_hours']['cost_savings'],
                        instance['optimization_potential']['weekdays_only']['cost_savings'],
                        instance['optimization_potential']['carbon_aware']['cost_savings']
                    )
                    total_potential_savings += best_savings
                    
                    # Identify high-cost instances for priority optimization
                    if instance.get('monthly_cost_eur', 0) > 50:
                        high_cost_instances.append(instance['name'])
            
            actions = [
                f"• Optimization potential: Up to €{total_potential_savings:.0f}/month savings available",
                f"• Priority: Focus on {len(high_cost_instances)} high-cost instances first" if high_cost_instances else "• Review all instances for optimization opportunities",
                "• Next steps: Check Optimization tab for detailed strategies",
                "• Monitor: Track carbon trends in Carbon & Power Data tab"
            ]
        
        return html.Div([html.P(action, style={'margin': '10px 0'}) for action in actions])

# Global instance for reuse
overview_tab = OverviewTab()