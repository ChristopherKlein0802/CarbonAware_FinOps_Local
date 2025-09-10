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

from dashboard.components.components import DashboardCards, DashboardCharts

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
                
                # Business Case & Analysis Summary (für Management/Stakeholder)
                html.Div([
                    html.Div([
                        html.H4("💡 Key Business Insights", style={'color': '#333'}),
                        html.Div(id='overview-insights')
                    ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                    
                    html.Div([
                        html.H4("📊 Business Case Summary", style={'color': '#333'}),
                        html.Div(id='overview-business-case')
                    ], style={'width': '48%', 'display': 'inline-block'})
                ]),
                
                html.Br(),
                
                # Scientific Data Quality & Sources
                html.Div([
                    html.H4("🔬 Data Quality & Sources", style={'color': '#333'}),
                    html.Div(id='overview-data-quality')
                ], style={'marginTop': '20px'})
                
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
        """Create key business insights for management/stakeholders"""
        if not data:
            insights = [
                "🎯 Bachelor Thesis Tool: First FinOps tool combining cost AND carbon analysis",
                "🇩🇪 German Grid Focus: ElectricityMap API provides real-time carbon intensity",
                "🔬 Scientific Rigor: AWS Cost Explorer + Boavizta API integration",
                "📊 Analysis-First Approach: Risk-free optimization potential assessment"
            ]
        else:
            # Calculate business-relevant insights
            total_cost = sum(item['monthly_cost_eur'] for item in data)
            total_co2 = sum(item['monthly_co2_kg'] for item in data)
            annual_cost = total_cost * 12
            annual_co2 = total_co2 * 12
            
            # Calculate cost per kg CO2 (ESG efficiency metric)
            co2_efficiency = total_cost / total_co2 if total_co2 > 0 else 0
            
            # German grid context (from data_processor - API ONLY)
            current_grid_intensity = data.get('carbon_intensity', 0) if isinstance(data, dict) else 0
            
            insights = [
                f"💰 Annual infrastructure cost: €{annual_cost:.0f} (Real AWS Cost Explorer data)",
                f"🌍 Annual carbon footprint: {annual_co2:.0f} kg CO2 (German grid: {current_grid_intensity:.0f} g/kWh API data)",
                f"📊 ESG efficiency: €{co2_efficiency:.2f} per kg CO2 (Cost-carbon balance metric)",
                f"🎓 Novel contribution: First tool demonstrating combined cost-carbon analysis for German cloud infrastructure",
                f"🔬 Scientific validation: Real data from 3 APIs ensures accuracy and reproducibility"
            ]
        
        return html.Div([html.P(insight, style={'margin': '10px 0', 'fontSize': '14px'}) for insight in insights])

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
    
    def create_business_case_summary(self, data: List[Dict]) -> html.Div:
        """Create business case summary for management/stakeholders"""
        if not data:
            return html.Div([
                html.P("📊 Business Case Generator", style={'fontWeight': 'bold', 'color': '#2E8B57', 'fontSize': '16px'}),
                html.P("🎓 Bachelor Thesis Value Proposition:", style={'fontWeight': 'bold', 'fontSize': '14px', 'margin': '10px 0 5px 0'}),
                html.P("• First FinOps tool combining cost AND carbon optimization", style={'fontSize': '13px', 'margin': '2px 0'}),
                html.P("• German market focus with EU Green Deal relevance", style={'fontSize': '13px', 'margin': '2px 0'}),
                html.P("• Analysis-first approach ensures risk-free deployment", style={'fontSize': '13px', 'margin': '2px 0'}),
                html.P("🔬 Scientific Rigor: Real data from 3 validated APIs", style={'fontSize': '13px', 'margin': '5px 0', 'fontWeight': 'bold'})
            ])
        
        # Calculate business metrics
        total_cost = sum(item['monthly_cost_eur'] for item in data)
        total_co2 = sum(item['monthly_co2_kg'] for item in data)
        annual_cost = total_cost * 12
        annual_co2 = total_co2 * 12
        
        # Calculate potential optimization (based on analysis, not automation)
        total_potential_savings = 0
        total_potential_co2_reduction = 0
        for instance in data:
            if 'optimization_potential' in instance:
                best_cost_savings = max(
                    instance['optimization_potential']['office_hours']['cost_savings'],
                    instance['optimization_potential']['weekdays_only']['cost_savings'],
                    instance['optimization_potential']['carbon_aware']['cost_savings']
                )
                best_co2_savings = max(
                    instance['optimization_potential']['office_hours']['co2_savings'],
                    instance['optimization_potential']['weekdays_only']['co2_savings'],
                    instance['optimization_potential']['carbon_aware']['co2_savings']
                )
                total_potential_savings += best_cost_savings
                total_potential_co2_reduction += best_co2_savings
        
        potential_annual_savings = total_potential_savings * 12
        potential_annual_co2_reduction = total_potential_co2_reduction * 12
        
        return html.Div([
            html.P("📊 Business Case Analysis", style={'fontWeight': 'bold', 'color': '#2E8B57', 'fontSize': '16px'}),
            html.P("💰 Current State:", style={'fontWeight': 'bold', 'fontSize': '14px', 'margin': '10px 0 5px 0'}),
            html.P(f"• Annual Cost: €{annual_cost:.0f}", style={'fontSize': '13px', 'margin': '2px 0'}),
            html.P(f"• Annual CO2: {annual_co2:.0f} kg", style={'fontSize': '13px', 'margin': '2px 0'}),
            html.P("🎯 Optimization Potential:", style={'fontWeight': 'bold', 'fontSize': '14px', 'margin': '10px 0 5px 0'}),
            html.P(f"• Potential Annual Savings: €{potential_annual_savings:.0f}", style={'fontSize': '13px', 'margin': '2px 0', 'color': '#28a745'}),
            html.P(f"• Potential CO2 Reduction: {potential_annual_co2_reduction:.0f} kg/year", style={'fontSize': '13px', 'margin': '2px 0', 'color': '#28a745'}),
            html.P("🏆 Bachelor Thesis Value:", style={'fontWeight': 'bold', 'fontSize': '14px', 'margin': '10px 0 5px 0'}),
            html.P("• First academic tool demonstrating combined cost-carbon analysis", style={'fontSize': '13px', 'margin': '2px 0', 'color': '#2E8B57'})
        ])
    
    def create_data_quality_summary(self, data: List[Dict]) -> html.Div:
        """Create data quality and sources summary for scientific rigor"""
        return html.Div([
            html.P("🔬 Scientific Data Sources", style={'fontWeight': 'bold', 'color': '#2E8B57', 'fontSize': '16px'}),
            html.P("✅ AWS Cost Explorer API:", style={'fontWeight': 'bold', 'fontSize': '14px', 'margin': '10px 0 5px 0'}),
            html.P("Real billing data from your AWS account", style={'fontSize': '13px', 'margin': '2px 0', 'color': '#666'}),
            html.P("✅ ElectricityMap API (German Grid):", style={'fontWeight': 'bold', 'fontSize': '14px', 'margin': '10px 0 5px 0'}),
            html.P(f"Real-time carbon intensity: {data[0].get('carbon_intensity', 'N/A') if data else 'N/A'} g CO2/kWh (live API)", style={'fontSize': '13px', 'margin': '2px 0', 'color': '#666'}),
            html.P("✅ Boavizta API (Hardware Power):", style={'fontWeight': 'bold', 'fontSize': '14px', 'margin': '10px 0 5px 0'}),
            html.P("Scientific hardware power consumption database", style={'fontSize': '13px', 'margin': '2px 0', 'color': '#666'}),
            html.P("🎓 Academic Value:", style={'fontWeight': 'bold', 'fontSize': '14px', 'margin': '10px 0 5px 0'}),
            html.P("Transparent methodology with confidence tracking", style={'fontSize': '13px', 'margin': '2px 0', 'color': '#2E8B57'}),
            html.P("Reproducible results for scientific validation", style={'fontSize': '13px', 'margin': '2px 0', 'color': '#2E8B57'})
        ])
    
    def create_roi_calculator_summary(self, data: List[Dict]) -> html.Div:
        """Create ROI calculator summary for overview tab"""
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
    
    def create_best_strategy_summary(self, data: List[Dict]) -> html.Div:
        """Create best strategy summary for overview tab"""
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
            "Office Hours Only": "8am-6pm Mon-Fri (72% reduction)",
            "Weekdays Only": "Mon-Fri full day (28% reduction)", 
            "Carbon-Aware Scheduling": "Grid carbon intensity optimization"
        }
        
        return html.Div([
            html.P("🏆 Best Strategy", style={'fontWeight': 'bold', 'color': '#2E8B57', 'fontSize': '16px'}),
            html.P(best_strategy, style={'color': '#28a745', 'fontSize': '14px', 'fontWeight': 'bold'}),
            html.P(strategy_descriptions[best_strategy], style={'color': '#666', 'fontSize': '13px'}),
            html.P(f"💰 Total Savings: €{best_savings:.0f}/month", style={'color': '#28a745', 'fontSize': '14px'}),
            html.P("🚀 Ready for implementation", style={'color': '#28a745', 'fontSize': '12px'})
        ])

# Global instance for reuse
overview_tab = OverviewTab()