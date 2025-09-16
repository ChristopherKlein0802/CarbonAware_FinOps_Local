"""
Error Handling Utilities Module
Centralized error handling patterns and specific exception handling

Provides reusable error handling decorators and specific exception types
to replace generic Exception handling throughout the codebase.

Academic Benefits:
- Specific error types for better debugging
- Consistent error messages and handling patterns
- Improved production error tracking
"""

import logging
import functools
from typing import Optional, Callable, Any
from datetime import datetime
import requests
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, TokenRefreshError

logger = logging.getLogger(__name__)


# Custom Exception Types for Better Error Handling
class CacheOperationError(Exception):
    """Non-critical cache read/write operation failures"""
    pass


class APIConnectionError(Exception):
    """Critical API connection and authentication failures"""
    pass


class AWSCredentialsError(Exception):
    """AWS credentials and token-related errors"""
    pass


class DataValidationError(Exception):
    """Data structure and validation errors"""
    pass


def handle_cache_operations(fallback_value=None):
    """
    Decorator for handling cache read/write operations

    Cache failures are non-critical - application should continue
    with fresh API calls or fallback values.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (FileNotFoundError, PermissionError, OSError) as e:
                logger.debug(f"🗃️ Cache operation failed (non-critical): {func.__name__} - {e}")
                return fallback_value
            except Exception as e:
                # Still catch unexpected errors but log them specifically
                logger.warning(f"⚠️ Unexpected cache error in {func.__name__}: {type(e).__name__}: {e}")
                return fallback_value
        return wrapper
    return decorator


def handle_api_requests(api_name: str):
    """
    Decorator for handling external API requests with specific error types

    Provides specific handling for different API failure modes:
    - Connection timeouts
    - Authentication failures
    - Rate limiting
    - Invalid responses
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.Timeout:
                logger.error(f"⏱️ {api_name} API timeout - check network connection")
                return None
            except requests.exceptions.ConnectionError:
                logger.error(f"🔌 {api_name} API connection failed - check internet connectivity")
                return None
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    logger.error(f"🔐 {api_name} API authentication failed - check API key")
                elif e.response.status_code == 429:
                    logger.warning(f"🚦 {api_name} API rate limited - reduce request frequency")
                elif e.response.status_code >= 500:
                    logger.error(f"🏥 {api_name} API server error ({e.response.status_code}) - try again later")
                else:
                    logger.error(f"❌ {api_name} API HTTP error: {e.response.status_code}")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ {api_name} API request failed: {type(e).__name__}: {e}")
                return None
            except Exception as e:
                # Last resort for truly unexpected errors
                logger.error(f"💥 Unexpected error in {api_name} API call: {type(e).__name__}: {e}")
                return None
        return wrapper
    return decorator


def handle_aws_operations(operation_type: str):
    """
    Decorator for handling AWS API operations with specific error handling

    Handles common AWS-specific error patterns:
    - SSO token expiration
    - Permission issues
    - Service availability
    - Resource not found
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except TokenRefreshError:
                logger.error("🔄 AWS SSO token expired - run 'aws sso login' to re-authenticate")
                logger.info("💡 Fix: aws sso login --profile <your-profile>")
                return None
            except NoCredentialsError:
                logger.error("🔐 AWS credentials not found - configure AWS CLI")
                logger.info("💡 Fix: aws configure or aws sso login")
                return None
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'InvalidGrantException':
                    logger.error("🔄 AWS SSO session expired - re-authenticate required")
                    logger.info("💡 Fix: aws sso login")
                elif error_code == 'AccessDenied':
                    logger.error(f"🚫 AWS access denied for {operation_type} - check permissions")
                elif error_code == 'ResourceNotFoundException':
                    logger.warning(f"📭 AWS resource not found for {operation_type}")
                elif error_code == 'ThrottlingException':
                    logger.warning(f"🚦 AWS API throttled for {operation_type} - reduce request rate")
                else:
                    logger.error(f"❌ AWS {operation_type} error: {error_code} - {e.response['Error']['Message']}")
                return None
            except Exception as e:
                logger.error(f"💥 Unexpected AWS {operation_type} error: {type(e).__name__}: {e}")
                return None
        return wrapper
    return decorator


def safe_json_operation(operation: str, fallback_value=None):
    """
    Handle JSON parsing and file operations safely

    Common pattern for cache files and API responses
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (ValueError, TypeError) as e:
                logger.warning(f"📄 JSON {operation} failed: Invalid format - {e}")
                return fallback_value
            except (FileNotFoundError, PermissionError) as e:
                logger.debug(f"📁 File {operation} failed: {e}")
                return fallback_value
            except Exception as e:
                logger.warning(f"⚠️ Unexpected {operation} error: {type(e).__name__}: {e}")
                return fallback_value
        return wrapper
    return decorator


def log_function_entry_exit(func):
    """
    Debug decorator for tracking function execution
    Useful for debugging complex data flows
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.debug(f"🔄 Entering {func_name}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"✅ Exiting {func_name} successfully")
            return result
        except Exception as e:
            logger.debug(f"❌ Exiting {func_name} with error: {type(e).__name__}")
            raise
    return wrapper


# Error message constants for consistency
class ErrorMessages:
    """Centralized error messages for consistent user experience"""

    # AWS SSO Messages
    AWS_SSO_EXPIRED = "AWS SSO token expired - run 'aws sso login' to re-authenticate"
    AWS_SSO_FIX = "💡 Fix: aws sso login --profile carbon-finops-sandbox"

    # API Messages
    API_KEY_MISSING = "API key not configured - check environment variables"
    API_KEY_INVALID = "API authentication failed - check API key validity"
    API_TIMEOUT = "API request timed out - check network connectivity"

    # Cache Messages
    CACHE_READ_FAILED = "Cache read failed (non-critical) - using fresh API call"
    CACHE_WRITE_FAILED = "Cache write failed (non-critical) - data still available"

    # Data Validation
    INVALID_INSTANCE_TYPE = "Invalid EC2 instance type provided"
    INVALID_REGION = "Invalid AWS region specified"
    MISSING_REQUIRED_DATA = "Required data missing from API response"


def get_error_context(error: Exception) -> dict:
    """
    Extract useful context from exceptions for debugging

    Returns structured error information for logging and monitoring
    """
    return {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': datetime.now().isoformat(),
        'is_retryable': isinstance(error, (requests.exceptions.Timeout,
                                         requests.exceptions.ConnectionError,
                                         TokenRefreshError))
    }