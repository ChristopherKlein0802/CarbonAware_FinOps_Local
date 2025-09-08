"""
Dashboard Layout Components for Carbon-Aware FinOps

Separated layouts for better maintainability:
1. Main Analysis Tab - Current optimization analysis
2. Historical Data Tab - DynamoDB stored data trends
3. Data Sources Tab - API status and configuration
"""

from dash import dcc, html

def create_main_layout():
    """Create the main dashboard layout with tabs."""
    return html.Div([
        # Header
        html.Div([
            html.H1("🔍 Infrastructure Analysis & Optimization Potential", 
                   style={'textAlign': 'center', 'color': '#2E8B57', 'marginBottom': '10px'}),
            html.H3("Analyze AWS Costs & CO2 → Calculate Optimization Savings Potential", 
                   style={'textAlign': 'center', 'color': '#666', 'marginBottom': '20px'}),
            html.P("Focus: German AWS Regions (eu-central-1) | Real AWS Cost Data + German Grid CO2 Data",
                  style={'textAlign': 'center', 'color': '#888', 'fontSize': '14px'}),
            
            # Status indicator
            html.Div([
                html.Span("🔄 Last updated: ", style={'color': '#666'}),
                html.Span(id='last-update-time', children="Loading...", 
                         style={'color': '#2E8B57', 'fontWeight': 'bold'})
            ], style={'textAlign': 'center', 'marginTop': '10px', 'fontSize': '12px'})
        ], style={'marginBottom': '20px'}),
        
        # Auto-refresh component
        dcc.Interval(
            id='interval-component',
            interval=60*1000,  # 60 seconds
            n_intervals=0
        ),
        
        # Navigation Tabs
        dcc.Tabs(
            id='main-tabs',
            value='analysis-tab',
            children=[
                dcc.Tab(
                    label='📊 Current Analysis',
                    value='analysis-tab',
                    style={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                    selected_style={'fontWeight': 'bold', 'backgroundColor': '#2E8B57', 'color': 'white'}
                ),
                dcc.Tab(
                    label='📈 Historical Data',
                    value='historical-tab',
                    style={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                    selected_style={'fontWeight': 'bold', 'backgroundColor': '#2E8B57', 'color': 'white'}
                ),
                dcc.Tab(
                    label='⚙️ Data Sources',
                    value='sources-tab',
                    style={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                    selected_style={'fontWeight': 'bold', 'backgroundColor': '#2E8B57', 'color': 'white'}
                )
            ],
            style={'marginBottom': '20px'}
        ),
        
        # Tab Content
        html.Div(id='tab-content')
        
    ], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#fafafa'})

def create_analysis_tab():
    """Create the main analysis tab content."""
    return html.Div([
        # Section 1: Current Infrastructure Overview
        html.Div([
            html.H2("📊 Current Infrastructure Analysis", 
                   style={'color': '#2E8B57', 'borderBottom': '2px solid #2E8B57', 'paddingBottom': '5px'}),
            
            # Key metrics cards
            html.Div([
                html.Div(id='cost-overview-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                html.Div(id='co2-overview-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                html.Div(id='instances-overview-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'}),
                html.Div(id='carbon-intensity-card', style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'})
            ]),
            
            html.Br(),
            
            # Instance breakdown
            html.Div([
                html.H4("🖥️ Instance-Level Analysis", style={'color': '#333'}),
                html.Div(id='instance-analysis-table')
            ])
            
        ], style={'marginBottom': '40px'}),
        
        # Section 2: Power Consumption Analysis
        html.Div([
            html.H2("⚡ Power Consumption & Carbon Footprint Analysis", 
                   style={'color': '#2E8B57', 'borderBottom': '2px solid #2E8B57', 'paddingBottom': '5px'}),
            
            html.Div([
                html.Div([
                    html.H4("🔋 Hardware Power Consumption", style={'color': '#333'}),
                    html.Div(id='power-consumption-chart')
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                
                html.Div([
                    html.H4("📊 Power Data Sources & Confidence", style={'color': '#333'}),
                    html.Div(id='power-data-sources-chart')
                ], style={'width': '48%', 'display': 'inline-block'}),
            ]),
            
            html.Br(),
            
            html.Div([
                html.H4("🌍 Carbon Footprint Breakdown", style={'color': '#333'}),
                html.Div(id='carbon-footprint-table')
            ])
            
        ], style={'marginBottom': '40px'}),
        
        # Section 3: Academic Analysis & Statistical Rigor
        html.Div([
            html.H2("📊 Academic Analysis & Statistical Validation", 
                   style={'color': '#2E8B57', 'borderBottom': '2px solid #2E8B57', 'paddingBottom': '5px'}),
            
            html.Div([
                html.Div([
                    html.H4("📈 German Grid Carbon Intensity Trends", style={'color': '#333'}),
                    html.Div(id='carbon-intensity-trends-chart')
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                
                html.Div([
                    html.H4("🎯 Optimization Statistical Significance", style={'color': '#333'}),
                    html.Div(id='statistical-significance-chart')
                ], style={'width': '48%', 'display': 'inline-block'}),
            ]),
            
            html.Br(),
            
            html.Div([
                html.H4("🌍 European Regional Context & Methodology", style={'color': '#333'}),
                html.Div([
                    html.Div([
                        html.Div(id='regional-comparison-chart')
                    ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                    
                    html.Div([
                        html.Div(id='seasonal-analysis-chart')
                    ], style={'width': '48%', 'display': 'inline-block'}),
                ])
            ])
            
        ], style={'marginBottom': '40px'}),
        
        # Section 4: Optimization Potential Analysis
        html.Div([
            html.H2("💡 Optimization Potential Calculator", 
                   style={'color': '#2E8B57', 'borderBottom': '2px solid #2E8B57', 'paddingBottom': '5px'}),
            
            html.Div([
                # Scheduling optimization potential
                html.Div([
                    html.H4("⏰ Scheduling Optimization Potential", style={'color': '#333'}),
                    dcc.Graph(id='scheduling-optimization-chart')
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                
                # Cost vs CO2 optimization comparison
                html.Div([
                    html.H4("⚖️ Cost vs CO2 Optimization Impact", style={'color': '#333'}),
                    dcc.Graph(id='cost-co2-comparison-chart')
                ], style={'width': '48%', 'display': 'inline-block'}),
            ]),
            
            html.Br(),
            
            # Detailed optimization recommendations
            html.Div([
                html.H4("🎯 Specific Optimization Recommendations", style={'color': '#333'}),
                html.Div(id='optimization-recommendations')
            ])
            
        ], style={'marginBottom': '40px'}),
        
        # Section 5: Business Case Generator
        html.Div([
            html.H2("🏢 Business Case for Management", 
                   style={'color': '#2E8B57', 'borderBottom': '2px solid #2E8B57', 'paddingBottom': '5px'}),
            
            html.Div([
                # ROI Calculator
                html.Div([
                    html.H4("📈 Return on Investment (ROI)", style={'color': '#333'}),
                    html.Div(id='roi-calculator')
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                
                # ESG Impact
                html.Div([
                    html.H4("🌍 ESG Impact Summary", style={'color': '#333'}),
                    html.Div(id='esg-impact-summary')
                ], style={'width': '48%', 'display': 'inline-block'}),
            ])
            
        ], style={'marginBottom': '40px'}),
        
        # Section 6: Methodology & Data Sources
        html.Div([
            html.H2("🔬 Calculation Methodology", 
                   style={'color': '#2E8B57', 'borderBottom': '2px solid #2E8B57', 'paddingBottom': '5px'}),
            html.Div(id='methodology-explanation')
            
        ], style={'marginBottom': '40px'})
    ])

def create_historical_tab():
    """Create the historical data tab content."""
    return html.Div([
        html.H2("📈 Historical Data Analysis", 
               style={'color': '#2E8B57', 'borderBottom': '2px solid #2E8B57', 'paddingBottom': '5px'}),
        
        # DynamoDB Status
        html.Div(id='dynamodb-status', style={'marginBottom': '20px'}),
        
        # Historical Data Controls
        html.Div([
            html.H4("🕒 Time Range Selection", style={'color': '#333'}),
            html.Div([
                html.Label("Select Data Range:", style={'marginRight': '10px'}),
                dcc.Dropdown(
                    id='historical-range-dropdown',
                    options=[
                        {'label': 'Last Hour', 'value': 1},
                        {'label': 'Last 6 Hours', 'value': 6},
                        {'label': 'Last 24 Hours', 'value': 24},
                        {'label': 'Last 3 Days', 'value': 72},
                        {'label': 'Last Week', 'value': 168}
                    ],
                    value=24,
                    style={'width': '200px', 'display': 'inline-block'}
                ),
                html.Button(
                    '🔄 Refresh Historical Data',
                    id='refresh-historical-btn',
                    style={'marginLeft': '20px', 'padding': '8px 16px', 'backgroundColor': '#2E8B57', 'color': 'white', 'border': 'none', 'borderRadius': '4px'}
                )
            ], style={'marginBottom': '20px'})
        ]),
        
        # Historical Charts
        html.Div([
            html.Div([
                html.H4("📊 Carbon Intensity History", style={'color': '#333'}),
                dcc.Graph(id='historical-carbon-chart')
            ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
            
            html.Div([
                html.H4("⚡ Power Data History", style={'color': '#333'}),
                dcc.Graph(id='historical-power-chart')
            ], style={'width': '48%', 'display': 'inline-block'}),
        ]),
        
        html.Br(),
        
        # Historical Data Table
        html.Div([
            html.H4("📋 Stored Data Summary", style={'color': '#333'}),
            html.Div(id='historical-data-table')
        ])
    ])

def create_sources_tab():
    """Create the data sources tab content."""
    return html.Div([
        html.H2("⚙️ Data Sources & Configuration", 
               style={'color': '#2E8B57', 'borderBottom': '2px solid #2E8B57', 'paddingBottom': '5px'}),
        
        # API Status Cards
        html.Div([
            html.Div(id='api-status-cards', style={'marginBottom': '30px'})
        ]),
        
        # DynamoDB Configuration
        html.Div([
            html.H4("🗄️ DynamoDB Configuration", style={'color': '#333'}),
            html.Div(id='dynamodb-config')
        ], style={'marginBottom': '30px'}),
        
        # Data Persistence Settings
        html.Div([
            html.H4("💾 Data Persistence Settings", style={'color': '#333'}),
            html.Div([
                html.P("Configure which data should be stored in DynamoDB for historical analysis:"),
                
                # Checkboxes for data types
                html.Div([
                    dcc.Checklist(
                        id='persistence-settings',
                        options=[
                            {'label': ' Store ElectricityMap Carbon Intensity Data', 'value': 'carbon'},
                            {'label': ' Store Boavizta Power Consumption Data', 'value': 'power'},
                            {'label': ' Store AWS Cost Explorer Data', 'value': 'cost'},
                            {'label': ' Store Analysis Results', 'value': 'analysis'}
                        ],
                        value=['carbon', 'power', 'cost', 'analysis'],
                        style={'fontSize': '14px'}
                    )
                ], style={'marginLeft': '20px'}),
                
                html.Button(
                    '💾 Update Persistence Settings',
                    id='update-persistence-btn',
                    style={'marginTop': '15px', 'padding': '8px 16px', 'backgroundColor': '#2E8B57', 'color': 'white', 'border': 'none', 'borderRadius': '4px'}
                )
            ])
        ])
    ])