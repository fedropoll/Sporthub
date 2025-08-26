from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class Command(BaseCommand):
    help = 'Проверка уникальности JWT токенов'

    def handle(self, *args, **options):
        users = User.objects.all()[:3]  # Проверяем первых 3 пользователей

        self.stdout.write("=" * 60)
        self.stdout.write("ПРОВЕРКА УНИКАЛЬНОСТИ JWT ТОКЕНОВ")
        self.stdout.write("=" * 60)

        for i, user in enumerate(users):
            refresh = RefreshToken.for_user(user)

            self.stdout.write(
                f"\nПользователь {i + 1}: {user.email}\n"
                f"User ID: {user.id}\n"
                f"Access Token: {refresh.access_token}\n"
                f"Refresh Token: {refresh}\n"
                f"Token payload user_id: {refresh.payload.get('user_id')}\n"
                f"Token jti: {refresh.payload.get('jti')}\n"
                f"{'-' * 40}"
            )

        # Проверяем, что токены действительно разные
        if len(users) >= 2:
            user1_refresh = RefreshToken.for_user(users[0])
            user2_refresh = RefreshToken.for_user(users[1])

            self.stdout.write(f"\nСРАВНЕНИЕ ТОКЕНОВ:")
            self.stdout.write(f"Access tokens разные: {user1_refresh.access_token != user2_refresh.access_token}")
            self.stdout.write(f"Refresh tokens разные: {user1_refresh != user2_refresh}")
            self.stdout.write(f"JTI разные: {user1_refresh.payload.get('jti') != user2_refresh.payload.get('jti')}")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("ПРОВЕРКА ЗАВЕРШЕНА")
        self.stdout.write("=" * 60)