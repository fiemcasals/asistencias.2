from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from ..models import Materia, Diplomatura, Nota, InscripcionMateria

User = get_user_model()

class NotaTests(TestCase):
    def setUp(self):
        # Crear usuarios
        self.profesor = User.objects.create_user(email='profesor@test.com', password='password', first_name='Profe', last_name='Sor', dni='123', nivel=2)
        self.alumno = User.objects.create_user(email='alumno@test.com', password='password', first_name='Alu', last_name='Mno', dni='456', nivel=1)
        self.coordinador = User.objects.create_user(email='coord@test.com', password='password', first_name='Coor', last_name='Dinador', dni='789', nivel=3)

        # Crear diplomatura y materia
        self.diplomatura = Diplomatura.objects.create(nombre='Diplo Test', codigo='D1')
        self.materia = Materia.objects.create(diplomatura=self.diplomatura, nombre='Materia Test', codigo='M1', profesor_titular=self.profesor)

        # Inscribir alumno
        InscripcionMateria.objects.create(user=self.alumno, materia=self.materia)

        self.client = Client()

    def test_crear_nota_modelo(self):
        nota = Nota.objects.create(alumno=self.alumno, materia=self.materia, valor=8.50, evaluador=self.profesor)
        self.assertEqual(nota.valor, 8.50)
        self.assertEqual(nota.alumno, self.alumno)

    def test_cargar_nota_view_profesor(self):
        self.client.login(email='profesor@test.com', password='password')
        url = reverse('asistencias:cargar_notas', args=[self.materia.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = {
            'alumno_id': self.alumno.id,
            'valor': 9.0,
            'observaciones': 'Muy bien'
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, url)
        self.assertTrue(Nota.objects.filter(alumno=self.alumno, valor=9.0).exists())

    def test_mis_notas_view_alumno(self):
        Nota.objects.create(alumno=self.alumno, materia=self.materia, valor=7.0, evaluador=self.profesor)
        self.client.login(email='alumno@test.com', password='password')
        url = reverse('asistencias:mis_notas')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '7')

    def test_promedios_view_coordinador(self):
        Nota.objects.create(alumno=self.alumno, materia=self.materia, valor=10.0, evaluador=self.profesor)
        self.client.login(email='coord@test.com', password='password')
        url = reverse('asistencias:promedios_materia', args=[self.materia.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '10')
