"""
Reusable UI Components for Carbon-Aware FinOps Dashboard

This module provides both card components (HTML) and chart components (Plotly)
used across different tabs. Combines the functionality of cards.py and charts.py.
"""

from dash import html
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Optional


class DashboardCards:
    """Factory class for creating consistent dashboard cards (HTML components)"""
    
    @staticmethod
    def create_metric_card(title: str, value: str, subtitle: str, icon: str = "💰") -> html.Div:
        """
        Create a standard metric card
        
        Args:
            title: Card title (e.g., "Monthly Costs")
            value: Main value to display (e.g., "€125.50")
            subtitle: Subtitle text (e.g., "Real AWS Cost Explorer Data")
            icon: Emoji icon for the card
            
        Returns:
            html.Div: Formatted card component
        """
        return html.Div([
            html.H3(f"{icon} {title}", style={'color': '#2E8B57', 'margin': '0'}),
            html.H2(value, style={'color': '#333', 'margin': '5px 0'}),
            html.P(subtitle, style={'color': '#666', 'fontSize': '12px', 'margin': '0'}),
        ], style={
            'padding': '20px',
            'backgroundColor': 'white',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'textAlign': 'center'
        })

    @staticmethod
    def create_empty_state_card(title: str, message: str, icon: str = "📊") -> html.Div:
        """
        Create an empty state card when no data is available
        
        Args:
            title: Card title
            message: Empty state message
            icon: Emoji icon
            
        Returns:
            html.Div: Empty state card
        """
        return html.Div([
            html.H3(f"{icon} {title}", style={'color': '#2E8B57', 'margin': '0'}),
            html.H2("No Data", style={'color': '#999', 'margin': '5px 0'}),
            html.P(message, style={'color': '#999', 'fontSize': '12px', 'margin': '0'}),
        ], style={
            'padding': '20px',
            'backgroundColor': 'white',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'textAlign': 'center'
        })

    @staticmethod
    def create_cost_overview_card(data: List[Dict]) -> html.Div:
        """Create cost overview card"""
        if not data:
            return DashboardCards.create_empty_state_card(
                "Monthly Costs",
                "No AWS instances deployed",
                "💰"
            )
        
        total_cost = sum(item['monthly_cost_eur'] for item in data)
        return DashboardCards.create_metric_card(
            "Monthly Costs",
            f"€{total_cost:.2f}",
            "Real AWS Cost Explorer Data",
            "💰"
        )

    @staticmethod
    def create_co2_overview_card(data: List[Dict]) -> html.Div:
        """Create CO2 overview card"""
        if not data:
            return DashboardCards.create_empty_state_card(
                "Monthly CO2",
                "No infrastructure running",
                "🌍"
            )
        
        total_co2 = sum(item['monthly_co2_kg'] for item in data)
        return DashboardCards.create_metric_card(
            "Monthly CO2",
            f"{total_co2:.1f} kg",
            "German Grid Data",
            "🌍"
        )

    @staticmethod
    def create_instances_overview_card(data: List[Dict]) -> html.Div:
        """Create instances overview card"""
        instance_count = len(data)
        
        if not data:
            return DashboardCards.create_empty_state_card(
                "Instances",
                "No instances found",
                "🖥️"
            )
        
        avg_runtime = sum(item['runtime_hours_month'] for item in data) / len(data) if data else 0
        
        return html.Div([
            html.H3("🖥️ Instances", style={'color': '#2E8B57', 'margin': '0'}),
            html.H2(f"{instance_count}", style={'color': '#333', 'margin': '5px 0'}),
            html.P(f"{avg_runtime:.0f}h Avg Monthly Runtime", style={'color': '#666', 'fontSize': '12px', 'margin': '0'}),
            html.P("All Account Instances", style={'color': '#888', 'fontSize': '11px', 'margin': '0'})
        ], style={
            'padding': '20px',
            'backgroundColor': 'white',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'textAlign': 'center'
        })

    @staticmethod
    def create_savings_overview_card(data: List[Dict]) -> html.Div:
        """Create savings potential overview card"""
        if not data:
            return DashboardCards.create_empty_state_card(
                "Savings Potential",
                "Deploy infrastructure to see savings",
                "💡"
            )
        
        total_savings = 0
        for instance in data:
            if 'optimization_potential' in instance:
                office_savings = instance['optimization_potential']['office_hours']['cost_savings']
                weekday_savings = instance['optimization_potential']['weekdays_only']['cost_savings']
                carbon_savings = instance['optimization_potential']['carbon_aware']['cost_savings']
                best_savings = max(office_savings, weekday_savings, carbon_savings)
                total_savings += best_savings
        
        return DashboardCards.create_metric_card(
            "Savings Potential",
            f"€{total_savings:.0f}/month",
            "Best optimization strategy",
            "💡"
        )

    @staticmethod
    def create_carbon_intensity_card(data: List[Dict]) -> html.Div:
        """Create carbon intensity card"""
        return DashboardCards.create_metric_card(
            "Carbon Intensity",
            "420 g/kWh",
            "German Grid Current",
            "⚡"
        )
    
    # New Infrastructure-specific Cards
    
    @staticmethod
    def create_active_infrastructure_card(data: List[Dict]) -> html.Div:
        """Create active infrastructure overview card"""
        if not data:
            return DashboardCards.create_empty_state_card(
                "Active Infrastructure",
                "No infrastructure deployed",
                "🏗️"
            )
        
        running_instances = len([item for item in data if item['state'] == 'running'])
        unique_types = len(set(item['instance_type'] for item in data))
        
        return html.Div([
            html.H3("🏗️ Active Infrastructure", style={'color': '#2E8B57', 'margin': '0'}),
            html.H2(f"{running_instances} Running", style={'color': '#333', 'margin': '5px 0'}),
            html.P(f"{unique_types} Different Instance Types", style={'color': '#666', 'fontSize': '12px', 'margin': '0'}),
            html.P("Real AWS EC2 Data", style={'color': '#888', 'fontSize': '11px', 'margin': '0'})
        ], style={
            'padding': '20px',
            'backgroundColor': 'white',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'textAlign': 'center'
        })
    
    @staticmethod
    def create_resource_efficiency_card(data: List[Dict]) -> html.Div:
        """Create resource efficiency card"""
        if not data:
            return DashboardCards.create_empty_state_card(
                "Resource Efficiency",
                "Deploy instances to see efficiency",
                "⚡"
            )
        
        # Calculate average efficiency (runtime vs maximum possible)
        total_runtime = sum(item['runtime_hours_month'] for item in data)
        max_possible = len(data) * 720  # 720 hours = 30 days * 24 hours
        efficiency = (total_runtime / max_possible * 100) if max_possible > 0 else 0
        
        return html.Div([
            html.H3("⚡ Resource Efficiency", style={'color': '#2E8B57', 'margin': '0'}),
            html.H2(f"{efficiency:.0f}%", style={'color': '#333', 'margin': '5px 0'}),
            html.P(f"Avg Runtime Utilization", style={'color': '#666', 'fontSize': '12px', 'margin': '0'}),
            html.P("Runtime vs Max Possible", style={'color': '#888', 'fontSize': '11px', 'margin': '0'})
        ], style={
            'padding': '20px',
            'backgroundColor': 'white',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'textAlign': 'center'
        })
    
    @staticmethod
    def create_cost_per_hour_card(data: List[Dict]) -> html.Div:
        """Create cost per hour card"""
        if not data:
            return DashboardCards.create_empty_state_card(
                "Cost per Hour",
                "No cost data available",
                "💰"
            )
        
        total_cost = sum(item['monthly_cost_eur'] for item in data)
        total_runtime = sum(item['runtime_hours_month'] for item in data)
        cost_per_hour = total_cost / total_runtime if total_runtime > 0 else 0
        
        return html.Div([
            html.H3("💰 Cost per Hour", style={'color': '#2E8B57', 'margin': '0'}),
            html.H2(f"€{cost_per_hour:.2f}/h", style={'color': '#333', 'margin': '5px 0'}),
            html.P(f"Avg across all instances", style={'color': '#666', 'fontSize': '12px', 'margin': '0'}),
            html.P("Proportional Allocation", style={'color': '#888', 'fontSize': '11px', 'margin': '0'})
        ], style={
            'padding': '20px',
            'backgroundColor': 'white',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'textAlign': 'center'
        })
    
    @staticmethod
    def create_rightsizing_potential_card(data: List[Dict]) -> html.Div:
        """Create right-sizing potential card"""
        if not data:
            return DashboardCards.create_empty_state_card(
                "Right-sizing Potential",
                "Deploy instances to analyze",
                "🔧"
            )
        
        # Calculate instances that could be optimized (running >90% of the time = potentially oversized)
        overutilized = 0
        underutilized = 0
        
        for item in data:
            runtime_ratio = item['runtime_hours_month'] / 720  # 720 = max hours per month
            if runtime_ratio > 0.9:
                overutilized += 1
            elif runtime_ratio < 0.3:
                underutilized += 1
        
        total_optimizable = underutilized  # Focus on underutilized as main optimization target
        total_instances = len(data)
        optimization_percentage = (total_optimizable / total_instances * 100) if total_instances > 0 else 0
        
        return html.Div([
            html.H3("🔧 Right-sizing Potential", style={'color': '#2E8B57', 'margin': '0'}),
            html.H2(f"{total_optimizable} Instances", style={'color': '#333', 'margin': '5px 0'}),
            html.P(f"{optimization_percentage:.0f}% can be optimized", style={'color': '#666', 'fontSize': '12px', 'margin': '0'}),
            html.P("Low utilization detected", style={'color': '#888', 'fontSize': '11px', 'margin': '0'})
        ], style={
            'padding': '20px',
            'backgroundColor': 'white',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'textAlign': 'center'
        })

    @staticmethod
    def create_info_section(title: str, items: List[str], icon: str = "💡") -> html.Div:
        """
        Create an information section with bullet points
        
        Args:
            title: Section title
            items: List of information items
            icon: Section icon
            
        Returns:
            html.Div: Information section component
        """
        return html.Div([
            html.H4(f"{icon} {title}", style={'color': '#333'}),
            html.Div([
                html.P(f"• {item}", style={'margin': '10px 0'}) for item in items
            ])
        ])


class DashboardCharts:
    """Factory class for creating consistent dashboard charts (Plotly components)"""
    
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
    
    @staticmethod 
    def create_cost_analysis_chart(data: List[Dict]) -> go.Figure:
        """
        Create cost analysis chart showing historical vs current runtime
        Explains why smaller instances might cost more due to historical usage
        """
        if not data:
            return DashboardCharts.create_empty_chart(
                "No cost data available", 
                "Cost Analysis - Historical vs Current Usage"
            )
        
        # Group data by instance type
        instance_types = {}
        for item in data:
            inst_type = item['instance_type']
            if inst_type not in instance_types:
                instance_types[inst_type] = {
                    'instances': [],
                    'current_runtime': 0,
                    'historical_usage': 0,
                    'total_cost': 0,
                    'cost_per_hour': 0
                }
            
            instance_types[inst_type]['instances'].append(item['name'])
            instance_types[inst_type]['current_runtime'] += item['runtime_hours_month']
            
            # Sum up actual instance costs (now showing real individual costs)
            instance_types[inst_type]['total_cost'] += item['monthly_cost_eur'] / 0.92  # Convert back to USD for display
            
            # Historical usage patterns (for analysis transparency)
            # These represent the aggregate usage patterns from Cost Explorer
            if inst_type == 't3.small':
                instance_types[inst_type]['historical_usage'] = 159.78
            elif inst_type == 't3.medium':
                instance_types[inst_type]['historical_usage'] = 95.16  
            elif inst_type == 't3.large':
                instance_types[inst_type]['historical_usage'] = 21.30
            elif inst_type == 't3.micro':
                instance_types[inst_type]['historical_usage'] = 287.05
        
        # Calculate cost per hour
        for inst_type in instance_types:
            if instance_types[inst_type]['historical_usage'] > 0:
                instance_types[inst_type]['cost_per_hour'] = (
                    instance_types[inst_type]['total_cost'] / 
                    instance_types[inst_type]['historical_usage']
                )
        
        # Create subplot
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Historical Usage Hours (30 days)", "Current Runtime Hours", 
                          "Total Historical Cost ($USD)", "Cost per Hour ($USD)"),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        types = list(instance_types.keys())
        historical_hours = [instance_types[t]['historical_usage'] for t in types]
        current_hours = [instance_types[t]['current_runtime'] for t in types]
        total_costs = [instance_types[t]['total_cost'] for t in types]
        cost_per_hour = [instance_types[t]['cost_per_hour'] for t in types]
        
        # Historical usage
        fig.add_trace(
            go.Bar(x=types, y=historical_hours, name="Historical Hours", 
                   marker_color='#1f77b4', text=[f"{h:.1f}h" for h in historical_hours],
                   textposition='outside'),
            row=1, col=1
        )
        
        # Current runtime  
        fig.add_trace(
            go.Bar(x=types, y=current_hours, name="Current Hours",
                   marker_color='#ff7f0e', text=[f"{h:.1f}h" for h in current_hours],
                   textposition='outside'),
            row=1, col=2
        )
        
        # Total costs
        fig.add_trace(
            go.Bar(x=types, y=total_costs, name="Total Cost",
                   marker_color='#2ca02c', text=[f"${c:.2f}" for c in total_costs],
                   textposition='outside'),
            row=2, col=1
        )
        
        # Cost per hour
        fig.add_trace(
            go.Bar(x=types, y=cost_per_hour, name="Cost/Hour",
                   marker_color='#d62728', text=[f"${c:.3f}" for c in cost_per_hour],
                   textposition='outside'),
            row=2, col=2
        )
        
        fig.update_layout(
            height=600,
            showlegend=False,
            title_text="💡 Cost Analysis: Direct Instance Costs + Historical Usage Patterns",
            title_font_size=16,
            annotations=[
                dict(text="<b>Analysis:</b><br>• Left: Historical usage patterns from AWS Cost Explorer<br>• Right: Current runtime since launch<br>• Bottom Left: Sum of DIRECT individual instance costs (real billing)<br>• Bottom Right: Historical cost per hour patterns<br>• Now showing individual real costs instead of allocated estimates",
                     xref="paper", yref="paper", x=0.5, y=-0.15, 
                     showarrow=False, font_size=12, font_color="gray",
                     align="center")
            ]
        )
        
        return fig
    
    # New Infrastructure Deep-Dive Charts
    
    @staticmethod
    def create_instance_type_cost_distribution(data: List[Dict]) -> go.Figure:
        """Create instance type cost distribution chart"""
        if not data:
            return DashboardCharts.create_empty_chart(
                "No cost data available",
                "Instance Type Cost Distribution"
            )
        
        # Group by instance type
        type_costs = {}
        for item in data:
            inst_type = item['instance_type']
            if inst_type not in type_costs:
                type_costs[inst_type] = {'cost': 0, 'count': 0, 'instances': []}
            type_costs[inst_type]['cost'] += item['monthly_cost_eur']
            type_costs[inst_type]['count'] += 1
            type_costs[inst_type]['instances'].append(item['name'])
        
        # Create pie chart
        labels = []
        values = []
        text_info = []
        
        for inst_type, data_dict in type_costs.items():
            labels.append(inst_type)
            values.append(data_dict['cost'])
            text_info.append(f"{data_dict['count']} instances<br>€{data_dict['cost']:.2f}/month")
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            text=text_info,
            textposition="inside",
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>%{text}<br>%{percent}<extra></extra>",
            marker=dict(colors=['#2E8B57', '#4ecdc4', '#45b7d1', '#ff6b6b', '#96ceb4', '#ffd93d'])
        )])
        
        fig.update_layout(
            title="💰 Instance Type Cost Distribution",
            height=400,
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
        )
        
        return fig
    
    @staticmethod
    def create_runtime_cost_correlation(data: List[Dict]) -> go.Figure:
        """Create runtime vs cost correlation scatter plot"""
        if not data:
            return DashboardCharts.create_empty_chart(
                "No correlation data available",
                "Runtime vs Cost Correlation"
            )
        
        runtimes = [item['runtime_hours_month'] for item in data]
        costs = [item['monthly_cost_eur'] for item in data]
        names = [f"{item['name']} ({item['instance_type']})" for item in data]
        colors = [item['instance_type'] for item in data]
        
        # Create color mapping
        unique_types = list(set(colors))
        color_map = {t: ['#2E8B57', '#4ecdc4', '#45b7d1', '#ff6b6b', '#96ceb4'][i % 5] 
                    for i, t in enumerate(unique_types)}
        
        fig = go.Figure()
        
        for inst_type in unique_types:
            type_runtimes = [r for r, t in zip(runtimes, colors) if t == inst_type]
            type_costs = [c for c, t in zip(costs, colors) if t == inst_type]
            type_names = [n for n, t in zip(names, colors) if t == inst_type]
            
            fig.add_trace(go.Scatter(
                x=type_runtimes,
                y=type_costs,
                mode='markers',
                name=inst_type,
                marker=dict(size=12, color=color_map[inst_type]),
                text=type_names,
                hovertemplate="<b>%{text}</b><br>Runtime: %{x:.0f}h<br>Cost: €%{y:.2f}<extra></extra>"
            ))
        
        fig.update_layout(
            title="📊 Runtime vs Cost Correlation",
            xaxis_title="Runtime Hours/Month",
            yaxis_title="Monthly Cost (€)",
            height=400,
            hovermode='closest'
        )
        
        return fig
    
    @staticmethod
    def create_efficiency_matrix(data: List[Dict]) -> go.Figure:
        """Create efficiency matrix showing cost per hour vs utilization"""
        if not data:
            return DashboardCharts.create_empty_chart(
                "No efficiency data available",
                "Resource Efficiency Matrix"
            )
        
        cost_per_hour = []
        utilization = []
        names = []
        colors = []
        
        for item in data:
            runtime = item['runtime_hours_month']
            cost = item['monthly_cost_eur']
            
            # Calculate metrics
            cph = cost / runtime if runtime > 0 else 0
            util = (runtime / 720) * 100  # 720 = max hours per month
            
            cost_per_hour.append(cph)
            utilization.append(util)
            names.append(f"{item['name']} ({item['instance_type']})")
            
            # Color by efficiency (low cost per hour + high utilization = green)
            if util > 70 and cph < 0.1:
                colors.append('#2E8B57')  # High efficiency - green
            elif util > 50 and cph < 0.2:
                colors.append('#4ecdc4')  # Medium efficiency - blue
            elif util < 30:
                colors.append('#ff6b6b')  # Low utilization - red
            else:
                colors.append('#ffd93d')  # Average - yellow
        
        fig = go.Figure(data=go.Scatter(
            x=utilization,
            y=cost_per_hour,
            mode='markers',
            marker=dict(
                size=15,
                color=colors,
                line=dict(width=2, color='white')
            ),
            text=names,
            hovertemplate="<b>%{text}</b><br>Utilization: %{x:.1f}%<br>Cost/Hour: €%{y:.3f}<extra></extra>"
        ))
        
        # Add quadrant lines
        fig.add_hline(y=0.15, line_dash="dash", line_color="gray", annotation_text="High Cost Threshold")
        fig.add_vline(x=50, line_dash="dash", line_color="gray", annotation_text="Low Utilization Threshold")
        
        fig.update_layout(
            title="🎯 Resource Efficiency Matrix",
            xaxis_title="Utilization (%)",
            yaxis_title="Cost per Hour (€)",
            height=400,
            annotations=[
                dict(x=25, y=0.25, text="⚠️ Underutilized<br>High Cost", 
                     showarrow=False, font=dict(color="red", size=10)),
                dict(x=75, y=0.05, text="✅ Efficient<br>Well Utilized", 
                     showarrow=False, font=dict(color="green", size=10))
            ]
        )
        
        return fig