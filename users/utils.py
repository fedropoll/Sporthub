import random
from django.core.mail import send_mail
from django.conf import settings
from .models import PasswordResetCode


def generate_and_send_code(user):
    PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

    code = f"{random.randint(1000, 9999)}"
    PasswordResetCode.objects.create(user=user, code=code)

    try:
        send_mail(
            subject="Код подтверждения SportHub",
            message=f"Ваш код подтверждения: {code}\n\nКод действителен 10 минут.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False
