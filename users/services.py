"""
User services.
"""

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


class UserService:
    @staticmethod
    def get_or_create_token(user):
        token, created = Token.objects.get_or_create(user=user)
        return token.key

    @staticmethod
    def delete_token(user):
        try:
            token = Token.objects.get(user=user)
            token.delete()
        except Token.DoesNotExist:
            pass

    @staticmethod
    def get_user_by_username(username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @staticmethod
    def update_user_password(user, new_password):
        user.set_password(new_password)
        user.save()
        return user
