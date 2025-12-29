from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from asistencias.models import Diplomatura, Materia, InscripcionDiplomatura, Clase, Asistencia
from django.urls import reverse
from datetime import date, time, datetime

User = get_user_model()

class RoleTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.supervisor = User.objects.create_user(email='sup@test.com', password='password', nivel=7, first_name='Super', last_name='Visor', dni='111')
        self.referente = User.objects.create_user(email='ref@test.com', password='password', nivel=6, first_name='Ref', last_name='Erente', dni='222')
        self.alumno = User.objects.create_user(email='alu@test.com', password='password', nivel=1, first_name='Alu', last_name='Mno', dni='333')
        
        # Create data
        self.diplo = Diplomatura.objects.create(nombre='Diplo Test', codigo='DT1')
        self.materia = Materia.objects.create(diplomatura=self.diplo, nombre='Mat 1', codigo='M1')
        self.clase = Clase.objects.create(materia=self.materia, fecha=date.today(), hora_inicio=datetime.now(), hora_fin=datetime.now(), tema='Tema 1')
        
        # Register Referente
        InscripcionDiplomatura.objects.create(user=self.referente, diplomatura=self.diplo)
        
    def test_supervisor_switch_role(self):
        self.client.login(email='sup@test.com', password='password')
        
        # Initial check: should be level 7
        response = self.client.get(reverse('asistencias:home'))
        self.assertEqual(response.wsgi_request.user.nivel, 7)
        
        # Switch to Alumno (1)
        response = self.client.get(reverse('asistencias:switch_role', args=[1]))
        self.assertEqual(response.status_code, 302)
        
        # Check if session has the role
        self.assertEqual(self.client.session['impersonate_role'], 1)
        
        # Check if middleware applies it
        response = self.client.get(reverse('asistencias:home'))
        self.assertEqual(response.wsgi_request.user.nivel, 1)
        
    def test_referente_dashboard_access(self):
        self.client.login(email='ref@test.com', password='password')
        response = self.client.get(reverse('asistencias:referente_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Diplo Test')
        
    def test_referente_calendar_access(self):
        self.client.login(email='ref@test.com', password='password')
        response = self.client.get(reverse('asistencias:calendario_referente', args=[self.diplo.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'stats') # Should contain stats in the template context/js
        
    def test_referente_export_access(self):
        self.client.login(email='ref@test.com', password='password')
        response = self.client.get(reverse('asistencias:exportar_asistencia_diplomatura', args=[self.diplo.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_referente_read_only_access(self):
        self.client.login(email='ref@test.com', password='password')
        
        # View class attendance
        response = self.client.get(reverse('asistencias:ver_asistencia_clase', args=[self.clase.id]))
        self.assertEqual(response.status_code, 200)
        
        # View subjects list
        response = self.client.get(reverse('asistencias:referente_materias', args=[self.diplo.id]))
        self.assertEqual(response.status_code, 200)
        
        # View grades (needs a Nota to be interesting, but 200 is enough for access check)
        response = self.client.get(reverse('asistencias:ver_notas_materia', args=[self.materia.id]))
        self.assertEqual(response.status_code, 200)

    def test_referente_write_restrictions(self):
        self.client.login(email='ref@test.com', password='password')
        
        # Create Materia
        response = self.client.get(reverse('asistencias:crear_materia'))
        self.assertEqual(response.status_code, 403)
        
        # Create Diplomatura
        response = self.client.get(reverse('asistencias:crear_diplomatura'))
        self.assertEqual(response.status_code, 403)
        
        # Load Grades
        response = self.client.get(reverse('asistencias:cargar_notas', args=[self.materia.id]))
        self.assertEqual(response.status_code, 403)
        
        # Edit Class
        response = self.client.get(reverse('asistencias:editar_clase', args=[self.clase.id]))
        self.assertEqual(response.status_code, 403)
        
        # Delete Class
        response = self.client.get(reverse('asistencias:eliminar_clase', args=[self.clase.id]))
        self.assertEqual(response.status_code, 403)

    def test_referente_cannot_see_create_class_modal(self):
        self.client.login(email='ref@test.com', password='password')
        response = self.client.get(reverse('asistencias:home'))
        self.assertEqual(response.status_code, 200)
        # Verify materias_creables is empty in context
        self.assertIn('materias_creables', response.context)
        self.assertEqual(len(response.context['materias_creables']), 0)

    def test_referente_navigation_link(self):
        self.client.login(email='ref@test.com', password='password')
        response = self.client.get(reverse('asistencias:home'))
        self.assertContains(response, reverse('asistencias:insc_diplomatura_codigo'))
        self.assertNotContains(response, reverse('asistencias:insc_materia_codigo'))

    def test_referente_calendar_stats(self):
        self.client.login(email='ref@test.com', password='password')
        response = self.client.get(reverse('asistencias:calendario_referente', args=[self.diplo.id]))
        self.assertEqual(response.status_code, 200)
        # Check if stats are in the event props (implicitly checked by response content or context)
        # Since stats are rendered in template JS, we check for presence of 'stats' string in response
        self.assertContains(response, 'stats:')
        self.assertContains(response, 'presentes:')

    def test_alumno_cannot_access_referente_views(self):
        self.client.login(email='alu@test.com', password='password')
        response = self.client.get(reverse('asistencias:referente_dashboard'))
        self.assertNotEqual(response.status_code, 200) # Should be forbidden or redirect
