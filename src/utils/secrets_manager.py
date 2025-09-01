"""
Secrets management utility for Carbon-Aware FinOps.
Supports AWS Secrets Manager, environment variables, and local configuration.
"""

import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .logging_config import LoggerMixin
from .retry_handler import AWSRetrySession, safe_aws_call


@dataclass
class SecretConfig:
    """Configuration for a secret."""

    key: str
    secret_name: Optional[str] = None
    env_var: Optional[str] = None
    default: Optional[str] = None
    required: bool = False


class SecretsManager(LoggerMixin):
    """
    Centralized secrets management supporting multiple backends.

    Priority order:
    1. AWS Secrets Manager (if configured)
    2. Environment variables
    3. Default values
    """

    def __init__(self, aws_profile: str = None, region: str = "eu-central-1"):
        self.aws_profile = aws_profile
        self.region = region
        self._secrets_cache = {}
        self._aws_session = None

        # Initialize AWS session if profile is provided
        if aws_profile:
            try:
                self._aws_session = AWSRetrySession(aws_profile, region)
                self.logger.info(f"AWS Secrets Manager initialized with profile: {aws_profile}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize AWS Secrets Manager: {e}")
                self._aws_session = None

        # Define secret configurations
        self.secret_configs = {
            "electricitymap_api_key": SecretConfig(
                key="electricitymap_api_key",
                secret_name="carbon-finops/electricitymap-api-key",
                env_var="ELECTRICITYMAP_API_KEY",
                required=False,
            ),
            "watttime_username": SecretConfig(
                key="watttime_username",
                secret_name="carbon-finops/watttime-credentials",
                env_var="WATTTIME_USERNAME",
                required=False,
            ),
            "watttime_password": SecretConfig(
                key="watttime_password",
                secret_name="carbon-finops/watttime-credentials",
                env_var="WATTTIME_PASSWORD",
                required=False,
            ),
            "dashboard_secret_key": SecretConfig(
                key="dashboard_secret_key",
                secret_name="carbon-finops/dashboard-secret",
                env_var="DASHBOARD_SECRET_KEY",
                default="dev-secret-key-change-in-production",
                required=True,
            ),
        }

    def get_secret(self, key: str) -> Optional[str]:
        """
        Get a secret value by key.

        Args:
            key: Secret key identifier

        Returns:
            Secret value or None if not found
        """
        # Check cache first
        if key in self._secrets_cache:
            return self._secrets_cache[key]

        config = self.secret_configs.get(key)
        if not config:
            self.logger.error(f"Unknown secret key: {key}")
            return None

        # Try AWS Secrets Manager first
        if self._aws_session and config.secret_name:
            value = self._get_from_aws_secrets(config.secret_name, key)
            if value:
                self._secrets_cache[key] = value
                return value

        # Try environment variable
        if config.env_var:
            value = os.getenv(config.env_var)
            if value:
                self._secrets_cache[key] = value
                self.logger.debug(f"Retrieved secret '{key}' from environment variable")
                return value

        # Use default value
        if config.default:
            self._secrets_cache[key] = config.default
            self.logger.debug(f"Using default value for secret '{key}'")
            return config.default

        # Handle required secrets
        if config.required:
            self.logger.error(f"Required secret '{key}' not found")
            raise ValueError(f"Required secret '{key}' not found")

        self.logger.warning(f"Secret '{key}' not found, returning None")
        return None

    def _get_from_aws_secrets(self, secret_name: str, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        try:
            client = self._aws_session.get_client("secretsmanager")
            response = safe_aws_call(client.get_secret_value, SecretId=secret_name)

            if not response:
                return None

            secret_data = response.get("SecretString")
            if not secret_data:
                return None

            # Handle JSON secrets
            try:
                secrets = json.loads(secret_data)
                if isinstance(secrets, dict):
                    return secrets.get(key)
                return secret_data if key in secret_name else None
            except json.JSONDecodeError:
                # Plain text secret
                return secret_data

        except Exception as e:
            self.logger.warning(f"Failed to retrieve secret '{secret_name}' from AWS: {e}")
            return None

    def get_all_secrets(self) -> Dict[str, Any]:
        """Get all configured secrets as a dictionary."""
        secrets = {}
        for key in self.secret_configs:
            value = self.get_secret(key)
            if value:
                secrets[key] = value
        return secrets

    def validate_required_secrets(self) -> bool:
        """
        Validate that all required secrets are available.

        Returns:
            True if all required secrets are available
        """
        missing_secrets = []

        for key, config in self.secret_configs.items():
            if config.required:
                try:
                    value = self.get_secret(key)
                    if not value:
                        missing_secrets.append(key)
                except ValueError:
                    missing_secrets.append(key)

        if missing_secrets:
            self.logger.error(f"Missing required secrets: {missing_secrets}")
            return False

        self.logger.info("All required secrets are available")
        return True

    def create_aws_secrets(self, secrets: Dict[str, str]) -> bool:
        """
        Create secrets in AWS Secrets Manager.

        Args:
            secrets: Dictionary of secret_name -> secret_value

        Returns:
            True if all secrets were created successfully
        """
        if not self._aws_session:
            self.logger.error("AWS session not available for creating secrets")
            return False

        client = self._aws_session.get_client("secretsmanager")
        success_count = 0

        for secret_name, secret_value in secrets.items():
            try:
                response = safe_aws_call(
                    client.create_secret,
                    Name=secret_name,
                    SecretString=secret_value,
                    Description=f"Carbon-Aware FinOps secret: {secret_name}",
                )

                if response:
                    self.logger.info(f"Created secret: {secret_name}")
                    success_count += 1
                else:
                    self.logger.error(f"Failed to create secret: {secret_name}")

            except Exception as e:
                self.logger.error(f"Error creating secret '{secret_name}': {e}")

        return success_count == len(secrets)

    def update_aws_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Update a secret in AWS Secrets Manager.

        Args:
            secret_name: Name of the secret
            secret_value: New secret value

        Returns:
            True if secret was updated successfully
        """
        if not self._aws_session:
            self.logger.error("AWS session not available for updating secrets")
            return False

        client = self._aws_session.get_client("secretsmanager")

        response = safe_aws_call(client.update_secret, SecretId=secret_name, SecretString=secret_value)

        if response:
            self.logger.info(f"Updated secret: {secret_name}")
            # Clear cache for this secret
            self._clear_cache()
            return True
        else:
            self.logger.error(f"Failed to update secret: {secret_name}")
            return False

    def _clear_cache(self):
        """Clear the secrets cache."""
        self._secrets_cache.clear()
        self.logger.debug("Secrets cache cleared")


# Global secrets manager instance
_secrets_manager = None


def get_secrets_manager(aws_profile: str = None, region: str = "eu-central-1") -> SecretsManager:
    """Get or create the global secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager(aws_profile, region)
    return _secrets_manager


def get_secret(key: str, aws_profile: str = None) -> Optional[str]:
    """
    Convenience function to get a secret.

    Args:
        key: Secret key identifier
        aws_profile: Optional AWS profile override

    Returns:
        Secret value or None if not found
    """
    manager = get_secrets_manager(aws_profile)
    return manager.get_secret(key)


def setup_secrets_from_env() -> Dict[str, str]:
    """
    Setup secrets from environment variables for AWS Secrets Manager.

    Returns:
        Dictionary of secrets that can be created in AWS
    """
    secrets = {}

    # ElectricityMap API Key
    electricitymap_key = os.getenv("ELECTRICITYMAP_API_KEY")
    if electricitymap_key:
        secrets["carbon-finops/electricitymap-api-key"] = electricitymap_key

    # WattTime Credentials
    watttime_username = os.getenv("WATTTIME_USERNAME")
    watttime_password = os.getenv("WATTTIME_PASSWORD")
    if watttime_username and watttime_password:
        watttime_creds = json.dumps({"username": watttime_username, "password": watttime_password})
        secrets["carbon-finops/watttime-credentials"] = watttime_creds

    # Dashboard Secret
    dashboard_secret = os.getenv("DASHBOARD_SECRET_KEY")
    if dashboard_secret:
        secrets["carbon-finops/dashboard-secret"] = dashboard_secret

    return secrets
