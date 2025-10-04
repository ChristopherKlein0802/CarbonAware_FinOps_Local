"""AWS client implementations for pricing and cost explorer interactions."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List

import boto3
from botocore.exceptions import ClientError

from ...config import settings
from ...constants import AcademicConstants
from ...infrastructure.cache import FileCacheRepository, CacheTTL
from ...models.aws import AWSCostData
from ...utils.errors import ErrorMessages

logger = logging.getLogger(__name__)


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

    def session(self) -> boto3.Session:
        self.ensure_session()
        return boto3.Session(profile_name=self._profile)


class AWSBillingClient:
    """Handles cost explorer and pricing API integrations."""

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
        # acceptable for validation purposes (TAC & Cost MAPE metrics).
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

                amount_eur = hourly_ec2_cost * AcademicConstants.EUR_USD_RATE
                series.append({"timestamp": timestamp.isoformat(), "cost_eur": round(amount_eur, 6)})
                if hourly_ec2_cost > 0:
                    logger.debug(f"💰 Cost hour {timestamp.strftime('%Y-%m-%d %H:%M')}: ${hourly_ec2_cost:.4f} → €{amount_eur:.4f}")
            day_cursor = next_day

        total_cost_usd = sum(entry["cost_eur"] / AcademicConstants.EUR_USD_RATE for entry in series)
        logger.info(f"✅ Fetched {len(series)} hourly cost entries, total: ${total_cost_usd:.2f} USD (€{total_cost_usd * AcademicConstants.EUR_USD_RATE:.2f})")
        series.sort(key=lambda entry: entry["timestamp"])
        self._repository.write_json(cache_path, series)
        return series

    def get_monthly_costs(self, region: str) -> Optional[AWSCostData]:
        cache_key = f"monthly_{region.replace('-', '_')}"
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
                        source=cached.get("source", "AWS_Cost_Explorer_Validation"),
                        fetched_at=fetched_at_dt,
                    )
                except (KeyError, ValueError, TypeError) as error:
                    logger.debug("Invalid cached monthly cost data: %s", error)

        cost_client = self._cost_client()
        end_date = datetime.now().date()
        start_date = (datetime.now() - timedelta(days=30)).date()
        region_label = self._pricing_mappings.get(region)

        request_kwargs: Dict[str, Any] = {
            "TimePeriod": {"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
            "Granularity": "DAILY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
        }

        # NOTE: Region filter disabled - AWS Cost Explorer uses different region naming
        # and filters out all data when using "EU (Frankfurt)" as REGION dimension.
        # Cost Explorer returns aggregated costs, which is acceptable for validation.
        # For instance-specific costs, use: hourly_price × runtime (calculated separately).

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
                    logger.debug(f"💰 Found EC2 service: '{service_name}' with ${cost_amount:.4f}")
        if ec2_cost == 0.0 and total_cost > 0.0:
            ec2_cost = total_cost

        fetched_at = datetime.now(timezone.utc)
        cost_data = AWSCostData(
            monthly_cost_usd=ec2_cost,
            service_costs=service_costs,
            region=self._session_helper.session().region_name or region,
            source="AWS_Cost_Explorer_Validation",
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


__all__ = ["AWSBillingClient"]
