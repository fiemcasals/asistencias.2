from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import timedelta
from asistencias.models import Diplomatura, Materia, Clase, InscripcionMateria, ProfesorMateria, Asistencia
from asistencias.permissions import requiere_nivel
from asistencias.permissions import requiere_nivel
from asistencias.forms import CrearMateriaForm, ClaseForm
from asistencias.models import ProfesorMateria
from django.db.models import Prefetch



@requiere_nivel(2)
def crear_materia(request):
    if request.method == "POST":
        form = CrearMateriaForm(request.POST)
        if form.is_valid():
            mat = form.save(commit=False)
            mat.profesor_titular = request.user
            mat.save()
            ProfesorMateria.objects.get_or_create(
                user=request.user, materia=mat, rol="titular"
            )
            messages.success(request, "Materia creada.")
            return redirect("asistencias:listar_materias")
    else:
        form = CrearMateriaForm()
    return render(request, "asistencias/crear_materia.html", {"form": form})



@requiere_nivel(2)
def crear_clase(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    if not ProfesorMateria.objects.filter(user=request.user, materia=materia).exists():
        return HttpResponseForbidden("No sos profesor de esta materia.")
    if request.method == 'POST':
        form = ClaseForm(request.POST)
        if form.is_valid():
            # Datos base
            materia = form.cleaned_data['materia']
            hi = form.cleaned_data['hora_inicio']
            hf = form.cleaned_data['hora_fin']
            tema = form.cleaned_data['tema']
            
            # Recurrencia
            cada_dias = form.cleaned_data.get('repetir_cada')
            hasta = form.cleaned_data.get('repetir_hasta')

            # Primera clase
            Clase.objects.create(
                materia=materia,
                fecha=hi.date(),
                hora_inicio=hi,
                hora_fin=hf,
                tema=tema
            )
            count = 1

            # Si hay recurrencia
            if cada_dias and hasta:
                current_hi = hi + timedelta(days=cada_dias)
                current_hf = hf + timedelta(days=cada_dias)
                
                while current_hi.date() <= hasta:
                    Clase.objects.create(
                        materia=materia,
                        fecha=current_hi.date(),
                        hora_inicio=current_hi,
                        hora_fin=current_hf,
                        tema=tema
                    )
                    current_hi += timedelta(days=cada_dias)
                    current_hf += timedelta(days=cada_dias)
                    count += 1

            messages.success(request, f"Se crearon {count} clase(s).")
            return redirect('asistencias:ver_clases', materia_id=materia.id)
    else:
        # Form inicial con materia pre-seleccionada
        form = ClaseForm(initial={'materia': materia})

    return render(request, 'asistencias/crear_clase.html', {'materia': materia, 'form': form})


@requiere_nivel(2)
def editar_clase(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    materia = clase.materia
    
    # Permisos (mismo check que crear_clase)
    if not (ProfesorMateria.objects.filter(user=request.user, materia=materia).exists() or materia.profesor_titular == request.user):
        return HttpResponseForbidden("No tenés permiso para editar esta clase.")

    if request.method == 'POST':
        form = ClaseForm(request.POST, instance=clase)
        if form.is_valid():
            form.save()
            messages.success(request, "Clase actualizada.")
            return redirect('asistencias:home') # O volver al calendario
    else:
        form = ClaseForm(instance=clase)

    return render(request, 'asistencias/editar_clase.html', {'form': form, 'clase': clase})


@requiere_nivel(2)
def eliminar_clase(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    materia = clase.materia
    
    if not (ProfesorMateria.objects.filter(user=request.user, materia=materia).exists() or materia.profesor_titular == request.user):
        return HttpResponseForbidden("No tenés permiso para eliminar esta clase.")

    if request.method == 'POST':
        clase.delete()
        messages.success(request, "Clase eliminada.")
        return redirect('asistencias:home')

    return render(request, 'asistencias/eliminar_clase.html', {'clase': clase})



@requiere_nivel(2)
def listado_presentes(request, materia_id):
    materia = get_object_or_404(Materia.objects.select_related('diplomatura'), id=materia_id)

    # Solo docentes (titular o adjunto) de esta materia
    if not ProfesorMateria.objects.filter(user=request.user, materia=materia).exists():
        return HttpResponseForbidden("No sos profesor de esta materia.")

    # Inscritos con user prefetch
    inscriptos = (InscripcionMateria.objects
                  .filter(materia=materia)
                  .select_related('user')
                  .order_by('user__last_name', 'user__first_name'))

    # Prefetch asistencias por clase para no hacer N+1
    clases = (materia.clases
              .all()
              .prefetch_related(
                  Prefetch('asistencias',
                           queryset=Asistencia.objects.select_related('user').only('user_id', 'presente', 'timestamp'))
              )
              .order_by('-fecha', '-hora_inicio'))

    # Armamos “filas” por clase: cada fila = un alumno inscrito + su asistencia (si existe)
    planillas = []  # [(clase, [filas])]
    for clase in clases:
        # Map rápido user_id -> asistencia
        a_por_uid = {a.user_id: a for a in clase.asistencias.all()}

        filas = []
        for ins in inscriptos:
            u = ins.user
            a = a_por_uid.get(u.id)  # puede ser None
            filas.append({
                'dni': u.dni,
                'alumno': f"{u.last_name}, {u.first_name}",
                'presente': (a.presente if a else False),
                'timestamp': (a.timestamp if a else None),
            })
        planillas.append((clase, filas))

    return render(request, 'asistencias/listado_presentes.html', {
        'materia': materia,
        'planillas': planillas,
    })


# asistencias/views/docentes.py (o donde la tengas)
from django.http import HttpResponseForbidden
from asistencias.models import AccesoToken, Materia

@requiere_nivel(2)
def generar_token_adjunto(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    if materia.profesor_titular_id != request.user.id:
        return HttpResponseForbidden("Sólo el titular puede generar este token.")

    tok = AccesoToken.objects.create(
        nivel_destino=2,
        materia=materia,
        creado_por=request.user,
    )
    messages.success(request, f"Token generado: {tok.code}")
    return redirect('asistencias:listado_presentes', materia_id=materia.id)
