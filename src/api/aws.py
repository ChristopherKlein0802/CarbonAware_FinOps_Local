"""
AWS API Integration
AWS services for pricing and cost data
"""

import json
import boto3
from datetime import datetime
from typing import Optional
from botocore.exceptions import ClientError

from ..utils.cache import is_cache_valid, get_standard_cache_path, ensure_cache_dir, CacheTTL
from ..utils.errors import handle_aws_operations, ErrorMessages
from ..utils.logging import get_performance_logger
from ..models.aws import AWSCostData

logger = get_performance_logger("aws_api")


class AWSAPIClient:
    """AWS API client for pricing and cost data"""

    def __init__(self, aws_profile: str = None):
        """Initialize AWS API client with optional profile"""
        self.aws_profile = aws_profile

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

    def get_monthly_costs(self) -> Optional[AWSCostData]:
        """Get monthly AWS costs for validation with 6-hour caching"""
        cache_path = get_standard_cache_path("cost_data", "monthly")
        ensure_cache_dir(cache_path)

        # Check cache first (6 hours - AWS Cost Explorer updates daily)
        if is_cache_valid(cache_path, CacheTTL.COST_DATA):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                logger.info("✅ Using cached Cost Explorer data")
                return AWSCostData(**cached_data)
            except (FileNotFoundError, PermissionError, json.JSONDecodeError, KeyError) as e:
                logger.warning(f"⚠️ Cost cache read failed: {e}")

        # Fetch fresh data from AWS Cost Explorer for validation
        try:
            session = boto3.Session(profile_name=self.aws_profile)
            cost_client = session.client("ce", region_name="us-east-1")

            logger.info("💰 Fetching Cost Explorer data for validation")

            # Get current month cost data
            end_date = datetime.now().date()
            start_date = end_date.replace(day=1)  # First day of current month

            response = cost_client.get_cost_and_usage(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d")
                },
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
            )

            service_costs = {}
            total_cost = 0.0

            for result in response["ResultsByTime"]:
                for group in result["Groups"]:
                    if group["Keys"]:
                        service_name = group["Keys"][0]
                        cost_amount_str = group["Metrics"]["UnblendedCost"]["Amount"]

                        try:
                            cost_amount = float(cost_amount_str)
                            if cost_amount < 0:
                                cost_amount = 0.0
                        except (ValueError, TypeError):
                            cost_amount = 0.0

                        service_costs[service_name] = cost_amount
                        total_cost += cost_amount

            # Focus on EC2 costs for validation
            ec2_cost = service_costs.get("Amazon Elastic Compute Cloud - Compute", 0.0)

            cost_data = AWSCostData(
                monthly_cost_usd=ec2_cost,  # Only EC2 costs for instance validation
                service_costs=service_costs,
                region="us-east-1",
                source="AWS_Cost_Explorer_Validation"
            )

            # Cache the result
            try:
                cache_data = {
                    "monthly_cost_usd": cost_data.monthly_cost_usd,
                    "service_costs": cost_data.service_costs,
                    "region": cost_data.region,
                    "source": cost_data.source
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
