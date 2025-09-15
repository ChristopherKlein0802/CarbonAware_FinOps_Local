"""
API Health Check Module - Carbon-Aware FinOps Dashboard
Bachelor Thesis Project

Provides health monitoring for all external APIs:
- ElectricityMap API (German grid data)
- Boavizta API (hardware power consumption)
- AWS Cost Explorer API (billing data)

All checks designed for academic transparency and production readiness.
"""

import logging
import time
from typing import Dict, Optional, Tuple
from datetime import datetime
import requests
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class HealthCheckManager:
    """Comprehensive API health monitoring for all dashboard services."""

    def __init__(self):
        """Initialize health check manager with API clients."""
        self.electricitymap_api_key = os.getenv("ELECTRICITYMAP_API_KEY")
        self.aws_profile = os.getenv("AWS_PROFILE", "carbon-finops-sandbox")
        self.aws_region = os.getenv("AWS_REGION", "eu-central-1")

        # API endpoints
        self.endpoints = {
            "electricitymap": "https://api-access.electricitymaps.com/v3/carbon-intensity/latest",
            "boavizta": "https://api.boavizta.org/v1/cloud/instance",
            "aws_cost_explorer": None,  # Uses boto3 client, not HTTP endpoint
        }

    def check_all_apis(self) -> Dict[str, Dict[str, any]]:
        """
        Run comprehensive health checks on all APIs.
        
        Returns:
            Dict with health status for each API service
        """
        logger.info("🔍 Starting comprehensive API health checks...")
        
        health_results = {}
        
        # Check ElectricityMap API
        health_results["electricitymap"] = self._check_electricitymap_api()
        
        # Check Boavizta API
        health_results["boavizta"] = self._check_boavizta_api()
        
        # Check AWS Cost Explorer API
        health_results["aws_cost_explorer"] = self._check_aws_cost_explorer()
        
        # Generate overall system health
        health_results["system_overall"] = self._generate_overall_health(health_results)
        
        logger.info("✅ API health check completed")
        return health_results

    def _check_electricitymap_api(self) -> Dict[str, any]:
        """Check ElectricityMap API health and connectivity."""
        start_time = time.time()
        result = {
            "service": "ElectricityMap API",
            "status": "unknown",
            "response_time_ms": 0,
            "error_message": None,
            "api_key_configured": bool(self.electricitymap_api_key),
            "last_check": datetime.now().isoformat(),
            "endpoint": self.endpoints["electricitymap"]
        }
        
        try:
            if not self.electricitymap_api_key:
                result["status"] = "error"
                result["error_message"] = "ElectricityMap API key not configured"
                logger.warning("❌ ElectricityMap API: No API key configured")
                return result

            # Test API with German zone
            headers = {"auth-token": self.electricitymap_api_key}
            params = {"zone": "DE"}
            
            response = requests.get(
                self.endpoints["electricitymap"],
                headers=headers,
                params=params,
                timeout=10
            )
            
            response_time = (time.time() - start_time) * 1000
            result["response_time_ms"] = round(response_time, 2)
            
            if response.status_code == 200:
                data = response.json()
                if "carbonIntensity" in data:
                    result["status"] = "healthy"
                    result["carbon_intensity"] = data["carbonIntensity"]
                    logger.info(f"✅ ElectricityMap API: Healthy ({response_time:.1f}ms)")
                else:
                    result["status"] = "degraded"
                    result["error_message"] = "Response missing expected data structure"
                    logger.warning("⚠️ ElectricityMap API: Response structure issue")
            else:
                result["status"] = "error"
                result["error_message"] = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ ElectricityMap API: HTTP {response.status_code}")
                
        except requests.RequestException as e:
            result["status"] = "error"
            result["error_message"] = f"Network error: {str(e)}"
            result["response_time_ms"] = (time.time() - start_time) * 1000
            logger.error(f"❌ ElectricityMap API: Network error - {e}")
        except Exception as e:
            result["status"] = "error"
            result["error_message"] = f"Unexpected error: {str(e)}"
            logger.error(f"❌ ElectricityMap API: Unexpected error - {e}")
            
        return result

    def _check_boavizta_api(self) -> Dict[str, any]:
        """Check Boavizta API health and connectivity."""
        start_time = time.time()
        result = {
            "service": "Boavizta API",
            "status": "unknown",
            "response_time_ms": 0,
            "error_message": None,
            "api_key_configured": True,  # Boavizta is public API
            "last_check": datetime.now().isoformat(),
            "endpoint": self.endpoints["boavizta"]
        }
        
        try:
            # Test with simple instance type query
            test_payload = {
                "provider": "aws",
                "instance_type": "m5.large"
            }
            
            response = requests.post(
                self.endpoints["boavizta"],
                json=test_payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            response_time = (time.time() - start_time) * 1000
            result["response_time_ms"] = round(response_time, 2)
            
            if response.status_code == 200:
                data = response.json()
                if "verbose" in data and "avg_power" in data["verbose"]:
                    result["status"] = "healthy"
                    result["test_power_watts"] = data["verbose"]["avg_power"]["value"]
                    logger.info(f"✅ Boavizta API: Healthy ({response_time:.1f}ms)")
                else:
                    result["status"] = "degraded"
                    result["error_message"] = "Response missing expected power data"
                    logger.warning("⚠️ Boavizta API: Response structure issue")
            else:
                result["status"] = "error"
                result["error_message"] = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Boavizta API: HTTP {response.status_code}")
                
        except requests.RequestException as e:
            result["status"] = "error"
            result["error_message"] = f"Network error: {str(e)}"
            result["response_time_ms"] = (time.time() - start_time) * 1000
            logger.error(f"❌ Boavizta API: Network error - {e}")
        except Exception as e:
            result["status"] = "error"
            result["error_message"] = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Boavizta API: Unexpected error - {e}")
            
        return result

    def _check_aws_cost_explorer(self) -> Dict[str, any]:
        """Check AWS Cost Explorer API connectivity and permissions."""
        start_time = time.time()
        result = {
            "service": "AWS Cost Explorer API",
            "status": "unknown",
            "response_time_ms": 0,
            "error_message": None,
            "aws_profile_configured": bool(self.aws_profile),
            "last_check": datetime.now().isoformat(),
            "aws_region": self.aws_region
        }
        
        try:
            # Initialize boto3 session with profile
            if self.aws_profile:
                session = boto3.Session(profile_name=self.aws_profile)
            else:
                session = boto3.Session()
                
            ce_client = session.client('ce', region_name=self.aws_region)
            
            # Test with simple cost query (last 7 days)
            from datetime import timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            response_time = (time.time() - start_time) * 1000
            result["response_time_ms"] = round(response_time, 2)
            
            if 'ResultsByTime' in response:
                result["status"] = "healthy"
                result["cost_data_available"] = len(response['ResultsByTime']) > 0
                logger.info(f"✅ AWS Cost Explorer: Healthy ({response_time:.1f}ms)")
            else:
                result["status"] = "degraded"
                result["error_message"] = "Response missing expected cost data structure"
                logger.warning("⚠️ AWS Cost Explorer: Response structure issue")
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            result["status"] = "error"
            result["error_message"] = f"AWS Error {error_code}: {str(e)}"
            result["response_time_ms"] = (time.time() - start_time) * 1000
            logger.error(f"❌ AWS Cost Explorer: ClientError {error_code} - {e}")
        except BotoCoreError as e:
            result["status"] = "error"
            result["error_message"] = f"AWS SDK error: {str(e)}"
            result["response_time_ms"] = (time.time() - start_time) * 1000
            logger.error(f"❌ AWS Cost Explorer: BotoCoreError - {e}")
        except Exception as e:
            result["status"] = "error"
            result["error_message"] = f"Unexpected error: {str(e)}"
            logger.error(f"❌ AWS Cost Explorer: Unexpected error - {e}")
            
        return result

    def _generate_overall_health(self, health_results: Dict[str, Dict]) -> Dict[str, any]:
        """Generate overall system health assessment."""
        services = ["electricitymap", "boavizta", "aws_cost_explorer"]
        
        healthy_count = 0
        degraded_count = 0
        error_count = 0
        
        for service in services:
            status = health_results.get(service, {}).get("status", "error")
            if status == "healthy":
                healthy_count += 1
            elif status == "degraded":
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
            "dashboard_ready": overall_status in ["healthy", "degraded"]
        }

    def get_health_summary(self) -> str:
        """Get a human-readable health summary."""
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


# Create global instance for easy importing
health_check_manager = HealthCheckManager()


def quick_health_check() -> bool:
    """
    Quick health check that returns True if dashboard can operate.
    
    Returns:
        bool: True if at least basic functionality is available
    """
    try:
        results = health_check_manager.check_all_apis()
        return results["system_overall"]["dashboard_ready"]
    except Exception as e:
        logger.error(f"Quick health check failed: {e}")
        return False


if __name__ == "__main__":
    # CLI health check for debugging
    print("🔍 Running API Health Check...")
    print(health_check_manager.get_health_summary())