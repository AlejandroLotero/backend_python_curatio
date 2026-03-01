# API de Medicamentos - Documentación

## Requerimientos Implementados

- **RFADMIN08**: Registrar medicamento
- **RFADMIN09**: Visualizar medicamento

## Endpoints

### 1. Buscar Medicamento por ID
**Endpoint**: `GET /api/medicines/search_by_id/?id={id}`

**Autenticación**: Requerida (cualquier usuario autenticado)

**Parámetros**:
- `id` (requerido): ID del medicamento

**Respuesta Exitosa** (200):
```json
{
  "id": 1,
  "name": "Ibuprofeno",
  "description": "Analgésico y antiinflamatorio",
  "active_ingredient": "Ibuprofeno",
  "concentration": "400mg",
  "presentation": "Tableta",
  "laboratory": "Laboratorio A",
  "registration_number": "REG001",
  "stock_quantity": 100,
  "minimum_stock": 10,
  "unit_price": "5.99",
  "manufacture_date": "2024-01-15",
  "expiration_date": "2025-01-15",
  "is_active": true,
  "state": "AVAILABLE",
  "is_expired": false,
  "days_to_expire": 350,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Errores**:
- 400: ID inválido o faltante
- 404: Medicamento no encontrado

---

### 2. Buscar Medicamento por Nombre
**Endpoint**: `GET /api/medicines/search_by_name/?name={nombre}`

**Autenticación**: Requerida

**Parámetros**:
- `name` (requerido): Nombre del medicamento

**Respuesta - Coincidencia Exacta** (200):
```json
{
  "type": "exact_match",
  "medicine": {
    "id": 1,
    "name": "Ibuprofeno",
    ...
  },
  "suggestions": []
}
```

**Respuesta - Sugerencias** (200):
```json
{
  "type": "suggestions",
  "medicine": null,
  "suggestions": [
    {
      "id": 1,
      "name": "Ibuprofeno",
      "concentration": "400mg",
      "similarity_score": 95.6
    }
  ],
  "message": "No se encontró coincidencia exacta. Se muestran 1 sugerencia(s) similar(es)."
}
```

**Respuesta - No Encontrado** (404):
```json
{
  "type": "not_found",
  "medicine": null,
  "suggestions": [],
  "detail": "No se encontró medicamento con el nombre \"NombreInexistente\""
}
```

---

### 3. Visualizar Medicamento (Solo Lectura)
**Endpoint**: `GET /api/medicines/{id}/retrieve_readonly/`

**Autenticación**: Requerida

**Parámetros**: Ninguno

**Respuesta Exitosa** (200):
- Retorna el medicamento completo con todos los campos de solo lectura

**Errores**:
- 404: Medicamento no encontrado

---

### 4. Registrar Medicamento (RFADMIN08)
**Endpoint**: `POST /api/medicines/`

**Autenticación**: Requerida como ADMIN

**Permisos**: Solo ADMIN

**Body**:
```json
{
  "name": "Amoxicilina",
  "description": "Antibiótico",
  "active_ingredient": "Amoxicilina",
  "concentration": "500mg",
  "presentation": "Cápsula",
  "laboratory": "Laboratorio B",
  "registration_number": "REG002",
  "stock_quantity": 50,
  "minimum_stock": 15,
  "unit_price": "8.50",
  "manufacture_date": "2024-01-15",
  "expiration_date": "2025-01-15",
  "is_active": true,
  "state": "AVAILABLE"
}
```

**Respuesta Exitosa** (201):
- Retorna el medicamento creado con ID

**Errores**:
- 400: Datos inválidos o falta de campos requeridos
- 403: No tiene permisos de ADMIN

---

## Reglas de Negocio Implementadas

### RFADMIN09:

1. **Solo lectura**: La información mostrada no permite edición
   - Todos los campos en `retrieve_readonly/` son read-only
   - Vista separada sin acceso a actualización

2. **Coincidencia exacta**:
   - Búsqueda por ID debe ser identificador numérico exacto
   - Búsqueda por nombre es case-insensitive pero debe ser nombre completo

3. **Sugerencias fuzzy**:
   - Si difiere en 1-2 letras (similitud >= 85%), se muestra como sugerencia
   - Máximo 5 sugerencias ordenadas por similitud
   - Usa algoritmo SequenceMatcher de difflib

---

## Validaciones

- Las fechas de caducidad deben ser posteriores a manufactura
- Stock mínimo no puede ser negativo
- Precio unitario no puede ser negativo
- Nombre y número de registro deben ser únicos

---

## Campos Calculados

- **is_expired**: Boolean que indica si el medicamento ha expirado
- **days_to_expire**: Cantidad de días hasta la expiración (negativo si ya expiró)

---

## Ejemplos de Uso

### Con cURL:

```bash
# Buscar por ID
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/medicines/search_by_id/?id=1"

# Buscar por nombre exacto
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/medicines/search_by_name/?name=Ibuprofeno"

# Búsqueda con sugerencias
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/medicines/search_by_name/?name=Ibuprofen"

# Ver medicamento en modo solo lectura
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/medicines/1/retrieve_readonly/"

# Registrar medicamento (solo ADMIN)
curl -X POST -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Amoxicilina",
    "active_ingredient": "Amoxicilina",
    "concentration": "500mg",
    "presentation": "Cápsula",
    "laboratory": "Lab B",
    "registration_number": "REG002",
    "stock_quantity": 50,
    "minimum_stock": 15,
    "unit_price": "8.50",
    "manufacture_date": "2024-01-15",
    "expiration_date": "2025-01-15"
  }' \
  "http://localhost:8000/api/medicines/"
```

---

## Próximos Pasos

1. Ejecutar migraciones:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. Crear un superuser para acceso al admin:
   ```bash
   python manage.py createsuperuser
   ```

3. Ejecutar tests:
   ```bash
   python manage.py test medicines
   ```

4. Iniciar el servidor:
   ```bash
   python manage.py runserver
   ```
