"""Unified AWS client for all AWS SDK interactions (EC2, CloudTrail, CloudWatch, Cost Explorer, Pricing)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List

import boto3
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    SSOError,
    TokenRetrievalError,
    UnauthorizedSSOTokenError,
)

from src.config import settings
from src.domain.constants import AcademicConstants
from src.infrastructure.cache import FileCacheRepository, CacheTTL
from src.domain.models import AWSCostData
from src.domain.errors import ErrorMessages, AWSAuthenticationError

logger = logging.getLogger(__name__)

AWSAuthErrors = (UnauthorizedSSOTokenError, SSOError, NoCredentialsError, TokenRetrievalError)


class AWSSessionHelper:
    """Ensures AWS SSO sessions are active before API calls."""

    def __init__(self, profile: Optional[str]) -> None:
        self._profile = profile or settings.aws_profile
        self._script_path = Path(__file__).resolve().parents[3] / "scripts" / "ensure_aws_session.sh"

    def ensure_session(self) -> None:
        if not self._script_path.exists():
            return
        command = [str(self._script_path)]
        env = os.environ.copy()
        if self._profile:
            command.append(self._profile)
            env.setdefault("AWS_PROFILE", self._profile)
        try:
            subprocess.run(command, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            logger.debug("AWS SSO helper script missing: %s", self._script_path)
        except subprocess.CalledProcessError as error:
            raise RuntimeError("AWS SSO auto-login failed") from error

    def session(self, region: Optional[str] = None) -> boto3.Session:
        self.ensure_session()
        return boto3.Session(profile_name=self._profile, region_name=region or settings.aws_region)


class AWSClient:
    """Unified AWS client for EC2, CloudTrail, CloudWatch, Cost Explorer, and Pricing APIs."""

    def __init__(
        self,
        *,
        repository: FileCacheRepository,
        profile: Optional[str] = None,
    ) -> None:
        self._repository = repository
        self._profile = profile or settings.aws_profile
        self._session_helper = AWSSessionHelper(self._profile)
        self._region_mappings = settings.aws_region_to_zone
        self._pricing_mappings = settings.aws_pricing_region_labels

    # =========================================================================
    # EC2 Discovery
    # =========================================================================

    def list_instances(self, region: str) -> List[Dict]:
        """List running/stopped EC2 instances in the specified region."""
        try:
            session = self._session_helper.session(region)
            ec2_client = session.client("ec2", region_name=region)
            response = ec2_client.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running", "stopped"]}]
            )
        except AWSAuthErrors as auth_error:
            logger.error("🚫 AWS authentication required for EC2 discovery: %s", auth_error)
            raise AWSAuthenticationError(ErrorMessages.AWS_SSO_EXPIRED) from auth_error
        except ClientError as client_error:
            logger.error("❌ AWS EC2 client error: %s", client_error)
            raise

        instances: List[Dict] = []
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_name = next(
                    (tag["Value"] for tag in instance.get("Tags", []) if tag.get("Key") == "Name"),
                    "Unnamed",
                )
                instance_id = instance["InstanceId"]
                launch_time = instance.get("LaunchTime")

                # Cache launch time permanently (365-day TTL)
                if launch_time:
                    self._cache_launch_time(instance_id, region, launch_time)

                instances.append(
                    {
                        "instance_id": instance_id,
                        "instance_type": instance["InstanceType"],
                        "state": instance["State"]["Name"],
                        "region": region,
                        "instance_name": instance_name,
                        "launch_time": launch_time,
                        "state_transition_reason": instance.get("StateTransitionReason", ""),
                    }
                )
        return instances

    # =========================================================================
    # CloudTrail Events
    # =========================================================================

    def lookup_instance_events(
        self,
        *,
        instance_id: str,
        region: str,
        lookup_start: datetime,
        lookup_end: datetime,
    ) -> List[Dict]:
        """Lookup CloudTrail events for a specific instance."""
        session = self._session_helper.session(region)
        cloudtrail = session.client("cloudtrail", region_name=region)
        paginator = cloudtrail.get_paginator("lookup_events")
        events: List[Dict] = []
        lookup_params = {
            "LookupAttributes": [{"AttributeKey": "ResourceName", "AttributeValue": instance_id}],
            "StartTime": lookup_start,
            "EndTime": lookup_end,
        }
        for page in paginator.paginate(**lookup_params):
            events.extend(page.get("Events", []))
        return events

    # =========================================================================
    # CloudWatch Metrics
    # =========================================================================

    def fetch_cpu_metrics(
        self,
        *,
        instance_id: str,
        region: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict]:
        """Fetch CPU utilization metrics from CloudWatch."""
        session = self._session_helper.session(region)
        cloudwatch = session.client("cloudwatch", region_name=region)
        response = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    "Id": "cpu_utilization",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/EC2",
                            "MetricName": "CPUUtilization",
                            "Dimensions": [{"Name": "InstanceId", "Value": instance_id}],
                        },
                        "Period": 3600,
                        "Stat": "Average",
                    },
                    "ReturnData": True,
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
        )
        return response.get("MetricDataResults", [])

    # =========================================================================
    # Cost Explorer & Pricing APIs
    # =========================================================================

    def _pricing_client(self):
        session = self._session_helper.session()
        return session.client("pricing", region_name="us-east-1")

    def _cost_client(self):
        session = self._session_helper.session()
        return session.client("ce", region_name="us-east-1")

    def _cache_path(self, category: str, identifier: str) -> Path:
        return self._repository.path(category, identifier)

    def get_instance_pricing(self, instance_type: str, region: str) -> Optional[float]:
        cache_path = self._cache_path("pricing", f"{instance_type}_{region}")
        if self._repository.is_valid(cache_path, CacheTTL.PRICING_DATA):
            cached = self._repository.read_json(cache_path)
            if cached:
                try:
                    return float(cached["hourly_price_usd"])
                except (KeyError, ValueError, TypeError):
                    logger.debug("Invalid pricing cache for %s", instance_type)

        pricing_client = self._pricing_client()
        location = self._pricing_mappings.get(region, "EU (Frankfurt)")

        try:
            response = pricing_client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {"Type": "TERM_MATCH", "Field": "location", "Value": location},
                    {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
                    {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
                    {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
                    {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
                    {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"},
                ],
            )
        except ClientError as error:
            logger.error("❌ AWS Pricing error: %s", error)
            return None
        except RuntimeError as error:
            logger.error("❌ AWS Pricing runtime error: %s", error)
            return None

        price_list = response.get("PriceList")
        if not price_list:
            return None
        price_item = json.loads(price_list[0])
        terms = price_item.get("terms", {}).get("OnDemand", {})
        for term in terms.values():
            for price in term.get("priceDimensions", {}).values():
                if "Hrs" in price.get("unit", ""):
                    hourly = float(price.get("pricePerUnit", {}).get("USD", 0.0))
                    self._repository.write_json(
                        cache_path,
                        {
                            "hourly_price_usd": hourly,
                            "instance_type": instance_type,
                            "region": region,
                            "location": location,
                            "source": "AWS_Pricing_API",
                        },
                    )
                    return hourly
        return None

    def get_hourly_costs(self, hours: int, region: str) -> Optional[List[dict[str, float]]]:
        hours = max(1, min(hours, 336))
        cache_key = f"hourly_{region.replace('-', '_')}_{hours}"
        cache_path = self._cache_path("cost_series", cache_key)
        if self._repository.is_valid(cache_path, CacheTTL.COST_DATA):
            cached = self._repository.read_json(cache_path)
            if isinstance(cached, list):
                return cached

        cost_client = self._cost_client()
        now_utc = datetime.now(timezone.utc)
        window_start = now_utc - timedelta(hours=hours)
        start_day = window_start.date()
        end_day = now_utc.date()

        # NOTE: Region filter disabled - AWS Cost Explorer uses different region naming
        # and filters out all data when using "EU (Frankfurt)" as REGION dimension.
        # Cost Explorer returns aggregated EC2 costs across all regions, which is
        # acceptable for validation purposes (validation factor calculation).
        # Instance-specific costs are NOT available via Cost Explorer API.
        filter_payload = None

        series: List[dict[str, float]] = []
        day_cursor = start_day
        while day_cursor <= end_day:
            next_day = day_cursor + timedelta(days=1)
            start_iso = f"{day_cursor.isoformat()}T00:00:00Z"
            end_iso = f"{next_day.isoformat()}T00:00:00Z"
            try:
                request_params = {
                    "TimePeriod": {"Start": start_iso, "End": end_iso},
                    "Granularity": "HOURLY",
                    "Metrics": ["UnblendedCost"],
                    "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
                }
                if filter_payload:
                    request_params["Filter"] = filter_payload
                response = cost_client.get_cost_and_usage(**request_params)
            except ClientError as error:
                logger.error("❌ AWS Cost Explorer error: %s", error)
                return None

            for result in response.get("ResultsByTime", []):
                start_ts = result.get("TimePeriod", {}).get("Start")
                if not start_ts:
                    continue
                timestamp = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
                if timestamp < window_start:
                    continue

                # Sum up all EC2-related services for this hour (same logic as get_monthly_costs)
                hourly_ec2_cost = 0.0
                for group in result.get("Groups", []):
                    keys = group.get("Keys") or []
                    if not keys:
                        continue
                    service_name = keys[0]
                    # Filter for EC2 services only (flexible matching)
                    if "EC2" not in service_name and "Amazon Elastic Compute Cloud" not in service_name:
                        continue
                    amount = group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", "0")
                    try:
                        amount_usd = float(amount)
                    except (TypeError, ValueError):
                        amount_usd = 0.0
                    if amount_usd < 0:
                        amount_usd = 0.0
                    hourly_ec2_cost += amount_usd

                amount_eur = hourly_ec2_cost * AcademicConstants.get_eur_usd_rate()
                series.append({"timestamp": timestamp.isoformat(), "cost_eur": round(amount_eur, 6)})
                if hourly_ec2_cost > 0:
                    logger.debug(
                        f"💰 Cost hour {timestamp.strftime('%Y-%m-%d %H:%M')}: ${hourly_ec2_cost:.4f} → €{amount_eur:.4f}"
                    )
            day_cursor = next_day

        total_cost_usd = sum(entry["cost_eur"] / AcademicConstants.get_eur_usd_rate() for entry in series)
        logger.info(
            f"✅ Fetched {len(series)} hourly cost entries, total: ${total_cost_usd:.2f} USD (€{total_cost_usd * AcademicConstants.get_eur_usd_rate():.2f})"
        )
        series.sort(key=lambda entry: entry["timestamp"])
        self._repository.write_json(cache_path, series)
        return series

    def get_costs(self, region: str, period_days: int = 30) -> Optional[AWSCostData]:
        """
        Get cost data from AWS Cost Explorer for specified period.

        Args:
            region: AWS region (e.g., "eu-central-1")
            period_days: Analysis period in days (1, 7, or 30)

        Returns:
            AWSCostData for the specified period, or None if error
        """
        # Period-specific cache key
        cache_key = f"costs_{period_days}d_{region.replace('-', '_')}"
        cache_path = self._cache_path("cost_data", cache_key)

        if self._repository.is_valid(cache_path, CacheTTL.COST_DATA):
            cached = self._repository.read_json(cache_path)
            if cached:
                try:
                    fetched_at = cached.get("fetched_at")
                    fetched_at_dt = datetime.fromisoformat(fetched_at) if fetched_at else None
                    return AWSCostData(
                        monthly_cost_usd=float(cached["monthly_cost_usd"]),
                        service_costs=cached.get("service_costs", {}),
                        region=cached.get("region", region),
                        source=cached.get("source", "AWS_Cost_Explorer"),
                        fetched_at=fetched_at_dt,
                    )
                except (KeyError, ValueError, TypeError) as error:
                    logger.debug("Invalid cached cost data: %s", error)

        cost_client = self._cost_client()

        # Dynamic date range based on period_days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period_days)

        # Auto-select granularity based on period length
        # AWS Cost Explorer limits: HOURLY max 14 days, DAILY unlimited
        granularity = "HOURLY" if period_days <= 14 else "DAILY"

        # AWS requires different date formats for different granularities:
        # - HOURLY: "YYYY-MM-DDTHH:MM:SSZ" (ISO 8601 with time)
        # - DAILY:  "YYYY-MM-DD" (date only, no time component)
        if granularity == "HOURLY":
            start_str = f"{start_date.isoformat()}T00:00:00Z"
            end_str = f"{end_date.isoformat()}T00:00:00Z"
        else:  # DAILY
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()

        request_kwargs: Dict[str, Any] = {
            "TimePeriod": {
                "Start": start_str,
                "End": end_str
            },
            "Granularity": granularity,
            "Metrics": ["UnblendedCost"],
            "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
            # Region filter: Use AWS region code format (e.g., "eu-central-1")
            "Filter": {
                "And": [
                    {"Dimensions": {"Key": "SERVICE", "Values": [
                        "Amazon Elastic Compute Cloud - Compute",
                        "EC2 - Other"
                    ]}},
                    {"Dimensions": {"Key": "REGION", "Values": [region]}},
                ]
            },
        }

        try:
            response = cost_client.get_cost_and_usage(**request_kwargs)
        except ClientError as error:
            logger.error("❌ AWS Cost Explorer error: %s", error)
            return None

        service_costs: Dict[str, float] = {}
        total_cost = 0.0
        ec2_cost = 0.0

        for result in response.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                keys = group.get("Keys") or []
                if not keys:
                    continue
                service_name = keys[0]
                amount = group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", "0")
                try:
                    cost_amount = float(amount)
                except (TypeError, ValueError):
                    cost_amount = 0.0
                if cost_amount < 0:
                    cost_amount = 0.0
                service_costs[service_name] = service_costs.get(service_name, 0.0) + cost_amount
                total_cost += cost_amount
                if "EC2" in service_name or "Amazon Elastic Compute Cloud" in service_name:
                    ec2_cost += cost_amount
                    logger.debug(f"💰 Found EC2 service in {region}: '{service_name}' with ${cost_amount:.4f}")

        if ec2_cost == 0.0 and total_cost > 0.0:
            ec2_cost = total_cost

        # Dynamic period label for logging
        if period_days == 1:
            period_label = "24 hours"
        elif period_days == 7:
            period_label = "7 days"
        else:
            period_label = f"{period_days} days"

        logger.info(
            f"✅ Cost Explorer: ${ec2_cost:.2f} EC2 costs in {region} over {period_label} "
            f"({granularity} granularity)"
        )

        fetched_at = datetime.now(timezone.utc)
        cost_data = AWSCostData(
            monthly_cost_usd=ec2_cost,
            service_costs=service_costs,
            region=self._session_helper.session().region_name or region,
            source=f"AWS_Cost_Explorer_{period_days}d",
            fetched_at=fetched_at,
        )

        self._repository.write_json(
            cache_path,
            {
                "monthly_cost_usd": cost_data.monthly_cost_usd,
                "service_costs": cost_data.service_costs,
                "region": cost_data.region,
                "source": cost_data.source,
                "fetched_at": cost_data.fetched_at.isoformat() if cost_data.fetched_at else None,
            },
        )
        return cost_data

    # =========================================================================
    # Instance Metadata Cache (Launch Time)
    # =========================================================================

    def _cache_launch_time(self, instance_id: str, region: str, launch_time: datetime) -> None:
        """Cache instance launch time permanently (365-day TTL)."""
        cache_key = f"{instance_id}_{region.replace('-', '_')}_launch_time"
        cache_path = self._cache_path("instance_metadata", cache_key)
        payload = {
            "instance_id": instance_id,
            "region": region,
            "launch_time": launch_time.isoformat() if launch_time else None,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        self._repository.write_json(cache_path, payload)
        logger.debug(f"💾 Cached launch time for {instance_id}: {launch_time}")

    def get_cached_launch_time(self, instance_id: str, region: str) -> Optional[datetime]:
        """Retrieve cached launch time for an instance (365-day TTL)."""
        cache_key = f"{instance_id}_{region.replace('-', '_')}_launch_time"
        cache_path = self._cache_path("instance_metadata", cache_key)

        if self._repository.is_valid(cache_path, CacheTTL.INSTANCE_METADATA):
            cached = self._repository.read_json(cache_path)
            if cached and cached.get("launch_time"):
                try:
                    launch_time = datetime.fromisoformat(cached["launch_time"])
                    logger.debug(f"✅ Retrieved cached launch time for {instance_id}: {launch_time}")
                    return launch_time
                except (ValueError, TypeError) as error:
                    logger.warning(f"⚠️ Invalid cached launch time for {instance_id}: {error}")
        return None


__all__ = ["AWSClient"]
