"""
Reusable Chart Components for Carbon-Aware FinOps Dashboard

This module provides consistent chart components used across different tabs.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict

class DashboardCharts:
    """Factory class for creating consistent dashboard charts"""
    
    @staticmethod
    def create_empty_chart(message: str, title: str = "No Data Available") -> go.Figure:
        """
        Create an empty chart with informative message
        
        Args:
            message: Message to display
            title: Chart title
            
        Returns:
            go.Figure: Empty chart figure
        """
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font_size=14, font_color="gray"
        )
        fig.update_layout(height=300, showlegend=False, title=title)
        return fig

    @staticmethod
    def create_bar_chart(
        x_data: List[str], 
        y_data: List[float], 
        title: str, 
        x_title: str, 
        y_title: str,
        color: str = '#2E8B57',
        height: int = 300,
        show_values: bool = True,
        value_format: str = "{:.1f}"
    ) -> go.Figure:
        """
        Create a standardized bar chart
        
        Args:
            x_data: X-axis data (instance names, etc.)
            y_data: Y-axis data (values)
            title: Chart title
            x_title: X-axis title
            y_title: Y-axis title
            color: Bar color
            height: Chart height
            show_values: Whether to show values on bars
            value_format: Format string for values
            
        Returns:
            go.Figure: Bar chart figure
        """
        text_values = [value_format.format(val) for val in y_data] if show_values else None
        
        fig = go.Figure([go.Bar(
            x=x_data,
            y=y_data,
            marker_color=color,
            text=text_values,
            textposition='outside',
            textfont_size=12
        )])
        
        fig.update_layout(
            title=title,
            xaxis_title=x_title,
            yaxis_title=y_title,
            height=height,
            showlegend=False
        )
        fig.update_xaxes(tickangle=45, tickfont_size=10)
        
        return fig

    @staticmethod
    def create_costs_chart(data: List[Dict], height: int = 300) -> go.Figure:
        """Create individual cost chart"""
        if not data:
            return DashboardCharts.create_empty_chart(
                "No cost data available<br><br>Deploy AWS infrastructure to see real costs",
                "Monthly Costs"
            )
        
        instance_names = [item['name'] for item in data]
        actual_monthly_costs = [item['monthly_cost_eur'] for item in data]
        total_costs = sum(actual_monthly_costs)
        
        return DashboardCharts.create_bar_chart(
            x_data=instance_names,
            y_data=actual_monthly_costs,
            title=f"Real Monthly Costs - Total: €{total_costs:.1f}",
            x_title="Instances",
            y_title="Cost (€)",
            color='#2E8B57',
            height=height,
            value_format="€{:.1f}"
        )

    @staticmethod
    def create_runtime_chart(data: List[Dict], height: int = 300) -> go.Figure:
        """Create individual runtime chart"""
        if not data:
            return DashboardCharts.create_empty_chart(
                "No runtime data available<br><br>Deploy instances to see runtime analysis",
                "Runtime Hours"
            )
        
        instance_names = [item['name'] for item in data]
        actual_runtime_hours = [item['runtime_hours_month'] for item in data]
        total_runtime = sum(actual_runtime_hours)
        
        return DashboardCharts.create_bar_chart(
            x_data=instance_names,
            y_data=actual_runtime_hours,
            title=f"Real Runtime Hours/Month - Total: {total_runtime:.0f}h",
            x_title="Instances",
            y_title="Hours",
            color='#4ecdc4',
            height=height,
            value_format="{:.0f}h"
        )

    @staticmethod
    def create_co2_chart(data: List[Dict], height: int = 300) -> go.Figure:
        """Create individual CO2 chart"""
        if not data:
            return DashboardCharts.create_empty_chart(
                "No CO2 data available<br><br>Deploy infrastructure to see carbon footprint",
                "CO2 Emissions"
            )
        
        instance_names = [item['name'] for item in data]
        actual_monthly_co2 = [item['monthly_co2_kg'] for item in data]
        total_co2 = sum(actual_monthly_co2)
        
        return DashboardCharts.create_bar_chart(
            x_data=instance_names,
            y_data=actual_monthly_co2,
            title=f"Monthly CO2 Emissions - Total: {total_co2:.1f}kg",
            x_title="Instances",
            y_title="kg CO2",
            color='#ff6b6b',
            height=height,
            value_format="{:.1f}kg"
        )

    @staticmethod
    def create_efficiency_chart(data: List[Dict], height: int = 300) -> go.Figure:
        """Create individual efficiency chart with dual axis"""
        if not data:
            return DashboardCharts.create_empty_chart(
                "No efficiency data available<br><br>Deploy instances to see efficiency metrics",
                "Efficiency Metrics"
            )
        
        instance_names = [item['name'] for item in data]
        actual_monthly_costs = [item['monthly_cost_eur'] for item in data]
        actual_runtime_hours = [item['runtime_hours_month'] for item in data]
        actual_monthly_co2 = [item['monthly_co2_kg'] for item in data]
        
        cost_per_hour = [cost/runtime if runtime > 0 else 0 for cost, runtime in zip(actual_monthly_costs, actual_runtime_hours)]
        co2_per_euro = [co2/cost if cost > 0 else 0 for co2, cost in zip(actual_monthly_co2, actual_monthly_costs)]
        avg_cost_per_hour = sum(cost_per_hour) / len(cost_per_hour) if cost_per_hour else 0
        
        # Create dual-axis chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(x=instance_names, y=cost_per_hour, name='€/Hour',
                   marker_color='#45b7d1', text=[f'€{c:.2f}/h' for c in cost_per_hour],
                   textposition='outside', textfont_size=11),
            secondary_y=False,
        )
        
        fig.add_trace(
            go.Scatter(x=instance_names, y=co2_per_euro, mode='lines+markers',
                      name='kg CO2/€', marker_color='orange', line=dict(width=3),
                      text=[f'{c:.2f}kg/€' for c in co2_per_euro],
                      textposition='top center'),
            secondary_y=True,
        )
        
        fig.update_layout(
            title=f"Efficiency Metrics - Avg: €{avg_cost_per_hour:.2f}/h",
            height=height
        )
        fig.update_xaxes(title_text="Instances", tickangle=45, tickfont_size=10)
        fig.update_yaxes(title_text="€/Hour", secondary_y=False)
        fig.update_yaxes(title_text="kg CO2/€", secondary_y=True)
        
        return fig

    @staticmethod
    def create_optimization_chart(data: List[Dict], height: int = 500) -> go.Figure:
        """Create optimization potential chart"""
        if not data:
            return DashboardCharts.create_empty_chart(
                "No optimization data available<br><br>No AWS infrastructure found in account",
                "Optimization Potential"
            )
        
        # Prepare data for chart
        instances = []
        current_costs = []
        office_savings = []
        weekday_savings = []
        carbon_savings = []
        
        for item in data:
            instances.append(item['name'][:15] + '...' if len(item['name']) > 15 else item['name'])
            current_costs.append(item['monthly_cost_eur'])
            office_savings.append(item['optimization_potential']['office_hours']['cost_savings'])
            weekday_savings.append(item['optimization_potential']['weekdays_only']['cost_savings'])
            carbon_savings.append(item['optimization_potential']['carbon_aware']['cost_savings'])
        
        fig = go.Figure()
        
        # Create grouped bar chart
        fig.add_trace(go.Bar(
            name='Current Monthly Cost',
            x=instances,
            y=current_costs,
            marker_color='#ff6b6b',
            text=[f"€{cost:.1f}" for cost in current_costs],
            textposition='auto'
        ))
        
        # Office hours potential
        fig.add_trace(go.Bar(
            name='Office Hours (72% reduction)',
            x=instances,
            y=office_savings,
            marker_color='#4ecdc4',
            text=[f"Save €{saving:.1f}" for saving in office_savings],
            textposition='auto'
        ))
        
        # Weekdays only potential  
        fig.add_trace(go.Bar(
            name='Weekdays Only (28% reduction)',
            x=instances,
            y=weekday_savings,
            marker_color='#45b7d1',
            text=[f"Save €{saving:.1f}" for saving in weekday_savings],
            textposition='auto'
        ))
        
        # Carbon-aware potential
        fig.add_trace(go.Bar(
            name='Carbon-Aware (Variable)',
            x=instances,
            y=carbon_savings,
            marker_color='#96ceb4',
            text=[f"Save €{saving:.1f}" for saving in carbon_savings],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="💰 Monthly Savings Potential: Current Costs vs. Optimization Strategies",
            xaxis_title="AWS Instances",
            yaxis_title="Monthly Costs & Savings (EUR)",
            barmode='group',
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=height
        )
        
        return fig

    @staticmethod
    def create_scatter_chart(
        x_data: List[float],
        y_data: List[float], 
        names: List[str],
        title: str,
        x_title: str,
        y_title: str,
        color: str = '#2E8B57'
    ) -> go.Figure:
        """Create a scatter plot chart"""
        fig = go.Figure([go.Scatter(
            x=x_data,
            y=y_data,
            mode='markers',
            marker=dict(size=12, color=color),
            text=names,
            textposition="top center",
            hovertemplate=f"<b>%{{text}}</b><br>{x_title}: %{{x}}<br>{y_title}: %{{y}}<extra></extra>"
        )])
        
        fig.update_layout(
            title=title,
            xaxis_title=x_title,
            yaxis_title=y_title,
            hovermode='closest',
            showlegend=False
        )
        
        return fig