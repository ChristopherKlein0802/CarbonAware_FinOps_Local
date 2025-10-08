"""
Carbon-Aware FinOps Dashboard Views
Modular view structure for better maintainability

This package contains all dashboard views split into logical modules
for improved code organization and maintainability.
"""

from .pages.overview import render_overview_page
from .pages.infrastructure_details import render_infrastructure_page
from .pages.carbon_analysis import render_carbon_page

__all__ = ["render_overview_page", "render_infrastructure_page", "render_carbon_page"]
