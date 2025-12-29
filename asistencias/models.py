# FILE: asistencias/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid
from django.conf import settings

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, verbose_name="Nombre")
    second_name = models.CharField(max_length=50, blank=True, verbose_name="Segundo nombre")
    last_name = models.CharField(max_length=50, verbose_name="Apellido")
    second_last_name = models.CharField(max_length=50, blank=True, verbose_name="Segundo apellido")
    dni = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número de teléfono")

    NIVEL_CHOICES = [
        (1, 'Alumno'),
        (2, 'Docente'),
        (3, 'Coordinador'),
        (4, 'Gestor'),
        (5, 'Administrador'),
        (6, 'Referente Municipal'),
        (7, 'Supervisor'),
    ]
    nivel = models.PositiveSmallIntegerField(choices=NIVEL_CHOICES, default=1)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'dni']
    objects = CustomUserManager()

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.get_nivel_display()})"

AUTH_USER = settings.AUTH_USER_MODEL

class Diplomatura(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True)
    codigo = models.CharField(max_length=20, unique=True)
    creada_por = models.ForeignKey(AUTH_USER, on_delete=models.SET_NULL, null=True, related_name='diplos_creadas')
    coordinadores = models.ManyToManyField(AUTH_USER, blank=True, related_name='diplos_coordinadas')
    municipio = models.CharField(max_length=100, default='CORONEL ROSALES')

    def __str__(self):
        return self.nombre

class Materia(models.Model):
    diplomatura = models.ForeignKey(Diplomatura, on_delete=models.CASCADE, related_name='materias')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    codigo = models.CharField(max_length=20, unique=True)
    profesor_titular = models.ForeignKey(AUTH_USER, on_delete=models.SET_NULL, null=True, related_name='materias_titular')
    link_clase = models.TextField(blank=True, help_text="Link por defecto")

    class Meta:
        unique_together = ('diplomatura', 'nombre')

    def __str__(self):
        return f"{self.nombre} ({self.diplomatura.nombre})"

class ProfesorMateria(models.Model):
    ROL = [('titular', 'Titular'), ('adjunto', 'Adjunto')]
    user = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='profesores')
    rol = models.CharField(max_length=10, choices=ROL, default='adjunto')

    class Meta:
        unique_together = ('user', 'materia')

    def __str__(self):
        return f"{self.user} -> {self.materia} ({self.rol})"

class AccesoToken(models.Model):
    NIVEL_CHOICES = [
        (1, 'Nivel 1 (Alumno)'),
        (2, 'Nivel 2 (Docente)'),
        (3, 'Nivel 3 (Coordinador)'),
    ]
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nivel_destino = models.PositiveSmallIntegerField(choices=NIVEL_CHOICES, default=2)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, null=True, blank=True, related_name='tokens')
    expires_at = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(AUTH_USER, on_delete=models.SET_NULL, null=True, blank=True, related_name='tokens_creados')
    usado_por = models.ForeignKey(AUTH_USER, on_delete=models.SET_NULL, null=True, blank=True, related_name='tokens_usados')
    usado_en = models.DateTimeField(null=True, blank=True)

    def es_valido(self):
        if not self.activo or self.usado_en: return False
        if self.expires_at and timezone.now() >= self.expires_at: return False
        return True

    def __str__(self):
        return f"Token {self.get_nivel_destino_display()} - {str(self.code)[:8]}"

class Clase(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='clases')
    fecha = models.DateField()
    hora_inicio = models.DateTimeField(help_text='Inicio ventana asistencia')
    hora_fin = models.DateTimeField(help_text='Fin ventana asistencia')
    tema = models.CharField(max_length=255, blank=True)
    link_clase = models.TextField(blank=True, help_text="Detalle específico")
    comentarios_docente = models.TextField(blank=True, verbose_name="Comentarios del Docente")
    creado_por = models.ForeignKey(AUTH_USER, on_delete=models.SET_NULL, null=True, related_name='clases_creadas')

    def ventana_activa(self):
        return self.hora_inicio <= timezone.now() <= self.hora_fin

    def __str__(self):
        return f"{self.materia.nombre} - {self.fecha}"

class Asistencia(models.Model):
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='asistencias')
    user = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE, related_name='asistencias')
    presente = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('clase', 'user')

class Nota(models.Model):
    alumno = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE, related_name='notas')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='notas')
    valor = models.DecimalField(max_digits=4, decimal_places=2)
    fecha = models.DateField(default=timezone.now)
    observaciones = models.TextField(blank=True)
    evaluador = models.ForeignKey(AUTH_USER, on_delete=models.SET_NULL, null=True, related_name='notas_asignadas')

    class Meta:
        ordering = ['-fecha']

class InscripcionDiplomatura(models.Model):
    user = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE, related_name='insc_diplos')
    diplomatura = models.ForeignKey(Diplomatura, on_delete=models.CASCADE, related_name='inscripciones')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'diplomatura')

class InscripcionMateria(models.Model):
    user = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE, related_name='insc_materias')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='inscripciones')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'materia')
