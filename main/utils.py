import random
from django.core.mail import send_mail
from .models import PasswordResetCode
from django.conf import settings

def generate_and_send_code(user):
    code = f"{random.randint(1000, 9999)}"
    PasswordResetCode.objects.create(user=user, code=code)

    send_mail(
        subject="Ваш код подтверждения",
        message=f"Ваш код подтверждения: {code}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
    )
