"""
Carbon-Aware FinOps Dashboard - Refactored Main Dashboard

This is the main dashboard file using the new modular architecture.
All tab-specific functionality has been moved to separate modules.
"""

import dash
from dash import dcc, html, Input, Output
import logging
from typing import List, Dict

# Import modular components
from utils.data_processing import data_processor
from tabs.overview_tab import overview_tab
from tabs.infrastructure_tab import infrastructure_tab
from tabs.carbon_tab import carbon_tab
from tabs.optimization_tab import optimization_tab
from tabs.academic_tab import academic_tab
from components.cards import DashboardCards

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CarbonAwareFinOpsDashboard:
    """
    Main Carbon-Aware FinOps Dashboard Class
    
    This class now orchestrates the modular dashboard components instead of
    containing all functionality in a single massive file.
    """
    
    def __init__(self):
        """Initialize the dashboard with modular architecture"""
        self.app = dash.Dash(__name__)
        self.data_processor = data_processor
        self.overview_tab = overview_tab
        self.infrastructure_tab = infrastructure_tab
        self.carbon_tab = carbon_tab
        self.optimization_tab = optimization_tab
        self.academic_tab = academic_tab
        self.cards = DashboardCards()
        
        # Setup dashboard
        self.setup_layout()
        self.setup_callbacks()
        
        logger.info("✅ Carbon-Aware FinOps Dashboard initialized with modular architecture")
    
    def setup_layout(self):
        """Setup the main dashboard layout"""
        self.app.layout = html.Div([
            # Update interval for real-time data
            dcc.Interval(
                id='interval-component',
                interval=60*1000,  # Update every minute
                n_intervals=0
            ),
            
            # Header
            html.Div([
                html.H1("🌍 Carbon-Aware FinOps Dashboard", 
                       style={'color': '#2E8B57', 'textAlign': 'center', 'margin': '10px 0'}),
                html.P("Real-time AWS infrastructure cost & carbon optimization analysis", 
                      style={'textAlign': 'center', 'fontSize': '18px', 'color': '#666', 'margin': '10px 0'})
            ], style={'backgroundColor': 'white', 'padding': '20px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            # Main tabs
            dcc.Tabs(
                id="main-tabs",
                value="overview-tab",
                children=[
                    # Overview Tab
                    dcc.Tab(
                        label="📊 Overview", 
                        value="overview-tab",
                        children=[self.overview_tab.create_layout()],
                        style={'padding': '10px', 'fontWeight': 'bold'},
                        selected_style={'padding': '10px', 'fontWeight': 'bold', 'backgroundColor': '#2E8B57', 'color': 'white'}
                    ),
                    
                    # Infrastructure Analysis Tab
                    dcc.Tab(
                        label="🏗️ Infrastructure Analysis", 
                        value="infrastructure-tab",
                        children=[self.infrastructure_tab.create_layout()],
                        style={'padding': '10px', 'fontWeight': 'bold'},
                        selected_style={'padding': '10px', 'fontWeight': 'bold', 'backgroundColor': '#2E8B57', 'color': 'white'}
                    ),
                    
                    # Carbon & Power Data Tab
                    dcc.Tab(
                        label="🌍 Carbon & Power Data", 
                        value="carbon-tab",
                        children=[self.carbon_tab.create_layout()],
                        style={'padding': '10px', 'fontWeight': 'bold'},
                        selected_style={'padding': '10px', 'fontWeight': 'bold', 'backgroundColor': '#2E8B57', 'color': 'white'}
                    ),
                    
                    # Optimization Tab
                    dcc.Tab(
                        label="💡 Optimization", 
                        value="optimization-tab",
                        children=[self.optimization_tab.create_layout()],
                        style={'padding': '10px', 'fontWeight': 'bold'},
                        selected_style={'padding': '10px', 'fontWeight': 'bold', 'backgroundColor': '#2E8B57', 'color': 'white'}
                    ),
                    
                    # Academic Value Tab
                    dcc.Tab(
                        label="🎓 Academic Value", 
                        value="academic-tab",
                        children=[self.academic_tab.create_layout()],
                        style={'padding': '10px', 'fontWeight': 'bold'},
                        selected_style={'padding': '10px', 'fontWeight': 'bold', 'backgroundColor': '#2E8B57', 'color': 'white'}
                    )
                ],
                style={'margin': '20px 0'}
            )
        ])
    
    def setup_callbacks(self):
        """Setup dashboard callbacks using modular approach"""
        
        # Overview Tab Callback
        @self.app.callback(
            [# Overview Tab outputs
             Output('overview-cost-card', 'children'),
             Output('overview-co2-card', 'children'),
             Output('overview-instances-card', 'children'),
             Output('overview-savings-card', 'children'),
             Output('overview-insights', 'children'),
             Output('overview-quick-actions', 'children'),
             Output('overview-costs-chart', 'figure'),
             Output('overview-runtime-chart', 'figure'),
             Output('overview-co2-chart', 'figure'),
             Output('overview-efficiency-chart', 'figure')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_overview_tab(_):
            """Update Overview tab using modular approach"""
            try:
                # Get data using centralized data processor
                data = self.data_processor.get_infrastructure_data()
                
                # Generate all components using modular tabs
                cost_card = self.overview_tab.create_cost_card(data)
                co2_card = self.overview_tab.create_co2_card(data)
                instances_card = self.overview_tab.create_instances_card(data)
                savings_card = self.overview_tab.create_savings_card(data)
                insights = self.overview_tab.create_insights(data)
                quick_actions = self.overview_tab.create_quick_actions(data)
                
                # Generate 4 separate charts using modular approach
                costs_chart = self.overview_tab.create_costs_chart(data)
                runtime_chart = self.overview_tab.create_runtime_chart(data)
                co2_chart = self.overview_tab.create_co2_chart(data)
                efficiency_chart = self.overview_tab.create_efficiency_chart(data)
                
                return (
                    cost_card, co2_card, instances_card, savings_card,
                    insights, quick_actions,
                    costs_chart, runtime_chart, co2_chart, efficiency_chart
                )
                
            except Exception as e:
                logger.error(f"❌ Overview tab update failed: {e}")
                # Return empty states for all components
                empty_card = self.cards.create_empty_state_card("Error", "Failed to load data", "❌")
                empty_chart = self.overview_tab.charts.create_empty_chart("Error loading data")
                empty_content = html.Div("Error loading insights")
                
                return (
                    empty_card, empty_card, empty_card, empty_card,
                    empty_content, empty_content,
                    empty_chart, empty_chart, empty_chart, empty_chart
                )
        
        # Infrastructure Tab Callback
        @self.app.callback(
            [Output('cost-overview-card', 'children'),
             Output('co2-overview-card', 'children'),
             Output('instances-overview-card', 'children'),
             Output('carbon-intensity-card', 'children'),
             Output('instance-analysis-table', 'children'),
             Output('aws-cost-explorer-data', 'children'),
             Output('runtime-analysis-data', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_infrastructure_tab(_):
            """Update Infrastructure tab using modular approach"""
            try:
                data = self.data_processor.get_infrastructure_data()
                
                return (
                    self.infrastructure_tab.create_cost_card(data),
                    self.infrastructure_tab.create_co2_card(data),
                    self.infrastructure_tab.create_instances_card(data),
                    self.infrastructure_tab.create_carbon_intensity_card(data),
                    self.infrastructure_tab.create_instance_analysis_table(data),
                    self.infrastructure_tab.create_aws_cost_explorer_data(data),
                    self.infrastructure_tab.create_runtime_analysis_data(data)
                )
            except Exception as e:
                logger.error(f"❌ Infrastructure tab update failed: {e}")
                empty_card = self.cards.create_empty_state_card("Error", "Failed to load data", "❌")
                empty_content = html.Div("Error loading data")
                return (empty_card, empty_card, empty_card, empty_card, empty_content, empty_content, empty_content)
        
        # Carbon Tab Callback
        @self.app.callback(
            [Output('carbon-intensity-trends-chart', 'children'),
             Output('power-consumption-chart', 'children'),
             Output('carbon-footprint-table', 'children'),
             Output('electricitymap-api-data', 'children'),
             Output('boavizta-api-data', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_carbon_tab(_):
            """Update Carbon tab using modular approach"""
            try:
                data = self.data_processor.get_infrastructure_data()
                
                return (
                    self.carbon_tab.create_carbon_intensity_trends_chart(),
                    self.carbon_tab.create_power_consumption_chart(data),
                    self.carbon_tab.create_carbon_footprint_table(data),
                    self.carbon_tab.create_electricitymap_api_data(),
                    self.carbon_tab.create_boavizta_api_data(data)
                )
            except Exception as e:
                logger.error(f"❌ Carbon tab update failed: {e}")
                empty_content = html.Div("Error loading data")
                return (empty_content, empty_content, empty_content, empty_content, empty_content)
        
        # Optimization Tab Callback
        @self.app.callback(
            [Output('scheduling-optimization-chart', 'figure'),
             Output('optimization-recommendations', 'children'),
             Output('optimization-scenarios', 'children'),
             Output('roi-calculator', 'children'),
             Output('esg-summary', 'children'),
             Output('best-strategy', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_optimization_tab(_):
            """Update Optimization tab using modular approach"""
            try:
                data = self.data_processor.get_infrastructure_data()
                
                return (
                    self.optimization_tab.create_scheduling_optimization_chart(data),
                    self.optimization_tab.create_optimization_recommendations(data),
                    self.optimization_tab.create_optimization_scenarios_table(data),
                    self.optimization_tab.create_roi_calculator(data),
                    self.optimization_tab.create_esg_impact_summary(data),
                    self.optimization_tab.create_best_strategy_recommendation(data)
                )
            except Exception as e:
                logger.error(f"❌ Optimization tab update failed: {e}")
                empty_chart = self.overview_tab.charts.create_empty_chart("Error loading data")
                empty_content = html.Div("Error loading data")
                return (empty_chart, empty_content, empty_content, empty_content, empty_content, empty_content)
        
        # Academic Tab Callback
        @self.app.callback(
            [Output('methodology', 'children'),
             Output('research-contribution', 'children'),
             Output('data-sources-apis', 'children'),
             Output('statistical-methods', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_academic_tab(_):
            """Update Academic tab using modular approach"""
            try:
                return (
                    self.academic_tab.create_methodology_explanation(),
                    self.academic_tab.create_research_contribution(),
                    self.academic_tab.create_data_sources_apis(),
                    self.academic_tab.create_statistical_methods()
                )
            except Exception as e:
                logger.error(f"❌ Academic tab update failed: {e}")
                empty_content = html.Div("Error loading content")
                return (empty_content, empty_content, empty_content, empty_content)
    
    def run_server(self, debug=True, host='127.0.0.1', port=8051):
        """Run the refactored dashboard server"""
        print(f"\n🔍 Carbon-Aware FinOps Dashboard (Refactored Architecture)")
        print(f"📊 Dashboard URL: http://{host}:{port}")
        print(f"🏗️  Architecture: Modular components with separate tab files")
        print(f"🎯 Focus: Cost & CO2 analysis + optimization potential calculations")
        print(f"🇩🇪 Region: German AWS regions with real grid data")
        print(f"🎓 Purpose: Bachelor thesis tool for FinOps + Carbon optimization")
        print(f"\nPress Ctrl+C to stop the dashboard\n")
        
        self.app.run(debug=debug, host=host, port=port)

def main():
    """Main function to run the refactored dashboard"""
    dashboard = CarbonAwareFinOpsDashboard()
    dashboard.run_server(debug=True, port=8051)

if __name__ == "__main__":
    main()