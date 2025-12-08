from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from asistencias.models import Diplomatura, InscripcionDiplomatura

User = get_user_model()

class GenerarConstanciaTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Usuarios
        self.admin = User.objects.create_superuser(email='admin@test.com', password='password', first_name='Admin', last_name='User', dni='1', nivel=5)
        self.coordinador = User.objects.create_user(email='coord@test.com', password='password', first_name='Coord', last_name='User', dni='2', nivel=3)
        self.alumno = User.objects.create_user(email='alumno@test.com', password='password', first_name='Alumno', last_name='Uno', dni='12345678', nivel=1)
        self.alumno_sin_diplo = User.objects.create_user(email='alumno2@test.com', password='password', first_name='Alumno', last_name='Dos', dni='87654321', nivel=1)
        
        # Diplomatura
        self.diplomatura = Diplomatura.objects.create(nombre='Diplo Test', codigo='D1', creada_por=self.admin)
        self.diplomatura.coordinadores.add(self.coordinador)
        
        # Inscripción
        InscripcionDiplomatura.objects.create(user=self.alumno, diplomatura=self.diplomatura)
        
        self.url = reverse('asistencias:generar_constancia')

    def test_acceso_prohibido_alumno(self):
        self.client.force_login(self.alumno)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_acceso_permitido_coordinador(self):
        self.client.force_login(self.coordinador)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'asistencias/generar_constancia.html')

    def test_generar_pdf_exitoso(self):
        self.client.force_login(self.coordinador)
        response = self.client.post(self.url, {'dni': '12345678'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="constancia_12345678.pdf"', response['Content-Disposition'])

    def test_alumno_no_encontrado(self):
        self.client.force_login(self.coordinador)
        response = self.client.post(self.url, {'dni': '99999999'})
        
        self.assertEqual(response.status_code, 200) # Renderiza template con error
        self.assertContains(response, 'Alumno no encontrado')

    def test_alumno_sin_diplomatura(self):
        self.client.force_login(self.coordinador)
        response = self.client.post(self.url, {'dni': '87654321'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'no está inscripto en ninguna diplomatura')
