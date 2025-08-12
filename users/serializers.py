from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from .models import (
    UserProfile, PasswordResetCode, Ad, Hall, Club, Trainer,
    Review, Notification, ClassSchedule, Joinclub, Payment, Attendance
)
from .utils import generate_and_send_code

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username']


class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Введите ваш email. На него придет код подтверждения.")
    password = serializers.CharField(write_only=True, min_length=8, help_text="Пароль должен содержать минимум 8 символов.")
    confirmPassword = serializers.CharField(write_only=True, help_text="Повторите пароль для подтверждения.")
    firstName = serializers.CharField(max_length=30, help_text="Ваше имя.")
    lastName = serializers.CharField(max_length=30, help_text="Ваша фамилия.")
    phone_number = serializers.CharField(max_length=20, help_text="Ваш номер телефона (например, +996123456789).")
    birth_date = serializers.DateField(help_text="Дата рождения в формате ГГГГ-ММ-ДД (например, 2000-01-01).")
    gender = serializers.CharField(max_length=10, required=False, help_text="Пол пользователя.")
    address = serializers.CharField(max_length=100, required=False, help_text="Адрес проживания.")
    remember = serializers.BooleanField(default=False, required=False, help_text="Запомнить меня на этом устройстве?")

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise ValidationError({"confirmPassword": "Пароли не совпадают"})
        if User.objects.filter(email=data['email']).exists():
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
            phone_number=validated_data.get('phone_number'),
            birth_date=validated_data.get('birth_date'),
            gender=validated_data.get('gender', ''),
            address=validated_data.get('address', '')
        )
        generate_and_send_code(user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'birth_date', 'has_paid', 'sport']
        read_only_fields = ['has_paid', 'sport']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.birth_date = validated_data.get('birth_date', instance.birth_date)
        instance.save()

        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.email = user_data.get('email', user.email)
        user.save()

        return instance


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_new_password = serializers.CharField(required=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "Новые пароли не совпадают"})

        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": "Неверный старый пароль"})
        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()


class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4, min_length=4)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise ValidationError({"email": "Пользователь не найден"})

        try:
            reset_code = PasswordResetCode.objects.filter(user=user, is_used=False).latest('created_at')
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
    remember = serializers.BooleanField(default=False, required=False)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise ValidationError("Необходимо ввести email и пароль.")

        user = authenticate(request=self.context.get('request'), username=email, password=password)

        if not user:
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    raise ValidationError("Неверный пароль.")
            except User.DoesNotExist:
                raise ValidationError("Пользователь с таким email не найден.")

        if not user.is_active:
            raise ValidationError("Аккаунт не активирован. Проверьте почту.")

        data['user'] = user
        return data


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
            reset_code = PasswordResetCode.objects.filter(user=user, is_used=False).latest('created_at')
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

        user.set_password(self.validated_data['new_password'])
        user.save()

        reset_code.is_used = True
        reset_code.save()

        return user


class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = '__all__'


class HallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hall
        fields = '__all__'
        ref_name = 'UserHall'  # добавлено уникальное имя


class ClassScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSchedule
        fields = ['id', 'title', 'day_of_week', 'start_time', 'end_time']


class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = '__all__'
        ref_name = 'UserClub'


class JoinclubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Joinclub
        fields = ['id', 'user', 'schedule', 'registration_date', 'age_group']


class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = '__all__'


class TrainerNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = ['first_name', 'last_name']


class PaymentSerializer(serializers.ModelSerializer):
    stripe_payment_intent_id = serializers.CharField(max_length=50, required=False, allow_blank=True)

    class Meta:
        model = Payment
        fields = ['id', 'joinclub', 'stripe_payment_intent_id', 'amount', 'payment_date']


class ClientDetailSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    trainer = TrainerNameSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'first_name', 'last_name', 'trainer', 'sport', 'has_paid']


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['id', 'joinclub', 'attendance_date', 'is_present', 'notes']


class ReviewSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    trainer_name = serializers.CharField(source='trainer.first_name', read_only=True)
    club_name = serializers.CharField(source='club.title', read_only=True)

    def get_user_info(self, obj):
        return {
            'username': obj.user.username,
            'email': obj.user.email
        }

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_info', 'trainer', 'trainer_name',
            'club', 'club_name', 'text', 'rating', 'created_at'
        ]
        read_only_fields = ['id', 'user_info', 'trainer_name', 'club_name', 'created_at']
        ref_name = 'UserReview'  # добавлено уникальное имя


class NotificationSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()

    def get_user_info(self, obj):
        if obj.user:
            return {
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None

    class Meta:
        model = Notification
        fields = ['id', 'user', 'user_info', 'message', 'type', 'is_read', 'created_at']
        read_only_fields = ['id', 'user', 'user_info', 'message', 'type', 'created_at']
