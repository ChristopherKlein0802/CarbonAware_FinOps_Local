"""
Health Monitoring for Carbon-Aware FinOps Dashboard
Pragmatic Professional Implementation - Clean system monitoring

Simple, effective health checks for all external services
No overengineering - focused on Bachelor thesis needs
"""

import logging
import time
import requests
from datetime import datetime
from typing import Dict, Any

from ...api.client import unified_api_client
from ...models.dashboard import APIHealthStatus

logger = logging.getLogger(__name__)

class HealthMonitor:
    """
    Professional Health Monitoring Controller

    Responsibilities:
    - Monitor external API availability
    - Track performance metrics
    - Provide health status for dashboard
    - Maintain academic transparency
    """

    def __init__(self):
        """Initialize health monitor"""
        logger.info("✅ Health Monitor initialized")

    def check_all_apis(self) -> Dict[str, APIHealthStatus]:
        """
        Comprehensive health check for all external APIs

        Returns:
            Dict: Complete health status for all services
        """
        logger.info("🔍 Starting API health checks...")

        health_results = {}

        # Check ElectricityMap API
        health_results["electricitymap"] = self._check_electricitymap_health()

        # Check Boavizta API
        health_results["boavizta"] = self._check_boavizta_health()

        # Check AWS Cost Explorer API
        health_results["aws_cost_explorer"] = self._check_aws_health()

        logger.info("✅ API health check completed")
        return health_results

    def _check_electricitymap_health(self) -> APIHealthStatus:
        """Check ElectricityMap API health and performance"""
        start_time = time.time()

        try:
            # Test API connection
            carbon_data = unified_api_client.get_current_carbon_intensity("eu-central-1")
            response_time = (time.time() - start_time) * 1000

            if carbon_data and carbon_data.value > 0:
                logger.info(f"✅ ElectricityMap API: Healthy ({response_time:.1f}ms)")
                return APIHealthStatus(
                    service="ElectricityMap API",
                    status="healthy",
                    response_time_ms=round(response_time, 2),
                    last_check=datetime.now(),
                    healthy=True
                )
            else:
                logger.warning("⚠️ ElectricityMap API: No valid data")
                return APIHealthStatus(
                    service="ElectricityMap API",
                    status="degraded",
                    response_time_ms=round(response_time, 2),
                    last_check=datetime.now(),
                    error_message="No valid carbon data received",
                    healthy=False
                )

        except (ConnectionError, TimeoutError, requests.exceptions.RequestException) as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"❌ ElectricityMap API network error: {e}")
            return APIHealthStatus(
                service="ElectricityMap API",
                status="error",
                response_time_ms=round(response_time, 2),
                last_check=datetime.now(),
                error_message=f"Network error: {str(e)}",
                healthy=False
            )
        except (RuntimeError, ValueError, TypeError) as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"❌ ElectricityMap API runtime/validation error: {e}")
            return APIHealthStatus(
                service="ElectricityMap API",
                status="error",
                response_time_ms=round(response_time, 2),
                last_check=datetime.now(),
                error_message=f"Unexpected error: {str(e)}",
                healthy=False
            )

    def _check_boavizta_health(self) -> APIHealthStatus:
        """Check Boavizta API health and performance"""
        start_time = time.time()

        try:
            # Test API with standard instance type
            power_data = unified_api_client.get_power_consumption("t3.medium")
            response_time = (time.time() - start_time) * 1000

            if power_data and power_data.avg_power_watts > 0:
                logger.info(f"✅ Boavizta API: Healthy ({response_time:.1f}ms)")
                return APIHealthStatus(
                    service="Boavizta API",
                    status="healthy",
                    response_time_ms=round(response_time, 2),
                    last_check=datetime.now(),
                    healthy=True
                )
            else:
                logger.warning("⚠️ Boavizta API: No valid data")
                return APIHealthStatus(
                    service="Boavizta API",
                    status="degraded",
                    response_time_ms=round(response_time, 2),
                    last_check=datetime.now(),
                    error_message="No valid power data received",
                    healthy=False
                )

        except (ConnectionError, TimeoutError, requests.exceptions.RequestException) as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Boavizta API network error: {e}")
            return APIHealthStatus(
                service="Boavizta API",
                status="error",
                response_time_ms=round(response_time, 2),
                last_check=datetime.now(),
                error_message=f"Network error: {str(e)}",
                healthy=False
            )
        except (RuntimeError, ValueError, TypeError) as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Boavizta API runtime/validation error: {e}")
            return APIHealthStatus(
                service="Boavizta API",
                status="error",
                response_time_ms=round(response_time, 2),
                last_check=datetime.now(),
                error_message=f"Unexpected error: {str(e)}",
                healthy=False
            )

    def _check_aws_health(self) -> APIHealthStatus:
        """Check AWS Cost Explorer health and connectivity"""
        start_time = time.time()

        try:
            # Test AWS connectivity
            cost_data = unified_api_client.get_monthly_costs()
            response_time = (time.time() - start_time) * 1000

            if cost_data and cost_data.monthly_cost_usd >= 0:
                logger.info(f"✅ AWS Cost Explorer: Healthy ({response_time:.1f}ms)")
                return APIHealthStatus(
                    service="AWS Cost Explorer API",
                    status="healthy",
                    response_time_ms=round(response_time, 2),
                    last_check=datetime.now(),
                    healthy=True
                )
            else:
                logger.warning("⚠️ AWS Cost Explorer: No valid data")
                return APIHealthStatus(
                    service="AWS Cost Explorer API",
                    status="degraded",
                    response_time_ms=round(response_time, 2),
                    last_check=datetime.now(),
                    error_message="No valid cost data received",
                    healthy=False
                )

        except (ConnectionError, TimeoutError) as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"❌ AWS Cost Explorer network error: {e}")
            return APIHealthStatus(
                service="AWS Cost Explorer API",
                status="error",
                response_time_ms=round(response_time, 2),
                last_check=datetime.now(),
                error_message=f"AWS network error: {str(e)}",
                healthy=False
            )
        except (RuntimeError, ValueError, TypeError) as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"❌ AWS Cost Explorer runtime/validation error: {e}")
            return APIHealthStatus(
                service="AWS Cost Explorer API",
                status="error",
                response_time_ms=round(response_time, 2),
                last_check=datetime.now(),
                error_message=f"Unexpected error: {str(e)}",
                healthy=False
            )

    def get_overall_health(self, health_results: Dict[str, APIHealthStatus]) -> Dict[str, Any]:
        """Generate overall system health assessment"""
        services = ["electricitymap", "boavizta", "aws_cost_explorer"]

        healthy_count = 0
        degraded_count = 0
        error_count = 0

        for service in services:
            service_result = health_results.get(service)
            if service_result and service_result.healthy:
                healthy_count += 1
            elif service_result and service_result.status == "degraded":
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
            "last_check": datetime.now(),
            "dashboard_ready": overall_status in ["healthy", "degraded"],
            "all_healthy": healthy_count == len(services)
        }

    def get_health_summary(self) -> str:
        """Get human-readable health summary"""
        health_results = self.check_all_apis()
        overall = self.get_overall_health(health_results)

        summary = f"🏥 API Health Status: {overall['overall_status'].upper()}\\n"
        summary += f"✅ Healthy: {overall['services_healthy']}/{overall['total_services']}\\n"

        if overall['services_degraded'] > 0:
            summary += f"⚠️ Degraded: {overall['services_degraded']}\\n"
        if overall['services_error'] > 0:
            summary += f"❌ Errors: {overall['services_error']}\\n"

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
            overall = self.get_overall_health(results)
            return overall["dashboard_ready"]
        except (RuntimeError, ValueError, AttributeError) as e:
            logger.error(f"Quick health check failed: {e}")
            return False

# Global instance
health_check_manager = HealthMonitor()