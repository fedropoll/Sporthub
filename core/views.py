from rest_framework import viewsets
from .models import Hall, Trainer, Club
from .serializers import HallSerializer, TrainerSerializer, ClubSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class HallViewSet(viewsets.ModelViewSet):
    queryset = Hall.objects.all()
    serializer_class = HallSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class TrainerViewSet(viewsets.ModelViewSet):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class ClubViewSet(viewsets.ModelViewSet):
    queryset = Club.objects.all()
    serializer_class = ClubSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
