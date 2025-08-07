from django.db import models
from django.contrib.auth import get_user_model
from halls.models import Hall
from clubs.models import Club

User = get_user_model()

class Review(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.hall:
            return f"Review by {self.user.username} for {self.hall.name}"
        elif self.club:
            return f"Review by {self.user.username} for {self.club.name}"
        return f"Review by {self.user.username}"

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment by {self.user.username} for {self.amount}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"