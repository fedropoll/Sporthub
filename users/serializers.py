from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, PasswordResetCode
from .utils import generate_and_send_code
from rest_framework.exceptions import ValidationError

User = get_user_model()


class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Введите ваш email. На него придет код подтверждения."
    )
    password = serializers.CharField(
        write_only=True, min_length=8,
        help_text="Пароль должен содержать минимум 8 символов."
    )
    confirmPassword = serializers.CharField(
        write_only=True,
        help_text="Повторите пароль для подтверждения."
    )
    firstName = serializers.CharField(
        max_length=30,
        help_text="Ваше имя."
    )
    lastName = serializers.CharField(
        max_length=30,
        help_text="Ваша фамилия."
    )
    phone_number = serializers.CharField(
        max_length=20,
        help_text="Ваш номер телефона (например, +996123456789)."
    )
    birth_date = serializers.DateField(
        help_text="Дата рождения в формате ГГГГ-ММ-ДД (например, 2000-01-01)."
    )
    remember = serializers.BooleanField(
        default=False,
        help_text="Запомнить меня на этом устройстве?"
    )

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise ValidationError({"confirmPassword": "Пароли не совпадают"})
        if User.objects.filter(email=data['email']).exists():
            raise ValidationError({"email": "Пользователь с таким email уже существует"})
        if User.objects.filter(username=data['email']).exists():
            raise ValidationError({"email": "Пользователь с таким email уже существует"})
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
    code = serializers.CharField(max_length=4, min_length=4)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise ValidationError({"email": "Пользователь не найден"})
        try:
            reset_code = PasswordResetCode.objects.filter(
                user=user,
                is_used=False
            ).latest('created_at')
        except PasswordResetCode.DoesNotExist:
            raise ValidationError({"code": "Код не найден или уже использован"})
        if reset_code.code != data['code']:
            raise ValidationError({"code": "Неверный код"})
        if reset_code.is_expired():
            raise ValidationError({"code": "Код истек. Запросите новый"})
        user.is_active = True
        user.save()
        reset_code.is_used = True
        reset_code.save()
        data['user'] = user
        return data


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    remember = serializers.BooleanField(default=False)


# --- Вот этот код нужно добавить ---
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise ValidationError("Пользователь с таким email не найден.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4, min_length=4)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise ValidationError({"confirm_new_password": "Пароли не совпадают"})
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise ValidationError({"email": "Пользователь не найден"})
        try:
            reset_code = PasswordResetCode.objects.filter(
                user=user,
                is_used=False
            ).latest('created_at')
        except PasswordResetCode.DoesNotExist:
            raise ValidationError({"code": "Код не найден или уже использован"})
        if reset_code.code != data['code']:
            raise ValidationError({"code": "Неверный код"})
        if reset_code.is_expired():
            raise ValidationError({"code": "Код истек. Запросите новый"})
        data['user'] = user
        data['reset_code'] = reset_code
        return data