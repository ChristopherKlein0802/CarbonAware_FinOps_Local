"""Centralised constants for the Carbon-Aware FinOps dashboard."""

from typing import Dict

from .config import settings


# =============================================================================
# ACADEMIC & BUSINESS CONSTANTS
# =============================================================================

class AcademicConstants:
    """
    Academic research and business calculation constants.

    Financial constants are now centralized in settings.py and can be
    overridden via environment variables.
    """

    # Financial Constants (Verifiable market data)
    # Note: EUR_USD_RATE now defaults to settings.eur_usd_rate (configurable via .env)
    EUR_USD_RATE: float = settings.eur_usd_rate   # ECB official rate (default: 0.92)
    EU_ETS_PRICE_PER_TONNE: float = 50.0          # €50/tonne CO₂ - EEX market price
    HOURS_PER_MONTH: int = 730                     # Mathematical constant (365.25 * 24 / 12)

    # Cost Optimization Constants
    CONSERVATIVE_SCENARIO_FACTOR: float = 0.10     # 10% conservative scenario
    MODERATE_SCENARIO_FACTOR: float = 0.20         # 20% moderate scenario


# =============================================================================
# CARBON INTENSITY & GRID CONSTANTS
# =============================================================================

class CarbonConstants:
    """German grid carbon intensity thresholds and classifications"""

    # Grid Status Thresholds (g CO₂/kWh)
    OPTIMAL_THRESHOLD: int = 200                  # <200g = Optimal (solar/wind)
    MODERATE_THRESHOLD: int = 350                 # 200-350g = Moderate (mixed)
    HIGH_CARBON_THRESHOLD: int = 450              # 350-450g = High (coal)


# =============================================================================
# API & CACHING CONSTANTS
# =============================================================================

class APIConstants:
    """API timeouts, cache TTLs, and request configuration"""

    STREAMLIT_DYNAMIC_CALCULATIONS: int = 300     # 5 minutes cache
# =============================================================================
# EXPORT ALL CONSTANTS
# =============================================================================

__all__ = [
    'AcademicConstants',
    'CarbonConstants',
    'APIConstants',
]
