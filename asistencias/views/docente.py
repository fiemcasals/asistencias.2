from django.db import models
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth import get_user_model
from functools import wraps
from ..models import Clase, Materia, User, Nota, Asistencia 
import csv

# 1. DECORADOR DE SEGURIDAD
def requiere_nivel(nivel_minimo):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.nivel >= nivel_minimo:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
        return _wrapped_view
    return decorator

# 2. LISTADO GENERAL DE ASISTENCIA (MATRIZ)
@requiere_nivel(2)
def listado_presentes(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    # Filtro por materia para evitar el mensaje "Sin clases"
    clases = Clase.objects.filter(materia=materia).order_by('fecha')
    
    alumnos = User.objects.filter(
        Q(insc_materias__materia=materia) | Q(insc_diplos__diplomatura=materia.diplomatura),
        nivel=1
    ).distinct().order_by('last_name')

    return render(request, 'asistencias/listado_presentes.html', {
        'materia': materia,
        'clases': clases,
        'alumnos': alumnos,
    })

# 3. DETALLE DE ASISTENCIA POR CLASE (La que faltaba en el import)
@requiere_nivel(2)
def detalle_asistencia_clase(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    materia = clase.materia
    
    alumnos_inscritos = User.objects.filter(
        Q(insc_materias__materia=materia) | Q(insc_diplos__diplomatura=materia.diplomatura),
        nivel=1
    ).distinct().order_by('last_name')

    # Obtenemos IDs de alumnos presentes usando el campo 'alumno_id'
    presentes_ids = clase.asistencias.filter(presente=True).values_list('alumno_id', flat=True)
    
    lista_asistencia = []
    for alumno in alumnos_inscritos:
        registro = clase.asistencias.filter(alumno=alumno).first()
        lista_asistencia.append({
            'alumno': alumno,
            'asistio': alumno.id in presentes_ids,
            'hora_registro': registro.timestamp if registro else None
        })
        
    return render(request, 'asistencias/detalle_asistencia.html', {
        'clase': clase,
        'materia': materia,
        'lista_asistencia': lista_asistencia
    })

# 4. EXPORTAR ASISTENCIA A CSV
@requiere_nivel(2)
def exportar_asistencia_materia(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    clases = materia.clases.all().order_by('fecha')
    
    alumnos = User.objects.filter(
        Q(insc_materias__materia=materia) | Q(insc_diplos__diplomatura=materia.diplomatura),
        nivel=1
    ).distinct().order_by('last_name')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="asistencia_{materia.nombre}.csv"'

    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    
    header = ['Alumno', 'DNI'] + [clase.fecha.strftime('%d/%m/%Y') for clase in clases]
    writer.writerow(header)

    for alumno in alumnos:
        fila = [f"{alumno.last_name}, {alumno.first_name}", alumno.dni]
        for clase in clases:
            asistio = clase.asistencias.filter(alumno=alumno, presente=True).exists()
            fila.append('P' if asistio else 'A')
        writer.writerow(fila)
        
    return response

# 5. VER NOTAS DE LA MATERIA
@requiere_nivel(2)
def ver_notas_materia(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    
    alumnos = User.objects.filter(
        Q(insc_materias__materia=materia) | Q(insc_diplos__diplomatura=materia.diplomatura),
        nivel=1
    ).distinct().order_by('last_name')

    listado_notas = []
    for alumno in alumnos:
        notas_alumno = Nota.objects.filter(alumno=alumno, materia=materia)
        listado_notas.append({
            'alumno': alumno,
            'notas': notas_alumno
        })

    return render(request, 'asistencias/ver_notas_materia.html', {
        'materia': materia,
        'listado_notas': listado_notas
    })

# 6. EDITAR TEMA DE CLASE
@requiere_nivel(2)
def editar_clase(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    from ..forms import ClaseForm
    
    if request.method == 'POST':
        form = ClaseForm(request.POST, instance=clase)
        if request.user.nivel == 2:
            form.fields.pop('fecha', None)
            form.fields.pop('hora_inicio', None)
            form.fields.pop('hora_fin', None)
            form.fields.pop('materia', None)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Cambios guardados exitosamente.")
            return redirect('asistencias:ver_clases', materia_id=clase.materia.id)
    else:
        form = ClaseForm(instance=clase)

    return render(request, 'asistencias/editar_clase.html', {'form': form, 'clase': clase})
