import random

def generate_and_send_code(user):
    """
    Генерирует 6-значный код и отправляет пользователю (пока просто выводим в консоль).
    """
    code = str(random.randint(100000, 999999))
    print(f"Код для {user.email if hasattr(user, 'email') else user}: {code}")
    return code
