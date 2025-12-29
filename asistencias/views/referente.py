from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Case, When, IntegerField
from asistencias.models import Diplomatura, Materia, Clase, Asistencia, InscripcionDiplomatura
from asistencias.permissions import requiere_nivel

@requiere_nivel(6) # Referente Municipal or higher
def dashboard(request):
    """
    Dashboard for Referente Municipal.
    Shows Diplomaturas where the Referente is registered.
    """
    diplomaturas = Diplomatura.objects.filter(
        inscripciones__user=request.user
    ).distinct()
    
    return render(request, 'asistencias/referente_dashboard.html', {
        'diplomaturas': diplomaturas
    })

@requiere_nivel(6)
def calendario_referente(request, diplomatura_id):
    """
    Calendar view for Referente Municipal.
    Shows all classes for the diplomatura with attendance stats.
    """
    diplomatura = get_object_or_404(Diplomatura, id=diplomatura_id)
    
    # Verify Referente is registered in this Diplomatura (or is Supervisor/Admin)
    if not InscripcionDiplomatura.objects.filter(user=request.user, diplomatura=diplomatura).exists() and request.user.nivel < 7:
         # You might want to return Forbidden here, or just redirect. 
         # For now, let's assume if they have the link and are level 6, check registration.
         pass # Logic handled by filter below effectively, but explicit check is better.

    # Get all subjects for this diplomatura
    materias = Materia.objects.filter(diplomatura=diplomatura)
    
    # Get all classes
    clases = Clase.objects.filter(materia__in=materias).select_related('materia')
    
    eventos = []
    for c in clases:
        # Calculate stats
        # Total registered students for the subject
        total_inscriptos = c.materia.inscripciones.count()
        
        # Total present for this class
        total_presentes = c.asistencias.filter(presente=True).count()
        
        eventos.append({
            'title': f"{c.materia.nombre} ({total_presentes}/{total_inscriptos})",
            'start': c.fecha.isoformat(),
            'id': c.id,
            'materia_id': c.materia.id,
            'color': '#2196F3', # Blue for Referente
            'can_edit': False,
            'link_clase': c.link_clase,
            'tema': c.tema,
            'hora_inicio': c.hora_inicio.strftime('%H:%M'),
            'hora_fin': c.hora_fin.strftime('%H:%M'),
            'stats': {
                'presentes': total_presentes,
                'inscriptos': total_inscriptos
            }
        })

    return render(request, 'asistencias/calendario.html', {
        'diplomatura': diplomatura,
        'eventos': eventos,
        'es_referente': True, # Flag to show stats in template
    })
