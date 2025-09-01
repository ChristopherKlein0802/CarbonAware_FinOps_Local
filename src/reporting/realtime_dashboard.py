"""
Real-time dashboard for Carbon-Aware FinOps metrics.
"""

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import boto3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CarbonFinOpsDashboard:
    """Real-time dashboard for Carbon-Aware FinOps metrics."""

    def __init__(self):
        self.app = dash.Dash(__name__)

        # FIX: Add CSS styling to the app instance
        self.app.css.append_css({
            'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
        })

        # Custom CSS - inline style
        self.custom_css = """
        <style>
        .kpi-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            margin: 10px;
        }
        .kpi-card h2 {
            margin: 10px 0;
            font-size: 2.5em;
            font-weight: bold;
        }
        .kpi-card h3 {
            margin: 10px 0;
            font-size: 1.2em;
        }
        </style>
        """

        try:
            self.dynamodb = boto3.resource('dynamodb')
            self.cloudwatch = boto3.client('cloudwatch')
            self.ce = boto3.client('ce')
            self.ec2 = boto3.client('ec2')
        except Exception as e:
            logger.warning(f"AWS clients initialization failed: {e}")
            # Initialize as None to handle offline mode
            self.dynamodb = None
            self.cloudwatch = None
            self.ce = None
            self.ec2 = None

        # Initialize layou
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self):
        """Setup dashboard layout."""

        self.app.layout = html.Div([
            # Add custom CSS
            html.Div(self.custom_css, dangerously_allow_html=True),

            html.Div([
                html.H1("Carbon-Aware FinOps Dashboard",
                       style={'textAlign': 'center', 'color': '#2c3e50'}),
                html.Hr(),
            ]),

            # KPI Cards Row
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Cost Savings", style={'color': '#27ae60'}),
                        html.H2(id='cost-savings', children='$0'),
                        html.P('This Month', style={'color': '#7f8c8d'})
                    ], className='kpi-card'),
                ], className='four columns'),

                html.Div([
                    html.Div([
                        html.H3("CO₂ Reduction", style={'color': '#2ecc71'}),
                        html.H2(id='carbon-reduction', children='0 kg'),
                        html.P('This Month', style={'color': '#7f8c8d'})
                    ], className='kpi-card'),
                ], className='four columns'),

                html.Div([
                    html.Div([
                        html.H3("Optimized Instances", style={'color': '#3498db'}),
                        html.H2(id='optimized-instances', children='0'),
                        html.P('Active Now', style={'color': '#7f8c8d'})
                    ], className='kpi-card'),
                ], className='four columns'),
            ], className='row'),

            # Charts Row
            html.Div([
                html.Div([
                    dcc.Graph(id='cost-timeline'),
                ], className='six columns'),

                html.Div([
                    dcc.Graph(id='carbon-timeline'),
                ], className='six columns'),
            ], className='row'),

            # Recommendations Table
            html.Div([
                html.H3("Active Recommendations"),
                html.Div(id='recommendations-table')
            ], style={'margin': '20px'}),

            # Instance Status
            html.Div([
                html.H3("Instance Status"),
                dcc.Graph(id='instance-status-chart')
            ], style={'margin': '20px'}),

            # Auto-refresh
            dcc.Interval(
                id='interval-component',
                interval=60 * 1000,  # Update every minute
                n_intervals=0
            )
        ])

    def setup_callbacks(self):
        """Setup dashboard callbacks."""

        @self.app.callback(
            [Output('cost-savings', 'children'),
             Output('carbon-reduction', 'children'),
             Output('optimized-instances', 'children'),
             Output('cost-timeline', 'figure'),
             Output('carbon-timeline', 'figure'),
             Output('recommendations-table', 'children'),
             Output('instance-status-chart', 'figure')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            # Get current metrics
            metrics = self.get_current_metrics()

            # Update KPIs
            cost_savings = f"${metrics['cost_savings']:.2f}"
            carbon_reduction = f"{metrics['carbon_reduction']:.1f} kg"
            optimized_count = str(metrics['optimized_instances'])

            # Create timeline charts
            cost_fig = self.create_cost_timeline()
            carbon_fig = self.create_carbon_timeline()

            # Create recommendations table
            recommendations_table = self.create_recommendations_table()

            # Create instance status char
            status_fig = self.create_instance_status_chart()

            return (cost_savings, carbon_reduction, optimized_count,
                   cost_fig, carbon_fig, recommendations_table, status_fig)

    def get_current_metrics(self):
        """Get current metrics from DynamoDB and CloudWatch."""

        # Default values for offline mode
        default_metrics = {
            'cost_savings': 0,
            'carbon_reduction': 0,
            'optimized_instances': 0,
            'total_shutdowns': 0,
            'total_startups': 0
        }

        if not self.dynamodb:
            return default_metrics

        try:
            # Get data from DynamoDB
            table = self.dynamodb.Table('carbon-aware-finops-state')

            # Query last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            response = table.scan(
                FilterExpression='#t >= :start',
                ExpressionAttributeNames={'#t': 'timestamp'},
                ExpressionAttributeValues={':start': int(start_date.timestamp())}
            )

            # Calculate metrics
            total_shutdowns = sum(item.get('shutdowns', 0) for item in response.get('Items', []))
            total_startups = sum(item.get('startups', 0) for item in response.get('Items', []))

            # Estimate savings (simplified)
            cost_per_hour = 0.05  # Average cost per instance hour
            carbon_per_hour = 0.2  # kg CO2 per instance hour

            hours_saved = total_shutdowns * 8

            return {
                'cost_savings': hours_saved * cost_per_hour,
                'carbon_reduction': hours_saved * carbon_per_hour,
                'optimized_instances': total_shutdowns,
                'total_shutdowns': total_shutdowns,
                'total_startups': total_startups
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return default_metrics

    def create_cost_timeline(self):
        """Create cost timeline chart."""

        if not self.ce:
            # Create sample data for offline mode
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            costs = np.random.uniform(10, 50, 30)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=costs,
                mode='lines+markers',
                name='Daily Cost (Sample)',
                line=dict(color='#e74c3c', width=2)
            ))

            fig.update_layout(
                title='Cost Trend (Sample Data)',
                xaxis_title='Date',
                yaxis_title='Cost ($)',
                hovermode='x unified'
            )

            return fig

        # Get cost data from Cost Explorer
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Tags': {
                        'Key': 'Project',
                        'Values': ['carbon-aware-finops']
                    }
                }
            )

            dates = [r['TimePeriod']['Start'] for r in response['ResultsByTime']]
            costs = [float(r['Total']['UnblendedCost']['Amount']) for r in response['ResultsByTime']]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=costs,
                mode='lines+markers',
                name='Daily Cost',
                line=dict(color='#e74c3c', width=2)
            ))

            fig.update_layout(
                title='Cost Trend (Last 30 Days)',
                xaxis_title='Date',
                yaxis_title='Cost ($)',
                hovermode='x unified'
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating cost timeline: {e}")
            # Return empty figure on error
            return go.Figure()

    def create_carbon_timeline(self):
        """Create carbon emissions timeline chart."""

        # Generate data (would come from actual calculations)
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        carbon_baseline = pd.Series([50 + np.random.randn() * 5 for _ in range(30)])
        carbon_optimized = pd.Series([35 + np.random.randn() * 3 for _ in range(30)])

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates, y=carbon_baseline,
            mode='lines',
            name='Baseline',
            fill='tonexty',
            line=dict(color='#e74c3c')
        ))

        fig.add_trace(go.Scatter(
            x=dates, y=carbon_optimized,
            mode='lines',
            name='Optimized',
            fill='tozeroy',
            line=dict(color='#27ae60')
        ))

        fig.update_layout(
            title='Carbon Emissions Comparison',
            xaxis_title='Date',
            yaxis_title='CO₂ (kg)',
            hovermode='x unified'
        )

        return fig

    def create_recommendations_table(self):
        """Create recommendations table."""

        # Sample recommendations (would come from DynamoDB in production)
        recommendations = [
            {'Instance': 'i-0123456', 'Current': 't3.large', 'Recommended': 't3.medium',
             'Savings': '$62.40/month', 'Action': 'Downsize'},
            {'Instance': 'i-0789012', 'Current': 't3.small', 'Recommended': 't3.micro',
             'Savings': '$7.80/month', 'Action': 'Downsize'},
            {'Instance': 'i-0345678', 'Current': 'On-Demand', 'Recommended': 'Spot',
             'Savings': '$45.00/month', 'Action': 'Convert to Spot'},
        ]

        df = pd.DataFrame(recommendations)

        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df.columns],
            style_cell={'textAlign': 'left'},
            style_data_conditional=[
                {
                    'if': {'column_id': 'Action', 'filter_query': '{Action} = "Downsize"'},
                    'backgroundColor': '#3498db',
                    'color': 'white',
                },
                {
                    'if': {'column_id': 'Action', 'filter_query': '{Action} = "Convert to Spot"'},
                    'backgroundColor': '#9b59b6',
                    'color': 'white',
                }
            ]
        )

    def create_instance_status_chart(self):
        """Create instance status pie chart."""

        if not self.ec2:
            # Sample data for offline mode
            status_counts = {'running': 2, 'stopped': 1, 'pending': 0, 'stopping': 0}
        else:
            try:
                # Get current instance states
                response = self.ec2.describe_instances(
                    Filters=[
                        {'Name': 'tag:Project', 'Values': ['carbon-aware-finops']}
                    ]
                )

                status_counts = {'running': 0, 'stopped': 0, 'pending': 0, 'stopping': 0}

                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        state = instance['State']['Name']
                        if state in status_counts:
                            status_counts[state] += 1
            except Exception as e:
                logger.error(f"Error getting instance status: {e}")
                status_counts = {'running': 0, 'stopped': 0}

        fig = go.Figure(data=[go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=.3
        )])

        fig.update_layout(
            title='Current Instance Status',
            annotations=[dict(text='Instances', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        return fig

    def run(self, debug=True, port=8050, host='127.0.0.1'):
        """Run the dashboard."""
        print(f"🚀 Starting dashboard at http://{host}:{port}")
        print("Press Ctrl+C to stop")
        self.app.run_server(debug=debug, port=port, host=host)


def main():
    """Main entry point for the dashboard."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    dashboard = CarbonFinOpsDashboard()
    dashboard.run()




if __name__ == "__main__":
    main()
