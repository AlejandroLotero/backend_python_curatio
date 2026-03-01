from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from difflib import SequenceMatcher
from .models import Medicine
from .serializers import MedicineSerializer, MedicineCreateUpdateSerializer
from .forms import MedicineForm
from .report_service import ExcelReportGenerator, PDFReportGenerator


class IsAdmin(IsAuthenticated):
    """Permiso personalizado para verificar si el usuario es ADMIN"""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        # Verifica si es ADMIN
        return hasattr(request.user, 'user_type') and request.user.user_type == 'ADMIN'


class MedicineViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de medicamentos
    
    RFADMIN08: Registrar medicamento
    RFADMIN09: Visualizar medicamento
    """
    queryset = Medicine.objects.all()
    permission_classes = [IsAdmin]
    
    def get_serializer_class(self):
        """
        Retorna diferentes serializers según la acción
        - read: MedicineSerializer (solo lectura con campos adicionales)
        - write: MedicineCreateUpdateSerializer
        """
        if self.action in ['create', 'update', 'partial_update']:
            return MedicineCreateUpdateSerializer
        return MedicineSerializer
    
    def create(self, request, *args, **kwargs):
        """
        RFADMIN08: Registrar medicamento
        POST /api/medicines/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Retorna con el serializer de lectura
        read_serializer = MedicineSerializer(serializer.instance)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """Previene la eliminación física de medicamentos"""
        return Response(
            {'detail': 'No se pueden eliminar medicamentos. Use el estado para descontinuar.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def search_by_id(self, request):
        """
        RFADMIN09: Buscar medicamento por ID
        GET /api/medicines/search_by_id/?id=1
        
        Regla de negocio 2: Debe existir coincidencia exacta
        """
        medicine_id = request.query_params.get('id')
        
        if not medicine_id:
            return Response(
                {'detail': 'El parámetro "id" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            medicine = Medicine.objects.get(id=int(medicine_id))
            serializer = MedicineSerializer(medicine)
            return Response(serializer.data)
        except Medicine.DoesNotExist:
            return Response(
                {'detail': f'Medicamento con ID {medicine_id} no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except (ValueError, TypeError):
            return Response(
                {'detail': 'El ID debe ser un número válido'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def search_by_name(self, request):
        """
        RFADMIN09: Buscar medicamento por nombre
        GET /api/medicines/search_by_name/?name=Ibuprofeno
        
        Regla de negocio 2: Coincidencia exacta (primera opción)
        Regla de negocio 3: Si difiere en 1-2 letras, mostrar como sugerencias
        """
        search_name = request.query_params.get('name', '').strip()
        
        if not search_name:
            return Response(
                {'detail': 'El parámetro "name" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 1. Búsqueda de coincidencia exacta (case-insensitive)
        exact_match = Medicine.objects.filter(
            name__iexact=search_name,
            is_active=True
        ).first()
        
        if exact_match:
            serializer = MedicineSerializer(exact_match)
            return Response({
                'type': 'exact_match',
                'medicine': serializer.data,
                'suggestions': []
            })
        
        # 2. Búsqueda de sugerencias (1-2 letras diferentes)
        all_medicines = Medicine.objects.filter(is_active=True)
        suggestions = []
        
        for medicine in all_medicines:
            # Calcula similitud entre strings
            similarity = SequenceMatcher(
                None,
                search_name.lower(),
                medicine.name.lower()
            ).ratio()
            
            # Si la similitud es >= 0.85 (aproximadamente 1-2 letras diferentes)
            if similarity >= 0.85:
                suggestions.append({
                    'id': medicine.id,
                    'name': medicine.name,
                    'concentration': medicine.concentration,
                    'similarity_score': round(similarity * 100, 2)
                })
        
        # Ordena sugerencias por similitud (de mayor a menor)
        suggestions.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        if suggestions:
            return Response({
                'type': 'suggestions',
                'medicine': None,
                'suggestions': suggestions[:5],  # Máximo 5 sugerencias
                'message': f'No se encontró coincidencia exacta. Se muestran {len(suggestions)} sugerencia(s) similar(es).'
            }, status=status.HTTP_200_OK)
        
        # Sin coincidencias
        return Response({
            'type': 'not_found',
            'medicine': None,
            'suggestions': [],
            'detail': f'No se encontró medicamento con el nombre "{search_name}"'
        }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticated])
    def retrieve_readonly(self, request, pk=None):
        """
        RFADMIN09: Visualizar medicamento - Vista de solo lectura
        GET /api/medicines/{id}/retrieve_readonly/
        """
        try:
            medicine = Medicine.objects.get(id=pk)
            serializer = MedicineSerializer(medicine)
            return Response(serializer.data)
        except Medicine.DoesNotExist:
            return Response(
                {'detail': f'Medicamento con ID {pk} no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # ============ RFADMIN13: GENERACIÓN DE REPORTES ============
    
    @action(detail=False, methods=['GET'], permission_classes=[IsAdmin])
    def generate_excel_report(self, request):
        """
        RFADMIN13: Generar reporte en Excel
        GET /api/medicines/generate_excel_report/?state=ACTIVO
        
        Parámetros:
        - state: ACTIVO, VENCIDO, AGOTADO, SUSPENDIDO, TODOS (default: TODOS)
        """
        state = request.query_params.get('state', 'TODOS').upper()
        
        # Validar estado
        valid_states = ['ACTIVO', 'VENCIDO', 'AGOTADO', 'SUSPENDIDO', 'TODOS']
        if state not in valid_states:
            return Response(
                {'detail': f'Estado inválido: {state}. Valores válidos: {", ".join(valid_states)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            return ExcelReportGenerator.generate(
                state=state if state != 'TODOS' else None,
                user=request.user
            )
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'detail': f'Error al generar reporte: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['GET'], permission_classes=[IsAdmin])
    def generate_pdf_report(self, request):
        """
        RFADMIN13: Generar reporte en PDF
        GET /api/medicines/generate_pdf_report/?state=ACTIVO
        
        Parámetros:
        - state: ACTIVO, VENCIDO, AGOTADO, SUSPENDIDO, TODOS (default: TODOS)
        """
        state = request.query_params.get('state', 'TODOS').upper()
        
        # Validar estado
        valid_states = ['ACTIVO', 'VENCIDO', 'AGOTADO', 'SUSPENDIDO', 'TODOS']
        if state not in valid_states:
            return Response(
                {'detail': f'Estado inválido: {state}. Valores válidos: {", ".join(valid_states)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            return PDFReportGenerator.generate(
                state=state if state != 'TODOS' else None,
                user=request.user
            )
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'detail': f'Error al generar reporte: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============ VISTAS WEB (RFADMIN09 - UI) ============

@login_required
def medicine_list(request):
    """Lista todos los medicamentos"""
    if request.user.user_type != 'ADMIN':
        messages.error(request, 'Solo ADMIN puede acceder')
        return redirect('dashboard')
    
    medicines = Medicine.objects.all()
    return render(request, 'medicines/list.html', {'medicines': medicines})


@login_required
def medicine_create(request):
    """Crear nuevo medicamento"""
    if request.user.user_type != 'ADMIN':
        messages.error(request, 'Solo ADMIN puede acceder')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicamento creado exitosamente')
            return redirect('medicine_list')
    else:
        form = MedicineForm()
    
    return render(request, 'medicines/form.html', {'form': form, 'title': 'Crear Medicamento'})


@login_required
def medicine_detail(request, pk):
    """Ver detalles de medicamento (RFADMIN09)"""
    if request.user.user_type != 'ADMIN':
        messages.error(request, 'Solo ADMIN puede acceder')
        return redirect('dashboard')
    
    medicine = get_object_or_404(Medicine, pk=pk)
    return render(request, 'medicines/detail.html', {'medicine': medicine})


@login_required
def medicine_update(request, pk):
    """Editar medicamento"""
    if request.user.user_type != 'ADMIN':
        messages.error(request, 'Solo ADMIN puede acceder')
        return redirect('dashboard')
    
    medicine = get_object_or_404(Medicine, pk=pk)
    
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicamento actualizado')
            return redirect('medicine_detail', pk=medicine.pk)
    else:
        form = MedicineForm(instance=medicine)
    
    return render(request, 'medicines/form.html', {'form': form, 'title': 'Editar Medicamento', 'medicine': medicine})


@login_required
def medicine_delete(request, pk):
    """Eliminar medicamento"""
    if request.user.user_type != 'ADMIN':
        messages.error(request, 'Solo ADMIN puede acceder')
        return redirect('dashboard')
    
    medicine = get_object_or_404(Medicine, pk=pk)
    
    if request.method == 'POST':
        medicine.delete()
        messages.success(request, 'Medicamento eliminado')
        return redirect('medicine_list')
    
    return render(request, 'medicines/confirm_delete.html', {'medicine': medicine})
