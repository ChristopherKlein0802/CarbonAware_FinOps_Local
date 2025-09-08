"""
Advanced Visualization Module for Carbon-Aware FinOps

Provides sophisticated charts for academic analysis and thesis documentation
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class AdvancedVisualization:
    """Advanced visualization components for academic rigor"""
    
    def __init__(self):
        self.colors = {
            'primary': '#2E8B57',
            'secondary': '#FFA500', 
            'accent': '#FF6347',
            'success': '#32CD32',
            'warning': '#FFD700',
            'danger': '#FF4500'
        }
    
    def create_time_series_carbon_intensity(self, hours: int = 168) -> go.Figure:
        """
        Create realistic German grid carbon intensity time series (1 week)
        
        This shows WHEN electricity is cleanest/dirtiest in Germany
        Essential for demonstrating carbon-aware scheduling benefits
        """
        # Generate realistic German grid data pattern
        timestamps = [datetime.now() - timedelta(hours=h) for h in range(hours, 0, -1)]
        
        # Simulate German grid patterns:
        # - Lower at midday (solar peak)
        # - Higher in evening (demand peak)
        # - Weekend differences
        carbon_intensity = []
        
        for ts in timestamps:
            hour = ts.hour
            day_of_week = ts.weekday()  # 0 = Monday
            
            # Base load pattern
            if 6 <= hour <= 10:  # Morning ramp-up
                base = 450 + (hour - 6) * 20
            elif 10 <= hour <= 14:  # Solar peak (cleanest)
                base = 300 - (hour - 12) * 15
            elif 14 <= hour <= 20:  # Evening demand peak (dirtiest)
                base = 350 + (hour - 14) * 35
            else:  # Night
                base = 380
            
            # Weekend effect (less industrial demand)
            if day_of_week >= 5:  # Weekend
                base *= 0.85
            
            # Add some realistic noise
            noise = np.random.normal(0, 20)
            carbon_intensity.append(max(200, base + noise))  # Minimum 200g CO2/kWh
        
        # Create time series chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=carbon_intensity,
            mode='lines+markers',
            name='German Grid Carbon Intensity',
            line=dict(color=self.colors['primary'], width=2),
            hovertemplate='<b>%{x}</b><br>Carbon Intensity: %{y:.0f} g CO2/kWh<extra></extra>'
        ))
        
        # Add optimal scheduling windows (when carbon is lowest)
        optimal_periods = []
        for i, (ts, carbon) in enumerate(zip(timestamps, carbon_intensity)):
            if carbon < 320:  # Below average
                optimal_periods.append((ts, carbon))
        
        if optimal_periods:
            opt_x, opt_y = zip(*optimal_periods)
            fig.add_trace(go.Scatter(
                x=opt_x,
                y=opt_y,
                mode='markers',
                name='Optimal Scheduling Windows',
                marker=dict(color=self.colors['success'], size=8, symbol='star'),
                hovertemplate='<b>Optimal Time</b><br>%{x}<br>Carbon: %{y:.0f} g CO2/kWh<extra></extra>'
            ))
        
        fig.update_layout(
            title='German Electricity Grid Carbon Intensity - 7 Day Analysis',
            xaxis_title='Time',
            yaxis_title='Carbon Intensity (g CO2/kWh)',
            hovermode='x unified',
            height=500
        )
        
        return fig
    
    def create_optimization_confidence_chart(self, scenarios: List[Dict]) -> go.Figure:
        """
        Create chart showing optimization results with confidence intervals
        
        This adds STATISTICAL RIGOR to your optimization analysis
        """
        from src.analytics.statistical_analysis import StatisticalAnalyzer
        analyzer = StatisticalAnalyzer()
        
        scenario_names = []
        carbon_estimates = []
        lower_bounds = []
        upper_bounds = []
        significance_levels = []
        
        for scenario in scenarios:
            # Calculate statistical confidence for each scenario
            stats = analyzer.carbon_calculation_with_confidence(
                power_watts=scenario.get('power_watts', 20),
                carbon_intensity=400,  # German average
                hours=24,
                power_source=scenario.get('power_source', 'fallback')
            )
            
            scenario_names.append(scenario['name'])
            carbon_estimates.append(stats['carbon_kg_estimate'])
            lower_bounds.append(stats['carbon_kg_lower_95'])
            upper_bounds.append(stats['carbon_kg_upper_95'])
            
            # Determine significance level
            if stats['relative_uncertainty_percent'] < 10:
                significance_levels.append('High Confidence')
            elif stats['relative_uncertainty_percent'] < 20:
                significance_levels.append('Medium Confidence')
            else:
                significance_levels.append('Low Confidence')
        
        # Create confidence interval chart
        fig = go.Figure()
        
        # Add confidence intervals as error bars
        fig.add_trace(go.Scatter(
            x=scenario_names,
            y=carbon_estimates,
            error_y=dict(
                type='data',
                symmetric=False,
                array=[u - e for u, e in zip(upper_bounds, carbon_estimates)],
                arrayminus=[e - l for e, l in zip(carbon_estimates, lower_bounds)],
                visible=True,
                color=self.colors['warning']
            ),
            mode='markers+lines',
            name='Carbon Emissions with 95% CI',
            marker=dict(size=10, color=self.colors['primary']),
            line=dict(color=self.colors['primary'], width=2)
        ))
        
        # Add data quality annotations
        for i, (name, significance) in enumerate(zip(scenario_names, significance_levels)):
            color = self.colors['success'] if 'High' in significance else \
                   self.colors['warning'] if 'Medium' in significance else \
                   self.colors['danger']
            
            fig.add_annotation(
                x=name,
                y=upper_bounds[i] + 0.01,
                text=significance,
                showarrow=False,
                font=dict(color=color, size=10),
                bgcolor='white',
                bordercolor=color,
                borderwidth=1
            )
        
        fig.update_layout(
            title='Carbon Optimization Results with Statistical Confidence Intervals',
            xaxis_title='Optimization Scenario',
            yaxis_title='Daily Carbon Emissions (kg CO2)',
            height=500,
            showlegend=True
        )
        
        return fig
    
    def create_seasonal_analysis_chart(self) -> go.Figure:
        """
        Create seasonal carbon intensity analysis for Germany
        
        Shows how carbon optimization effectiveness varies throughout the year
        """
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # German seasonal patterns (realistic data based on renewable energy)
        avg_carbon_intensity = [520, 480, 420, 380, 320, 290,
                              280, 300, 350, 400, 460, 510]  # g CO2/kWh
        
        renewable_percentage = [25, 30, 35, 45, 55, 65,
                              70, 65, 50, 40, 30, 25]  # % renewable
        
        # Calculate optimization potential (higher when renewables are high)
        optimization_potential = [100 - (r * 0.8) for r in renewable_percentage]
        
        # Create subplot with secondary y-axis
        from plotly.subplots import make_subplots
        fig = make_subplots(
            rows=1, cols=1,
            specs=[[{"secondary_y": True}]]
        )
        
        # Carbon intensity trend
        fig.add_trace(
            go.Scatter(
                x=months,
                y=avg_carbon_intensity,
                mode='lines+markers',
                name='Average Carbon Intensity',
                line=dict(color=self.colors['danger'], width=3),
                marker=dict(size=8)
            ),
            secondary_y=False,
        )
        
        # Renewable energy percentage
        fig.add_trace(
            go.Scatter(
                x=months,
                y=renewable_percentage,
                mode='lines+markers',
                name='Renewable Energy %',
                line=dict(color=self.colors['success'], width=3),
                marker=dict(size=8)
            ),
            secondary_y=True,
        )
        
        # Add shaded regions for best optimization periods
        fig.add_shape(
            type="rect",
            x0="May", x1="Aug",
            y0=0, y1=700,
            fillcolor=self.colors['success'],
            opacity=0.2,
            layer="below",
            line_width=0,
        )
        
        fig.add_annotation(
            x="Jun",
            y=600,
            text="Best Optimization Period<br>(High Renewable Energy)",
            showarrow=False,
            bgcolor=self.colors['success'],
            font=dict(color='white', size=12),
            opacity=0.8
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text="Carbon Intensity (g CO2/kWh)", secondary_y=False)
        fig.update_yaxes(title_text="Renewable Energy (%)", secondary_y=True)
        
        fig.update_layout(
            title='German Grid: Seasonal Carbon Intensity & Optimization Opportunities',
            xaxis_title='Month',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    def create_multi_region_comparison(self) -> go.Figure:
        """
        Compare carbon intensity across European regions
        
        Shows why German focus is relevant for EU optimization
        """
        regions = ['Germany', 'France', 'Poland', 'Denmark', 'Netherlands', 'Austria']
        avg_carbon_intensity = [400, 180, 650, 250, 380, 220]  # g CO2/kWh (realistic values)
        renewable_mix = [45, 75, 15, 80, 35, 70]  # % renewable
        
        # Create bubble chart: x=renewable%, y=carbon intensity, size=optimization potential
        optimization_potential = [100 - (c / 10) for c in avg_carbon_intensity]  # Inverse relationship
        
        fig = go.Figure()
        
        # Add bubble for each region
        colors = px.colors.qualitative.Set3[:len(regions)]
        
        for i, (region, carbon, renewable, potential) in enumerate(
            zip(regions, avg_carbon_intensity, renewable_mix, optimization_potential)
        ):
            fig.add_trace(go.Scatter(
                x=[renewable],
                y=[carbon],
                mode='markers+text',
                name=region,
                marker=dict(
                    size=potential,
                    color=colors[i],
                    opacity=0.7,
                    sizemode='diameter',
                    sizeref=2. * max(optimization_potential) / (40.**2),
                    sizemin=4,
                    line=dict(width=2, color='white')
                ),
                text=[region],
                textposition="middle center",
                textfont=dict(color='white', size=10),
                hovertemplate=f'<b>{region}</b><br>' +
                            'Renewable Energy: %{x}%<br>' +
                            'Carbon Intensity: %{y} g CO2/kWh<br>' +
                            f'Optimization Potential: {potential:.0f}%<extra></extra>'
            ))
        
        # Highlight Germany
        germany_idx = regions.index('Germany')
        fig.add_shape(
            type="circle",
            x0=renewable_mix[germany_idx] - 5,
            y0=avg_carbon_intensity[germany_idx] - 30,
            x1=renewable_mix[germany_idx] + 5,
            y1=avg_carbon_intensity[germany_idx] + 30,
            line=dict(color=self.colors['primary'], width=3),
        )
        
        fig.add_annotation(
            x=renewable_mix[germany_idx] + 10,
            y=avg_carbon_intensity[germany_idx],
            text="Focus Region<br>(Thesis Scope)",
            showarrow=True,
            arrowcolor=self.colors['primary'],
            font=dict(color=self.colors['primary'], size=12),
            bgcolor='white',
            bordercolor=self.colors['primary'],
            borderwidth=2
        )
        
        fig.update_layout(
            title='European Regional Carbon Intensity Comparison',
            xaxis_title='Renewable Energy Mix (%)',
            yaxis_title='Average Carbon Intensity (g CO2/kWh)',
            height=500,
            showlegend=False,
            annotations=[
                dict(
                    x=0.02, y=0.98,
                    xref='paper', yref='paper',
                    text='Bubble size = Optimization Potential',
                    showarrow=False,
                    bgcolor='white',
                    bordercolor='gray',
                    borderwidth=1,
                    font=dict(size=10)
                )
            ]
        )
        
        return fig