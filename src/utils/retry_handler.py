"""
Retry handler with exponential backoff for AWS API calls.
"""

import time
import random
from functools import wraps
from typing import Callable, Tuple, Type, Union
import logging

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError

logger = logging.getLogger(__name__)


class RetryableError(Exception):
    """Base class for retryable errors."""
    pass


class NonRetryableError(Exception):
    """Base class for non-retryable errors."""
    pass


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error should be retried.
    
    Args:
        error: The exception that occurred
        
    Returns:
        True if the error should be retried
    """
    if isinstance(error, NoCredentialsError):
        return False
    
    if isinstance(error, EndpointConnectionError):
        return True
    
    if isinstance(error, ClientError):
        error_code = error.response.get('Error', {}).get('Code', '')
        
        # Don't retry client errors (4xx)
        non_retryable_codes = {
            'AccessDenied',
            'InvalidParameterValue', 
            'InvalidParameterCombination',
            'MissingParameter',
            'ValidationException',
            'ResourceNotFound',
            'AuthFailure'
        }
        
        if error_code in non_retryable_codes:
            return False
        
        # Retry server errors (5xx) and throttling
        retryable_codes = {
            'InternalError',
            'ServiceUnavailable', 
            'Throttling',
            'ThrottlingException',
            'ProvisionedThroughputExceededException',
            'RequestTimeout'
        }
        
        return error_code in retryable_codes
    
    # Retry generic connection errors
    return isinstance(error, (ConnectionError, TimeoutError))


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> Callable:
    """
    Decorator for exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    if not is_retryable_error(e):
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
                    
                    logger.warning(
                        f"Attempt {attempt + 1} of {func.__name__} failed: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


class AWSRetrySession:
    """AWS session with built-in retry logic."""
    
    def __init__(self, aws_profile: str = None, region: str = 'eu-central-1'):
        self.aws_profile = aws_profile
        self.region = region
        self._session = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def session(self) -> boto3.Session:
        """Get or create AWS session."""
        if self._session is None:
            try:
                if self.aws_profile:
                    self._session = boto3.Session(profile_name=self.aws_profile)
                else:
                    self._session = boto3.Session()
                
                # Test the session
                sts = self._session.client('sts', region_name=self.region)
                identity = sts.get_caller_identity()
                self.logger.info(f"AWS session established for account: {identity.get('Account')}")
                
            except Exception as e:
                self.logger.error(f"Failed to create AWS session: {e}")
                raise NonRetryableError(f"AWS authentication failed: {e}")
        
        return self._session
    
    @exponential_backoff(max_retries=3)
    def get_client(self, service_name: str, **kwargs):
        """Get AWS client with retry logic."""
        return self.session.client(service_name, region_name=self.region, **kwargs)
    
    @exponential_backoff(max_retries=3)
    def get_resource(self, service_name: str, **kwargs):
        """Get AWS resource with retry logic."""
        return self.session.resource(service_name, region_name=self.region, **kwargs)


def safe_aws_call(func: Callable, *args, **kwargs):
    """
    Safe wrapper for AWS API calls with error handling.
    
    Args:
        func: AWS API function to call
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        API response or None if failed
    """
    try:
        return func(*args, **kwargs)
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"AWS API call failed [{error_code}]: {error_message}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in AWS API call: {e}")
        return None