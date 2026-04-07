# Serialización de usuarios para respuestas API (perfil, sesión, listados).
# La contraseña y datos internos sensibles no se incluyen nunca.


def _build_media_absolute_url(request, file_field):
    """
    URL absoluta del archivo en MEDIA (misma idea que products.api_views._build_media_url)
    para que el SPA en otro origen pueda mostrar la imagen.
    """
    if not request or not file_field:
        return None
    try:
        return request.build_absolute_uri(file_field.url)
    except Exception:
        return None


def _user_photo_url(user, request):
    if not user.foto:
        return None
    absolute_url = _build_media_absolute_url(request, user.foto)
    if absolute_url:
        return absolute_url
    try:
        return user.foto.url
    except Exception:
        return None


def serialize_user_for_profile(user, *, viewer_is_admin: bool, request=None):
    """
    Datos de cuenta en solo lectura.
    Si quien consulta es ADMIN: incluye estado, fechas de registro/actualización y último acceso.
    Si no es ADMIN: solo ve su perfil sin esos campos (reglas de negocio FFARMA02).
    """
    data = {
        "id": user.id,
        "name": user.nombre,
        "email": user.email,
        "role": user.rol,
        "document_type": user.tipo_documento,
        "document_number": user.numero_documento,
        "phone": user.telefono,
        "secondary_phone": user.telefono_secundario,
        "address": user.direccion,
        "photo": _user_photo_url(user, request),
        "start_date": user.fecha_inicio.isoformat() if user.fecha_inicio else None,
        "end_date": user.fecha_fin.isoformat() if user.fecha_fin else None,
        "email_confirmed": getattr(user, "email_confirmed", True),
    }
    if viewer_is_admin:
        data["is_active"] = user.estado
        data["created_at"] = user.creado_en.isoformat() if user.creado_en else None
        data["updated_at"] = user.actualizado_en.isoformat() if user.actualizado_en else None
        last = getattr(user, "last_login", None)
        data["last_login"] = last.isoformat() if last else None
    return data
