from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from ..models import Materia, Nota, InscripcionMateria, User
from ..forms import NotaForm

@login_required
def cargar_notas(request, materia_id):
    if request.user.nivel == 6:
        return HttpResponseForbidden("No tenés permisos para cargar notas.")
    materia = get_object_or_404(Materia, id=materia_id)
    
    # Verificar si el usuario es profesor de la materia o coordinador
    es_profesor = materia.profesores.filter(user=request.user).exists()
    es_titular = materia.profesor_titular == request.user
    es_coordinador = request.user.nivel >= 3 # Asumiendo 3 es coordinador
    
    if not (es_profesor or es_titular or es_coordinador):
        messages.error(request, "No tienes permiso para cargar notas en esta materia.")
        return redirect('asistencias:home')

    alumnos = User.objects.filter(insc_materias__materia=materia).order_by('last_name', 'first_name')
    
    if request.method == 'POST':
        alumno_id = request.POST.get('alumno_id')
        alumno = get_object_or_404(User, id=alumno_id)
        form = NotaForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.alumno = alumno
            nota.materia = materia
            nota.evaluador = request.user
            nota.save()
            messages.success(request, f"Nota cargada para {alumno}")
            return redirect('asistencias:cargar_notas', materia_id=materia.id)
    else:
        form = NotaForm()

    context = {
        'materia': materia,
        'alumnos': alumnos,
        'form': form,
    }
    return render(request, 'asistencias/cargar_notas.html', context)

@login_required
def mis_notas(request):
    notas = Nota.objects.filter(alumno=request.user).order_by('-fecha')
    promedios = Nota.objects.filter(alumno=request.user).values('materia__nombre').annotate(promedio=Avg('valor'))
    
    context = {
        'notas': notas,
        'promedios': promedios,
    }
    return render(request, 'asistencias/mis_notas.html', context)

@login_required
def promedios_materia(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    
    # Verificar permisos (similar a cargar_notas)
    es_profesor = materia.profesores.filter(user=request.user).exists()
    es_titular = materia.profesor_titular == request.user
    es_coordinador = request.user.nivel >= 3
    
    if not (es_profesor or es_titular or es_coordinador):
        messages.error(request, "No tienes permiso para ver los promedios de esta materia.")
        return redirect('asistencias:home')

    promedios = Nota.objects.filter(materia=materia).values('alumno__last_name', 'alumno__first_name').annotate(promedio=Avg('valor')).order_by('alumno__last_name')
    
    context = {
        'materia': materia,
        'promedios': promedios,
    }
    return render(request, 'asistencias/promedios_materia.html', context)
