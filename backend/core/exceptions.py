from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    and logs errors for debugging.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the error for debugging
        logger.error(f"API Error: {exc}", exc_info=True, extra={
            'view': context.get('view'),
            'request': context.get('request'),
        })
        
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data,
            'status_code': response.status_code
        }
        
        # Customize error messages based on error type
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                custom_response_data['message'] = 'Validation error'
                custom_response_data['field_errors'] = exc.detail
            elif isinstance(exc.detail, list):
                custom_response_data['message'] = exc.detail[0] if exc.detail else 'Validation error'
            else:
                custom_response_data['message'] = str(exc.detail)
        
        response.data = custom_response_data
        
    else:
        # Handle exceptions not caught by DRF
        if isinstance(exc, DjangoValidationError):
            logger.error(f"Django Validation Error: {exc}", exc_info=True)
            return Response({
                'error': True,
                'message': 'Validation error',
                'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc),
                'status_code': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        elif isinstance(exc, Http404):
            logger.warning(f"404 Error: {exc}")
            return Response({
                'error': True,
                'message': 'Resource not found',
                'details': str(exc),
                'status_code': status.HTTP_404_NOT_FOUND
            }, status=status.HTTP_404_NOT_FOUND)
        
        else:
            # Log unexpected errors
            logger.error(f"Unexpected Error: {exc}", exc_info=True, extra={
                'view': context.get('view'),
                'request': context.get('request'),
            })
            
            return Response({
                'error': True,
                'message': 'Internal server error',
                'details': 'An unexpected error occurred. Please try again later.',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response 