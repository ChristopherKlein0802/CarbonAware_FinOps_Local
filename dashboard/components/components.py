"""
Modern Dashboard Components - Builder.io Optimized
Carbon-Aware FinOps Dashboard - Bachelor Thesis

CLEAN VERSION: Only Chart.js compatible components
- Legacy Plotly code removed
- 90% size reduction (58KB → 5KB)
- Only essential DashboardCards functionality
"""

from dash import html
from typing import List, Dict, Optional


class DashboardCards:
    """Factory class for creating modern Builder.io dashboard cards"""

    @staticmethod
    def create_metric_card(title: str, value: str, subtitle: str, icon: str = "💰") -> html.Div:
        """Create modern metric card with Builder.io styling"""
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(icon, className="card-icon"),
                        html.Div(
                            [
                                html.H3(value, className="card-value"),
                                html.P(title, className="card-label"),
                                html.Span(subtitle, className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card",
        )

    @staticmethod
    def create_empty_state_card(title: str, message: str, icon: str = "📊") -> html.Div:
        """Create modern empty state card with Builder.io styling"""
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(icon, className="card-icon"),
                        html.Div(
                            [
                                html.H3("No Data", className="card-value empty"),
                                html.P(title, className="card-label"),
                                html.Span(message, className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card empty-card",
        )

    @staticmethod
    def create_status_card(title: str, status: str, message: str, icon: str = "⚡") -> html.Div:
        """Create status card with Builder.io styling"""
        status_class = "success" if status.lower() == "active" else "warning"
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(icon, className="card-icon"),
                        html.Div(
                            [
                                html.H3(status, className=f"card-value {status_class}"),
                                html.P(title, className="card-label"),
                                html.Span(message, className="card-detail"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card",
        )

    @staticmethod
    def create_comparison_card(title: str, current: str, previous: str, icon: str = "📈") -> html.Div:
        """Create comparison card with trend indication"""
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(icon, className="card-icon"),
                        html.Div(
                            [
                                html.H3(current, className="card-value"),
                                html.P(title, className="card-label"),
                                html.Span(f"vs {previous}", className="card-detail trend"),
                            ],
                            className="card-content",
                        ),
                    ],
                    className="card-inner",
                )
            ],
            className="modern-card trend-card",
        )
