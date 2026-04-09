from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone

from .models import ExclusiveSession


class SessionExclusivityService:
    """
    Servicio de dominio para controlar la política de sesión exclusiva.

    Responsabilidades:
    - Detectar conflictos de sesión.
    - Transferir la posesión de la cuenta.
    - Invalidar la sesión previa si el usuario decide quedarse en la nueva.
    """

    @staticmethod
    def get_lock_for_user(user):
        """
        Retorna el registro de exclusividad del usuario, exista o no activo.
        Como la relación es OneToOne, solo debería existir uno.
        """
        return ExclusiveSession.objects.filter(user=user).first()

    @staticmethod
    @transaction.atomic
    def acquire_or_detect_conflict(user, session_key, client_instance_id):
        """
        Intenta registrar la sesión actual como dueña.

        Casos:
        - Si no existe registro, lo crea.
        - Si el registro pertenece a esta misma pestaña/sesión, renueva actividad.
        - Si existe otra sesión activa distinta, informa conflicto.
        - Si existe un registro inactivo o huérfano, reutiliza el mismo registro.
        """
        current_lock = (
            ExclusiveSession.objects.select_for_update()
            .filter(user=user)
            .first()
        )

        # Caso 1: no existe ningún registro todavía para este usuario
        if current_lock is None:
            lock = ExclusiveSession.objects.create(
                user=user,
                session_key=session_key,
                client_instance_id=client_instance_id,
                acquired_at=timezone.now(),
                last_seen_at=timezone.now(),
                replaced_at=None,
                is_active=True,
            )
            return {
                "success": True,
                "lock": lock,
                "conflict": None,
            }

        # Caso 2: ya es esta misma sesión / misma pestaña
        same_owner = (
            current_lock.is_active
            and current_lock.session_key == session_key
            and current_lock.client_instance_id == client_instance_id
        )

        if same_owner:
            current_lock.last_seen_at = timezone.now()
            current_lock.save(update_fields=["last_seen_at"])
            return {
                "success": True,
                "lock": current_lock,
                "conflict": None,
            }

        # Caso 3: existe otra sesión activa distinta => conflicto real
        if current_lock.is_active:
            return {
                "success": False,
                "lock": None,
                "conflict": current_lock,
            }

        # Caso 4: existe registro pero está inactivo.
        # No intentamos crear otro porque el user es OneToOne.
        # Reutilizamos el mismo registro.
        current_lock.session_key = session_key
        current_lock.client_instance_id = client_instance_id
        current_lock.acquired_at = timezone.now()
        current_lock.last_seen_at = timezone.now()
        current_lock.replaced_at = None
        current_lock.is_active = True
        current_lock.save()

        return {
            "success": True,
            "lock": current_lock,
            "conflict": None,
        }

    @staticmethod
    @transaction.atomic
    def force_takeover(user, new_session_key, new_client_instance_id):
        """
        Fuerza la toma de control de la cuenta desde una nueva sesión.

        Lógica:
        - Si existe una sesión previa activa y es distinta, se elimina
          la sesión anterior de Django.
        - Luego se actualiza o crea el registro exclusivo del usuario.
        """
        current_lock = (
            ExclusiveSession.objects.select_for_update()
            .filter(user=user)
            .first()
        )

        if current_lock and current_lock.is_active and current_lock.session_key != new_session_key:
            Session.objects.filter(session_key=current_lock.session_key).delete()

        lock, _ = ExclusiveSession.objects.update_or_create(
            user=user,
            defaults={
                "session_key": new_session_key,
                "client_instance_id": new_client_instance_id,
                "is_active": True,
                "acquired_at": timezone.now(),
                "last_seen_at": timezone.now(),
                "replaced_at": None,
            },
        )

        return lock

    @staticmethod
    def release_if_owner(user, session_key):
        """
        Libera la exclusividad solamente si la sesión actual era la dueña.
        """
        ExclusiveSession.objects.filter(
            user=user,
            session_key=session_key,
            is_active=True,
        ).update(
            is_active=False,
            replaced_at=timezone.now(),
        )