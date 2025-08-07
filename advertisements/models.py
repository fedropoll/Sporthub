from django.db import models
from halls.models import Hall


class Advertisement(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    phone = models.CharField(max_length=20)
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='advertisements')
    images = models.JSONField(default=list, blank=True)
    working_hours = models.JSONField(default=dict, blank=True)
    website_name = models.CharField(max_length=100, blank=True)
    website_url = models.URLField(max_length=200, blank=True)
    installment_plan = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.title