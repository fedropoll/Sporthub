from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, PasswordResetCode, ClassSchedule, Joinclub, Payment, Attendance
from .utils import generate_and_send_code
from rest_framework.exceptions import ValidationError


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirmPassword = serializers.CharField(write_only=True)
    firstName = serializers.CharField(max_length=30)
    lastName = serializers.CharField(max_length=30)
    phone_number = serializers.CharField(max_length=20)
    birth_date = serializers.DateField()
    remember = serializers.BooleanField(default=False)

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

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise ValidationError({"email": "Пользователь с таким email не найден"})

        if not user.check_password(data['password']):
            raise ValidationError({"password": "Неверный пароль"})

        if not user.is_active:
            raise ValidationError({"email": "Аккаунт не активирован. Проверьте почту"})

        data['user'] = user
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise ValidationError("Аккаунт не активирован")
        except User.DoesNotExist:
            raise ValidationError("Пользователь с таким email не найден")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4, min_length=4)
    password = serializers.CharField(write_only=True, min_length=8)
    confirmPassword = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise ValidationError({"confirmPassword": "Пароли не совпадают"})

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

    def save(self):
        user = self.validated_data['user']
        reset_code = self.validated_data['reset_code']

        user.set_password(self.validated_data['password'])
        user.save()

        reset_code.is_used = True
        reset_code.save()

        return user

class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)  # Email читается только для отображения
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)

    class Meta:
        model = UserProfile
        fields = ['id', 'phone_number', 'birth_date', 'address', 'gender', 'email', 'first_name', 'last_name']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.birth_date = validated_data.get('birth_date', instance.birth_date)
        instance.address = validated_data.get('address', instance.address)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.save()

        # Обновление связанных полей пользователя
        user = instance.user
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.save()

        return instance

class ClassScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSchedule
        fields = ['id', 'title', 'day_of_week', 'start_time', 'end_time',]

class JoinclubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Joinclub
        fields = ['id', 'user', 'schedule', 'registration_date', 'age_group']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'joinclub', 'card_number', 'amount', 'payment_date']

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['id', 'joinclub', 'attendance_date', 'is_present', 'notes']

    def create(self, validated_data):
        joinclub = self.context.get('joinclub')
        return Attendance.objects.create(joinclub=joinclub, **validated_data)