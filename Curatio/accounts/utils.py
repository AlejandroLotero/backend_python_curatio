#GENERADOR DE CONTRASEÑA SEGURA
import random
import string

def generar_password():
    caracteres = string.ascii_letters + string.digits + "!@#$%&*"

    while True:
        password = ''.join(random.choice(caracteres) for _ in range(10))

        if (any(c.isupper() for c in password) and
            any(c.islower() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in "!@#$%&*" for c in password)):
            return password

