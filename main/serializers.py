from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, PasswordResetCode
from django.utils import timezone
from datetime import timedelta
from .utils import generate_reset_code

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(write_only=True)
    birth_date = serializers.DateField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name',
            'phone_number', 'birth_date',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Пароли не совпадают")
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2')
        phone_number = validated_data.pop('phone_number')
        birth_date = validated_data.pop('birth_date')

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        UserProfile.objects.create(
            user=user,
            phone_number=phone_number,
            birth_date=birth_date
        )

        return user

class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email не найден")
        return value

    def create(self, validated_data):
        user = User.objects.get(email=validated_data['email'])
        last_code = PasswordResetCode.objects.filter(user=user).order_by('-created_at').first()
        if last_code and last_code.created_at + timedelta(seconds=30) > timezone.now():
            raise serializers.ValidationError("Подожди 30 секунд перед повторным запросом")

        code = generate_reset_code()
        PasswordResetCode.objects.create(user=user, code=code)

        print(f"Отправляем код {code} на {user.email}")

        return {'email': user.email}

class ConfirmPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4)
    new_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден")

        reset_code = PasswordResetCode.objects.filter(user=user, code=attrs['code']).order_by('-created_at').first()
        if not reset_code:
            raise serializers.ValidationError("Неверный код")

        if reset_code.is_expired():
            raise serializers.ValidationError("Код просрочен")

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
