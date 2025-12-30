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
    solo_una_diplo = False

    if request.user.is_authenticated:
        u = request.user

        # 1. Filtrado de Diplomaturas según el rol
        dips_alumno = Diplomatura.objects.filter(
            models.Q(inscripciones__user=u) | 
            models.Q(materias__inscripciones__user=u)
        )
        dips_docente = Diplomatura.objects.filter(
            models.Q(materias__profesor_titular=u) |
            models.Q(materias__profesores__user=u)
        )
        dips_coord = Diplomatura.objects.filter(coordinadores=u)

        if u.nivel >= 3:
            qs = (dips_alumno | dips_docente | dips_coord)
        elif u.nivel >= 2:
            qs = (dips_alumno | dips_docente)
        else:
            qs = dips_alumno

        diplomaturas = qs.distinct().prefetch_related('materias')
        
        solo_una_diplo = diplomaturas.count() == 1

        # 2. Paleta de colores
        COLORES_PALETA = ['#4CAF50', '#2196F3', '#FF9800', '#E91E63', '#9C27B0', '#00BCD4']
        diplo_ids_list = list(diplomaturas.values_list('id', flat=True))
        color_map = {d_id: COLORES_PALETA[i % len(COLORES_PALETA)] for i, d_id in enumerate(diplo_ids_list)}

        # 3. Materias para el Calendario
        if u.nivel >= 4 or getattr(u, 'is_superuser', False):
            mats_ids = Materia.objects.filter(Q(diplomatura__in=diplomaturas)).values_list('id', flat=True)
        elif u.nivel >= 3:
            mats_ids = Materia.objects.filter(
                Q(profesores__user=u) | Q(profesor_titular=u) | Q(diplomatura__coordinadores=u)
            ).values_list('id', flat=True)
        else:
            mats_ids = Materia.objects.filter(
                Q(inscripciones__user=u) | Q(profesores__user=u) | Q(profesor_titular=u)
            ).values_list('id', flat=True)

        # 4. Procesar Clases
        materias_donde_es_profe = set(ProfesorMateria.objects.filter(user=u).values_list('materia_id', flat=True))
        materias_donde_es_profe.update(Materia.objects.filter(profesor_titular=u).values_list('id', flat=True))
        materias_coordinadas = set(Materia.objects.filter(diplomatura__coordinadores=u).values_list('id', flat=True))
        materias_inscripto = set(InscripcionMateria.objects.filter(user=u).values_list('materia_id', flat=True))

        clases = Clase.objects.filter(materia_id__in=mats_ids).select_related('materia', 'materia__diplomatura')
        for c in clases:
            es_coord_de_esta = c.materia_id in materias_coordinadas
            es_profe_de_esta = c.materia_id in materias_donde_es_profe
            es_alumno_de_esta = c.materia_id in materias_inscripto
            es_supervisor = u.nivel >= 4 or u.is_superuser

            can_edit = (es_coord_de_esta or es_profe_de_esta) and u.nivel != 6
            can_access = es_supervisor or es_coord_de_esta or es_profe_de_esta or es_alumno_de_esta
            color_evento = color_map.get(c.materia.diplomatura_id, '#888')

            # --- ESTO ES LO QUE DEBES ASEGURARTE QUE ESTÉ ASÍ ---
            eventos.append({
                'title': f"{c.materia.nombre}",
                'start': c.fecha.isoformat(),
                'id': c.id,
                'materia_id': c.materia.id,
                'color': color_evento,
                'can_edit': can_edit,
                'can_access': can_access,
                'extendedProps': {
                    'tema': c.tema or "Sin tema especificado",
                    'link_clase': c.link_clase or "",
                    'hora_inicio': c.hora_inicio.strftime('%H:%M') if c.hora_inicio else "",
                    'hora_fin': c.hora_fin.strftime('%H:%M') if c.hora_fin else "",
                }
            })
        if u.nivel >= 3:
            materias_creables = Materia.objects.filter(diplomatura__coordinadores=u).distinct()

    return render(request, 'asistencias/home.html', {
        'diplomaturas': diplomaturas,
        'eventos': eventos,
        'mostrar_calendario_general': request.user.is_authenticated,
        'materias_creables': materias_creables,
        'solo_una_diplo': solo_una_diplo,
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
    base = (Materia.objects.select_related('diplomatura', 'profesor_titular')
            .prefetch_related('inscripciones', 'profesores')
            .order_by('diplomatura__nombre', 'nombre'))

    if u.nivel >= 4 or getattr(u, 'is_superuser', False):
        mats = base
    else:
        mats = base.filter(
            models.Q(inscripciones__user=u) |
            models.Q(profesor_titular=u) |
            models.Q(profesores__user=u) |
            models.Q(diplomatura__coordinadores=u)
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
    
    es_supervisor = u.nivel >= 4 or getattr(u, 'is_superuser', False)
    es_docente = (materia.profesor_titular == u or 
                  materia.profesores.filter(user=u).exists())
    es_coord = (u.nivel >= 3 and 
                materia.diplomatura.coordinadores.filter(id=u.id).exists())
    es_alumno = InscripcionMateria.objects.filter(user=u, materia=materia).exists()

    # Si es docente, coordinador o supervisor, puede gestionar
    can_manage = (es_docente or es_coord or es_supervisor) and u.nivel != 6

    if es_supervisor or es_docente or es_coord or es_alumno:
        clases = materia.clases.all().order_by('-fecha')
        return render(request, 'asistencias/clases.html', {
            'materia': materia, 
            'clases': clases,
            'es_docente': es_docente, 
            'es_coord': es_coord, 
            'es_alumno': es_alumno,
            'es_supervisor': es_supervisor,
            'can_manage': can_manage,  # <--- Nueva variable para el template
        })
    
    messages.error(request, "No tienes permiso para acceder a esta materia.")
    return redirect('asistencias:home')

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
