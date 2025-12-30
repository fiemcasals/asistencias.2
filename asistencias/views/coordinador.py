# FILE: asistencias/views/coordinador.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib import messages

from asistencias.models import Diplomatura
from asistencias.permissions import requiere_nivel
from asistencias.forms import CrearMateriaForm  # Importante para que crear_materia no falle

@requiere_nivel(3)
def crear_materia(request):
    """Permite a los coordinadores crear materias."""
    if request.method == 'POST':
        form = CrearMateriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Materia creada correctamente por el coordinador.")
            return redirect('asistencias:home')
    else:
        form = CrearMateriaForm()
    return render(request, 'asistencias/crear_materia.html', {'form': form})

@requiere_nivel(3)
def crear_diplomatura(request):
    """Permite a los coordinadores crear diplomaturas, excluyendo al nivel 6."""
    if request.user.nivel == 6:
        return HttpResponseForbidden("No tenés permisos para crear diplomaturas.")
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        codigo = request.POST.get('codigo', '').strip()
        Diplomatura.objects.create(nombre=nombre, codigo=codigo, creada_por=request.user)
        messages.success(request, "Diplomatura creada.")
        return redirect('asistencias:home') # Cambiado para evitar error si 'listar_diplomaturas' no existe
    return render(request, 'asistencias/crear_diplomatura.html')

@requiere_nivel(3)
def cargar_excel_inscripciones(request, diplo_id):
    """Lógica para cargar archivos de inscripciones."""
    dip = get_object_or_404(Diplomatura, id=diplo_id)
    if request.method == 'POST' and request.FILES.get('archivo'):
        # TODO: parsear CSV/XLSX aquí
        messages.success(request, "Carga procesada (demo).")
        return redirect('asistencias:home')
    return render(request, 'asistencias/cargar_excel.html', {'diplomatura': dip})

@requiere_nivel(3)
def generar_constancia(request):
    """Función placeholder para evitar errores de importación en el inicio del sistema."""
    # Aquí puedes añadir la lógica de generación de PDF en el futuro.
    return render(request, 'asistencias/generar_constancia.html')

# Al final de asistencias/views/coordinador.py

@requiere_nivel(1) # O el nivel que corresponda
def calendario_diplomatura(request, diplomatura_id):
    dip = get_object_or_404(Diplomatura, id=diplomatura_id)
    # Lógica para obtener eventos de la diplomatura...
    return render(request, 'asistencias/calendario_diplomatura.html', {'diplomatura': dip})
