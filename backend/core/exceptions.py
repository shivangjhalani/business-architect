from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        logger.error(f"API Error: {exc}")
        
        custom_response_data = {
            'error': True,
            'message': str(exc),
            'status_code': response.status_code
        }
        
        if hasattr(exc, 'detail'):
            custom_response_data['details'] = exc.detail
        
        response.data = custom_response_data
    
    return response


class BusinessCapabilityException(Exception):
    pass


class VectorSearchException(Exception):
    pass


def handle_unexpected_error(exc, context=None):
    logger.error(f"Unexpected error: {exc}")
    
    return Response({
        'error': True,
        'message': 'An unexpected error occurred',
        'status_code': 500
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 