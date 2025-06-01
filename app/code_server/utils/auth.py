import logging
from fastapi import Security
from fastapi.security import APIKeyHeader


logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s')


api_key_header = APIKeyHeader(name="X-API-Key", scheme_name="API Key")
application_header = APIKeyHeader(name="X-Application", scheme_name="Application")


def get_user(api_key_head: str = Security(api_key_header), application_head: str = Security(application_header)):
    """
    Dummy implementation for example purposes.
    Always returns 'example_user' regardless of the input credentials.
    
    Args:
        api_key_head: API key from request header
        application_head: Application name from request header
        
    Returns:
        str: A fixed username for demonstration
    """
    return "example_user"