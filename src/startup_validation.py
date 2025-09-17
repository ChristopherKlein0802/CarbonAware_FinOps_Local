"""
Startup Validation for Carbon-Aware FinOps Dashboard
Ensures all required environment variables and dependencies are available
"""

import os
import sys
import logging
import subprocess
from typing import List, Tuple
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validate required environment variables and system dependencies

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_issues)
    """
    # Load .env file if it exists
    env_file_loaded = load_dotenv()

    issues = []

    # Check if .env file exists and was loaded
    if not env_file_loaded:
        if os.path.exists(".env"):
            issues.append("⚠️  .env file found but could not be loaded")
        else:
            issues.append("⚠️  No .env file found - using system environment variables only")

    # Check AWS profile configuration
    aws_profile = os.getenv("AWS_PROFILE")
    if not aws_profile:
        issues.append("⚠️  AWS_PROFILE not set - will use default AWS configuration")
    else:
        # Check if AWS profile is accessible (but don't fail if SSO token expired)
        try:
            result = subprocess.run(
                ["aws", "configure", "list", "--profile", aws_profile],
                capture_output=True, text=True, timeout=10
            )
            if "expired" in result.stderr.lower() or "sso" in result.stderr.lower():
                issues.append(f"⚠️  AWS SSO token for profile '{aws_profile}' may have expired")
                issues.append(f"💡 Run: aws sso login --profile {aws_profile}")
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # AWS CLI not available or other issues - not critical for startup
            pass

    # Check ElectricityMap API key
    if not os.getenv("ELECTRICITYMAP_API_KEY"):
        issues.append("❌ Missing environment variable: ELECTRICITYMAP_API_KEY (ElectricityMap API key for carbon intensity data)")

    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"❌ Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}")

    # Check critical imports
    critical_modules = [
        ("streamlit", "Streamlit web framework"),
        ("boto3", "AWS SDK"),
        ("requests", "HTTP requests"),
        ("pandas", "Data processing"),
        ("plotly", "Data visualization")
    ]

    for module_name, description in critical_modules:
        try:
            __import__(module_name)
        except ImportError:
            issues.append(f"❌ Missing required module: {module_name} ({description})")

    return len(issues) == 0, issues


def validate_aws_configuration() -> Tuple[bool, List[str]]:
    """
    Validate AWS configuration and credentials

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_issues)
    """
    issues = []

    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ProfileNotFound

        aws_profile = os.getenv("AWS_PROFILE")
        if aws_profile:
            try:
                session = boto3.Session(profile_name=aws_profile)
                # Try to get credentials (this will raise an exception if profile doesn't exist)
                credentials = session.get_credentials()
                if credentials:
                    logger.info(f"✅ AWS profile '{aws_profile}' configured correctly")
                else:
                    issues.append(f"⚠️ AWS profile '{aws_profile}' exists but has no valid credentials")
            except ProfileNotFound:
                issues.append(f"❌ AWS profile '{aws_profile}' not found")
            except NoCredentialsError:
                issues.append("❌ No AWS credentials available")
        else:
            issues.append("⚠️ AWS_PROFILE not set - AWS features will be unavailable")

    except ImportError:
        issues.append("❌ boto3 not available - AWS features disabled")

    return len(issues) == 0, issues


def validate_api_connectivity() -> Tuple[bool, List[str]]:
    """
    Basic validation of external API connectivity (optional)

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_warnings)
    """
    warnings = []

    # Check ElectricityMap API key format (basic validation)
    api_key = os.getenv("ELECTRICITYMAP_API_KEY")
    if api_key:
        if len(api_key) < 10:
            warnings.append("⚠️ ElectricityMap API key seems too short - verify correctness")
        else:
            logger.info("✅ ElectricityMap API key provided")
    else:
        warnings.append("⚠️ ElectricityMap API key not set - carbon data will be unavailable")

    return True, warnings  # Non-blocking warnings


def print_startup_banner():
    """Print professional startup banner"""
    print("🎓 Carbon-Aware FinOps Dashboard")
    print("=" * 50)
    print("Bachelor Thesis - Integrated Carbon & Cost Optimization")
    print("Version: Academic Prototype 2025")
    print("=" * 50)


def run_full_validation() -> bool:
    """
    Run complete startup validation

    Returns:
        bool: True if all critical validations pass
    """
    print_startup_banner()

    all_valid = True

    # Environment validation (critical)
    env_valid, env_issues = validate_environment()
    if not env_valid:
        print("\n❌ ENVIRONMENT VALIDATION FAILED:")
        for issue in env_issues:
            print(f"  {issue}")
        all_valid = False
    else:
        print("\n✅ Environment validation passed")

    # AWS validation (important but not blocking)
    aws_valid, aws_issues = validate_aws_configuration()
    if not aws_valid:
        print("\n⚠️ AWS CONFIGURATION ISSUES:")
        for issue in aws_issues:
            print(f"  {issue}")
        print("  💡 Dashboard will start but AWS features may be limited")
    else:
        print("\n✅ AWS configuration validated")

    # API connectivity (warnings only)
    api_valid, api_warnings = validate_api_connectivity()
    if api_warnings:
        print("\n⚠️ API CONFIGURATION WARNINGS:")
        for warning in api_warnings:
            print(f"  {warning}")

    if all_valid:
        print("\n🚀 Startup validation completed successfully!")
        print("💡 Run 'make dashboard' to start the application")
    else:
        print("\n❌ Critical validation issues found!")
        print("💡 Please fix the issues above before starting the dashboard")
        print("📖 See .env.example for configuration help")

    return all_valid


if __name__ == "__main__":
    success = run_full_validation()
    sys.exit(0 if success else 1)