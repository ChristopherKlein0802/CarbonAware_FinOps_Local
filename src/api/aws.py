"""
AWS API Integration
AWS services for pricing and cost data
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from ..utils.cache import is_cache_valid, get_standard_cache_path, ensure_cache_dir, CacheTTL
from ..utils.errors import handle_aws_operations, ErrorMessages
from ..utils.logging import get_performance_logger
from ..models.aws import AWSCostData
from ..constants import AcademicConstants

logger = get_performance_logger("aws_api")


class AWSAPIClient:
    """AWS API client for pricing and cost data"""

    def __init__(self, aws_profile: str = None):
        """Initialize AWS API client with optional profile"""
        self.aws_profile = aws_profile

    @staticmethod
    def _map_cost_explorer_region(region: Optional[str]) -> Optional[str]:
        if not region:
            return None

        region_mapping = {
            "eu-central-1": "EU (Frankfurt)",
            "eu-west-1": "EU (Ireland)",
            "us-east-1": "US East (N. Virginia)",
            "us-west-2": "US West (Oregon)",
        }
        return region_mapping.get(region, None)

    def _ensure_session(self) -> None:
        """Ensure AWS SSO session is active, invoking helper script when present."""

        script_path = Path(__file__).resolve().parents[2] / "scripts" / "ensure_aws_session.sh"
        if not script_path.exists():
            return

        profile = self.aws_profile or os.environ.get("AWS_PROFILE")
        command = [str(script_path)]
        if profile:
            command.append(profile)

        env = os.environ.copy()
        if profile:
            env.setdefault("AWS_PROFILE", profile)

        try:
            subprocess.run(command, check=True, env=env)
        except FileNotFoundError:
            logger.warning("AWS SSO helper script missing: %s", script_path)
        except subprocess.CalledProcessError as error:
            logger.error("AWS SSO auto-login failed for profile %s", profile or "default")
            raise RuntimeError("AWS SSO auto-login failed") from error

    def get_instance_pricing(self, instance_type: str, region: str = "eu-central-1") -> Optional[float]:
        """Get AWS EC2 instance pricing from AWS Pricing API with 7-day caching"""
        cache_path = get_standard_cache_path("pricing", f"{instance_type}_{region}")
        ensure_cache_dir(cache_path)

        # Check cache first (7 days - AWS pricing changes rarely)
        if is_cache_valid(cache_path, CacheTTL.PRICING_DATA):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                logger.info(f"✅ Using cached pricing for {instance_type}")
                return cached_data["hourly_price_usd"]
            except (FileNotFoundError, PermissionError, OSError):
                pass  # Cache miss - use fresh API call
            except (ValueError, TypeError) as e:
                logger.warning(f"📄 Pricing cache corrupted: {e} - using fresh API call")

        # Fetch fresh pricing from AWS Pricing API
        try:
            self._ensure_session()
            session = boto3.Session(profile_name=self.aws_profile)
            pricing_client = session.client('pricing', region_name='us-east-1')

            # Map region to pricing location
            region_mapping = {
                "eu-central-1": "EU (Frankfurt)",
                "eu-west-1": "EU (Ireland)",
                "us-east-1": "US East (N. Virginia)",
                "us-west-2": "US West (Oregon)"
            }
            location = region_mapping.get(region, "EU (Frankfurt)")

            logger.info(f"💰 Fetching fresh pricing for {instance_type} in {location}")

            response = pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                    {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                    {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
                ]
            )

            if not response.get('PriceList'):
                logger.error(f"❌ No pricing data found for {instance_type} in {location}")
                return None

            # Parse the complex pricing JSON structure
            price_item = json.loads(response['PriceList'][0])
            terms = price_item['terms']['OnDemand']

            # Extract the hourly price
            for term_key, term_value in terms.items():
                for price_key, price_value in term_value['priceDimensions'].items():
                    if 'Hrs' in price_value['unit']:
                        hourly_price = float(price_value['pricePerUnit']['USD'])

                        # Cache the result
                        try:
                            cache_data = {
                                "hourly_price_usd": hourly_price,
                                "instance_type": instance_type,
                                "region": region,
                                "location": location,
                                "source": "AWS_Pricing_API"
                            }
                            with open(cache_path, "w") as f:
                                json.dump(cache_data, f)
                            logger.info(f"✅ Pricing: {instance_type} = ${hourly_price:.4f}/hour (cached 24h)")
                        except (PermissionError, OSError):
                            pass  # Cache write failed - data still available

                        return hourly_price

            logger.error(f"❌ Could not parse pricing data for {instance_type}")
            return None

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidGrantException':
                logger.error("🔄 AWS SSO session expired for Pricing API - re-authenticate required")
                logger.info("💡 Fix: aws sso login")
            elif error_code == 'AccessDenied':
                logger.error(f"🚫 AWS access denied for Pricing API - check permissions")
            else:
                logger.error(f"❌ AWS Pricing API error: {error_code} for {instance_type}")
            return None
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"❌ AWS Pricing data validation failed for {instance_type}: {e}")
            return None
        except (RuntimeError, OSError) as e:
            if "Token has expired" in str(e) or "InvalidGrantException" in str(e):
                logger.error(ErrorMessages.AWS_SSO_EXPIRED)
                logger.info(ErrorMessages.AWS_SSO_FIX)
            else:
                logger.error(f"❌ AWS Pricing API runtime error for {instance_type}: {e}")
            return None

    def get_hourly_costs(self, hours: int = 48, region: str = "eu-central-1") -> Optional[list[dict]]:
        """Fetch hourly EC2 costs from AWS Cost Explorer for the recent window."""

        hours = max(1, min(hours, 336))  # Cost Explorer limits hourly data to ~14 Tage
        cache_key = f"hourly_{region.replace('-', '_')}_{hours}"
        cache_path = get_standard_cache_path("cost_series", cache_key)
        ensure_cache_dir(cache_path)

        if is_cache_valid(cache_path, CacheTTL.COST_DATA):
            try:
                with open(cache_path, "r", encoding="utf-8") as handle:
                    cached_payload = json.load(handle)
                logger.info("✅ Using cached hourly cost series")
                return cached_payload
            except (OSError, ValueError, TypeError) as error:
                logger.warning("⚠️ Unable to read hourly cost cache: %s", error)

        try:
            self._ensure_session()
            session = boto3.Session(profile_name=self.aws_profile)
            cost_client = session.client("ce", region_name="us-east-1")

            now_utc = datetime.now(timezone.utc)
            window_start = now_utc - timedelta(hours=hours)

            # Collect day boundaries for per-day Cost Explorer calls (HOURLY granularity requires 1-day windows)
            start_day = window_start.date()
            end_day = now_utc.date()

            logger.info("💰 Fetching hourly EC2 costs from %s to %s", start_day.isoformat(), end_day.isoformat())

            series: list[dict] = []

            day_cursor = start_day
            filter_conditions = [
                {
                    "Dimensions": {
                        "Key": "SERVICE",
                        "Values": ["Amazon Elastic Compute Cloud - Compute"],
                    }
                }
            ]

            region_label = self._map_cost_explorer_region(region)
            if region_label:
                filter_conditions.append(
                    {
                        "Dimensions": {
                            "Key": "REGION",
                            "Values": [region_label],
                        }
                    }
                )

            if len(filter_conditions) == 1:
                filter_payload = filter_conditions[0]
            else:
                filter_payload = {"And": filter_conditions}

            while day_cursor <= end_day:
                next_day = day_cursor + timedelta(days=1)

                start_iso = f"{day_cursor.isoformat()}T00:00:00Z"
                end_iso = f"{next_day.isoformat()}T00:00:00Z"

                try:
                    response = cost_client.get_cost_and_usage(
                        TimePeriod={"Start": start_iso, "End": end_iso},
                        Granularity="HOURLY",
                        Metrics=["UnblendedCost"],
                        Filter=filter_payload,
                    )
                except ClientError as error:
                    code = error.response.get("Error", {}).get("Code")
                    message = error.response.get("Error", {}).get("Message")
                    logger.error("❌ AWS Cost Explorer error: %s (%s)", code, message)
                    return None

                for result in response.get("ResultsByTime", []):
                    start_ts = result.get("TimePeriod", {}).get("Start")
                    if not start_ts:
                        continue
                    try:
                        timestamp = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    if timestamp < window_start:
                        continue

                    amount_str = result.get("Total", {}).get("UnblendedCost", {}).get("Amount", "0")
                    try:
                        amount_usd = float(amount_str)
                    except (TypeError, ValueError):
                        amount_usd = 0.0

                    if amount_usd < 0:
                        amount_usd = 0.0

                    amount_eur = amount_usd * AcademicConstants.EUR_USD_RATE
                    series.append(
                        {
                            "timestamp": timestamp.isoformat(),
                            "cost_eur": round(amount_eur, 6),
                        }
                    )

                day_cursor = next_day

            series.sort(key=lambda entry: entry["timestamp"])

            try:
                with open(cache_path, "w", encoding="utf-8") as handle:
                    json.dump(series, handle, indent=2)
            except OSError as error:
                logger.warning("⚠️ Failed to cache hourly cost series: %s", error)

            return series

        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            if code == "InvalidGrantException":
                logger.error(ErrorMessages.AWS_SSO_EXPIRED)
                logger.info(ErrorMessages.AWS_SSO_FIX)
            elif code == "AccessDeniedException":
                logger.error("🚫 AWS access denied for Cost Explorer hourly data")
            else:
                logger.error("❌ AWS Cost Explorer error: %s", code)
            return None
        except (RuntimeError, OSError) as error:
            logger.error("❌ AWS Cost Explorer runtime error: %s", error)
            return None

    def get_monthly_costs(self, region: str = "eu-central-1") -> Optional[AWSCostData]:
        """Get monthly AWS costs for validation with 6-hour caching"""
        cache_key = f"monthly_{region.replace('-', '_')}"
        cache_path = get_standard_cache_path("cost_data", cache_key)
        ensure_cache_dir(cache_path)

        # Check cache first (6 hours - AWS Cost Explorer updates daily)
        if is_cache_valid(cache_path, CacheTTL.COST_DATA):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                logger.info("✅ Using cached Cost Explorer data")
                if "fetched_at" in cached_data and cached_data["fetched_at"]:
                    cached_data["fetched_at"] = datetime.fromisoformat(cached_data["fetched_at"])
                return AWSCostData(**cached_data)
            except (FileNotFoundError, PermissionError, json.JSONDecodeError, KeyError) as e:
                logger.warning(f"⚠️ Cost cache read failed: {e}")

        # Fetch fresh data from AWS Cost Explorer for validation
        try:
            self._ensure_session()
            session = boto3.Session(profile_name=self.aws_profile)
            cost_client = session.client("ce", region_name="us-east-1")

            logger.info("💰 Fetching Cost Explorer data for validation")

            # Get trailing 30-day period (end is exclusive per AWS API)
            end_date = datetime.now().date()
            start_date = (datetime.now() - timedelta(days=30)).date()

            region_label = self._map_cost_explorer_region(region)

            request_kwargs = {
                "TimePeriod": {
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d")
                },
                "Granularity": "DAILY",
                "Metrics": ["UnblendedCost"],
                "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
            }

            filter_conditions = []
            if region_label:
                filter_conditions.append(
                    {
                        "Dimensions": {
                            "Key": "REGION",
                            "Values": [region_label],
                        }
                    }
                )

            if filter_conditions:
                if len(filter_conditions) == 1:
                    request_kwargs["Filter"] = filter_conditions[0]
                else:
                    request_kwargs["Filter"] = {"And": filter_conditions}

            response = cost_client.get_cost_and_usage(**request_kwargs)

            service_costs: dict[str, float] = {}
            total_cost = 0.0
            ec2_cost = 0.0
            ec2_keywords = (
                "Amazon Elastic Compute Cloud",
                "EC2",
            )

            for result in response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    keys = group.get("Keys") or []
                    if not keys:
                        continue
                    service_name = keys[0]
                    cost_amount_str = (
                        group.get("Metrics", {})
                        .get("UnblendedCost", {})
                        .get("Amount", "0")
                    )

                    try:
                        cost_amount = float(cost_amount_str)
                        if cost_amount < 0:
                            cost_amount = 0.0
                    except (ValueError, TypeError):
                        cost_amount = 0.0

                    service_costs[service_name] = service_costs.get(service_name, 0.0) + cost_amount
                    total_cost += cost_amount

                    if any(keyword in service_name for keyword in ec2_keywords):
                        ec2_cost += cost_amount
            # Focus on EC2 costs for validation
            if ec2_cost == 0.0 and total_cost > 0.0:
                logger.info(
                    "ℹ️ Cost Explorer reported zero EC2 spend; falling back to total monthly cost for validation"
                )
                ec2_cost = total_cost

            fetched_at = datetime.now(timezone.utc)
            cost_data = AWSCostData(
                monthly_cost_usd=ec2_cost,  # Only EC2 costs for instance validation
                service_costs=service_costs,
                region="us-east-1",
                source="AWS_Cost_Explorer_Validation",
                fetched_at=fetched_at
            )

            # Cache the result
            try:
                cache_data = {
                    "monthly_cost_usd": cost_data.monthly_cost_usd,
                    "service_costs": cost_data.service_costs,
                    "region": cost_data.region,
                    "source": cost_data.source,
                    "fetched_at": cost_data.fetched_at.isoformat() if cost_data.fetched_at else None
                }
                with open(cache_path, "w") as f:
                    json.dump(cache_data, f)
                logger.info(f"✅ AWS EC2 costs: ${ec2_cost:.2f} USD (validation data, cached 1h)")
            except (OSError, PermissionError, TypeError, ValueError) as e:
                logger.warning(f"⚠️ Failed to cache cost data: {e}")

            return cost_data

        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"❌ AWS Cost Explorer data validation failed: {e} - NO FALLBACK used")
            return None
        except (RuntimeError, OSError) as e:
            logger.error(f"❌ AWS Cost Explorer runtime error: {e} - NO FALLBACK used")
            # Check if it's an SSO token issue
            if "Token has expired" in str(e) or "InvalidGrantException" in str(e):
                logger.warning(ErrorMessages.AWS_SSO_EXPIRED)
                logger.info(ErrorMessages.AWS_SSO_FIX)
            return None
