"""
Standard API response format.
"""

from rest_framework.response import Response
from rest_framework import status


class APIResponse:
    @staticmethod
    def success(data=None, message="操作成功", code=200):
        return Response({
            'code': code,
            'message': message,
            'data': data
        }, status=status.HTTP_200_OK)

    @staticmethod
    def error(message="操作失败", code=400, data=None):
        return Response({
            'code': code,
            'message': message,
            'data': data
        }, status=code)

    @staticmethod
    def created(data=None, message="创建成功"):
        return Response({
            'code': 201,
            'message': message,
            'data': data
        }, status=status.HTTP_201_CREATED)

    @staticmethod
    def not_found(message="资源不存在"):
        return Response({
            'code': 404,
            'message': message,
            'data': None
        }, status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def unauthorized(message="未授权"):
        return Response({
            'code': 401,
            'message': message,
            'data': None
        }, status=status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def forbidden(message="无权限访问"):
        return Response({
            'code': 403,
            'message': message,
            'data': None
        }, status=status.HTTP_403_FORBIDDEN)
