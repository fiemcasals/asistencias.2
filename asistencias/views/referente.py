from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Prefetch, Avg
from asistencias.models import Diplomatura, InscripcionDiplomatura, Clase, Asistencia, Materia, InscripcionMateria, Nota
from asistencias.permissions import requiere_nivel

@requiere_nivel(6)
def dashboard(request):
    diplomaturas = Diplomatura.objects.filter(
        inscripciones__user=request.user
    ).distinct()
    return render(request, 'asistencias/referente_dashboard.html', {'diplomaturas': diplomaturas})

@requiere_nivel(6)
def calendario_referente(request, diplomatura_id):
    diplomatura = get_object_or_404(Diplomatura, id=diplomatura_id)
    
    if not InscripcionDiplomatura.objects.filter(user=request.user, diplomatura=diplomatura).exists() and request.user.nivel != 7:
         return redirect('asistencias:referente_dashboard')

    clases = Clase.objects.filter(materia__diplomatura=diplomatura).select_related('materia')
    
    eventos = []
    for c in clases:
        total_inscriptos = c.materia.inscripciones.count()
        total_presentes = c.asistencias.filter(presente=True).count()
        
        eventos.append({
            'id': c.id,
            'title': f"{c.materia.nombre} ({total_presentes}/{total_inscriptos})",
            'start': c.fecha.isoformat(),
            'hora_inicio': c.hora_inicio.strftime("%H:%M"),
            'hora_fin': c.hora_fin.strftime("%H:%M"),
            'tema': c.tema,
            'link_clase': c.link_clase,
            'materia_id': c.materia.id,
            'can_edit': False,
            'color': '#28a745' if total_presentes > 0 else '#6c757d',
            'url': f"/referente/clases/{c.id}/asistencia/", # Link to details
            'stats': {
                'presentes': total_presentes,
                'inscriptos': total_inscriptos
            }
        })

    return render(request, 'asistencias/calendario.html', {
        'diplomatura': diplomatura,
        'eventos': eventos,
        'es_referente': True
    })

@requiere_nivel(6)
def ver_asistencia_clase(request, clase_id):
    clase = get_object_or_404(Clase.objects.select_related('materia', 'materia__diplomatura'), id=clase_id)
    diplomatura = clase.materia.diplomatura
    
    if not InscripcionDiplomatura.objects.filter(user=request.user, diplomatura=diplomatura).exists() and request.user.nivel != 7:
         return redirect('asistencias:referente_dashboard')

    asistencias = Asistencia.objects.filter(clase=clase).select_related('user').order_by('user__last_name')
    inscriptos = InscripcionMateria.objects.filter(materia=clase.materia).select_related('user').order_by('user__last_name')
    
    lista_completa = []
    asistencia_map = {a.user_id: a for a in asistencias}
    
    for insc in inscriptos:
        a = asistencia_map.get(insc.user.id)
        lista_completa.append({
            'alumno': insc.user,
            'presente': a.presente if a else False,
            'timestamp': a.timestamp if a else None
        })

    return render(request, 'asistencias/ver_asistencia_clase.html', {
        'clase': clase,
        'lista_completa': lista_completa
    })

@requiere_nivel(6)
def listar_materias_referente(request, diplomatura_id):
    diplomatura = get_object_or_404(Diplomatura, id=diplomatura_id)
    
    if not InscripcionDiplomatura.objects.filter(user=request.user, diplomatura=diplomatura).exists() and request.user.nivel != 7:
         return redirect('asistencias:referente_dashboard')

    materias = Materia.objects.filter(diplomatura=diplomatura)
    
    return render(request, 'asistencias/referente_materias.html', {
        'diplomatura': diplomatura,
        'materias': materias
    })

@requiere_nivel(6)
def ver_notas_materia(request, materia_id):
    materia = get_object_or_404(Materia.objects.select_related('diplomatura'), id=materia_id)
    diplomatura = materia.diplomatura
    
    if not InscripcionDiplomatura.objects.filter(user=request.user, diplomatura=diplomatura).exists() and request.user.nivel != 7:
         return redirect('asistencias:referente_dashboard')

    notas = Nota.objects.filter(materia=materia).select_related('alumno', 'evaluador').order_by('alumno__last_name')
    
    return render(request, 'asistencias/ver_notas_materia.html', {
        'materia': materia,
        'notas': notas
    })
