"""
Custom exception handler for REST framework.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
import traceback

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'code': response.status_code,
            'message': response.data.get('detail', str(response.data)),
            'data': None
        }
        response.data = custom_response_data
        logger.error(f"Exception: {exc}, Context: {context}")
        print(f"[ERROR] Exception: {exc}")
        traceback.print_exc()
    else:
        logger.error(f"Unhandled exception: {exc}, Context: {context}")
        print(f"[ERROR] Unhandled exception: {exc}")
        traceback.print_exc()
        custom_response_data = {
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'message': '服务器内部错误',
            'data': None
        }
        response = Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response


class BusinessException(Exception):
    def __init__(self, message, code=400):
        self.message = message
        self.code = code
        super().__init__(self.message)
