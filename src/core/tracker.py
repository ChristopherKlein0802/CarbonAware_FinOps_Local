"""Runtime tracking and AWS data collection utilities."""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from ..models.aws import EC2Instance
from ..utils.cache import CacheTTL, ensure_cache_dir, get_standard_cache_path, is_cache_valid
from ..constants import AcademicConstants

logger = logging.getLogger(__name__)


class RuntimeTracker:
    """Tracker for precise runtime calculation using CloudTrail"""

    def __init__(self):
        """Initialize runtime tracker"""
        logger.info("✅ Runtime Tracker initialized")

    def get_all_ec2_instances(self) -> List[Dict]:
        """Get all AWS EC2 instances in eu-central-1"""
        try:
            # Initialize AWS session
            session = boto3.Session(profile_name=os.getenv("AWS_PROFILE", "carbon-finops-sandbox"))
            ec2_client = session.client("ec2", region_name="eu-central-1")

            response = ec2_client.describe_instances(
                Filters=[
                    {"Name": "instance-state-name", "Values": ["running", "stopped"]}
                ]
            )

            instances = []
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    # Extract instance name from tags
                    instance_name = "Unnamed"
                    for tag in instance.get("Tags", []):
                        if tag["Key"] == "Name":
                            instance_name = tag["Value"]
                            break

                    instances.append({
                        "instance_id": instance["InstanceId"],
                        "instance_type": instance["InstanceType"],
                        "state": instance["State"]["Name"],
                        "region": "eu-central-1",
                        "instance_name": instance_name,
                        "launch_time": instance.get("LaunchTime"),
                        "state_transition_reason": instance.get("StateTransitionReason", "")
                    })

            logger.info(f"✅ Found {len(instances)} instances in eu-central-1")
            return instances

        except Exception as e:
            logger.error(f"❌ AWS EC2 collection error: {e}")
            return []

    def get_precise_runtime_hours(self, instance: Dict) -> Optional[float]:
        """Calculate runtime hours from CloudTrail start/stop events."""
        instance_id = instance["instance_id"]
        region = instance.get("region", "eu-central-1")

        cache_identifier = f"{instance_id}_{region}"
        cache_path = get_standard_cache_path("cloudtrail_runtime", cache_identifier)
        ensure_cache_dir(cache_path)

        if is_cache_valid(cache_path, CacheTTL.CLOUDTRAIL_EVENTS):
            try:
                with open(cache_path, "r", encoding="utf-8") as cache_file:
                    cached_payload = json.load(cache_file)
                runtime_hours = cached_payload.get("runtime_hours")
                if runtime_hours is not None:
                    logger.debug(
                        "Using cached CloudTrail runtime for %s (%.2f h)",
                        instance_id,
                        runtime_hours,
                    )
                    return runtime_hours
            except (OSError, ValueError, KeyError) as cache_error:
                logger.warning(
                    "CloudTrail runtime cache invalid for %s: %s",
                    instance_id,
                    cache_error,
                )

        try:
            session = boto3.Session(
                profile_name=os.getenv("AWS_PROFILE", "carbon-finops-sandbox")
            )
            cloudtrail = session.client("cloudtrail", region_name=region)

            start_time = datetime.now(timezone.utc) - timedelta(days=30)
            end_time = datetime.now(timezone.utc)

            lookup_params = {
                "LookupAttributes": [
                    {
                        "AttributeKey": "ResourceName",
                        "AttributeValue": instance_id,
                    }
                ],
                "StartTime": start_time,
                "EndTime": end_time,
            }

            events: List[Dict] = []
            paginator = cloudtrail.get_paginator("lookup_events")
            for page in paginator.paginate(**lookup_params):
                events.extend(page.get("Events", []))

            relevant_events = self._extract_relevant_events(events, instance_id)
            if not relevant_events:
                logger.warning(
                    "No CloudTrail state change events for %s in last 30 days", instance_id
                )
                return None

            runtime_hours = self._calculate_runtime_from_events(
                relevant_events, end_time
            )

            try:
                payload = {
                    "runtime_hours": runtime_hours,
                    "event_count": len(relevant_events),
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                }
                with open(cache_path, "w", encoding="utf-8") as cache_file:
                    json.dump(payload, cache_file)
            except OSError as cache_error:
                logger.warning(
                    "Failed to cache CloudTrail runtime for %s: %s",
                    instance_id,
                    cache_error,
                )

            logger.info(
                "CloudTrail runtime calculated for %s: %.2f h from %d events",
                instance_id,
                runtime_hours,
                len(relevant_events),
            )
            return runtime_hours

        except ClientError as aws_error:
            logger.error("CloudTrail client error for %s: %s", instance_id, aws_error)
            return None
        except Exception as error:  # pragma: no cover - safeguard for unexpected issues
            logger.error("Runtime calculation error for %s: %s", instance_id, error)
            return None

    def _extract_relevant_events(
        self, events: List[Dict], instance_id: str
    ) -> List[Dict]:
        """Filter CloudTrail events to those marking instance lifecycle changes."""
        start_events = {"RunInstances", "StartInstances"}
        stop_events = {"StopInstances", "TerminateInstances"}
        relevant: List[Dict] = []

        for event in events:
            event_name = event.get("EventName")
            event_time = event.get("EventTime")
            if event_name not in start_events | stop_events:
                continue
            if event_time is None:
                continue

            resources = event.get("Resources", []) or []
            if not any(r.get("ResourceName") == instance_id for r in resources):
                continue

            relevant.append({"name": event_name, "time": event_time})

        relevant.sort(key=lambda entry: entry["time"])
        return relevant

    def _calculate_runtime_from_events(
        self, events: List[Dict], end_time: datetime
    ) -> float:
        """Accumulate runtime hours from ordered CloudTrail events."""
        session_start: Optional[datetime] = None
        runtime_hours = 0.0
        start_events = {"RunInstances", "StartInstances"}
        stop_events = {"StopInstances", "TerminateInstances"}

        for event in events:
            event_time = event["time"]
            event_name = event["name"]

            if event_name in start_events:
                session_start = event_time
            elif event_name in stop_events and session_start is not None:
                runtime_hours += (event_time - session_start).total_seconds() / 3600.0
                session_start = None

        if session_start is not None:
            runtime_hours += (end_time - session_start).total_seconds() / 3600.0

        return round(runtime_hours, 2)

    def get_cpu_utilization(self, instance_id: str) -> Optional[float]:
        """Get average CPU utilization from CloudWatch with 3-hour caching"""
        # Use persistent cache directory like other APIs
        cache_path = get_standard_cache_path("cpu_utilization", instance_id)
        ensure_cache_dir(cache_path)

        # Check cache first (3 hours for CPU data - cost optimization)
        if is_cache_valid(cache_path, CacheTTL.CPU_UTILIZATION):
            try:
                import json
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                return cached_data["cpu_utilization"]
            except (FileNotFoundError, PermissionError, json.JSONDecodeError) as e:
                logger.warning(f"⚠️ CPU cache read failed: {e}")

        try:
            import os
            session = boto3.Session(profile_name=os.getenv("AWS_PROFILE", "carbon-finops-sandbox"))
            cloudwatch = session.client("cloudwatch", region_name="eu-central-1")

            # Use modern get_metric_data API
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)

            response = cloudwatch.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'cpu_utilization',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/EC2',
                                'MetricName': 'CPUUtilization',
                                'Dimensions': [
                                    {
                                        'Name': 'InstanceId',
                                        'Value': instance_id
                                    }
                                ]
                            },
                            'Period': 3600,  # 1-hour periods
                            'Stat': 'Average'
                        },
                        'ReturnData': True
                    }
                ],
                StartTime=start_time,
                EndTime=end_time
            )

            if response['MetricDataResults'][0]['Values']:
                values = response['MetricDataResults'][0]['Values']
                avg_cpu = sum(values) / len(values)

                # Cache the result
                try:
                    import json
                    cache_data = {
                        "cpu_utilization": avg_cpu,
                        "instance_id": instance_id,
                        "timestamp": datetime.now().isoformat(),
                        "source": "CloudWatch_get_metric_data"
                    }
                    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                    with open(cache_path, "w") as f:
                        json.dump(cache_data, f)
                    logger.info(f"✅ CPU Utilization {instance_id}: {avg_cpu:.1f}% (cached 1h)")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cache CPU data: {e}")

                return avg_cpu
            else:
                logger.error(f"❌ No CPU data available for {instance_id} - NO-FALLBACK policy enforced")
                return None  # NO-FALLBACK: Return None instead of synthetic data

        except Exception as e:
            logger.warning(f"⚠️ CloudWatch CPU query error for {instance_id}: {e}")
            return None  # NO-FALLBACK: No synthetic data

    def process_instance_enhanced(self, instance: Dict, carbon_intensity: float) -> Optional[EC2Instance]:
        """Enhanced instance processing with runtime tracking and CPU utilization"""
        try:
            from ..api.client import unified_api_client
            from ..utils.calculations import safe_round, calculate_simple_power_consumption

            # Get power consumption from Boavizta (24h cache)
            power_data = unified_api_client.get_power_consumption(instance["instance_type"])
            avg_power_watts = power_data.avg_power_watts if power_data else None

            # Get real AWS pricing from Pricing API
            hourly_price_usd = unified_api_client.get_instance_pricing(instance["instance_type"], instance["region"])

            # Get actual runtime hours
            actual_runtime_hours = self.get_precise_runtime_hours(instance)

            # Get CPU utilization for power calculation
            cpu_utilization = self.get_cpu_utilization(instance["instance_id"])

            effective_power_watts = None
            hourly_co2_g = None
            monthly_co2_kg = None
            monthly_cost_usd = None
            monthly_cost_eur = None

            if avg_power_watts is not None and cpu_utilization is not None:
                effective_power_watts = calculate_simple_power_consumption(avg_power_watts, cpu_utilization)

            if effective_power_watts is not None and actual_runtime_hours is not None:
                from ..utils.calculations import calculate_co2_emissions
                monthly_co2_kg = calculate_co2_emissions(effective_power_watts, carbon_intensity, actual_runtime_hours)
                power_kw = effective_power_watts / 1000.0
                hourly_co2_g = power_kw * carbon_intensity

            if hourly_price_usd is not None and actual_runtime_hours is not None:
                monthly_cost_usd = hourly_price_usd * actual_runtime_hours
                monthly_cost_eur = monthly_cost_usd * AcademicConstants.EUR_USD_RATE

            # Determine confidence level and data sources
            confidence_level, data_sources = self._get_enhanced_confidence_metadata(
                has_power_data=avg_power_watts is not None,
                has_pricing_data=hourly_price_usd is not None,
                has_cpu_data=cpu_utilization is not None,
                has_runtime_data=actual_runtime_hours is not None,
            )

            # Determine data quality based on available sources
            if all([
                actual_runtime_hours is not None,
                cpu_utilization is not None,
                effective_power_watts is not None,
                monthly_cost_eur is not None
            ]):
                data_quality = "measured"
            elif any([
                actual_runtime_hours is not None,
                cpu_utilization is not None,
                effective_power_watts is not None,
                monthly_cost_eur is not None
            ]):
                data_quality = "partial"
            else:
                data_quality = "limited"

            return EC2Instance(
                instance_id=instance["instance_id"],
                instance_type=instance["instance_type"],
                state=instance["state"],
                region=instance["region"],
                instance_name=instance.get("instance_name", "Unnamed"),  # NEW: Store instance name
                power_watts=safe_round(effective_power_watts, 1),
                hourly_co2_g=safe_round(hourly_co2_g, 2),
                monthly_co2_kg=safe_round(monthly_co2_kg, 3),
                monthly_cost_usd=safe_round(monthly_cost_usd, 2),
                monthly_cost_eur=safe_round(monthly_cost_eur, 2),
                runtime_hours=safe_round(actual_runtime_hours, 1),  # NEW: Store actual runtime
                hourly_price_usd=safe_round(hourly_price_usd, 4),  # NEW: Store hourly pricing
                cpu_utilization=safe_round(cpu_utilization, 1),  # NEW: Store CPU utilization
                data_quality=data_quality,  # NEW: Store data quality assessment
                confidence_level=confidence_level,
                data_sources=data_sources,
                last_updated=datetime.now()
            )

        except Exception as e:
            logger.error(f"❌ Error processing instance {instance.get('instance_id', 'unknown')}: {e}")
            return None

    def _get_enhanced_confidence_metadata(
        self,
        *,
        has_power_data: bool,
        has_pricing_data: bool,
        has_cpu_data: bool,
        has_runtime_data: bool,
    ) -> tuple[str, List[str]]:
        """Derive confidence metadata based on the sources that contributed data."""
        data_sources: List[str] = ["aws_api"]

        if has_power_data:
            data_sources.append("boavizta")
        if has_pricing_data:
            data_sources.append("aws_pricing")
        if has_cpu_data:
            data_sources.append("cloudwatch")
        if has_runtime_data:
            data_sources.append("cloudtrail_audit")

        if len(data_sources) >= 4:
            confidence_level = "high"
        elif len(data_sources) >= 3:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        return confidence_level, data_sources
