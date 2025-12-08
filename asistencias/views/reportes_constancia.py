from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from io import BytesIO
import locale

from ..models import Diplomatura, InscripcionDiplomatura

User = get_user_model()

def generar_constancia(request):
    # Solo Coordinadores (3) o Administradores (5)
    if not request.user.is_authenticated or request.user.nivel not in (3, 5):
        return HttpResponseForbidden("No autorizado.")

    if request.method == 'POST':
        dni = request.POST.get('dni')
        # municipio = request.POST.get('municipio', 'CORONEL ROSALES') # Ya no se usa input manual
        
        # Buscar alumno por DNI
        try:
            alumno = User.objects.get(dni=dni)
        except User.DoesNotExist:
            return render(request, 'asistencias/generar_constancia.html', {'error': 'Alumno no encontrado con ese DNI.'})

        # Buscar diplomatura del alumno
        # 1. Intentar buscar inscripción directa a diplomatura
        inscripcion_diplo = InscripcionDiplomatura.objects.filter(user=alumno).first()
        
        if inscripcion_diplo:
            diplomatura = inscripcion_diplo.diplomatura
        else:
            # 2. Si no, buscar inscripción a alguna materia y obtener la diplomatura de ahí
            from ..models import InscripcionMateria
            inscripcion_materia = InscripcionMateria.objects.filter(user=alumno).select_related('materia__diplomatura').first()
            
            if inscripcion_materia:
                diplomatura = inscripcion_materia.materia.diplomatura
            else:
                return render(request, 'asistencias/generar_constancia.html', {'error': 'El alumno no está inscripto en ninguna diplomatura ni materia.'})

        # Verificar si el coordinador tiene acceso a esta diplomatura (si no es admin)
        if request.user.nivel != 5:
            es_coordinador = diplomatura.coordinadores.filter(id=request.user.id).exists()
            es_creador = diplomatura.creada_por_id == request.user.id
            
            if not (es_coordinador or es_creador):
                 return render(request, 'asistencias/generar_constancia.html', {'error': 'No tienes permisos sobre la diplomatura de este alumno.'})

        # Generar PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=2.5*cm, leftMargin=2.5*cm,
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        style_title = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=14,
            spaceAfter=30,
            fontName='Helvetica-Bold',
            textTransform='uppercase',
            underline=True
        )
        
        style_body = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            alignment=TA_JUSTIFY,
            fontSize=12,
            leading=24, # Interlineado
            spaceAfter=20,
            fontName='Times-Roman'
        )
        
        style_date = ParagraphStyle(
            'CustomDate',
            parent=styles['Normal'],
            alignment=TA_RIGHT,
            fontSize=12,
            spaceAfter=50,
            fontName='Times-Roman'
        )

        style_signature = ParagraphStyle(
            'CustomSignature',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=11,
            leading=14,
            fontName='Times-Italic'
        )

        # Header (Logos)
        # Intentar cargar logos si existen
        # Se asume que están en static/core/img/
        import os
        from django.conf import settings
        
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'core', 'img', 'header_logos.png')
        if os.path.exists(logo_path):
            # Ajustar tamaño según necesidad, ej: 16cm ancho
            elements.append(Image(logo_path, width=16*cm, height=2.5*cm))
        else:
            elements.append(Spacer(1, 2.5*cm)) # Espacio si no hay logo

        elements.append(Spacer(1, 1*cm))

        # Título
        elements.append(Paragraph("CONSTANCIA DE ALUMNO REGULAR", style_title))
        elements.append(Spacer(1, 1*cm))

        # Cuerpo
        # Configurar locale para fecha en español
        try:
            locale.setlocale(locale.LC_TIME, 'es_AR.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
            except:
                pass # Fallback a default

        fecha_actual = timezone.now()
        fecha_str = fecha_actual.strftime("%d de %B de %Y")
        
        # Texto modificado: Se quita "Diplomatura en:" para no repetir
        texto = f"""
        Se deja constancia que el Señor/a <b>{alumno.first_name} {alumno.last_name}</b>, DNI <b>{alumno.dni}</b>,
        es alumno regular de la: <b>{diplomatura.nombre}</b> dependiente de
        Universidad Tecnológica Nacional, a través del Plan de Integración Territorial
        de la Provincia de Buenos Aires (PROGRAMA PUENTES).
        """
        elements.append(Paragraph(texto, style_body))

        texto2 = """
        Se extiende el presente certificado a solicitud del/la interesado/a, a solo efecto
        de ser presentado ante quien corresponda. La presente constancia tiene una
        validez de 30 días una vez emitida la misma. ----------------------------------------
        """
        elements.append(Paragraph(texto2, style_body))
        
        elements.append(Spacer(1, 1*cm))

        # Fecha (Solo fecha, sin lugar fijo para no errar)
        elements.append(Paragraph(f"{fecha_str}", style_date))

        elements.append(Spacer(1, 2*cm))

        # Firma
        firma_path = os.path.join(settings.BASE_DIR, 'static', 'core', 'img', 'firma_lucia.png')
        if os.path.exists(firma_path):
            # Ajustar tamaño: duplicado a 10cm ancho x 5cm alto (aprox) para que se vea bien
            elements.append(Image(firma_path, width=10*cm, height=5*cm))
        else:
            # Fallback si no está la imagen
            elements.append(Paragraph("___________________________", style_signature))
            elements.append(Paragraph("Prof. Lucia Yacoy", style_signature))
            elements.append(Paragraph("Dir. Unidad de Gestión del Plan de Integración Territorial de la", style_signature))
            elements.append(Paragraph("Universidad Tecnológica Nacional", style_signature))

        doc.build(elements)
        
        buffer.seek(0)
        filename = f"constancia_{alumno.dni}.pdf"
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    else:
        # GET: Mostrar formulario simple
        return render(request, 'asistencias/generar_constancia.html')
