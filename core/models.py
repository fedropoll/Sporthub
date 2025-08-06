from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Hall(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    working_hours = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hall = models.ForeignKey(Hall, on_delete=models.SET_NULL, null=True, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email

class Club(models.Model):
    name = models.CharField(max_length=100)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True)
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    schedule = models.TextField(blank=True)  # Можно потом сделать отдельной моделью для расписания

    def __str__(self):
        return self.name
