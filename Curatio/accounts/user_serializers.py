# Serialización de usuarios para respuestas API (perfil, sesión, listados).
# La contraseña y datos internos sensibles no se incluyen nunca.


def serialize_user_for_profile(user, *, viewer_is_admin: bool):
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
        "photo": user.foto.url if user.foto else None,
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
