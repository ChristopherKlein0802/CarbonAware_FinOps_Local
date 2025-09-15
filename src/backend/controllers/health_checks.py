"""
API Health Check Controller - Professional MVC Implementation
Backend Controller responsible for monitoring external API health

Architecture:
- Clean separation from services layer
- Professional health monitoring patterns
- Academic transparency with no fallback data
- Production-ready error handling
"""

import logging
import time
from typing import Dict, Optional
from datetime import datetime

# Import from services layer (clean architecture)
from ..services.api_clients.unified_api_client import UnifiedAPIClient

logger = logging.getLogger(__name__)


class HealthCheckController:
    """
    Professional MVC Controller for API Health Monitoring

    Responsibilities:
    - Monitor external API availability
    - Track performance metrics
    - Provide health status for dashboard
    - Maintain academic transparency (no fallback data)
    """

    def __init__(self):
        """Initialize health check controller"""
        self.api_client = UnifiedAPIClient()
        logger.info("✅ Health Check Controller initialized")

    def check_all_apis(self) -> Dict[str, Dict[str, any]]:
        """
        Comprehensive health check for all external APIs

        Returns:
            Dict: Complete health status for all services
        """
        logger.info("🔍 Starting comprehensive API health checks...")

        health_results = {}

        # Check ElectricityMap API
        health_results["electricitymap"] = self._check_electricitymap_health()

        # Check Boavizta API
        health_results["boavizta"] = self._check_boavizta_health()

        # Check AWS Cost Explorer API
        health_results["aws_cost_explorer"] = self._check_aws_health()

        # Generate overall system health
        health_results["system_overall"] = self._generate_overall_health(health_results)

        logger.info("✅ API health check completed")
        return health_results

    def _check_electricitymap_health(self) -> Dict[str, any]:
        """Check ElectricityMap API health and performance"""
        start_time = time.time()
        result = {
            "service": "ElectricityMap API",
            "status": "unknown",
            "response_time_ms": 0,
            "error_message": None,
            "last_check": datetime.now().isoformat(),
            "healthy": False
        }

        try:
            # Test API connection
            carbon_data = self.api_client.get_current_carbon_intensity("eu-central-1")
            response_time = (time.time() - start_time) * 1000

            result["response_time_ms"] = round(response_time, 2)

            if carbon_data and carbon_data.value > 0:
                result["status"] = "healthy"
                result["healthy"] = True
                result["carbon_intensity"] = carbon_data.value
                logger.info(f"✅ ElectricityMap API: Healthy ({response_time:.1f}ms)")
            else:
                result["status"] = "degraded"
                result["error_message"] = "No valid carbon data received"
                logger.warning("⚠️ ElectricityMap API: No valid data")

        except Exception as e:
            result["status"] = "error"
            result["error_message"] = str(e)
            result["response_time_ms"] = (time.time() - start_time) * 1000
            logger.error(f"❌ ElectricityMap API: {e}")

        return result

    def _check_boavizta_health(self) -> Dict[str, any]:
        """Check Boavizta API health and performance"""
        start_time = time.time()
        result = {
            "service": "Boavizta API",
            "status": "unknown",
            "response_time_ms": 0,
            "error_message": None,
            "last_check": datetime.now().isoformat(),
            "healthy": False
        }

        try:
            # Test API with standard instance type
            power_data = self.api_client.get_power_consumption("t3.medium")
            response_time = (time.time() - start_time) * 1000

            result["response_time_ms"] = round(response_time, 2)

            if power_data and power_data.avg_power_watts > 0:
                result["status"] = "healthy"
                result["healthy"] = True
                result["test_power_watts"] = power_data.avg_power_watts
                logger.info(f"✅ Boavizta API: Healthy ({response_time:.1f}ms)")
            else:
                result["status"] = "degraded"
                result["error_message"] = "No valid power data received"
                logger.warning("⚠️ Boavizta API: No valid data")

        except Exception as e:
            result["status"] = "error"
            result["error_message"] = str(e)
            result["response_time_ms"] = (time.time() - start_time) * 1000
            logger.error(f"❌ Boavizta API: {e}")

        return result

    def _check_aws_health(self) -> Dict[str, any]:
        """Check AWS Cost Explorer health and connectivity"""
        start_time = time.time()
        result = {
            "service": "AWS Cost Explorer API",
            "status": "unknown",
            "response_time_ms": 0,
            "error_message": None,
            "last_check": datetime.now().isoformat(),
            "healthy": False
        }

        try:
            # Test AWS connectivity
            cost_data = self.api_client.get_monthly_costs()
            response_time = (time.time() - start_time) * 1000

            result["response_time_ms"] = round(response_time, 2)

            if cost_data and cost_data.monthly_cost_usd >= 0:
                result["status"] = "healthy"
                result["healthy"] = True
                result["cost_data_available"] = True
                logger.info(f"✅ AWS Cost Explorer: Healthy ({response_time:.1f}ms)")
            else:
                result["status"] = "degraded"
                result["error_message"] = "No valid cost data received"
                logger.warning("⚠️ AWS Cost Explorer: No valid data")

        except Exception as e:
            result["status"] = "error"
            result["error_message"] = str(e)
            result["response_time_ms"] = (time.time() - start_time) * 1000
            logger.error(f"❌ AWS Cost Explorer: {e}")

        return result

    def _generate_overall_health(self, health_results: Dict[str, Dict]) -> Dict[str, any]:
        """Generate overall system health assessment"""
        services = ["electricitymap", "boavizta", "aws_cost_explorer"]

        healthy_count = 0
        degraded_count = 0
        error_count = 0

        for service in services:
            service_result = health_results.get(service, {})
            if service_result.get("healthy", False):
                healthy_count += 1
            elif service_result.get("status") == "degraded":
                degraded_count += 1
            else:
                error_count += 1

        # Determine overall status
        if error_count == 0 and degraded_count == 0:
            overall_status = "healthy"
        elif error_count == 0:
            overall_status = "degraded"
        else:
            overall_status = "error"

        return {
            "overall_status": overall_status,
            "services_healthy": healthy_count,
            "services_degraded": degraded_count,
            "services_error": error_count,
            "total_services": len(services),
            "last_check": datetime.now().isoformat(),
            "dashboard_ready": overall_status in ["healthy", "degraded"],
            "all_healthy": healthy_count == len(services)
        }

    def get_health_summary(self) -> str:
        """Get human-readable health summary"""
        health_results = self.check_all_apis()
        overall = health_results["system_overall"]

        summary = f"🏥 API Health Status: {overall['overall_status'].upper()}\n"
        summary += f"✅ Healthy: {overall['services_healthy']}/{overall['total_services']}\n"

        if overall['services_degraded'] > 0:
            summary += f"⚠️ Degraded: {overall['services_degraded']}\n"
        if overall['services_error'] > 0:
            summary += f"❌ Errors: {overall['services_error']}\n"

        summary += f"Dashboard Ready: {'✅' if overall['dashboard_ready'] else '❌'}"

        return summary

    def quick_health_check(self) -> bool:
        """
        Quick health check for startup validation

        Returns:
            bool: True if dashboard can operate with current API status
        """
        try:
            results = self.check_all_apis()
            return results["system_overall"]["dashboard_ready"]
        except Exception as e:
            logger.error(f"Quick health check failed: {e}")
            return False


# Global instance for application use
health_check_manager = HealthCheckController()