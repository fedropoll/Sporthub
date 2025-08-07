from django.db import models


class Hall(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    working_hours = models.JSONField(default=dict, blank=True)
    images = models.JSONField(default=list, blank=True)
    advantages = models.JSONField(default=list, blank=True)

    # Добавление полей из макета "Admin/Зал"
    size = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=50, blank=True)
    coating = models.CharField(max_length=50, blank=True)
    inventory = models.CharField(max_length=100, blank=True)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dressing_room = models.BooleanField(default=False)
    lighting = models.BooleanField(default=False)
    shower = models.BooleanField(default=False)

    def __str__(self):
        return self.name