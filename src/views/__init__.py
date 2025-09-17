"""
Carbon-Aware FinOps Dashboard Views
Modular view structure for better maintainability

This package contains all dashboard views split into logical modules
for improved code organization and maintainability.
"""

from .overview import render_overview_page
from .infrastructure import render_infrastructure_page
from .carbon import render_carbon_page
from .competitive import render_competitive_analysis_page
from .research import render_research_methods_page

__all__ = [
    'render_overview_page',
    'render_infrastructure_page',
    'render_carbon_page',
    'render_competitive_analysis_page',
    'render_research_methods_page'
]