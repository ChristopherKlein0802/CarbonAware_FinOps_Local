"""
Academic Value Tab for Carbon-Aware FinOps Dashboard

This module handles the Academic Value tab functionality including:
- Methodology explanation
- Research contribution
- Data sources and APIs
- Statistical methods
"""

from dash import html
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.components import DashboardCards

class AcademicTab:
    """Handles all Academic Value tab functionality"""
    
    def __init__(self):
        self.cards = DashboardCards()
    
    def create_layout(self) -> html.Div:
        """
        Create the complete Academic Value tab layout
        
        Returns:
            html.Div: Complete academic tab layout
        """
        return html.Div([
            html.H2("🎓 Academic Research Value", 
                   style={'color': '#2E8B57', 'borderBottom': '2px solid #2E8B57', 'paddingBottom': '5px', 'marginBottom': '20px'}),
            
            # Methodology section
            html.Div([
                html.H3("📋 Research Methodology", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                html.Div(id='methodology')
            ], style={'marginBottom': '30px'}),
            
            # Research contribution
            html.Div([
                html.H3("🔬 Research Contribution", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                html.Div(id='research-contribution')
            ], style={'marginBottom': '30px'}),
            
            # Data sources and statistical methods
            html.Div([
                html.Div([
                    html.H3("📊 Data Sources & APIs", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                    html.Div(id='data-sources-apis')
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                
                html.Div([
                    html.H3("📈 Statistical Methods", style={'color': '#2E8B57', 'marginBottom': '15px'}),
                    html.Div(id='statistical-methods')
                ], style={'width': '48%', 'display': 'inline-block'})
            ])
        ], style={'padding': '20px'})
    
    def create_methodology_explanation(self) -> html.Div:
        """Create comprehensive methodology explanation"""
        return html.Div([
            html.H4("🎯 Research Objective", style={'color': '#333', 'marginBottom': '10px'}),
            html.P("This bachelor thesis demonstrates the practical implementation of carbon-aware cloud computing principles in enterprise FinOps environments, bridging the gap between environmental sustainability and financial optimization in cloud infrastructure management."),
            
            html.H4("🏗️ System Architecture", style={'color': '#333', 'marginBottom': '10px', 'marginTop': '20px'}),
            html.Ul([
                html.Li("Real-time AWS infrastructure monitoring via AWS APIs"),
                html.Li("Carbon intensity data integration from ElectricityMap API"),
                html.Li("Hardware power consumption analysis using Boavizta API"),
                html.Li("Multi-criteria optimization engine for cost and carbon trade-offs"),
                html.Li("Interactive dashboard for stakeholder decision support")
            ]),
            
            html.H4("⚖️ Optimization Strategies", style={'color': '#333', 'marginBottom': '10px', 'marginTop': '20px'}),
            html.Ul([
                html.Li("📅 Temporal Optimization: Office hours and weekday scheduling"),
                html.Li("🌍 Carbon-Aware Scheduling: Grid carbon intensity-based optimization"),
                html.Li("💰 Cost-Effectiveness Analysis: Multi-objective decision support"),
                html.Li("🔄 Real-time Adaptation: Dynamic optimization based on current conditions")
            ]),
            
            html.H4("📏 Evaluation Metrics", style={'color': '#333', 'marginBottom': '10px', 'marginTop': '20px'}),
            html.Ul([
                html.Li("Cost reduction percentage and absolute savings (€/month)"),
                html.Li("Carbon emission reduction (kg CO2/month)"),
                html.Li("Energy efficiency improvements (kWh optimization)"),
                html.Li("Return on Investment (ROI) and payback periods"),
                html.Li("ESG compliance and UN SDG alignment")
            ])
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '8px'})
    
    def create_research_contribution(self) -> html.Div:
        """Create research contribution explanation"""
        return html.Div([
            html.H4("🔬 Novel Contributions", style={'color': '#333', 'marginBottom': '10px'}),
            
            html.Div([
                html.H5("1. Integrated Carbon-FinOps Framework", style={'color': '#2E8B57', 'margin': '15px 0 5px 0'}),
                html.P("First comprehensive integration of real-time carbon intensity data with AWS Cost Explorer for simultaneous cost and carbon optimization in cloud environments."),
                
                html.H5("2. Multi-API Data Fusion Approach", style={'color': '#2E8B57', 'margin': '15px 0 5px 0'}),
                html.P("Novel methodology combining ElectricityMap (grid data), Boavizta (hardware data), and AWS APIs for comprehensive carbon footprint analysis."),
                
                html.H5("3. Real-World Implementation", style={'color': '#2E8B57', 'margin': '15px 0 5px 0'}),
                html.P("Practical dashboard implementation demonstrating viability of carbon-aware computing in enterprise environments, moving beyond theoretical frameworks."),
                
                html.H5("4. German Grid Analysis", style={'color': '#2E8B57', 'margin': '15px 0 5px 0'}),
                html.P("Specific focus on German electricity grid characteristics and EU-Central-1 AWS region, providing localized carbon optimization strategies."),
                
                html.H5("5. Multi-Stakeholder Dashboard Design", style={'color': '#2E8B57', 'margin': '15px 0 5px 0'}),
                html.P("User-centered design supporting both technical teams and business stakeholders in carbon-aware decision making.")
            ]),
            
            html.H4("🎯 Academic Impact", style={'color': '#333', 'marginBottom': '10px', 'marginTop': '20px'}),
            html.Ul([
                html.Li("📚 Contributes to emerging field of Sustainable Cloud Computing"),
                html.Li("🌍 Supports UN Sustainable Development Goals 7 (Clean Energy) and 13 (Climate Action)"),
                html.Li("💼 Bridges academic research with industry-applicable solutions"),
                html.Li("📊 Provides reproducible methodology for future research"),
                html.Li("🔄 Demonstrates scalability from prototype to production systems")
            ])
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '8px'})
    
    def create_data_sources_apis(self) -> html.Div:
        """Create data sources and APIs explanation"""
        return html.Div([
            html.H4("🔗 Primary Data Sources", style={'color': '#333', 'marginBottom': '15px'}),
            
            html.Div([
                html.H5("📊 AWS APIs", style={'color': '#2E8B57', 'margin': '10px 0 5px 0'}),
                html.Ul([
                    html.Li("EC2 API: Instance metadata and state monitoring"),
                    html.Li("Cost Explorer API: Real-time cost and usage data"),
                    html.Li("CloudWatch API: Performance and utilization metrics")
                ]),
                
                html.H5("🗺️ ElectricityMap API", style={'color': '#2E8B57', 'margin': '15px 0 5px 0'}),
                html.Ul([
                    html.Li("Real-time German grid carbon intensity (g CO2/kWh)"),
                    html.Li("Renewable energy percentage tracking"),
                    html.Li("Historical carbon intensity trends")
                ]),
                
                html.H5("🔧 Boavizta API", style={'color': '#2E8B57', 'margin': '15px 0 5px 0'}),
                html.Ul([
                    html.Li("Scientific hardware power consumption database"),
                    html.Li("AWS instance type power profiling"),
                    html.Li("Manufacturing and operational carbon footprint")
                ])
            ]),
            
            html.H4("📈 Data Processing Pipeline", style={'color': '#333', 'marginBottom': '10px', 'marginTop': '20px'}),
            html.Ol([
                html.Li("Real-time data collection from multiple APIs"),
                html.Li("Data validation and consistency checking"),
                html.Li("Power consumption modeling and carbon calculations"),
                html.Li("Optimization scenario generation and analysis"),
                html.Li("Interactive visualization and stakeholder reporting")
            ])
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'border': '1px solid #ddd'})
    
    def create_statistical_methods(self) -> html.Div:
        """Create statistical methods explanation"""
        return html.Div([
            html.H4("📊 Statistical Analysis Framework", style={'color': '#333', 'marginBottom': '15px'}),
            
            html.Div([
                html.H5("📈 Descriptive Statistics", style={'color': '#2E8B57', 'margin': '10px 0 5px 0'}),
                html.Ul([
                    html.Li("Cost distribution analysis across instance types"),
                    html.Li("Carbon intensity temporal patterns (hourly/daily)"),
                    html.Li("Power consumption variability assessment"),
                    html.Li("Runtime utilization statistical summaries")
                ]),
                
                html.H5("🔬 Optimization Modeling", style={'color': '#2E8B57', 'margin': '15px 0 5px 0'}),
                html.Ul([
                    html.Li("Multi-objective optimization (cost vs. carbon)"),
                    html.Li("Pareto frontier analysis for trade-off visualization"),
                    html.Li("Scenario-based comparison (office hours, weekdays, carbon-aware)"),
                    html.Li("Sensitivity analysis for parameter variations")
                ]),
                
                html.H5("📊 Validation Methods", style={'color': '#2E8B57', 'margin': '15px 0 5px 0'}),
                html.Ul([
                    html.Li("Real-world AWS data validation against Cost Explorer"),
                    html.Li("Carbon intensity correlation with grid data sources"),
                    html.Li("Power consumption validation with hardware specifications"),
                    html.Li("Optimization results cross-validation")
                ])
            ]),
            
            html.H4("🔢 Key Performance Indicators", style={'color': '#333', 'marginBottom': '10px', 'marginTop': '20px'}),
            html.Ul([
                html.Li("💰 Cost Reduction Ratio: (Original - Optimized) / Original × 100%"),
                html.Li("🌍 Carbon Reduction Ratio: (Baseline - Optimized) CO2 / Baseline × 100%"),
                html.Li("⚡ Energy Efficiency: kWh saved per € cost reduction"),
                html.Li("📊 ROI Calculation: Annual savings / Implementation costs"),
                html.Li("🎯 Multi-criteria Score: Weighted cost + carbon optimization score")
            ])
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'border': '1px solid #ddd'})

# Global instance for reuse
academic_tab = AcademicTab()