from rest_framework import serializers
from .models import Client, Payment, Review
from django.contrib.auth import get_user_model
from core.serializers import ClubSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class ClientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    clubs = ClubSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = ('id', 'user', 'date_of_birth', 'clubs')

class PaymentSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    club = ClubSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ('id', 'client', 'club', 'amount', 'date')

class ReviewSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    club = ClubSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'client', 'club', 'rating', 'text')
