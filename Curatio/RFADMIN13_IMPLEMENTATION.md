# RFADMIN13: Guía de Implementación - Generar Reportes de Medicamentos

## 📋 Cambios Realizados

### 1. ✅ Actualizaciones del Modelo (medicines/models.py)

Se actualizó el modelo `Medicine` con los siguientes campos y características:

#### Nuevos Campos Agregados:
- **pharmaceutical_form**: Forma farmacéutica (ESPECIAL, LIQUIDA, GASEOSA, SEMISÓLIDA, SOLIDA)
- **presentation**: Presentación con validación según forma farmacéutica
- **administration_route**: Vía de administración (Oral, Bucal, Intramuscular, etc.)
- **laboratory**: Laboratorio con opciones predefinidas
- **batch_number**: Número de lote
- **purchase_price**: Precio de compra
- **sale_price**: Precio de venta
- **supplier**: Proveedor
- **requires_formula**: Booleano indicando si requiere fórmula médica
- **state**: Estado mejorado (ACTIVO, VENCIDO, AGOTADO, SUSPENDIDO)

#### Nuevos Métodos:
- `update_state_automatically()`: Actualiza automáticamente el estado según reglas de negocio

---

### 2. ✅ Servicios de Reporte (medicines/report_service.py)

Se creó un nuevo archivo con tres clases principales:

#### `MedicineReportService`
- Filtrado de medicamentos por estado
- Preparación de datos para reportes
- Generación de metadatos

**Ejemplo de uso:**
```python
medicines = MedicineReportService.filter_medicines_by_state('ACTIVO')
report_data = MedicineReportService.prepare_report_data(medicines)
metadata = MedicineReportService.get_metadata('ACTIVO', request.user)
```

#### `ExcelReportGenerator`
- Genera reportes en formato Excel (.xlsx)
- Incluye encabezados formateados con colores
- Tabla de datos con información completa
- Resumen de conteos por estado

**Características:**
- Estilos profesionales con colores
- Ancho de columnas automático
- Colores diferenciados por estado (verde=Activo, naranja=Vencido, etc.)

#### `PDFReportGenerator`
- Genera reportes en formato PDF
- Diseño landscape para mejor visualización
- Tabla formateada y profesional
- Resumen al final

---

### 3. ✅ Endpoints API (medicines/views.py)

Se agregaron dos nuevas acciones al `MedicineViewSet`:

#### Generar Reporte Excel
```
GET /api/medicines/generate_excel_report/?state=ACTIVO
```

**Parámetros:**
- `state` (obtional): ACTIVO, VENCIDO, AGOTADO, SUSPENDIDO, TODOS (default: TODOS)

**Respuesta:**
- Descarga de archivo Excel

#### Generar Reporte PDF
```
GET /api/medicines/generate_pdf_report/?state=ACTIVO
```

**Parámetros:**
- `state` (opcional): ACTIVO, VENCIDO, AGOTADO, SUSPENDIDO, TODOS (default: TODOS)

**Respuesta:**
- Descarga de archivo PDF

---

### 4. ✅ Tests (medicines/tests.py)

Se agregaron **14 nuevos tests** para validar:

#### Tests de Generación de Reportes (RFADMIN13):
- ✓ Generar Excel con estado ACTIVO
- ✓ Generar Excel con TODOS
- ✓ Generar Excel con estado VENCIDO
- ✓ Generar Excel con estado AGOTADO
- ✓ Generar Excel con estado SUSPENDIDO
- ✓ Generar PDF con estado ACTIVO
- ✓ Generar PDF con TODOS
- ✓ Validar estado inválido
- ✓ Rechazar acceso sin autenticación
- ✓ Rechazar acceso de no-ADMIN
- ✓ Manejo de resultados vacíos

**Ejecutar tests:**
```bash
python manage.py test medicines.tests.MedicineReportTestCase
```

---

### 5. ✅ Serializers Actualizado (medicines/serializers.py)

Se actualizó `MedicineSerializer` para incluir:
- Todos los nuevos campos del modelo
- Campos de display legibles (ej: `pharmaceutical_form_display`)
- Métodos de solo lectura mejorados

---

### 6. ✅ Formulario Actualizado (medicines/forms.py)

Se actualizó `MedicineForm` con:
- Todos los nuevos campos del modelo
- Widgets HTML5 apropidados (date, number, select)
- Estilos CSS de Bootstrap

---

## 🚀 Instalación de Dependencias

Antes de usar la funcionalidad de reportes, instala las librerías requeridas:

```bash
pip install openpyxl reportlab
```

**Alternativa con requirements.txt:**
```
openpyxl==3.11.0
reportlab==4.0.9
```

---

## 📊 Estructura de Datos en Reportes

### Campos Incluidos en Reportes:
1. **Nombre** - Nombre del medicamento
2. **Forma Farmacéutica** - (Especial, Líquida, Gaseosa, Semisólida, Sólida)
3. **Presentación** - (Tableta, Cápsula, Inyectable, etc.)
4. **Concentración** - (400mg, 500mg, etc.)
5. **Vía de Administración** - (Oral, Intramuscular, etc.)
6. **Laboratorio** - (Bayer, Pfizer, Abbott, etc.)
7. **Lote** - Número de lote
8. **Fecha de Fabricación** - DD/MM/YYYY
9. **Fecha de Vencimiento** - DD/MM/YYYY
10. **Stock** - Cantidad en inventario
11. **Precio de Compra** - Formato: $0.00
12. **Precio de Venta** - Formato: $0.00
13. **Proveedor** - Nombre del proveedor
14. **Requiere Fórmula** - Sí/No
15. **Descripción** - Texto descriptivo
16. **Estado** - (Activo, Vencido, Agotado, Suspendido)

---

## 📝 Metadatos en Reportes

Cada reporte incluye:
- **Fecha y Hora de Generación** - Timestamp de creación
- **Usuario Generador** - Nombre completo del administrador
- **Filtro Aplicado** - Estado seleccionado
- **Título del Sistema** - "SISTEMA DE GESTIÓN FARMACÉUTICA - CURATIO"

---

## 🔒 Seguridad

### Permisos Requeridos:
- ✓ Autenticación activa (login requerido)
- ✓ Rol de ADMIN (user_type='ADMIN')
- ✓ Validación previa del filtro elegido

### Manejo de Errores:
- ✓ Valida estados válidos
- ✓ Rechaza usuarios no autenticados
- ✓ Rechaza usuarios sin rol ADMIN
- ✓ Maneja casos sin datos coincidentes
- ✓ Captura y reporta excepciones

---

## 🧪 Ejemplos de Uso

### Ejemplo 1: Generar Reporte Excel de Activos
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/medicines/generate_excel_report/?state=ACTIVO"
```

### Ejemplo 2: Generar Reporte PDF de Todos
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/medicines/generate_pdf_report/?state=TODOS"
```

### Ejemplo 3: En JavaScript/Fetch
```javascript
fetch('/api/medicines/generate_excel_report/?state=ACTIVO', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
})
.then(response => response.blob())
.then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `reporte.xlsx`;
    a.click();
});
```

---

## 🔄 Migración de Base de Datos

Después de aplicar estos cambios, ejecuta:

```bash
python manage.py makemigrations medicines
python manage.py migrate medicines
```

---

## ⚠️ Notas Importantes

1. **Campos Obligatorios**: Todos los nuevos campos del modelo son obligatorios
2. **Estados Automáticos**: El estado puede actualizarse automáticamente usando `update_state_automatically()`
3. **Validación de Fechas**: La fecha de vencimiento debe ser posterior a la de fabricación
4. **Cambios Retroactivos**: Los medicamentos existentes necesitarán ser actualizados con los nuevos campos

---

## 📧 Soporte

Para reportar problemas o mejoras del RFADMIN13, contacta al equipo de desarrollo.

---

**Versión:** 1.0  
**Requerimiento:** RFADMIN13  
**Estado:** ✅ Implementado  
**Fecha:** Marzo 2026
