# FILE: asistencias/views/docente.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import timedelta
from asistencias.models import Diplomatura, Materia, Clase, InscripcionMateria, ProfesorMateria, Asistencia, AccesoToken
from asistencias.permissions import requiere_nivel
from asistencias.forms import CrearMateriaForm, ClaseForm

@requiere_nivel(2)
def crear_clase(request, materia_id):
    # RESTRICCIÓN ESTRICTA: Solo Coordinadores (nivel 3+) pueden crear clases.
    if request.user.nivel < 3:
        return HttpResponseForbidden("Solo los coordinadores pueden crear o definir cronogramas de clases.")
    
    materia = get_object_or_404(Materia, id=materia_id)
    if request.method == 'POST':
        form = ClaseForm(request.POST)
        if form.is_valid():
            hi = form.cleaned_data['hora_inicio']
            hf = form.cleaned_data['hora_fin']
            tema = form.cleaned_data['tema']
            link = form.cleaned_data.get('link_clase', '')
            cada_dias = form.cleaned_data.get('repetir_cada')
            hasta = form.cleaned_data.get('repetir_hasta')

            clase_base = Clase.objects.create(
                materia=materia, fecha=hi.date(), hora_inicio=hi, hora_fin=hf,
                tema=tema, link_clase=link, creado_por=request.user
            )
            count = 1
            if cada_dias and hasta:
                curr_hi, curr_hf = hi + timedelta(days=cada_dias), hf + timedelta(days=cada_dias)
                while curr_hi.date() <= hasta:
                    Clase.objects.create(
                        materia=materia, fecha=curr_hi.date(), hora_inicio=curr_hi, 
                        hora_fin=curr_hf, tema=tema, link_clase=link, creado_por=request.user
                    )
                    curr_hi += timedelta(days=cada_dias)
                    curr_hf += timedelta(days=cada_dias)
                    count += 1
            messages.success(request, f"Se crearon {count} clase(s).")
            return redirect('asistencias:ver_clases', materia_id=materia.id)
    else:
        # Se pre-carga la fecha si viene por GET desde el calendario
        fecha_get = request.GET.get('fecha')
        form = ClaseForm(initial={'materia': materia, 'link_clase': materia.link_clase, 'fecha': fecha_get})
    return render(request, 'asistencias/crear_clase.html', {'materia': materia, 'form': form})

@requiere_nivel(2)
def editar_clase(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    u = request.user
    # Es coordinador si nivel >= 3 o si está en la lista de coordinadores de la diplo
    es_coord = u.nivel >= 3 or clase.materia.diplomatura.coordinadores.filter(id=u.id).exists()
    
    # El docente nivel 2 solo puede entrar si es titular o profesor asignado
    es_profe = ProfesorMateria.objects.filter(user=u, materia=clase.materia).exists() or clase.materia.profesor_titular == u

    if not (es_coord or es_profe):
        return HttpResponseForbidden("No tienes permiso para editar esta clase.")

    if request.method == 'POST':
        form = ClaseForm(request.POST, instance=clase)
        if form.is_valid():
            instancia = form.save(commit=False)
            # SI NO ES COORDINADOR: Forzamos que los campos administrativos no cambien
            if not es_coord:
                # Recuperamos los valores originales de la DB para asegurar que no se alteren
                clase_original = Clase.objects.get(id=clase.id)
                instancia.fecha = clase_original.fecha
                instancia.hora_inicio = clase_original.hora_inicio
                instancia.hora_fin = clase_original.hora_fin
                instancia.materia = clase_original.materia
            
            instancia.save()
            messages.success(request, "Cambios guardados correctamente.")
            return redirect('asistencias:home')
    else:
        form = ClaseForm(instance=clase)
        # Si es Profe (Nivel 2), deshabilitamos los campos en el formulario (visual)
        if not es_coord:
            for campo in ['fecha', 'hora_inicio', 'hora_fin', 'materia']:
                form.fields[campo].widget.attrs['readonly'] = True
                form.fields[campo].widget.attrs['class'] = 'form-control bg-dark muted'

    return render(request, 'asistencias/editar_clase.html', {
        'form': form, 
        'clase': clase, 
        'es_coord': es_coord
    })

@requiere_nivel(2)
def eliminar_clase(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    # SOLO Coordinadores eliminan
    if request.user.nivel < 3:
        return HttpResponseForbidden("Solo los coordinadores pueden eliminar clases.")
    if request.method == 'POST':
        clase.delete()
        messages.success(request, "Clase eliminada del cronograma.")
        return redirect('asistencias:home')
    return render(request, 'asistencias/eliminar_clase.html', {'clase': clase})
