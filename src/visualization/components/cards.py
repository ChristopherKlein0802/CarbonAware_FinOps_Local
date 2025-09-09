"""
Reusable Card Components for Carbon-Aware FinOps Dashboard

This module provides consistent card components used across different tabs.
"""

from dash import html
from typing import List, Dict, Optional

class DashboardCards:
    """Factory class for creating consistent dashboard cards"""
    
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