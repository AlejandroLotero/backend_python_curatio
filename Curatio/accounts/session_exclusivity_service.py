from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import ExclusiveSession


class SessionExclusivityService:
    @staticmethod
    def get_lock_for_user(user):
        return ExclusiveSession.objects.filter(user=user).first()

    @staticmethod
    @transaction.atomic
    def acquire_or_detect_conflict(user, session_key, client_instance_id):
        current_lock = (
            ExclusiveSession.objects.select_for_update()
            .filter(user=user)
            .first()
        )

        now = timezone.now()

        if current_lock is None:
            lock = ExclusiveSession.objects.create(
                user=user,
                session_key=session_key,
                client_instance_id=client_instance_id,
                acquired_at=now,
                last_seen_at=now,
                replaced_at=None,
                is_active=True,
            )
            return {"success": True, "lock": lock, "conflict": None}

        same_owner = (
            current_lock.is_active
            and current_lock.session_key == session_key
            and current_lock.client_instance_id == client_instance_id
        )

        if same_owner:
            current_lock.last_seen_at = now
            current_lock.save(update_fields=["last_seen_at"])
            return {"success": True, "lock": current_lock, "conflict": None}

        # Detectar lock huérfano: la sesión real ya no existe
        session_exists = Session.objects.filter(
            session_key=current_lock.session_key
        ).exists()

        # Detectar lock vencido por inactividad
        timeout_seconds = settings.SESSION_CONFIG["INACTIVITY_TIMEOUT"]
        is_stale = current_lock.last_seen_at < now - timedelta(seconds=timeout_seconds)

        if current_lock.is_active and (not session_exists or is_stale):
            current_lock.session_key = session_key
            current_lock.client_instance_id = client_instance_id
            current_lock.acquired_at = now
            current_lock.last_seen_at = now
            current_lock.replaced_at = None
            current_lock.is_active = True
            current_lock.save()

            return {"success": True, "lock": current_lock, "conflict": None}

        if current_lock.is_active:
            return {"success": False, "lock": None, "conflict": current_lock}

        current_lock.session_key = session_key
        current_lock.client_instance_id = client_instance_id
        current_lock.acquired_at = now
        current_lock.last_seen_at = now
        current_lock.replaced_at = None
        current_lock.is_active = True
        current_lock.save()

        return {"success": True, "lock": current_lock, "conflict": None}

    @staticmethod
    @transaction.atomic
    def force_takeover(user, new_session_key, new_client_instance_id):
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
        ExclusiveSession.objects.filter(
            user=user,
            session_key=session_key,
            is_active=True,
        ).update(
            is_active=False,
            replaced_at=timezone.now(),
        )