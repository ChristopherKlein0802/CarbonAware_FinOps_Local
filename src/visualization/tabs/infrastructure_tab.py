"""
Infrastructure Analysis Tab for Carbon-Aware FinOps Dashboard

This module handles the Infrastructure Analysis tab functionality including:
- Key metric cards
- Instance analysis table
- AWS Cost Explorer data
- Runtime analysis data
"""

from dash import html, dash_table
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.cards import DashboardCards
from components.charts import DashboardCharts

class InfrastructureTab:
    """Handles all Infrastructure Analysis tab functionality"""
    
    def __init__(self):
        self.cards = DashboardCards()
        self.charts = DashboardCharts()
    
    def create_layout(self) -> html.Div:
        """
        Create the complete Infrastructure Analysis tab layout
        
        Returns:
            html.Div: Complete infrastructure tab layout
        """
        return html.Div([
            html.H2("📊 Current Infrastructure Analysis", 
                   style={'color': '#2E8B57', 'borderBottom': '2px solid #2E8B57', 'paddingBottom': '5px', 'marginBottom': '20px'}),
            
            # Key metrics cards
            html.Div([
                html.Div(id='cost-overview-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                html.Div(id='co2-overview-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                html.Div(id='instances-overview-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                html.Div(id='carbon-intensity-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'})
            ], style={'marginBottom': '30px'}),
            
            # Cost Analysis Chart
            html.Div([
                html.H3("💡 Cost Analysis - Historical vs Current Usage", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                html.Div(id='cost-analysis-chart')
            ], style={'marginBottom': '30px'}),
            
            # Instance analysis section
            html.Div([
                html.H3("🖥️ Instance Analysis", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                html.Div(id='instance-analysis-table')
            ], style={'marginBottom': '30px'}),
            
            # Data source information
            html.Div([
                html.Div([
                    html.H4("💰 AWS Cost Explorer Data", style={'color': '#333'}),
                    html.Div(id='aws-cost-explorer-data')
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                
                html.Div([
                    html.H4("⏱️ Runtime Analysis Data", style={'color': '#333'}),
                    html.Div(id='runtime-analysis-data')
                ], style={'width': '48%', 'display': 'inline-block'})
            ])
        ], style={'padding': '20px'})
    
    def create_cost_card(self, data: List[Dict]) -> html.Div:
        """Create cost overview card"""
        return self.cards.create_cost_overview_card(data)
    
    def create_co2_card(self, data: List[Dict]) -> html.Div:
        """Create CO2 overview card"""
        return self.cards.create_co2_overview_card(data)
    
    def create_instances_card(self, data: List[Dict]) -> html.Div:
        """Create instances overview card"""
        return self.cards.create_instances_overview_card(data)
    
    def create_carbon_intensity_card(self, data: List[Dict]) -> html.Div:
        """Create carbon intensity card"""
        return self.cards.create_carbon_intensity_card(data)
    
    def create_cost_analysis_chart(self, data: List[Dict]):
        """Create cost analysis chart showing historical vs current usage"""
        return self.charts.create_cost_analysis_chart(data)
    
    def create_instance_analysis_table(self, data: List[Dict]) -> html.Div:
        """Create instance analysis table"""
        if not data:
            return html.Div([
                html.P("No instances available for analysis", 
                      style={'textAlign': 'center', 'color': '#666', 'fontSize': '16px', 'padding': '40px'}),
                html.P("Deploy AWS infrastructure to see detailed instance analysis", 
                      style={'textAlign': 'center', 'color': '#999', 'fontSize': '14px'})
            ], style={'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'border': '1px dashed #ccc'})
        
        # Prepare table data
        table_data = []
        for item in data:
            table_data.append({
                'Instance Name': item['name'],
                'Type': item['instance_type'],
                'State': item['state'],
                'Monthly Cost (€)': f"€{item['monthly_cost_eur']:.2f}",
                'Runtime (h/month)': f"{item['runtime_hours_month']:.0f}h",
                'CO2 (kg/month)': f"{item['monthly_co2_kg']:.1f}kg",
                'Power (W)': f"{item['power_consumption_watts']:.0f}W"
            })
        
        return dash_table.DataTable(
            data=table_data,
            columns=[{"name": col, "id": col} for col in table_data[0].keys()],
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontSize': '13px',
                'fontFamily': 'Arial'
            },
            style_header={
                'backgroundColor': '#2E8B57',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ],
            style_table={'overflowX': 'auto'}
        )
    
    def create_aws_cost_explorer_data(self, data: List[Dict]) -> html.Div:
        """Create AWS Cost Explorer data summary"""
        if not data:
            return html.Div([
                html.P("No Cost Explorer data available", style={'color': '#666'}),
                html.P("Deploy infrastructure to see real AWS costs", style={'color': '#999', 'fontSize': '12px'})
            ])
        
        total_cost = sum(item.get('monthly_cost_eur', 0) for item in data)
        
        return html.Div([
            html.P(f"📊 Total Monthly Cost: €{total_cost:.2f}", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#2E8B57'}),
            html.P(f"📈 Data Source: AWS Cost Explorer API", style={'color': '#666', 'fontSize': '14px'}),
            html.P(f"🔄 Last Updated: Real-time data", style={'color': '#999', 'fontSize': '12px'}),
            html.P(f"💰 Cost includes: EC2, Storage, Data Transfer", style={'color': '#999', 'fontSize': '12px'})
        ])
    
    def create_runtime_analysis_data(self, data: List[Dict]) -> html.Div:
        """Create runtime analysis data summary"""
        if not data:
            return html.Div([
                html.P("No runtime data available", style={'color': '#666'}),
                html.P("Deploy instances to see runtime analysis", style={'color': '#999', 'fontSize': '12px'})
            ])
        
        total_runtime = sum(item.get('runtime_hours_month', 0) for item in data)
        avg_runtime = total_runtime / len(data) if data else 0
        max_runtime_instance = max(data, key=lambda x: x.get('runtime_hours_month', 0))
        
        return html.Div([
            html.P(f"⏱️ Total Runtime: {total_runtime:.0f} hours/month", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#2E8B57'}),
            html.P(f"📊 Average Runtime: {avg_runtime:.0f} hours/month per instance", style={'color': '#666', 'fontSize': '14px'}),
            html.P(f"🥇 Highest Usage: {max_runtime_instance['name']} ({max_runtime_instance.get('runtime_hours_month', 0):.0f}h)", style={'color': '#666', 'fontSize': '14px'}),
            html.P(f"📈 Data Source: AWS API + Launch Time Analysis", style={'color': '#999', 'fontSize': '12px'})
        ])

# Global instance for reuse
infrastructure_tab = InfrastructureTab()