# FILE: asistencias/views/alumno.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db import models, transaction
from django.db.models import Q
from asistencias.models import (
    User, Diplomatura, Materia, Clase, Asistencia,
    InscripcionDiplomatura, InscripcionMateria, ProfesorMateria
)
from asistencias.forms import PerfilForm
from asistencias.permissions import requiere_nivel

def home(request):
    diplomaturas = Diplomatura.objects.none()
    eventos = []
    materias_creables = []

    if request.user.is_authenticated:
        u = request.user

        # Diplomaturas por rol
        dips_alumno = Diplomatura.objects.filter(
            models.Q(inscripciones__user=u) | 
            models.Q(materias__inscripciones__user=u)
        )
        dips_docente = Diplomatura.objects.filter(
            models.Q(materias__profesor_titular=u) |
            models.Q(materias__profesores__user=u)
        )
        dips_coord = Diplomatura.objects.filter(coordinadores=u)

        # Combinamos según nivel
        if u.nivel >= 3:
            qs = (dips_alumno | dips_docente | dips_coord)
        elif u.nivel >= 2:
            qs = (dips_alumno | dips_docente)
        else:
            qs = dips_alumno

        diplomaturas = qs.distinct().prefetch_related('materias')

        # Materias para el Calendario
        if u.nivel >= 3:
            # Coordinador ve sus materias Y todas las de las diplomaturas que coordina
            mats_ids = Materia.objects.filter(
                models.Q(profesores__user=u) |
                models.Q(profesor_titular=u) |
                models.Q(diplomatura__coordinadores=u)
            ).values_list('id', flat=True)
        else:
            mats_ids = Materia.objects.filter(
                models.Q(inscripciones__user=u) |
                models.Q(profesores__user=u) |
                models.Q(profesor_titular=u)
            ).values_list('id', flat=True)

        # Cache de permisos de edición
        materias_donde_es_profe = set(ProfesorMateria.objects.filter(user=u).values_list('materia_id', flat=True))
        materias_donde_es_profe.update(Materia.objects.filter(profesor_titular=u).values_list('id', flat=True))
        # El coordinador puede editar cualquier materia de su diplomatura
        materias_coordinadas = set(Materia.objects.filter(diplomatura__coordinadores=u).values_list('id', flat=True))

        clases = Clase.objects.filter(materia_id__in=mats_ids).select_related('materia')
        
        for c in clases:
            # Lógica de edición: Solo nivel >= 3 puede cambiar horarios. Nivel 2 solo tema/comentario.
            # En el calendario ponemos can_edit si tiene algún permiso de edición
            es_coord_de_esta = c.materia_id in materias_coordinadas
            es_profe_de_esta = c.materia_id in materias_donde_es_profe
            
            can_edit = (es_coord_de_esta or es_profe_de_esta) and u.nivel != 6

            eventos.append({
                'title': f"{c.materia.nombre} ({c.hora_inicio.strftime('%H:%M')})",
                'start': c.fecha.isoformat(),
                'id': c.id,
                'materia_id': c.materia.id,
                'color': '#4CAF50' if c.ventana_activa() else '#888',
                'can_edit': can_edit,
                'link_clase': c.link_clase,
                'tema': c.tema,
                'hora_inicio': c.hora_inicio.strftime('%H:%M'),
                'hora_fin': c.hora_fin.strftime('%H:%M'),
            })

        # Materias donde puede CREAR nuevas clases (Solo Coordinadores nivel 3+)
        if u.nivel >= 3:
            materias_creables = Materia.objects.filter(diplomatura__coordinadores=u).distinct()

    mostrar_calendario_general = request.user.is_authenticated and (request.user.nivel >= 3 or diplomaturas.count() > 1)

    return render(request, 'asistencias/home.html', {
        'diplomaturas': diplomaturas,
        'eventos': eventos,
        'mostrar_calendario_general': mostrar_calendario_general,
        'materias_creables': materias_creables,
    })

@requiere_nivel(1)
def perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado.")
            return redirect('asistencias:perfil')
    else:
        form = PerfilForm(instance=request.user)
    return render(request, 'asistencias/perfil.html', {'form': form})

@requiere_nivel(1)
def listar_diplomaturas(request):
    dips = Diplomatura.objects.all()
    return render(request, 'asistencias/diplomaturas.html', {'diplomaturas': dips})

@requiere_nivel(1)
def listar_materias(request):
    u = request.user
    base = (Materia.objects.select_related('diplomatura')
            .prefetch_related('inscripciones', 'profesores')
            .order_by('diplomatura__nombre', 'nombre'))

    if getattr(u, 'is_superuser', False) or u.nivel >= 4:
        mats = base
    else:
        mats = base.filter(
            Q(inscripciones__user=u) |
            Q(profesores__user=u) |
            Q(diplomatura__coordinadores=u)
        ).distinct()
    return render(request, 'asistencias/materias.html', {'materias': mats})

@requiere_nivel(1)
def insc_diplomatura_por_codigo(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        dip = get_object_or_404(Diplomatura, codigo=codigo)
        if request.user.nivel >= 3:
            dip.coordinadores.add(request.user)
            messages.success(request, f"Te has vinculado como Coordinador de {dip.nombre}.")
        else:
            InscripcionDiplomatura.objects.get_or_create(user=request.user, diplomatura=dip)
            messages.success(request, "Inscripción a diplomatura OK.")
        return redirect('asistencias:home')
    return render(request, 'asistencias/insc_diplo.html')

@requiere_nivel(1)
def insc_materia_por_codigo(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        mat = get_object_or_404(Materia, codigo=codigo)
        InscripcionMateria.objects.get_or_create(user=request.user, materia=mat)
        messages.success(request, "Inscripción a materia OK.")
        return redirect('asistencias:listar_materias')
    return render(request, 'asistencias/insc_materia.html')

@requiere_nivel(1)
def ver_clases_materia(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    u = request.user
    es_alumno = InscripcionMateria.objects.filter(user=u, materia=materia).exists()
    es_docente = ProfesorMateria.objects.filter(user=u, materia=materia).exists() or materia.profesor_titular == u
    es_coord = u.nivel >= 3 and diplomatura.coordinadores.filter(id=u.id).exists()

    if not (es_alumno or es_docente or es_coord or u.nivel >= 4):
        return HttpResponseForbidden("No tienes acceso a esta materia.")

    now = timezone.localtime()
    clases = materia.clases.all().order_by('-fecha')
    return render(request, 'asistencias/clases.html', {
        'materia': materia, 'clases': clases,
        'es_docente': es_docente, 'es_coord': es_coord, 'es_alumno': es_alumno,
    })

@requiere_nivel(1)
def marcar_presente(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    if ProfesorMateria.objects.filter(user=request.user, materia=clase.materia).exists():
        return HttpResponseForbidden("Docentes no marcan asistencia.")
    if not InscripcionMateria.objects.filter(user=request.user, materia=clase.materia).exists():
        return HttpResponseForbidden("No estás inscripto.")
    if not clase.ventana_activa():
        messages.error(request, "Fuera de ventana horaria.")
        return redirect('asistencias:ver_clases', materia_id=clase.materia.id)
    Asistencia.objects.get_or_create(clase=clase, user=request.user)
    messages.success(request, "Presente registrado.")
    return redirect('asistencias:ver_clases', materia_id=clase.materia.id)

@requiere_nivel(1)
def desinscribirse_materia(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    insc = InscripcionMateria.objects.filter(user=request.user, materia=materia).first()
    if request.method == 'POST' and insc:
        insc.delete()
        messages.success(request, "Desinscripción exitosa.")
        return redirect('asistencias:listar_materias')
    return render(request, 'asistencias/confirmar_desinscripcion.html', {'materia': materia})
