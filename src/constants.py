"""
Constants Module for Carbon-Aware FinOps Dashboard
Centralized constants to eliminate magic numbers throughout the codebase

This module consolidates all hard-coded values found across the application
into a single, maintainable location with clear documentation.
"""

from enum import Enum
from typing import Dict, Any


# =============================================================================
# ACADEMIC & BUSINESS CONSTANTS
# =============================================================================

class AcademicConstants:
    """Academic research and business calculation constants"""

    # Financial Constants (Verifiable market data)
    EUR_USD_RATE: float = 0.92                    # ECB official rate September 2025
    EU_ETS_PRICE_PER_TONNE: float = 50.0         # €50/tonne CO₂ - EEX market price
    HOURS_PER_MONTH: int = 730                    # Mathematical constant (365.25 * 24 / 12)

    # Cost Optimization Constants
    SME_TOOL_COST_EUR: float = 20.0               # Our tool monthly cost
    ENTERPRISE_TOOL_COST_EUR: float = 200.0       # Competitor tools cost
    SEPARATE_TOOLS_COST_EUR: float = 200.0        # Multiple separate tools

    # Scenario Analysis Constants (Round numbers for demonstrative analysis)
    CONSERVATIVE_SCENARIO_FACTOR: float = 0.10    # 10% conservative scenario
    MODERATE_SCENARIO_FACTOR: float = 0.20        # 20% moderate scenario
    SELECTED_SCENARIO_FACTOR: float = 0.20        # Using moderate scenario

    # CloudTrail vs Estimates Accuracy
    CLOUDTRAIL_ACCURACY_PERCENT: float = 5.0      # ±5% with CloudTrail audit
    ESTIMATE_ACCURACY_PERCENT: float = 40.0       # ±40% with estimates

    # SME Market Constants
    TYPICAL_SME_MIN_INSTANCES: int = 20           # Small SME
    TYPICAL_SME_MID_INSTANCES: int = 50           # Medium SME
    TYPICAL_SME_MAX_INSTANCES: int = 100          # Large SME

    # NO-FALLBACK Policy: Values removed to enforce academic integrity
    # DEFAULT_COST_PER_INSTANCE_EUR: Removed per NO-FALLBACK policy
    # DEFAULT_CO2_PER_INSTANCE_KG: Removed per NO-FALLBACK policy

    # Precision Analysis Thresholds
    PRECISION_HIGH_THRESHOLD: int = 50             # >50% = High confidence
    PRECISION_MIXED_THRESHOLD: int = 30            # 30-50% = Mixed precision


# =============================================================================
# CARBON INTENSITY & GRID CONSTANTS
# =============================================================================

class CarbonConstants:
    """German grid carbon intensity thresholds and classifications"""

    # Grid Status Thresholds (g CO₂/kWh)
    OPTIMAL_THRESHOLD: int = 200                  # <200g = Optimal (solar/wind)
    MODERATE_THRESHOLD: int = 350                 # 200-350g = Moderate (mixed)
    HIGH_CARBON_THRESHOLD: int = 450              # 350-450g = High (coal)

    # Grid Status Boundaries for Classification
    LOW_CARBON_BOUNDARY: int = 300                # <300g = Low emissions
    MEDIUM_CARBON_BOUNDARY: int = 500             # 300-500g = Medium emissions

    # NO-FALLBACK Policy: EU average removed to maintain academic integrity
    # EU_CONSERVATIVE_AVERAGE: Removed per NO-FALLBACK policy

    # Power Calculation Constants
    WATTS_TO_KW_CONVERSION: int = 1000            # 1kW = 1000W
    GRAMS_TO_KG_CONVERSION: int = 1000            # 1kg = 1000g
    SECONDS_TO_HOURS_CONVERSION: int = 3600       # 1h = 3600s

    # CPU Utilization Constants
    MIN_CPU_UTILIZATION: int = 0                  # 0% minimum CPU
    MAX_CPU_UTILIZATION: int = 100                # 100% maximum CPU
    DEFAULT_CPU_UTILIZATION: float = 30.0         # Default enterprise average

    # CO2 Savings Calculation (EU ETS integration)
    KG_TO_TONNES_CONVERSION: int = 1000           # 1 tonne = 1000 kg


# =============================================================================
# API & CACHING CONSTANTS
# =============================================================================

class APIConstants:
    """API timeouts, cache TTLs, and request configuration"""

    # API Timeout Values (seconds)
    ELECTRICITYMAP_TIMEOUT: int = 30              # ElectricityMaps API timeout
    BOAVIZTA_TIMEOUT: int = 10                    # Boavizta API timeout
    AWS_DEFAULT_TIMEOUT: int = 30                 # AWS APIs timeout

    # Cache TTL Values (minutes) - From cache_utils.py
    CARBON_DATA_TTL: int = 60                     # 60 minutes - ElectricityMaps updates
    CARBON_24H_TTL: int = 120                     # 2 hours - Refresh 24h history frequently
    POWER_DATA_TTL: int = 10080                   # 7 days - Hardware specs don't change
    PRICING_DATA_TTL: int = 10080                 # 7 days - AWS pricing stable
    COST_DATA_TTL: int = 360                      # 6 hours - Cost Explorer updates
    CPU_UTILIZATION_TTL: int = 180                # 3 hours - Performance metrics
    CLOUDTRAIL_EVENTS_TTL: int = 1440             # 24 hours - Audit events immutable

    # Streamlit Cache TTL Values (seconds)
    STREAMLIT_INFRASTRUCTURE_CACHE: int = 1800    # 30 minutes cache
    STREAMLIT_RAPID_CALCULATIONS: int = 600       # 10 minutes cache
    STREAMLIT_DYNAMIC_CALCULATIONS: int = 300     # 5 minutes cache

    # Magic Numbers Replacements
    STREAMLIT_DEFAULT_CACHE_TTL: int = 1800        # Default cache TTL for app.py

    # CloudTrail Configuration
    CLOUDTRAIL_LOOKBACK_DAYS: int = 30            # 30-day audit trail lookback

    # Performance Monitoring
    RESPONSE_TIME_MULTIPLIER: int = 1000          # Convert seconds to milliseconds


# =============================================================================
# UI & DISPLAY CONSTANTS
# =============================================================================

class UIConstants:
    """User interface display and formatting constants"""

    # String Truncation
    INSTANCE_ID_DISPLAY_LENGTH: int = 10          # Show first 10 chars + "..."
    INSTANCE_ID_SHORT_LENGTH: int = 8             # Short display (8 chars)

    # Confidence Assessment (Weighted percentages)
    DATA_INTEGRATION_CONFIDENCE: float = 0.90     # 90% - APIs work
    METHODOLOGY_CONFIDENCE: float = 0.85          # 85% - CloudTrail approach sound
    SCENARIO_APPLICABILITY: float = 0.60          # 60% - Scenarios demonstrative

    # Confidence Weighting (Total = 1.0)
    DATA_INTEGRATION_WEIGHT: float = 0.4          # 40% weight
    METHODOLOGY_WEIGHT: float = 0.4               # 40% weight
    SCENARIO_WEIGHT: float = 0.2                  # 20% weight

    # UI Styling Constants
    HERO_SECTION_PADDING: str = "20px"            # Hero section padding
    HERO_SECTION_BORDER_RADIUS: str = "10px"      # Hero section border radius
    HERO_SECTION_MARGIN: str = "10px 0"          # Hero section margin

    # Chart Configuration
    CHART_HEIGHT: int = 400                       # Standard chart height
    CHART_HEIGHT_LARGE: int = 500                 # Large chart height


# =============================================================================
# AWS REGION MAPPINGS
# =============================================================================

class AWSConstants:
    """AWS-specific constants and region mappings"""

    # AWS region to ElectricityMap zone mappings (from api_client.py)
    REGION_MAPPINGS: Dict[str, str] = {
        "eu-central-1": "DE",        # Germany
        "eu-west-1": "IE",           # Ireland
        "eu-west-2": "GB",           # United Kingdom
        "eu-west-3": "FR",           # France
        "eu-north-1": "SE",          # Sweden
        "us-east-1": "US-NE-ISO",    # US East
        "us-west-2": "US-NW-PACW",   # US West
    }

    # AWS Pricing Region Mappings
    PRICING_REGION_MAPPINGS: Dict[str, str] = {
        "eu-central-1": "EU (Frankfurt)",
        "eu-west-1": "EU (Ireland)",
        "us-east-1": "US East (N. Virginia)",
        "us-west-2": "US West (Oregon)"
    }

    # Default Configuration
    DEFAULT_AWS_PROFILE: str = "carbon-finops-sandbox"
    DEFAULT_REGION: str = "eu-central-1"

    # CloudWatch Configuration
    CLOUDWATCH_METRIC_PERIOD: int = 3600         # 1-hour periods for CPU metrics


# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

class ValidationConstants:
    """Data validation and accuracy assessment constants"""

    # Validation Factor Ranges (for cost validation)
    EXCELLENT_VALIDATION_MIN: float = 0.8        # ±20% = excellent
    EXCELLENT_VALIDATION_MAX: float = 1.2

    GOOD_VALIDATION_MIN: float = 0.6              # ±40% = good
    GOOD_VALIDATION_MAX: float = 1.4

    # Enhanced Accuracy Ranges (for mixed workloads)
    ENHANCED_EXCELLENT_MIN: float = 0.7           # ±30% for mixed workloads
    ENHANCED_EXCELLENT_MAX: float = 1.3

    ENHANCED_GOOD_MIN: float = 0.5                # ±50% acceptable for mixed
    ENHANCED_GOOD_MAX: float = 1.5

    # State-based Accuracy Expectations
    MOSTLY_RUNNING_THRESHOLD: float = 0.8         # >80% running instances
    MIXED_STATE_THRESHOLD: float = 0.3            # 30-80% running instances

    # Minimum Valid Values
    MIN_VALID_RUNTIME_HOURS: float = 0.5          # Minimum 0.5h for any launched instance
    MIN_POWER_CONSUMPTION: float = 0.1            # Minimum 0.1W power draw

    # Academic Integrity Constants
    MODEL_UNCERTAINTY: str = "±15%"               # Documented uncertainty range
    NO_FALLBACK_POLICY: str = "NO-FALLBACK"      # Academic policy


# =============================================================================
# OPTIMIZATION FACTORS
# =============================================================================

class OptimizationConstants:
    """Runtime optimization and scaling factors"""

    # Conservative Runtime Estimates (when CloudTrail unavailable)
    NANO_MICRO_BASE_FACTOR: float = 0.6          # Small instances factor
    LARGE_XLARGE_BASE_FACTOR: float = 0.3        # Large instances factor
    MEDIUM_DEFAULT_BASE_FACTOR: float = 0.4      # Medium instances factor

    # State-based Adjustments
    RUNNING_STATE_FACTOR: float = 0.8            # Running instances adjustment
    STOPPED_STATE_FACTOR: float = 0.4            # Stopped instances adjustment
    UNKNOWN_STATE_FACTOR: float = 0.2            # Unknown states adjustment

    # Power Scaling (Simple Linear Model)
    BASE_POWER_MULTIPLIER: float = 1.0           # Base power factor
    CPU_UTILIZATION_SCALING: float = 100.0       # CPU % to decimal conversion
    POWER_MIN_MAX_FACTOR: float = 0.8            # Min power = 80% of avg
    POWER_MAX_FACTOR: float = 1.2                # Max power = 120% of avg


# =============================================================================
# ERROR HANDLING CONSTANTS
# =============================================================================

class ErrorConstants:
    """Error messages and handling configuration"""

    # AWS SSO Error Messages
    AWS_SSO_EXPIRED_MSG: str = "AWS SSO token expired - run 'aws sso login' to re-authenticate"
    AWS_SSO_FIX_MSG: str = "💡 Fix: aws sso login --profile carbon-finops-sandbox"

    # API Error Messages
    API_KEY_MISSING_MSG: str = "API key not configured - check environment variables"
    API_TIMEOUT_MSG: str = "API request timed out - check network connectivity"

    # Cache Operation Messages
    CACHE_READ_FAILED_MSG: str = "Cache read failed (non-critical) - using fresh API call"
    CACHE_WRITE_FAILED_MSG: str = "Cache write failed (non-critical) - data still available"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_scenario_factor(scenario_name: str) -> float:
    """Get optimization scenario factor by name"""
    scenarios = {
        "conservative": AcademicConstants.CONSERVATIVE_SCENARIO_FACTOR,
        "moderate": AcademicConstants.MODERATE_SCENARIO_FACTOR,
        "selected": AcademicConstants.SELECTED_SCENARIO_FACTOR
    }
    return scenarios.get(scenario_name.lower(), 0.0)


def get_grid_status_threshold(status_name: str) -> int:
    """Get carbon intensity threshold by status name"""
    thresholds = {
        "optimal": CarbonConstants.OPTIMAL_THRESHOLD,
        "moderate": CarbonConstants.MODERATE_THRESHOLD,
        "high": CarbonConstants.HIGH_CARBON_THRESHOLD
    }
    return thresholds.get(status_name.lower(), CarbonConstants.MODERATE_THRESHOLD)


def get_cache_ttl(cache_type: str) -> int:
    """Get cache TTL by data type"""
    ttls = {
        "carbon": APIConstants.CARBON_DATA_TTL,
        "carbon_24h": APIConstants.CARBON_24H_TTL,
        "power": APIConstants.POWER_DATA_TTL,
        "pricing": APIConstants.PRICING_DATA_TTL,
        "cost": APIConstants.COST_DATA_TTL,
        "cpu": APIConstants.CPU_UTILIZATION_TTL,
        "cloudtrail": APIConstants.CLOUDTRAIL_EVENTS_TTL
    }
    return ttls.get(cache_type.lower(), APIConstants.CARBON_DATA_TTL)


# =============================================================================
# EXPORT ALL CONSTANTS
# =============================================================================

__all__ = [
    'AcademicConstants',
    'CarbonConstants',
    'APIConstants',
    'UIConstants',
    'AWSConstants',
    'ValidationConstants',
    'OptimizationConstants',
    'ErrorConstants',
    'get_scenario_factor',
    'get_grid_status_threshold',
    'get_cache_ttl'
]
