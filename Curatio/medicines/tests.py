from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime, timedelta
from .models import Medicine

User = get_user_model()


class MedicineModelTestCase(TestCase):
    """Tests para los métodos del modelo Medicine (RFADMIN08, RFADMIN09)"""
    
    def setUp(self):
        """Configuración inicial de datos de prueba"""
        self.medicine_active = Medicine.objects.create(
            name='Ibuprofeno',
            description='Analgésico',
            active_ingredient='Ibuprofeno',
            concentration='400mg',
            pharmaceutical_form='SOLIDA',
            presentation='PASTILLA',
            administration_route='ORAL',
            laboratory='BAYER',
            registration_number='REG001',
            batch_number='BATCH001',
            stock_quantity=100,
            minimum_stock=10,
            manufacture_date=datetime.now().date() - timedelta(days=365),
            expiration_date=datetime.now().date() + timedelta(days=365),
            purchase_price=2.50,
            sale_price=5.99,
            supplier='Proveedor A',
            state='ACTIVO'
        )
    
    def test_is_expired(self):
        """Test: Método is_expired funciona correctamente"""
        expired_medicine = Medicine.objects.create(
            name='Medicina Expirada',
            active_ingredient='Test',
            concentration='100mg',
            pharmaceutical_form='SOLIDA',
            presentation='PASTILLA',
            administration_route='ORAL',
            laboratory='ABBOTT',
            registration_number='REG999',
            batch_number='BATCH999',
            stock_quantity=10,
            minimum_stock=5,
            manufacture_date=datetime.now().date() - timedelta(days=730),
            expiration_date=datetime.now().date() - timedelta(days=1),
            purchase_price=1.00,
            sale_price=3.00,
            supplier='Proveedor B',
            state='ACTIVO'
        )
        
        self.assertTrue(expired_medicine.is_expired())
        self.assertFalse(self.medicine_active.is_expired())
    
    def test_days_to_expire(self):
        """Test: Método days_to_expire calcula correctamente"""
        future_date = datetime.now().date() + timedelta(days=30)
        medicine = Medicine.objects.create(
            name='Medicina 30 Días',
            active_ingredient='Test',
            concentration='100mg',
            pharmaceutical_form='SOLIDA',
            presentation='PASTILLA',
            administration_route='ORAL',
            laboratory='PFIZER',
            registration_number='REG998',
            batch_number='BATCH998',
            stock_quantity=10,
            minimum_stock=5,
            manufacture_date=datetime.now().date(),
            expiration_date=future_date,
            purchase_price=1.00,
            sale_price=3.00,
            supplier='Proveedor C',
            state='ACTIVO'
        )
        
        days = medicine.days_to_expire()
        self.assertIn(days, [29, 30])


class MedicineViewSetTestCase(TestCase):
    """Tests para RFADMIN09: Visualizar medicamento"""
    
    def setUp(self):
        """Configuración inicial de datos de prueba"""
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='TestPass123!',
            user_type='ADMIN',
            is_active=True
        )
        
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='TestPass123!',
            user_type='PATIENT',
            is_active=True
        )
        
        # Crear medicamentos de prueba
        self.medicine1 = Medicine.objects.create(
            name='Ibuprofeno',
            description='Analgésico y antiinflamatorio',
            active_ingredient='Ibuprofeno',
            concentration='400mg',
            pharmaceutical_form='SOLIDA',
            presentation='PASTILLA',
            administration_route='ORAL',
            laboratory='BAYER',
            registration_number='REG001',
            batch_number='BATCH001',
            stock_quantity=100,
            minimum_stock=10,
            manufacture_date=datetime.now().date() - timedelta(days=365),
            expiration_date=datetime.now().date() + timedelta(days=365),
            purchase_price=2.50,
            sale_price=5.99,
            supplier='Proveedor A',
            is_active=True,
            state='ACTIVO'
        )
        
        self.medicine2 = Medicine.objects.create(
            name='Amoxicilina',
            description='Antibiótico',
            active_ingredient='Amoxicilina',
            concentration='500mg',
            pharmaceutical_form='SOLIDA',
            presentation='CAPSULA',
            administration_route='ORAL',
            laboratory='ABBOTT',
            registration_number='REG002',
            batch_number='BATCH002',
            stock_quantity=50,
            minimum_stock=15,
            manufacture_date=datetime.now().date() - timedelta(days=730),
            expiration_date=datetime.now().date() + timedelta(days=730),
            purchase_price=3.00,
            sale_price=8.50,
            supplier='Proveedor B',
            is_active=True,
            state='ACTIVO'
        )
        
        self.client = APIClient()
    
    def test_search_by_id_success(self):
        """Test: Búsqueda exitosa por ID"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f'/api/medicines/search_by_id/?id={self.medicine1.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Ibuprofeno')
        self.assertEqual(response.data['concentration'], '400mg')
    
    def test_search_by_id_not_found(self):
        """Test: ID no existe"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/search_by_id/?id=9999')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('no encontrado', response.data['detail'].lower())
    
    def test_search_by_id_invalid(self):
        """Test: ID inválido (no es número)"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/search_by_id/?id=abc')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('número', response.data['detail'].lower())
    
    def test_search_by_id_missing_parameter(self):
        """Test: Parámetro ID faltante"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/search_by_id/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('requerido', response.data['detail'].lower())
    
    def test_search_by_name_exact_match(self):
        """Test: Búsqueda exacta por nombre"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/search_by_name/?name=Ibuprofeno')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'exact_match')
        self.assertEqual(response.data['medicine']['name'], 'Ibuprofeno')
    
    def test_search_by_name_case_insensitive(self):
        """Test: Búsqueda case-insensitive"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/search_by_name/?name=ibuprofeno')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['medicine']['name'], 'Ibuprofeno')
    
    def test_search_by_name_fuzzy_suggestions(self):
        """Test: Búsqueda fuzzy con sugerencias"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/search_by_name/?name=Ibuprofen')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'suggestions')
        self.assertGreater(len(response.data['suggestions']), 0)
    
    def test_search_by_name_not_found(self):
        """Test: Nombre no existe"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/search_by_name/?name=MedicamentoInexistente')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['type'], 'not_found')
    
    def test_retrieve_readonly(self):
        """Test: Vista de solo lectura"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f'/api/medicines/{self.medicine1.id}/retrieve_readonly/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
    
    def test_unauthenticated_access_denied(self):
        """Test: Acceso sin autenticación"""
        response = self.client.get(f'/api/medicines/search_by_id/?id={self.medicine1.id}')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MedicineReportTestCase(TestCase):
    """Tests para RFADMIN13: Generar reportes de medicamentos"""
    
    def setUp(self):
        """Configuración inicial de datos de prueba"""
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='TestPass123!',
            user_type='ADMIN',
            is_active=True,
            first_name='Admin',
            last_name='User'
        )
        
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='TestPass123!',
            user_type='PATIENT',
            is_active=True
        )
        
        # Medicamento ACTIVO
        self.medicine_active = Medicine.objects.create(
            name='Ibuprofeno',
            description='Analgésico',
            active_ingredient='Ibuprofeno',
            concentration='400mg',
            pharmaceutical_form='SOLIDA',
            presentation='PASTILLA',
            administration_route='ORAL',
            laboratory='BAYER',
            registration_number='REG001',
            batch_number='BATCH001',
            stock_quantity=100,
            minimum_stock=10,
            manufacture_date=datetime.now().date() - timedelta(days=365),
            expiration_date=datetime.now().date() + timedelta(days=365),
            purchase_price=2.50,
            sale_price=5.99,
            supplier='Proveedor A',
            state='ACTIVO'
        )
        
        # Medicamento VENCIDO
        self.medicine_expired = Medicine.objects.create(
            name='Amoxicilina',
            description='Antibiótico',
            active_ingredient='Amoxicilina',
            concentration='500mg',
            pharmaceutical_form='SOLIDA',
            presentation='CAPSULA',
            administration_route='ORAL',
            laboratory='ABBOTT',
            registration_number='REG002',
            batch_number='BATCH002',
            stock_quantity=30,
            minimum_stock=15,
            manufacture_date=datetime.now().date() - timedelta(days=730),
            expiration_date=datetime.now().date() - timedelta(days=10),
            purchase_price=3.00,
            sale_price=8.50,
            supplier='Proveedor B',
            state='VENCIDO'
        )
        
        # Medicamento AGOTADO
        self.medicine_outofstock = Medicine.objects.create(
            name='Paracetamol',
            description='Analgésico',
            active_ingredient='Paracetamol',
            concentration='500mg',
            pharmaceutical_form='SOLIDA',
            presentation='PASTILLA',
            administration_route='ORAL',
            laboratory='PFIZER',
            registration_number='REG003',
            batch_number='BATCH003',
            stock_quantity=0,
            minimum_stock=10,
            manufacture_date=datetime.now().date(),
            expiration_date=datetime.now().date() + timedelta(days=365),
            purchase_price=1.50,
            sale_price=4.99,
            supplier='Proveedor C',
            state='AGOTADO'
        )
        
        # Medicamento SUSPENDIDO
        self.medicine_suspended = Medicine.objects.create(
            name='Aspirin',
            description='Antiinflamatorio',
            active_ingredient='Ácido Acetilsalicílico',
            concentration='500mg',
            pharmaceutical_form='SOLIDA',
            presentation='PASTILLA',
            administration_route='ORAL',
            laboratory='BAYER',
            registration_number='REG004',
            batch_number='BATCH004',
            stock_quantity=50,
            minimum_stock=10,
            manufacture_date=datetime.now().date(),
            expiration_date=datetime.now().date() + timedelta(days=365),
            purchase_price=1.00,
            sale_price=3.50,
            supplier='Proveedor D',
            state='SUSPENDIDO'
        )
        
        self.client = APIClient()
    
    def test_generate_excel_report_activo(self):
        """Test: Generar reporte Excel con medicamentos ACTIVOS"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/generate_excel_report/?state=ACTIVO')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_generate_excel_report_todos(self):
        """Test: Generar reporte Excel con TODOS los medicamentos"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/generate_excel_report/?state=TODOS')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'],
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    def test_generate_excel_report_vencido(self):
        """Test: Generar reporte Excel con medicamentos VENCIDOS"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/generate_excel_report/?state=VENCIDO')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_generate_excel_report_agotado(self):
        """Test: Generar reporte Excel con medicamentos AGOTADOS"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/generate_excel_report/?state=AGOTADO')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_generate_excel_report_suspendido(self):
        """Test: Generar reporte Excel con medicamentos SUSPENDIDOS"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/generate_excel_report/?state=SUSPENDIDO')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_generate_pdf_report_activo(self):
        """Test: Generar reporte PDF con medicamentos ACTIVOS"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/generate_pdf_report/?state=ACTIVO')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_generate_pdf_report_todos(self):
        """Test: Generar reporte PDF con TODOS los medicamentos"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/generate_pdf_report/?state=TODOS')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_generate_report_invalid_state(self):
        """Test: Estado inválido"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/generate_excel_report/?state=INVALIDO')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('inválido', response.data['detail'].lower())
    
    def test_generate_report_unauthenticated(self):
        """Test: Generar reporte sin autenticación"""
        response = self.client.get('/api/medicines/generate_excel_report/?state=ACTIVO')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_generate_report_non_admin_user(self):
        """Test: Usuario no-ADMIN no puede generar reportes"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/medicines/generate_excel_report/?state=ACTIVO')
        
        # Debe retornar 403 Forbidden o similar
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])
    
    def test_generate_report_empty_result(self):
        """Test: No hay medicamentos con el estado seleccionado"""
        # Eliminar todos los medicamentos suspendidos
        Medicine.objects.filter(state='SUSPENDIDO').delete()
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/medicines/generate_excel_report/?state=SUSPENDIDO')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('no hay', response.data['detail'].lower())

