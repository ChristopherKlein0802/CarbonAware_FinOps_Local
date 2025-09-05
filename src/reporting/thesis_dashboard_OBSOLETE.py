"""
Streamlined Thesis Dashboard - Cost and Carbon Savings Visualization

This dashboard demonstrates the financial and environmental impact of carbon-aware scheduling
for EC2 instances. Designed specifically for bachelor thesis demonstration.

Key Features:
- Real-time cost savings visualization
- Carbon emission reduction tracking  
- Scheduling effectiveness comparison
- Simple, clear metrics for thesis presentation
"""

import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.graph_objects as go
import pandas as pd
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class ThesisDashboard:
    """Simplified dashboard for thesis demonstration of carbon-aware scheduling benefits."""
    
    def __init__(self, aws_profile='carbon-finops-sandbox', project_name='carbon-aware-finops'):
        self.aws_profile = aws_profile
        self.project_name = project_name
        
        # Initialize Dash app
        self.app = dash.Dash(__name__)
        self.app.title = "Carbon-Aware FinOps - Thesis Demo"
        
        # Initialize AWS clients
        try:
            boto3.setup_default_session(profile_name=aws_profile)
            self.dynamodb = boto3.resource('dynamodb')
            self.ec2 = boto3.client('ec2')
            self.ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer only in us-east-1
            logger.info("AWS clients initialized successfully")
        except Exception as e:
            logger.error(f"AWS initialization failed: {e}")
            # Set to None for offline demo mode
            self.dynamodb = None
            self.ec2 = None
            self.ce = None
        
        # Setup dashboard layout and callbacks
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Create the dashboard layout focused on thesis metrics."""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("Carbon-Aware FinOps - Bachelor Thesis Demonstration", 
                       className="text-center mb-4"),
                html.P("Quantifying Cost and Carbon Savings through Intelligent EC2 Scheduling", 
                       className="text-center text-muted mb-4"),
            ], className="container-fluid bg-primary text-white py-4 mb-4"),
            
            # Auto-refresh component
            dcc.Interval(
                id='interval-component',
                interval=30*1000,  # Refresh every 30 seconds
                n_intervals=0
            ),
            
            # Main content container
            html.Div([
                # Key Metrics Row
                html.Div([
                    html.H2("📊 Real-Time Savings Overview", className="mb-3"),
                    
                    # Total Savings Cards
                    html.Div([
                        # Cost Savings Card
                        html.Div([
                            html.Div([
                                html.H3("💰 Total Cost Savings", className="card-title"),
                                html.H2(id="total-cost-savings", children="$0.00", 
                                        className="text-success display-4"),
                                html.P("Daily savings from scheduling optimization", 
                                       className="text-muted")
                            ], className="card-body text-center")
                        ], className="card h-100"),
                        
                        # Carbon Savings Card  
                        html.Div([
                            html.Div([
                                html.H3("🌱 Carbon Reduction", className="card-title"),
                                html.H2(id="total-carbon-savings", children="0.00 kg", 
                                        className="text-success display-4"),
                                html.P("CO2 emissions avoided through scheduling", 
                                       className="text-muted")
                            ], className="card-body text-center")
                        ], className="card h-100"),
                        
                        # Current Carbon Intensity Card
                        html.Div([
                            html.Div([
                                html.H3("⚡ Carbon Intensity", className="card-title"),
                                html.H2(id="current-carbon-intensity", children="350 gCO2/kWh", 
                                        className="display-4"),
                                html.P("Current grid carbon intensity", 
                                       className="text-muted")
                            ], className="card-body text-center")
                        ], className="card h-100"),
                        
                    ], className="row mb-4", style={'display': 'grid', 'grid-template-columns': '1fr 1fr 1fr', 'gap': '20px'}),
                    
                ], className="mb-5"),
                
                # Charts Row
                html.Div([
                    html.H2("📈 Scheduling Comparison Analysis", className="mb-3"),
                    
                    html.Div([
                        # Instance Comparison Chart
                        html.Div([
                            html.H4("Instance Scheduling Effectiveness", className="text-center mb-3"),
                            dcc.Graph(id="instance-comparison-chart")
                        ], className="col-md-6"),
                        
                        # Savings Trend Chart
                        html.Div([
                            html.H4("Cumulative Savings Trend", className="text-center mb-3"),
                            dcc.Graph(id="savings-trend-chart")
                        ], className="col-md-6"),
                        
                    ], className="row mb-4"),
                    
                ], className="mb-5"),
                
                # Instance Details Table
                html.Div([
                    html.H2("🖥️ Instance Analysis Details", className="mb-3"),
                    html.Div(id="instance-details-table")
                ], className="mb-5"),
                
                # Footer
                html.Div([
                    html.Hr(),
                    html.P([
                        "Bachelor Thesis Project - ",
                        html.Strong("Carbon-Aware FinOps for Cloud Cost and Environmental Optimization"),
                        " | Data updated every 30 seconds"
                    ], className="text-center text-muted")
                ])
                
            ], className="container-fluid px-4")
            
        ], style={'font-family': 'Arial, sans-serif'})
    
    def setup_callbacks(self):
        """Setup dashboard callbacks for real-time updates."""
        
        @self.app.callback(
            [Output('total-cost-savings', 'children'),
             Output('total-carbon-savings', 'children'),
             Output('current-carbon-intensity', 'children'),
             Output('instance-comparison-chart', 'figure'),
             Output('savings-trend-chart', 'figure'),
             Output('instance-details-table', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            """Update all dashboard components."""
            try:
                # Get latest analysis data
                analysis_data = self.get_analysis_data()
                
                if not analysis_data:
                    # Return default values if no data
                    return ("$0.00", "0.00 kg", "350 gCO2/kWh", 
                           self.create_empty_chart("No data available"),
                           self.create_empty_chart("No data available"),
                           html.P("No instance data available", className="text-center text-muted"))
                
                # Calculate totals
                total_cost_savings = sum(item.get('cost_savings_usd', 0) for item in analysis_data 
                                       if item.get('instance_id') != 'AGGREGATED_TOTALS')
                total_carbon_savings = sum(item.get('carbon_savings_kg', 0) for item in analysis_data
                                         if item.get('instance_id') != 'AGGREGATED_TOTALS')
                
                # Get current carbon intensity (from latest record)
                latest_record = max(analysis_data, key=lambda x: x.get('timestamp', 0), default={})
                carbon_intensity = latest_record.get('carbon_intensity', 350)
                
                # Create charts
                comparison_chart = self.create_instance_comparison_chart(analysis_data)
                trend_chart = self.create_savings_trend_chart(analysis_data)
                details_table = self.create_instance_details_table(analysis_data)
                
                return (
                    f"${total_cost_savings:.2f}",
                    f"{total_carbon_savings:.2f} kg",
                    f"{carbon_intensity:.0f} gCO2/kWh",
                    comparison_chart,
                    trend_chart,
                    details_table
                )
                
            except Exception as e:
                logger.error(f"Error updating dashboard: {e}")
                return ("Error", "Error", "Error",
                       self.create_empty_chart(f"Error: {str(e)}"),
                       self.create_empty_chart(f"Error: {str(e)}"),
                       html.P(f"Error loading data: {str(e)}", className="text-center text-danger"))
    
    def get_analysis_data(self) -> List[Dict]:
        """Get analysis data from DynamoDB."""
        try:
            if not self.dynamodb:
                # Return demo data if AWS not available
                return self.get_demo_data()
            
            results_table = self.dynamodb.Table(f"{self.project_name}-results")
            
            # Get data from last 24 hours
            current_time = int(datetime.utcnow().timestamp())
            yesterday = current_time - (24 * 60 * 60)
            
            response = results_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('timestamp').gt(yesterday)
            )
            
            # Convert Decimal to float for JSON serialization
            items = []
            for item in response.get('Items', []):
                converted_item = {}
                for key, value in item.items():
                    if isinstance(value, Decimal):
                        converted_item[key] = float(value)
                    else:
                        converted_item[key] = value
                items.append(converted_item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting analysis data: {e}")
            return self.get_demo_data()
    
    def get_demo_data(self) -> List[Dict]:
        """Return demo data for presentation when AWS is not available."""
        current_time = int(datetime.utcnow().timestamp())
        
        return [
            {
                'instance_id': 'i-1234567890abcdef0',
                'timestamp': current_time,
                'schedule_type': 'baseline',
                'current_cost_usd': 0.50,
                'optimized_cost_usd': 0.50,
                'cost_savings_usd': 0.00,
                'current_carbon_kg': 0.046,
                'optimized_carbon_kg': 0.046,
                'carbon_savings_kg': 0.000,
                'carbon_intensity': 380,
                'instance_type': 't3.micro',
                'state': 'running'
            },
            {
                'instance_id': 'i-2234567890abcdef0',
                'timestamp': current_time,
                'schedule_type': 'office-hours',
                'current_cost_usd': 0.50,
                'optimized_cost_usd': 0.12,
                'cost_savings_usd': 0.38,
                'current_carbon_kg': 0.046,
                'optimized_carbon_kg': 0.011,
                'carbon_savings_kg': 0.035,
                'carbon_intensity': 380,
                'instance_type': 't3.micro',
                'state': 'stopped'
            },
            {
                'instance_id': 'i-3234567890abcdef0',
                'timestamp': current_time,
                'schedule_type': 'weekdays-only',
                'current_cost_usd': 0.50,
                'optimized_cost_usd': 0.36,
                'cost_savings_usd': 0.14,
                'current_carbon_kg': 0.046,
                'optimized_carbon_kg': 0.033,
                'carbon_savings_kg': 0.013,
                'carbon_intensity': 380,
                'instance_type': 't3.micro',
                'state': 'running'
            },
            {
                'instance_id': 'i-4234567890abcdef0',
                'timestamp': current_time,
                'schedule_type': 'carbon-aware',
                'current_cost_usd': 0.50,
                'optimized_cost_usd': 0.35,
                'cost_savings_usd': 0.15,
                'current_carbon_kg': 0.046,
                'optimized_carbon_kg': 0.032,
                'carbon_savings_kg': 0.014,
                'carbon_intensity': 380,
                'instance_type': 't3.micro',
                'state': 'running'
            }
        ]
    
    def create_instance_comparison_chart(self, data: List[Dict]) -> Dict:
        """Create instance comparison chart showing scheduling effectiveness."""
        try:
            # Filter out aggregated records
            instance_data = [item for item in data if item.get('instance_id') != 'AGGREGATED_TOTALS']
            
            if not instance_data:
                return self.create_empty_chart("No instance data available")
            
            df = pd.DataFrame(instance_data)
            
            fig = go.Figure()
            
            # Cost savings by schedule type
            fig.add_trace(go.Bar(
                name='Cost Savings ($)',
                x=df['schedule_type'],
                y=df['cost_savings_usd'],
                yaxis='y',
                marker_color='#28a745'
            ))
            
            # Carbon savings by schedule type (scaled for visibility)
            fig.add_trace(go.Bar(
                name='Carbon Savings (kg × 10)',
                x=df['schedule_type'],
                y=df['carbon_savings_kg'] * 10,  # Scale for visibility
                yaxis='y2',
                marker_color='#17a2b8',
                opacity=0.7
            ))
            
            fig.update_layout(
                title="Scheduling Strategy Effectiveness",
                xaxis_title="Schedule Type",
                yaxis=dict(title="Cost Savings ($)", side='left'),
                yaxis2=dict(title="Carbon Savings (kg × 10)", side='right', overlaying='y'),
                barmode='group',
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating comparison chart: {e}")
            return self.create_empty_chart(f"Error: {str(e)}")
    
    def create_savings_trend_chart(self, data: List[Dict]) -> Dict:
        """Create cumulative savings trend chart."""
        try:
            # Filter and sort by timestamp
            filtered_data = [item for item in data if item.get('instance_id') != 'AGGREGATED_TOTALS']
            filtered_data.sort(key=lambda x: x.get('timestamp', 0))
            
            if not filtered_data:
                return self.create_empty_chart("No trend data available")
            
            # Calculate cumulative savings
            cumulative_cost = 0
            cumulative_carbon = 0
            timestamps = []
            cost_savings = []
            carbon_savings = []
            
            for item in filtered_data:
                cumulative_cost += item.get('cost_savings_usd', 0)
                cumulative_carbon += item.get('carbon_savings_kg', 0)
                timestamps.append(datetime.fromtimestamp(item.get('timestamp', 0)))
                cost_savings.append(cumulative_cost)
                carbon_savings.append(cumulative_carbon)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=cost_savings,
                mode='lines+markers',
                name='Cumulative Cost Savings ($)',
                line=dict(color='#28a745', width=3),
                yaxis='y'
            ))
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=carbon_savings,
                mode='lines+markers',
                name='Cumulative Carbon Savings (kg)',
                line=dict(color='#17a2b8', width=3),
                yaxis='y2'
            ))
            
            fig.update_layout(
                title="Cumulative Savings Over Time",
                xaxis_title="Time",
                yaxis=dict(title="Cost Savings ($)", side='left'),
                yaxis2=dict(title="Carbon Savings (kg)", side='right', overlaying='y'),
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating trend chart: {e}")
            return self.create_empty_chart(f"Error: {str(e)}")
    
    def create_instance_details_table(self, data: List[Dict]):
        """Create detailed instance analysis table."""
        try:
            # Filter out aggregated records
            instance_data = [item for item in data if item.get('instance_id') != 'AGGREGATED_TOTALS']
            
            if not instance_data:
                return html.P("No instance data available", className="text-center text-muted")
            
            # Prepare table data
            table_data = []
            for item in instance_data:
                table_data.append({
                    'Instance ID': item.get('instance_id', 'Unknown')[-8:],  # Last 8 chars
                    'Schedule Type': item.get('schedule_type', 'Unknown').title(),
                    'Current State': item.get('state', 'Unknown').title(),
                    'Cost Savings': f"${item.get('cost_savings_usd', 0):.3f}",
                    'Carbon Savings': f"{item.get('carbon_savings_kg', 0):.3f} kg",
                    'Efficiency': f"{(item.get('cost_savings_usd', 0) / max(item.get('current_cost_usd', 0.01), 0.01)) * 100:.1f}%"
                })
            
            return dash_table.DataTable(
                data=table_data,
                columns=[{"name": i, "id": i} for i in table_data[0].keys() if table_data],
                style_cell={'textAlign': 'center', 'padding': '10px'},
                style_header={'backgroundColor': '#007bff', 'color': 'white', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa'
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Error creating details table: {e}")
            return html.P(f"Error creating table: {str(e)}", className="text-center text-danger")
    
    def create_empty_chart(self, message: str) -> Dict:
        """Create empty chart with message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(height=400)
        return fig
    
    def run_server(self, debug=True, host='127.0.0.1', port=8050):
        """Run the dashboard server."""
        print(f"\n🌱 Carbon-Aware FinOps Thesis Dashboard")
        print(f"📊 Dashboard URL: http://{host}:{port}")
        print(f"🔄 Auto-refresh: Every 30 seconds")
        print(f"📈 Demonstrating: Cost and Carbon savings through intelligent EC2 scheduling")
        print(f"\nPress Ctrl+C to stop the dashboard\n")
        
        self.app.run(debug=debug, host=host, port=port)


def main():
    """Main function to run the thesis dashboard."""
    dashboard = ThesisDashboard()
    dashboard.run_server(debug=True)


if __name__ == "__main__":
    main()