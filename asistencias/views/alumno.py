from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from asistencias.models import ProfesorMateria

from asistencias.models import (
    User, Diplomatura, Materia, Clase, Asistencia,
    InscripcionDiplomatura, InscripcionMateria, ProfesorMateria,
)
from asistencias.forms import PerfilForm
from asistencias.permissions import requiere_nivel


# asistencias/views/home.py  (o donde tengas la view)

from django.db.models import Q
from django.db.models import Q

# asistencias/views/home.py (o donde tengas la view)
from django.db import models
from django.db import transaction



def home(request):
    diplomaturas = Diplomatura.objects.none()

    if request.user.is_authenticated:
        u = request.user

        # ALUMNO: por diplo directa o por materias inscriptas
        dips_alumno = Diplomatura.objects.filter(
            models.Q(inscripciones__user=u) |                 # InscripcionDiplomatura
            models.Q(materias__inscripciones__user=u)        # InscripcionMateria → trae la diplo de esa materia
        )

        # DOCENTE (titular o adjunto)
        dips_docente = Diplomatura.objects.filter(
            models.Q(materias__profesor_titular=u) |
            models.Q(materias__profesores__user=u)
        )

        # COORDINADOR (si usás campo ManyToMany 'coordinadores')
        dips_coord = Diplomatura.objects.filter(coordinadores=u)

        # combinamos según nivel
        if u.nivel >= 3:
            qs = (dips_alumno | dips_docente | dips_coord)
        elif u.nivel >= 2:
            qs = (dips_alumno | dips_docente)
        else:
            qs = dips_alumno

        diplomaturas = qs.distinct().prefetch_related('materias')

    # Calendario: traer clases de las materias donde el usuario participa
    eventos = []
    if request.user.is_authenticated:
        # Materias donde es alumno o profesor
        mats_ids = Materia.objects.filter(
            models.Q(inscripciones__user=request.user) |
            models.Q(profesores__user=request.user) |
            models.Q(profesor_titular=request.user)
        ).values_list('id', flat=True)
        
        # Cachear permisos de profesor por materia
        # Set de materias donde es profe
        materias_profe = set(ProfesorMateria.objects.filter(user=request.user).values_list('materia_id', flat=True))
        # Agregar materias donde es titular
        materias_profe.update(Materia.objects.filter(profesor_titular=request.user).values_list('id', flat=True))

        clases = Clase.objects.filter(materia_id__in=mats_ids).select_related('materia')
        
        for c in clases:
            es_profe_de_esta = c.materia_id in materias_profe
            eventos.append({
                'title': f"{c.materia.nombre} ({c.hora_inicio.strftime('%H:%M')})",
                'start': c.fecha.isoformat(),
                'id': c.id,
                'materia_id': c.materia.id,
                'color': '#4CAF50' if c.ventana_activa() else '#888',
                'can_edit': es_profe_de_esta,
                'link_clase': c.link_clase,
                'tema': c.tema,
                'hora_inicio': c.hora_inicio.strftime('%H:%M'),
                'hora_fin': c.hora_fin.strftime('%H:%M'),
            })

    # Mostrar calendario general solo si es nivel >= 3 (coordinador) o tiene más de 1 diplomatura
    mostrar_calendario_general = False
    if request.user.is_authenticated:
        if request.user.nivel >= 3 or diplomaturas.count() > 1:
            mostrar_calendario_general = True

    # Materias donde el usuario puede crear clases (para el modal del calendario)
    materias_creables = []
    if request.user.is_authenticated and (request.user.nivel >= 2):
        # Titular o profesor adjunto
        materias_creables = Materia.objects.filter(
            models.Q(profesor_titular=request.user) |
            models.Q(profesores__user=request.user)
        ).distinct()

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


from django.db.models import Q

@requiere_nivel(1)
def listar_materias(request):
    u = request.user
    base = (Materia.objects
            .select_related('diplomatura')
            .prefetch_related('inscripciones', 'profesores')
            .order_by('diplomatura__nombre', 'nombre'))

    # Admin/gestor (nivel ≥4) o superuser ven todo
    if getattr(u, 'is_superuser', False) or getattr(u, 'is_nivel', lambda *_: False)(4):
        mats = base
    else:
        # Alumno inscripto, docente asignado o coordinador de la diplomatura
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
        InscripcionDiplomatura.objects.get_or_create(user=request.user, diplomatura=dip)
        messages.success(request, "Inscripción a diplomatura OK.")
        return redirect('asistencias:listar_diplomaturas')
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

    es_alumno = InscripcionMateria.objects.filter(user=request.user, materia=materia).exists()
    es_docente = ProfesorMateria.objects.filter(user=request.user, materia=materia).exists()
    es_coord   = getattr(request.user, "nivel", 1) >= 3

    if not (es_alumno or es_docente or es_coord):
        return HttpResponseForbidden("No estás inscripto en esta materia.")

 

    now = timezone.localtime()
    clases = (materia.clases
            .filter(hora_inicio__lte=now, hora_fin__gte=now)
            .order_by('hora_inicio'))
    can_manage = (
        materia.profesor_titular_id == request.user.id or 
        es_docente or 
        es_coord or 
        (getattr(request.user, 'nivel', 1) >= 2 and es_alumno)
    )

    return render(request, 'asistencias/clases.html', {
        'materia': materia, 
        'clases': clases,
        'es_docente': es_docente,
        'es_coord': es_coord,
        'es_alumno': es_alumno,
        'can_manage': can_manage,
    })


@requiere_nivel(1)
def calendario_diplomatura(request, diplomatura_id):
    diplomatura = get_object_or_404(Diplomatura, id=diplomatura_id)
    
    # Verificar acceso (alumno inscrito, docente, o coordinador)
    # Reutilizamos lógica de home pero filtrando por esta diplo
    
    eventos = []
    
    # Materias de esta diplo
    materias = Materia.objects.filter(diplomatura=diplomatura)
    
    # Filtrar solo las que el usuario tiene acceso si es alumno?
    # Generalmente el calendario de la diplo muestra todo el cronograma, 
    # pero para evitar confusión, mostremos solo donde está inscrito o es profe, 
    # O mostremos TODO el cronograma de la diplo?
    # "Calendario por diplo" suena a cronograma completo.
    # Pero mantengamos la coherencia: solo lo que cursa/da clases.
    
    # IDs de materias donde participa
    mats_ids = Materia.objects.filter(
        diplomatura=diplomatura
    ).filter(
        models.Q(inscripciones__user=request.user) |
        models.Q(profesores__user=request.user) |
        models.Q(profesor_titular=request.user)
    ).values_list('id', flat=True)

    # Si es coordinador, ve todo
    if request.user.nivel >= 3:
        mats_ids = Materia.objects.filter(diplomatura=diplomatura).values_list('id', flat=True)

    clases = Clase.objects.filter(materia_id__in=mats_ids).select_related('materia')
    
    # Permisos de edición
    materias_profe = set(ProfesorMateria.objects.filter(user=request.user).values_list('materia_id', flat=True))
    materias_profe.update(Materia.objects.filter(profesor_titular=request.user).values_list('id', flat=True))

    for c in clases:
        es_profe_de_esta = c.materia_id in materias_profe
        eventos.append({
            'title': f"{c.materia.nombre} ({c.hora_inicio.strftime('%H:%M')})",
            'start': c.fecha.isoformat(),
            'id': c.id,
            'materia_id': c.materia.id,
            'color': '#4CAF50' if c.ventana_activa() else '#888',
            'can_edit': es_profe_de_esta,
            'link_clase': c.link_clase,
            'tema': c.tema,
            'hora_inicio': c.hora_inicio.strftime('%H:%M'),
            'hora_fin': c.hora_fin.strftime('%H:%M'),
        })

        })

    # Materias donde el usuario puede crear clases (para el modal del calendario)
    materias_creables = []
    if request.user.is_authenticated and (request.user.nivel >= 2):
        # Titular o profesor adjunto
        materias_creables = Materia.objects.filter(
            models.Q(profesor_titular=request.user) |
            models.Q(profesores__user=request.user)
        ).distinct()

    return render(request, 'asistencias/calendario.html', {
        'diplomatura': diplomatura,
        'eventos': eventos,
        'materias_creables': materias_creables,
    })




@requiere_nivel(1)
def marcar_presente(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)

    # Bloquear docentes de esa materia
    if ProfesorMateria.objects.filter(user=request.user, materia=clase.materia).exists():
        return HttpResponseForbidden("Los docentes no marcan asistencia en su propia materia.")

    # Debe estar inscripto como alumno
    if not InscripcionMateria.objects.filter(user=request.user, materia=clase.materia).exists():
        return HttpResponseForbidden("No estás inscripto en la materia.")

    if not clase.ventana_activa():
        messages.error(request, "Fuera de la ventana horaria.")
        return redirect('asistencias:ver_clases', materia_id=clase.materia.id)

    Asistencia.objects.get_or_create(clase=clase, user=request.user)
    messages.success(request, "Presente registrado.")
    return redirect('asistencias:ver_clases', materia_id=clase.materia.id)


@requiere_nivel(1)
def desinscribirse_materia(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    if ProfesorMateria.objects.filter(user=request.user, materia=materia).exists():
        return HttpResponseForbidden("Sos profesor de esta materia: no podés desinscribirte como alumno.")
    insc = InscripcionMateria.objects.filter(user=request.user, materia=materia).first()
    if not insc:
        messages.info(request, "No estabas inscripto en esta materia.")
        return redirect('asistencias:listar_materias')
    if request.method == 'POST':
        insc.delete()
        messages.success(request, f"Te desinscribiste de {materia.nombre}.")
        return redirect('asistencias:listar_materias')
    return render(request, 'asistencias/confirmar_desinscripcion.html', {'materia': materia})

# (… y el resto de vistas de alumno: home, perfil, etc.)
