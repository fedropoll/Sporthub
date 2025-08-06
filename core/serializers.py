from rest_framework import serializers
from .models import Hall, Trainer, Club
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class HallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hall
        fields = ('id', 'name', 'address', 'phone', 'working_hours')

class TrainerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    hall = HallSerializer(read_only=True)

    class Meta:
        model = Trainer
        fields = ('id', 'user', 'hall', 'bio')

class ClubSerializer(serializers.ModelSerializer):
    trainer = TrainerSerializer(read_only=True)
    hall = HallSerializer(read_only=True)

    class Meta:
        model = Club
        fields = ('id', 'name', 'trainer', 'hall', 'schedule')
