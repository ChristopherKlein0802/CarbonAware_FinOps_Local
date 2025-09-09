"""
Optimization Tab for Carbon-Aware FinOps Dashboard

This module handles the Optimization tab functionality including:
- Scheduling optimization chart
- Optimization recommendations
- Optimization scenarios table
- ROI calculator
- ESG impact summary
- Best strategy recommendation
"""

from dash import html, dash_table
import plotly.graph_objects as go
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.components import DashboardCards, DashboardCharts

class OptimizationTab:
    """Handles all Optimization tab functionality"""
    
    def __init__(self):
        self.cards = DashboardCards()
        self.charts = DashboardCharts()
    
    def create_layout(self) -> html.Div:
        """
        Create the complete Optimization tab layout
        
        Returns:
            html.Div: Complete optimization tab layout
        """
        return html.Div([
            html.H2("💡 Optimization Strategies", 
                   style={'color': '#2E8B57', 'borderBottom': '2px solid #2E8B57', 'paddingBottom': '5px', 'marginBottom': '20px'}),
            
            # Scheduling optimization chart
            html.Div([
                html.H3("📊 Scheduling Optimization Potential", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                html.Div(id='scheduling-optimization-chart')
            ], style={'marginBottom': '30px'}),
            
            # Optimization recommendations and scenarios
            html.Div([
                html.Div([
                    html.H3("🎯 Optimization Recommendations", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                    html.Div(id='optimization-recommendations')
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                
                html.Div([
                    html.H3("📋 Optimization Scenarios", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                    html.Div(id='optimization-scenarios')
                ], style={'width': '48%', 'display': 'inline-block'})
            ], style={'marginBottom': '30px'}),
            
            # ROI and ESG impact
            html.Div([
                html.Div([
                    html.H3("💰 ROI Calculator", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                    html.Div(id='roi-calculator')
                ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '2%'}),
                
                html.Div([
                    html.H3("🌱 ESG Impact Summary", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                    html.Div(id='esg-summary')
                ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '2%'}),
                
                html.Div([
                    html.H3("🏆 Best Strategy", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                    html.Div(id='best-strategy')
                ], style={'width': '32%', 'display': 'inline-block'})
            ])
        ], style={'padding': '20px'})
    
    def create_scheduling_optimization_chart(self, data: List[Dict]):
        """Create scheduling optimization chart"""
        return self.charts.create_optimization_chart(data, height=500)
    
    def create_optimization_recommendations(self, data: List[Dict]) -> html.Div:
        """Create specific optimization recommendations"""
        if not data:
            return html.Div([
                html.H4("🎯 No Recommendations Available", style={'color': '#2E8B57', 'textAlign': 'center', 'margin': '20px 0'}),
                html.P("No AWS instances found to optimize.", 
                      style={'textAlign': 'center', 'color': '#666', 'fontSize': '14px'})
            ], style={'padding': '30px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'})
        
        recommendations = []
        
        for item in data:
            # Calculate best optimization strategy
            office_savings = item['optimization_potential']['office_hours']['cost_savings']
            weekday_savings = item['optimization_potential']['weekdays_only']['cost_savings']
            carbon_savings = item['optimization_potential']['carbon_aware']['cost_savings']
            
            best_strategy = "office_hours" if office_savings >= max(weekday_savings, carbon_savings) else \
                           "weekdays_only" if weekday_savings >= carbon_savings else "carbon_aware"
            
            strategy_names = {
                "office_hours": "Office Hours Only",
                "weekdays_only": "Weekdays Only", 
                "carbon_aware": "Carbon-Aware Scheduling"
            }
            
            best_savings = max(office_savings, weekday_savings, carbon_savings)
            
            if best_savings > 5:  # Only show recommendations with significant savings
                recommendations.append({
                    'instance': item['name'],
                    'current_cost': item['monthly_cost_eur'],
                    'strategy': strategy_names[best_strategy],
                    'savings': best_savings
                })
        
        if not recommendations:
            return html.Div([
                html.H4("✅ All Instances Optimized", style={'color': '#28a745', 'textAlign': 'center'}),
                html.P("Current instances already running efficiently", style={'textAlign': 'center', 'color': '#666'})
            ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'})
        
        recommendation_items = []
        for rec in recommendations[:5]:  # Show top 5 recommendations
            recommendation_items.append(
                html.Div([
                    html.H5(f"🖥️ {rec['instance']}", style={'color': '#2E8B57', 'margin': '10px 0 5px 0'}),
                    html.P(f"💰 Current: €{rec['current_cost']:.1f}/month", style={'margin': '0', 'fontSize': '13px'}),
                    html.P(f"🎯 Strategy: {rec['strategy']}", style={'margin': '0', 'fontSize': '13px', 'color': '#666'}),
                    html.P(f"💡 Save: €{rec['savings']:.1f}/month", style={'margin': '0', 'fontSize': '13px', 'color': '#28a745', 'fontWeight': 'bold'})
                ], style={'padding': '15px', 'backgroundColor': 'white', 'borderRadius': '5px', 'marginBottom': '10px', 'border': '1px solid #ddd'})
            )
        
        return html.Div(recommendation_items)
    
    def create_optimization_scenarios_table(self, data: List[Dict]) -> html.Div:
        """Create optimization scenarios table"""
        if not data:
            return html.Div([
                html.P("No optimization scenarios available", 
                      style={'textAlign': 'center', 'color': '#666', 'fontSize': '14px', 'padding': '40px'}),
                html.P("Deploy infrastructure to see optimization strategies", 
                      style={'textAlign': 'center', 'color': '#999', 'fontSize': '12px'})
            ], style={'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'border': '1px dashed #ccc'})
        
        scenarios_data = []
        for item in data:
            scenarios_data.append({
                'Instance': item['name'],
                'Current (€/month)': f"€{item['monthly_cost_eur']:.1f}",
                'Office Hours': f"€{item['optimization_potential']['office_hours']['cost_savings']:.1f}",
                'Weekdays Only': f"€{item['optimization_potential']['weekdays_only']['cost_savings']:.1f}",
                'Carbon-Aware': f"€{item['optimization_potential']['carbon_aware']['cost_savings']:.1f}",
                'Best Strategy': self._get_best_strategy(item)
            })
        
        return dash_table.DataTable(
            data=scenarios_data,
            columns=[{"name": col, "id": col} for col in scenarios_data[0].keys()],
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontSize': '12px',
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
    
    def create_roi_calculator(self, data: List[Dict]) -> html.Div:
        """Create ROI calculator summary"""
        if not data:
            return html.Div([
                html.P("💰 ROI Calculator", style={'fontWeight': 'bold', 'color': '#2E8B57', 'fontSize': '16px'}),
                html.P("No data for ROI calculation", style={'color': '#666', 'fontSize': '14px'}),
                html.P("Deploy instances to calculate returns", style={'color': '#999', 'fontSize': '12px'})
            ])
        
        total_current_cost = sum(item['monthly_cost_eur'] for item in data)
        total_savings = sum(max(
            item['optimization_potential']['office_hours']['cost_savings'],
            item['optimization_potential']['weekdays_only']['cost_savings'],
            item['optimization_potential']['carbon_aware']['cost_savings']
        ) for item in data)
        
        annual_savings = total_savings * 12
        roi_percentage = (total_savings / total_current_cost * 100) if total_current_cost > 0 else 0
        
        return html.Div([
            html.P("💰 ROI Calculator", style={'fontWeight': 'bold', 'color': '#2E8B57', 'fontSize': '16px'}),
            html.P(f"💡 Monthly Savings: €{total_savings:.0f}", style={'color': '#28a745', 'fontSize': '14px', 'fontWeight': 'bold'}),
            html.P(f"📅 Annual Savings: €{annual_savings:.0f}", style={'color': '#666', 'fontSize': '14px'}),
            html.P(f"📊 Cost Reduction: {roi_percentage:.1f}%", style={'color': '#666', 'fontSize': '14px'}),
            html.P(f"⚡ Payback Period: Immediate", style={'color': '#28a745', 'fontSize': '12px'})
        ])
    
    def create_esg_impact_summary(self, data: List[Dict]) -> html.Div:
        """Create ESG impact summary"""
        if not data:
            return html.Div([
                html.P("🌱 ESG Impact", style={'fontWeight': 'bold', 'color': '#2E8B57', 'fontSize': '16px'}),
                html.P("No ESG data available", style={'color': '#666', 'fontSize': '14px'}),
                html.P("Deploy instances to see impact", style={'color': '#999', 'fontSize': '12px'})
            ])
        
        total_co2 = sum(item['monthly_co2_kg'] for item in data)
        total_co2_savings = sum(max(
            item['optimization_potential']['office_hours']['co2_savings'],
            item['optimization_potential']['weekdays_only']['co2_savings'],
            item['optimization_potential']['carbon_aware']['co2_savings']
        ) for item in data)
        
        co2_reduction_percent = (total_co2_savings / total_co2 * 100) if total_co2 > 0 else 0
        trees_equivalent = total_co2_savings * 12 / 21  # ~21kg CO2 per tree per year
        
        return html.Div([
            html.P("🌱 ESG Impact", style={'fontWeight': 'bold', 'color': '#2E8B57', 'fontSize': '16px'}),
            html.P(f"🌍 CO2 Reduction: {total_co2_savings:.1f} kg/month", style={'color': '#28a745', 'fontSize': '14px', 'fontWeight': 'bold'}),
            html.P(f"📊 Emission Reduction: {co2_reduction_percent:.1f}%", style={'color': '#666', 'fontSize': '14px'}),
            html.P(f"🌳 Trees Equivalent: {trees_equivalent:.0f} trees/year", style={'color': '#666', 'fontSize': '14px'}),
            html.P(f"✅ Supports UN SDG 7 & 13", style={'color': '#28a745', 'fontSize': '12px'})
        ])
    
    def create_best_strategy_recommendation(self, data: List[Dict]) -> html.Div:
        """Create best strategy recommendation"""
        if not data:
            return html.Div([
                html.P("🏆 Best Strategy", style={'fontWeight': 'bold', 'color': '#2E8B57', 'fontSize': '16px'}),
                html.P("No strategy data available", style={'color': '#666', 'fontSize': '14px'}),
                html.P("Deploy instances for recommendations", style={'color': '#999', 'fontSize': '12px'})
            ])
        
        # Calculate which strategy provides best overall results
        office_total = sum(item['optimization_potential']['office_hours']['cost_savings'] for item in data)
        weekday_total = sum(item['optimization_potential']['weekdays_only']['cost_savings'] for item in data)
        carbon_total = sum(item['optimization_potential']['carbon_aware']['cost_savings'] for item in data)
        
        best_strategy = "Office Hours Only" if office_total >= max(weekday_total, carbon_total) else \
                       "Weekdays Only" if weekday_total >= carbon_total else "Carbon-Aware Scheduling"
        
        best_savings = max(office_total, weekday_total, carbon_total)
        
        strategy_descriptions = {
            "Office Hours Only": "Run instances 8am-6pm Mon-Fri (72% reduction)",
            "Weekdays Only": "Run instances Mon-Fri full day (28% reduction)", 
            "Carbon-Aware Scheduling": "Optimize based on grid carbon intensity"
        }
        
        return html.Div([
            html.P("🏆 Best Strategy", style={'fontWeight': 'bold', 'color': '#2E8B57', 'fontSize': '16px'}),
            html.P(best_strategy, style={'color': '#28a745', 'fontSize': '14px', 'fontWeight': 'bold'}),
            html.P(strategy_descriptions[best_strategy], style={'color': '#666', 'fontSize': '13px'}),
            html.P(f"💰 Total Savings: €{best_savings:.0f}/month", style={'color': '#28a745', 'fontSize': '14px'}),
            html.P("🚀 Ready for implementation", style={'color': '#28a745', 'fontSize': '12px'})
        ])
    
    def _get_best_strategy(self, item: Dict) -> str:
        """Get the best strategy for an instance"""
        office_savings = item['optimization_potential']['office_hours']['cost_savings']
        weekday_savings = item['optimization_potential']['weekdays_only']['cost_savings']
        carbon_savings = item['optimization_potential']['carbon_aware']['cost_savings']
        
        if office_savings >= max(weekday_savings, carbon_savings):
            return "Office Hours"
        elif weekday_savings >= carbon_savings:
            return "Weekdays Only"
        else:
            return "Carbon-Aware"

# Global instance for reuse
optimization_tab = OptimizationTab()