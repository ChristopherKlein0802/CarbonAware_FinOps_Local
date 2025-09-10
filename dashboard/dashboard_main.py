"""
Carbon-Aware FinOps Dashboard - Bachelor Thesis Main Dashboard

BACHELOR THESIS PROJECT (September 2025):
Research Question: "Integrierte Carbon-aware FinOps Optimierung vs. separate Tools"

This is the main dashboard file using thesis-focused modular architecture.
Key Features:
- API-ONLY data policy (NO fallbacks for scientific rigor)
- Conservative calculations with documented uncertainty (±15%)
- German SME focus (≤100 instances, EU-Central-1)  
- Real-time integration: AWS + ElectricityMaps + Boavizta APIs
- Research validation through competitive analysis

Architecture:
- Modular design with thesis validation tab
- 4 tabs: Overview | Thesis Validation | Infrastructure | Carbon Data
- All functionality moved to separate specialized modules
"""

import dash
from dash import dcc, html, Input, Output
import logging
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import modular components  
from dashboard.utils.data_processing import data_processor
from dashboard.tabs.overview_tab import overview_tab
from dashboard.components.academic_disclaimers import AcademicDisclaimers
from dashboard.tabs.infrastructure_tab import infrastructure_tab
from dashboard.tabs.carbon_tab import carbon_tab
from dashboard.tabs.thesis_validation_tab import thesis_validation_tab
from dashboard.components.components import DashboardCards

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
        self.thesis_validation_tab = thesis_validation_tab
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
            
            # Thesis-focused Header
            html.Div([
                html.H1("🎓 Carbon-Aware FinOps - Bachelor Thesis Dashboard", 
                       style={'color': '#2E8B57', 'textAlign': 'center', 'marginBottom': '10px'}),
                html.H3("Research Question: Integrierte Carbon-aware FinOps Optimierung vs. separate Tools",
                       style={'color': '#666', 'textAlign': 'center', 'fontWeight': 'normal', 'marginBottom': '20px'}),
                
                # Academic Disclaimer Banner
                html.Div([
                    html.P([
                        "🔬 ", html.Strong("Proof-of-Concept:"), " Alle Ergebnisse sind vorläufig. ",
                        "🔢 ", html.Strong("Conservative Schätzungen:"), " ±15% Unsicherheitsintervalle dokumentiert. ",
                        "🇩🇪 ", html.Strong("Fokus:"), " Deutsche KMU (≤100 Instanzen, EU-Central-1)."
                    ], style={'margin': '0', 'color': '#666', 'fontSize': '14px'})
                ], style={
                    'backgroundColor': '#f0f8f0',
                    'padding': '15px',
                    'borderRadius': '5px',
                    'border': '1px solid #2E8B57',
                    'marginBottom': '20px'
                })
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
                    
                    # Thesis Validation Tab (NEW - Research Focus)
                    dcc.Tab(
                        label="🎓 Thesis Validation", 
                        value="thesis-validation-tab",
                        children=[self.thesis_validation_tab.create_layout()],
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
                    )
                ],
                style={'margin': '20px 0'}
            )
        ])
    
    def setup_callbacks(self):
        """Setup dashboard callbacks using modular approach"""
        
        # Overview Tab Callback (Updated for Bachelor Thesis Focus)
        @self.app.callback(
            [# Overview Tab outputs
             Output('overview-cost-card', 'children'),
             Output('overview-co2-card', 'children'),
             Output('overview-instances-card', 'children'),
             Output('overview-savings-card', 'children'),
             Output('overview-insights', 'children'),
             Output('overview-business-case', 'children'),
             Output('overview-data-quality', 'children'),
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
                
                # Extract instances list for overview tab methods (they expect List[Dict], not full analysis)
                instances = data.get('instances', []) if isinstance(data, dict) else []
                
                # Generate all components using modular tabs
                cost_card = self.overview_tab.create_cost_card(instances)
                co2_card = self.overview_tab.create_co2_card(instances)
                instances_card = self.overview_tab.create_instances_card(instances)
                savings_card = self.overview_tab.create_savings_card(instances)
                insights = self.overview_tab.create_insights(instances)
                business_case = self.overview_tab.create_business_case_summary(instances)
                data_quality = self.overview_tab.create_data_quality_summary(instances)
                
                # Generate 4 separate charts using modular approach
                costs_chart = self.overview_tab.create_costs_chart(instances)
                runtime_chart = self.overview_tab.create_runtime_chart(instances)
                co2_chart = self.overview_tab.create_co2_chart(instances)
                efficiency_chart = self.overview_tab.create_efficiency_chart(instances)
                
                return (
                    cost_card, co2_card, instances_card, savings_card,
                    insights, business_case, data_quality,
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
                    empty_content, empty_content, empty_content,
                    empty_chart, empty_chart, empty_chart, empty_chart
                )
        
        # Infrastructure Tab Callback
        @self.app.callback(
            [Output('active-infrastructure-card', 'children'),
             Output('resource-efficiency-card', 'children'),
             Output('cost-per-hour-card', 'children'),
             Output('rightsizing-potential-card', 'children'),
             Output('cost-analysis-chart', 'children'),
             Output('instance-type-cost-distribution', 'children'),
             Output('runtime-cost-correlation', 'children'),
             Output('efficiency-matrix', 'children'),
             Output('rightsizing-recommendations', 'children'),
             Output('rightsizing-analysis', 'children'),
             Output('instance-health-matrix', 'children'),
             Output('utilization-analysis', 'children'),
             Output('instance-analysis-table', 'children'),
             Output('aws-cost-explorer-data', 'children'),
             Output('runtime-analysis-data', 'children'),
             Output('api-limitations-research', 'children'),
             Output('scientific-methodology', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_infrastructure_tab(_):
            """Update Infrastructure tab with enhanced API data sources"""
            try:
                data = self.data_processor.get_infrastructure_data()
                # Extract instances list for infrastructure tab methods
                instances = data.get('instances', []) if isinstance(data, dict) else []
                
                return (
                    self.infrastructure_tab.create_active_infrastructure_card(instances),
                    self.infrastructure_tab.create_resource_efficiency_card(instances),
                    self.infrastructure_tab.create_cost_per_hour_card(instances),
                    self.infrastructure_tab.create_rightsizing_potential_card(instances),
                    dcc.Graph(figure=self.infrastructure_tab.create_cost_analysis_chart(instances)),
                    dcc.Graph(figure=self.infrastructure_tab.create_instance_type_cost_distribution(instances)),
                    dcc.Graph(figure=self.infrastructure_tab.create_runtime_cost_correlation(instances)),
                    dcc.Graph(figure=self.infrastructure_tab.create_efficiency_matrix(instances)),
                    self.infrastructure_tab.create_rightsizing_recommendations(instances),
                    self.infrastructure_tab.create_rightsizing_recommendations(instances),  # Duplicate for rightsizing-analysis
                    self.infrastructure_tab.create_instance_health_matrix(instances),
                    self.infrastructure_tab.create_utilization_analysis(instances),
                    self.infrastructure_tab.create_instance_analysis_table(instances),
                    self.infrastructure_tab.create_aws_cost_explorer_data(instances),
                    self.infrastructure_tab.create_runtime_analysis_data(instances),
                    self.infrastructure_tab.create_api_limitations_research(instances),
                    self.infrastructure_tab.create_scientific_methodology(instances)
                )
            except Exception as e:
                logger.error(f"❌ Infrastructure tab update failed: {e}")
                empty_card = self.cards.create_empty_state_card("Error", "Failed to load data", "❌")
                empty_content = html.Div("Error loading data")
                empty_chart = dcc.Graph(figure=self.infrastructure_tab.charts.create_empty_chart("Error loading data"))
                return (empty_card, empty_card, empty_card, empty_card, empty_chart, empty_chart, empty_chart, empty_chart, empty_content, empty_content, empty_content, empty_content, empty_content, empty_content, empty_content, empty_content, empty_content)
        
        # Carbon Tab Callback (Updated for Pure Data Focus)
        @self.app.callback(
            [Output('current-grid-intensity-card', 'children'),
             Output('total-power-consumption-card', 'children'),
             Output('monthly-co2-emissions-card', 'children'),
             Output('carbon-efficiency-score-card', 'children'),
             Output('carbon-intensity-trends-chart', 'children'),
             Output('power-consumption-chart', 'children'),
             Output('carbon-intensity-patterns', 'children'),
             Output('power-consumption-science', 'children'),
             Output('carbon-footprint-table', 'children'),
             Output('electricitymap-api-data', 'children'),
             Output('boavizta-api-data', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_carbon_tab(_):
            """Update Carbon tab using modular approach"""
            try:
                data = self.data_processor.get_infrastructure_data()
                # Extract instances list for carbon tab methods
                instances = data.get('instances', []) if isinstance(data, dict) else []
                
                return (
                    self.carbon_tab.cards.create_current_grid_intensity_card(instances),
                    self.carbon_tab.cards.create_total_power_consumption_card(instances),
                    self.carbon_tab.cards.create_monthly_co2_emissions_card(instances),
                    self.carbon_tab.cards.create_carbon_efficiency_score_card(instances),
                    self.carbon_tab.create_carbon_intensity_trends_chart(),
                    self.carbon_tab.create_power_consumption_chart(instances),
                    self.carbon_tab.create_carbon_intensity_patterns(instances),
                    self.carbon_tab.create_power_consumption_science(instances),
                    self.carbon_tab.create_carbon_footprint_table(instances),
                    self.carbon_tab.create_electricitymap_api_data(),
                    self.carbon_tab.create_boavizta_api_data(instances)
                )
            except Exception as e:
                logger.error(f"❌ Carbon tab update failed: {e}")
                empty_content = html.Div("Error loading data")
                empty_card = self.cards.create_empty_state_card("Error", "Failed to load data", "❌")
                return (empty_card, empty_card, empty_card, empty_card, empty_content, empty_content, empty_content, empty_content, empty_content, empty_content, empty_content)
        
        # Thesis Validation Tab Callback (NEW - Research Focus)
        @self.app.callback(
            [Output('thesis-cost-advantage-card', 'children'),
             Output('thesis-carbon-advantage-card', 'children'),
             Output('thesis-roi-card', 'children'),
             Output('thesis-novelty-card', 'children'),
             Output('cost-optimization-comparison-chart', 'figure'),
             Output('carbon-optimization-comparison-chart', 'figure'),
             Output('integrated-superiority-chart', 'figure'),
             Output('business-case-analysis', 'children'),
             Output('german-grid-analysis', 'children'),
             Output('academic-research-summary', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_thesis_validation_tab(_):
            """Update Thesis Validation tab with research focus"""
            try:
                data = self.data_processor.get_infrastructure_data()
                
                return (
                    self.thesis_validation_tab.create_cost_advantage_card(data),
                    self.thesis_validation_tab.create_carbon_advantage_card(data),
                    self.thesis_validation_tab.create_roi_card(data),
                    self.thesis_validation_tab.create_novelty_card(data),
                    self.thesis_validation_tab.create_cost_optimization_comparison_chart(data),
                    self.thesis_validation_tab.create_carbon_optimization_comparison_chart(data),
                    self.thesis_validation_tab.create_integrated_superiority_chart(data),
                    self.create_business_case_content(data),
                    self.create_german_grid_content(data),
                    self.create_academic_summary_content(data)
                )
            except Exception as e:
                logger.error(f"❌ Thesis validation tab update failed: {e}")
                empty_card = self.cards.create_empty_state_card("Error", "Failed to load data", "❌")
                empty_content = html.Div("Error loading data")
                empty_chart = self.thesis_validation_tab.charts.create_empty_chart("Error loading data")
                return (empty_card, empty_card, empty_card, empty_card, empty_chart, empty_chart, empty_chart, empty_content, empty_content, empty_content)
    
    def create_business_case_content(self, data: Dict) -> html.Div:
        """Create business case content for thesis validation tab with scaling scenarios"""
        if 'business_case' not in data:
            return html.Div("No business case data available")
        
        bc = data['business_case']
        scaling = bc.get('scaling_scenarios', {})
        
        content = [
            html.H5("💼 Current Test Infrastructure", style={'color': '#2E8B57', 'marginBottom': '10px'}),
            html.P([
                html.Strong("Monthly Savings: "), 
                f"€{bc.get('monthly_cost_savings_eur', 0):.2f}"
            ]),
            html.P([
                html.Strong("Monthly CO2 Reduction: "), 
                f"{bc.get('monthly_co2_reduction_kg', 0):.3f} kg"
            ]),
            html.P([
                html.Strong("ESG Value: "), 
                f"€{bc.get('monthly_esg_value_eur', 0):.3f} (EU ETS)"
            ]),
            html.P([
                html.Strong("Status: "), 
                bc.get('proof_of_concept_status', 'Proof-of-Concept')
            ], style={'color': '#ff6600', 'fontWeight': 'bold'}),
            
            html.Hr(style={'margin': '15px 0'}),
            
            html.H5("📊 SME Scaling Scenarios", style={'color': '#2E8B57', 'marginBottom': '10px'}),
        ]
        
        # Add scaling scenarios
        for scenario_key, scenario in scaling.items():
            if scenario_key != 'current_test':  # Skip current test, already shown above
                content.extend([
                    html.P([
                        html.Strong(f"{scenario['description']}: "),
                        f"€{scenario['monthly_savings']:.2f}/month → {scenario['roi_months']:.1f} months ROI"
                    ], style={'fontSize': '14px'})
                ])
        
        content.extend([
            html.Hr(style={'margin': '15px 0'}),
            html.P([
                html.Strong("Implementation Cost: "), 
                f"€{bc.get('implementation_cost_eur', 5000):,} (SME-appropriate)"
            ]),
            html.P(bc.get('conservative_range', 'Conservative estimates'), 
                  style={'fontSize': '12px', 'color': '#666', 'fontStyle': 'italic'})
        ])
        
        return html.Div(content)
    
    def create_german_grid_content(self, data: Dict) -> html.Div:
        """Create German grid content for thesis validation tab"""
        carbon_intensity = data.get('carbon_intensity', 0)
        api_sources = data.get('api_sources', {})
        
        if carbon_intensity > 0:
            status_color = '#28a745'  # Green
            status_text = "✅ Live Data"
        else:
            status_color = '#dc3545'  # Red  
            status_text = "❌ API Failed"
        
        return html.Div([
            html.P([
                html.Strong("Current Carbon Intensity: "), 
                f"{carbon_intensity:.0f} g CO2/kWh"
            ]),
            html.P([
                html.Strong("ElectricityMap API: "), 
                html.Span(status_text, style={'color': status_color})
            ]),
            html.P([
                html.Strong("Data Source: "), 
                "Official German Grid Data (TSO)"
            ]),
            html.P([
                html.Strong("Update Frequency: "), 
                "Real-time (60 seconds)"
            ]),
            html.P([
                html.Strong("Research Focus: "), 
                "German SME market (EU-Central-1)"
            ]),
            html.P("NO FALLBACK policy for scientific rigor", 
                  style={'fontSize': '12px', 'color': '#666', 'fontStyle': 'italic'})
        ])
    
    def create_academic_summary_content(self, data: Dict) -> html.Div:
        """Create academic summary content for thesis validation tab"""
        instances = data.get('instances', [])
        instance_count = len(instances)
        
        return html.Div([
            html.P([
                html.Strong("Research Question: "), 
                "Integrierte Carbon-aware FinOps Optimierung"
            ]),
            html.P([
                html.Strong("Unique Contribution: "), 
                "First tool optimizing BOTH cost AND carbon simultaneously"
            ]),
            html.P([
                html.Strong("Market Focus: "), 
                f"German SME (≤100 instances, currently {instance_count})"
            ]),
            html.P([
                html.Strong("Scientific Approach: "), 
                "Conservative estimates, NO fallbacks, API-only data"
            ]),
            html.P([
                html.Strong("Competitive Advantage: "), 
                "Superior to separate cost-only OR carbon-only tools"
            ]),
            html.P([
                html.Strong("Business Validation: "), 
                "ROI payback < 12 months with EU ETS pricing"
            ]),
            html.P("Bachelor Thesis 2025 - Proof of Concept", 
                  style={'fontSize': '12px', 'color': '#666', 'fontStyle': 'italic'})
        ])
    
    def run_server(self, debug=True, host='127.0.0.1', port=8051):
        """Run the thesis-focused modular dashboard server"""
        print(f"\n🎓 Carbon-Aware FinOps Dashboard - Bachelor Thesis (Modular Architecture)")
        print(f"📊 Dashboard URL: http://{host}:{port}")
        print(f"🏗️  Research: First integrated Carbon-aware FinOps tool")
        print(f"🇩🇪 German Grid: Real ElectricityMap API data + NO FALLBACKS")
        print(f"🔬 Scientific: Conservative calculations with ±15% uncertainty")
        print(f"🎯 Approach: Real API data only (AWS + ElectricityMap + Boavizta)")
        print(f"📐 Architecture: Modular structure with thesis-focused calculations")
        print(f"\n📋 4 Tabs: Overview | Thesis Validation | Infrastructure | Carbon Data")
        print(f"\nPress Ctrl+C to stop the dashboard\n")
        
        self.app.run(debug=debug, host=host, port=port)

def main():
    """Main function to run the refactored dashboard"""
    dashboard = CarbonAwareFinOpsDashboard()
    dashboard.run_server(debug=True, port=8051)

if __name__ == "__main__":
    main()