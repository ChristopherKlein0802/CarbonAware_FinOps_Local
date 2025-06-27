"""
Dashboard for unified cost and carbon reporting.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class CarbonFinOpsDashboard:
    """Dashboard for visualizing cost and carbon metrics."""
    
    def __init__(self):
        self.figures = {}
    
    def create_cost_carbon_correlation(self, 
                                     cost_data: pd.DataFrame, 
                                     carbon_data: pd.DataFrame) -> go.Figure:
        """Create correlation plot between cost and carbon emissions."""
        
        # Merge data on timestamp
        merged = pd.merge(
            cost_data, 
            carbon_data, 
            on='timestamp', 
            how='inner'
        )
        
        fig = px.scatter(
            merged,
            x='cost',
            y='carbon_emissions',
            title='Cost vs Carbon Emissions Correlation',
            labels={
                'cost': 'Cost ($)',
                'carbon_emissions': 'Carbon Emissions (kgCO2)'
            },
            trendline='ols'
        )
        
        return fig
    
    def create_savings_summary(self, 
                             baseline: Dict, 
                             optimized: Dict) -> go.Figure:
        """Create savings summary chart."""
        
        categories = ['Cost', 'Carbon Emissions']
        baseline_values = [
            baseline['total_cost'], 
            baseline['total_carbon']
        ]
        optimized_values = [
            optimized['total_cost'], 
            optimized['total_carbon']
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Baseline',
            x=categories,
            y=baseline_values,
            marker_color='red'
        ))
        
        fig.add_trace(go.Bar(
            name='Optimized',
            x=categories,
            y=optimized_values,
            marker_color='green'
        ))
        
        # Calculate percentage savings
        cost_savings = ((baseline['total_cost'] - optimized['total_cost']) / 
                       baseline['total_cost'] * 100)
        carbon_savings = ((baseline['total_carbon'] - optimized['total_carbon']) / 
                         baseline['total_carbon'] * 100)
        
        fig.update_layout(
            title=f'Savings Summary - Cost: {cost_savings:.1f}%, Carbon: {carbon_savings:.1f}%',
            barmode='group',
            yaxis_title='Value'
        )
        
        return fig
    
    def create_timeline_chart(self, 
                            data: pd.DataFrame, 
                            metric: str) -> go.Figure:
        """Create timeline chart for a specific metric."""
        
        fig = px.line(
            data,
            x='timestamp',
            y=metric,
            title=f'{metric.title()} Over Time',
            labels={
                'timestamp': 'Date',
                metric: metric.title()
            }
        )
        
        return fig
    
    def generate_html_report(self, output_path: str):
        """Generate HTML report with all visualizations."""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Carbon-Aware FinOps Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .chart { margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>Carbon-Aware FinOps Report</h1>
            <h2>Executive Summary</h2>
            <div id="summary"></div>
            {charts}
        </body>
        </html>
        """
        
        # Generate chart HTML
        charts_html = ""
        for name, fig in self.figures.items():
            charts_html += f'<div class="chart" id="{name}"></div>'
            charts_html += f'<script>{fig.to_html(include_plotlyjs=False)}</script>'
        
        # Write report
        with open(output_path, 'w') as f:
            f.write(html_template.format(charts=charts_html))
        
        logger.info(f"Report generated: {output_path}")