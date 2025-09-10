"""
Academic Disclaimers and Risk Mitigation Components
For Bachelor Thesis: Carbon-Aware FinOps Tool

This module provides conservative language and academic disclaimers
to ensure scientific rigor and risk mitigation.
"""

from dash import html
from typing import Optional


class AcademicDisclaimers:
    """Factory class for academic disclaimers and conservative language"""
    
    @staticmethod
    def create_methodology_disclaimer() -> html.Div:
        """Create main methodology disclaimer for dashboard header"""
        return html.Div([
            html.Div([
                html.H6("📋 Research Methodology Notice", className="text-info mb-2"),
                html.P([
                    "This tool represents a ",
                    html.Strong("Proof-of-Concept implementation"),
                    " for Bachelor thesis research. Results are preliminary and based on Q1 2025 data. "
                    "API dependencies may affect availability. Real-world deployment requires additional validation."
                ], className="small text-muted mb-1"),
                html.P([
                    html.Strong("Scope: "),
                    "German SMEs (≤100 instances), EU-Central-1 region, t3 instance family focus"
                ], className="small text-muted")
            ], className="alert alert-info", style={'margin': '10px 0', 'padding': '10px'})
        ])
    
    @staticmethod
    def create_data_confidence_note(api_name: str, confidence_level: str) -> html.Div:
        """Create confidence level notice for specific data sources"""
        confidence_colors = {
            "high": "success",
            "medium": "warning", 
            "low": "danger"
        }
        
        return html.Div([
            html.Small([
                f"📊 Data: {api_name} (Confidence: ±{confidence_level})"
            ], className=f"text-{confidence_colors.get(confidence_level.lower(), 'muted')}")
        ])
    
    @staticmethod
    def create_carbon_calculation_disclaimer() -> html.Div:
        """Disclaimer specific to carbon calculations"""
        return html.Div([
            html.Details([
                html.Summary("⚠️ Carbon Calculation Methodology", className="text-warning"),
                html.P([
                    html.Strong("Formula: "),
                    "CO₂ = Power(kW) × Grid_Intensity(g CO₂/kWh) ÷ 1000"
                ], className="small"),
                html.P([
                    html.Strong("Data Sources: "),
                    "Boavizta API (±10%), ElectricityMaps API (±5%), German grid focus"
                ], className="small"),
                html.P([
                    html.Strong("Limitations: "),
                    "Single region, preliminary analysis, API-dependent"
                ], className="small text-muted")
            ], className="mt-2")
        ])
    
    @staticmethod  
    def create_cost_optimization_disclaimer() -> html.Div:
        """Disclaimer for cost optimization claims"""
        return html.Div([
            html.Details([
                html.Summary("💰 Cost Optimization Methodology", className="text-info"),
                html.P([
                    html.Strong("Approach: "),
                    "Analysis-only tool - no automatic infrastructure changes"
                ], className="small"),
                html.P([
                    html.Strong("Estimates: "),
                    "Based on AWS Cost Explorer data with 85-95% efficiency assumptions"
                ], className="small"),
                html.P([
                    html.Strong("ESG Value: "),
                    "€25-75 per tonne CO₂ (EU ETS pricing range 2025)"
                ], className="small text-muted")
            ], className="mt-2")
        ])
    
    @staticmethod
    def create_conservative_savings_text(percentage: float) -> str:
        """Convert absolute percentages to conservative ranges"""
        if percentage >= 70:
            return f"60-{percentage:.0f}%"
        elif percentage >= 40:
            return f"30-{percentage:.0f}%"
        elif percentage >= 20:
            return f"15-{percentage:.0f}%"
        else:
            return f"up to {percentage:.0f}%"
    
    @staticmethod
    def create_competitive_advantage_note() -> html.Div:
        """Note about competitive differentiation"""
        return html.Div([
            html.Div([
                html.H6("🏆 Research Contribution", className="text-success mb-2"),
                html.P([
                    html.Strong("Novel Integration: "),
                    "First tool combining AWS Cost Explorer + Real-time German grid data + Business case generation"
                ], className="small"),
                html.P([
                    html.Strong("Differentiation: "),
                    "Existing tools provide either cost OR carbon data, not integrated optimization"
                ], className="small"),
                html.P([
                    html.Strong("Validation: "),
                    "Competitive analysis completed Jan 2025 - no equivalent integrated solution found"
                ], className="small text-muted")
            ], className="alert alert-success", style={'margin': '10px 0', 'padding': '10px'})
        ])
    
    @staticmethod
    def create_api_status_indicator(api_name: str, status: str, last_update: str) -> html.Div:
        """Create API status indicator with timestamp"""
        status_colors = {
            "active": "success",
            "limited": "warning",
            "failed": "danger"
        }
        
        status_icons = {
            "active": "✅",
            "limited": "⚠️",
            "failed": "❌"
        }
        
        return html.Div([
            html.Span(status_icons.get(status, "❓")),
            html.Span(f" {api_name}: ", className="fw-bold"),
            html.Span(status.title(), className=f"text-{status_colors.get(status, 'muted')}"),
            html.Small(f" (Updated: {last_update})", className="text-muted ms-2")
        ], className="d-flex align-items-center mb-1")
    
    @staticmethod
    def get_conservative_language_map():
        """Mapping from strong claims to conservative academic language"""
        return {
            "saves": "may save",
            "reduces": "can reduce", 
            "eliminates": "may eliminate",
            "proves": "suggests",
            "guarantees": "indicates potential for",
            "always": "typically",
            "never": "rarely",
            "will": "may",
            "must": "should consider",
            "best": "among the better",
            "optimal": "near-optimal",
            "maximum": "significant",
            "revolutionary": "innovative",
            "breakthrough": "novel approach"
        }


class RiskMitigationComponents:
    """Components specifically for thesis risk mitigation"""
    
    @staticmethod
    def create_limitations_section() -> html.Div:
        """Create comprehensive limitations section"""
        return html.Div([
            html.H5("⚠️ Current Limitations & Future Work", className="text-warning"),
            html.Ul([
                html.Li("Geographic scope: German grid data only (EU-Central-1)"),
                html.Li("Instance coverage: Focus on t3 family, broader testing needed"), 
                html.Li("Scale validation: SME scenarios (<100 instances)"),
                html.Li("API dependencies: Real-time data requires stable connectivity"),
                html.Li("Preliminary results: Production validation recommended"),
                html.Li("Business case: ESG valuations vary by organization")
            ], className="small"),
            html.P([
                html.Strong("Academic Status: "),
                "This represents a proof-of-concept implementation demonstrating the feasibility "
                "of integrated Carbon-aware FinOps optimization. Further research and "
                "industry validation are recommended for production deployment."
            ], className="small text-muted mt-3")
        ], className="mt-4 p-3 border-left border-warning")
    
    @staticmethod
    def create_sensitivity_analysis_note(parameter: str, variance: str) -> html.Div:
        """Create sensitivity analysis note for key parameters"""
        return html.Div([
            html.Small([
                html.Strong("Sensitivity: "),
                f"±{variance} variation in {parameter} affects results by approximately ±{int(float(variance.rstrip('%')) * 0.8)}%"
            ], className="text-muted")
        ])