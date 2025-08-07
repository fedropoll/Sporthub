from django.db import models
from django.contrib.auth import get_user_model
from halls.models import Hall
from trainers.models import Trainer

User = get_user_model()

class Club(models.Model):
    name = models.CharField(max_length=100)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True, related_name='clubs')
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='clubs')
    schedule = models.JSONField(default=dict, blank=True)
    members = models.ManyToManyField(User, related_name='clubs', blank=True)

    def __str__(self):
        return self.name