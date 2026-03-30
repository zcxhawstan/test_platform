"""
User views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from utils.response import APIResponse
from utils.permissions import IsAdminUser
from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    UserLoginSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer
)
from .services import UserService

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register', 'login']:
            return [AllowAny()]
        elif self.action in ['destroy', 'update_role']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'register':
            return UserRegisterSerializer
        elif self.action == 'login':
            return UserLoginSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = UserService.get_or_create_token(user)
        return APIResponse.created({
            'user': UserSerializer(user).data,
            'token': token
        }, '注册成功')

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=username, password=password)
        if not user:
            return APIResponse.error('用户名或密码错误', 400)
        
        if not user.is_active:
            return APIResponse.error('账号已被禁用', 403)
        
        login(request, user)
        token = UserService.get_or_create_token(user)
        
        return APIResponse.success({
            'user': UserSerializer(user).data,
            'token': token
        }, '登录成功')

    @action(detail=False, methods=['post'])
    def logout(self, request):
        UserService.delete_token(request.user)
        logout(request)
        return APIResponse.success(message='退出成功')

    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return APIResponse.success(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        UserService.update_user_password(request.user, serializer.validated_data['new_password'])
        return APIResponse.success(message='密码修改成功')

    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def update_role(self, request, pk=None):
        user = self.get_object()
        role = request.data.get('role')
        if role not in ['admin', 'tester_dev', 'tester']:
            return APIResponse.error('无效的角色', 400)
        user.role = role
        user.save()
        return APIResponse.success(UserSerializer(user).data, '角色更新成功')
