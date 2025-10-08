"""
Domain Constants - Academic and business constants for Carbon-Aware FinOps

This module contains FIXED academic constants based on literature and standards.
For configurable runtime settings, see config/settings.py.
"""

from typing import Dict


# =============================================================================
# ACADEMIC CONSTANTS (Literature-based, NOT configurable)
# =============================================================================


class AcademicConstants:
    """
    Academic research constants derived from published literature.

    These values are FIXED and should NOT be changed via environment variables.
    They represent established research findings and market data.

    Sources:
    - EU ETS prices: European Energy Exchange (EEX) market data
    - Optimization factors: McKinsey [7], MIT carbon-aware scheduling [20]
    - EUR/USD rate: European Central Bank (ECB) official rates
    """

    # Market-based financial constants (verifiable external data)
    EU_ETS_PRICE_PER_TONNE: float = 50.0  # €50/tonne CO₂ - EEX market price
    HOURS_PER_MONTH: int = 730  # Mathematical constant (365.25 * 24 / 12)

    # Literature-derived optimization factors
    CONSERVATIVE_SCENARIO_FACTOR: float = 0.10  # 10% conservative scenario (lower bound)
    MODERATE_SCENARIO_FACTOR: float = 0.20  # 20% moderate scenario (literature median)

    # Currency conversion (class-level property)
    @staticmethod
    def get_eur_usd_rate() -> float:
        """
        Get EUR/USD exchange rate from configuration.

        This is configurable via .env to allow updates without code changes,
        while maintaining the academic constant pattern.

        Returns:
            float: EUR/USD rate (default: 0.92 - ECB official rate)
        """
        from src.config import settings

        return settings.eur_usd_rate

# Export the class (not an instance)
# Usage: AcademicConstants.EU_ETS_PRICE_PER_TONNE or AcademicConstants.get_eur_usd_rate()


# =============================================================================
# CARBON GRID THRESHOLDS (German grid classification)
# =============================================================================


class CarbonConstants:
    """
    German electricity grid carbon intensity thresholds.

    Based on typical generation mix classifications:
    - <200g: High renewable penetration (solar/wind dominant)
    - 200-350g: Mixed generation (renewables + gas)
    - 350-450g: High fossil fuel usage (coal/lignite)
    - >450g: Critical carbon intensity (emergency generation)
    """

    OPTIMAL_THRESHOLD: int = 200  # g CO₂/kWh - Optimal (renewable-heavy)
    MODERATE_THRESHOLD: int = 350  # g CO₂/kWh - Moderate (mixed sources)
    HIGH_CARBON_THRESHOLD: int = 450  # g CO₂/kWh - High (coal-dominant)


# =============================================================================
# DASHBOARD UI CONSTANTS
# =============================================================================


class UIConstants:
    """Dashboard-specific UI and caching constants."""

    STREAMLIT_CACHE_TTL_SECONDS: int = 300  # 5 minutes cache for dynamic calculations


# =============================================================================
# EXPORT ALL CONSTANTS
# =============================================================================

__all__ = [
    "AcademicConstants",
    "CarbonConstants",
    "UIConstants",
]
