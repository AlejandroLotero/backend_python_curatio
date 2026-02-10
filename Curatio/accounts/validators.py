from django.core.exceptions import ValidationError

class MaxLengthValidator:
    def __init__(self, max_length=10):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                f"La contraseña es demasiado larga (máximo {self.max_length} caracteres).",
                code='password_too_long',
            )

    def get_help_text(self):
        return f"Tu contraseña no puede tener más de {self.max_length} caracteres."