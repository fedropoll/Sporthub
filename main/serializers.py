from django.contrib.auth.models import User
from .models import UserProfile, PasswordResetCode
from .utils import generate_and_send_code
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirmPassword = serializers.CharField(write_only=True)
    firstName = serializers.CharField()
    lastName = serializers.CharField()
    phone_number = serializers.CharField()
    birth_date = serializers.DateField()

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise serializers.ValidationError("Пароли не совпадают")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['firstName'],
            last_name=validated_data['lastName'],
            is_active=False
        )
        UserProfile.objects.create(
            user=user,
            phone_number=validated_data['phone_number'],
            birth_date=validated_data['birth_date']
        )
        generate_and_send_code(user)
        return user


class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.RegexField(regex=r'^\d{4}$')

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден")

        try:
            reset_code = PasswordResetCode.objects.filter(user=user).latest('created_at')
        except PasswordResetCode.DoesNotExist:
            raise serializers.ValidationError("Код не найден")

        if reset_code.code != data['code']:
            raise serializers.ValidationError("Неверный код")
        if reset_code.is_expired():
            raise serializers.ValidationError("Код истек")

        user.is_active = True
        user.save()
        return data



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Нет пользователя с таким email")

        if not user.check_password(password):
            raise AuthenticationFailed("Неверный пароль")
        if not user.is_active:
            raise AuthenticationFailed("Пользователь не активирован")

        return super().validate({
            "username": user.username,
            "password": password
        })
# https://github.com/fedropoll/Klub


User = get_user_model()

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    role = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        role = attrs.get("role")

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("Пользователь с таким email не найден")
        if not user.check_password(password):
            raise serializers.ValidationError("Неверный пароль")
        if not hasattr(user, 'user_profile'):
            raise serializers.ValidationError("Профиль пользователя не найден")
        if user.user_profile.role != role:
            raise serializers.ValidationError("Роль пользователя не совпадает")

        data = super().validate(attrs)
        data['role'] = user.user_profile.role
        data['email'] = user.email
        return data
