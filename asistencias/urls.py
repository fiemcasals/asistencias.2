from django.urls import path
from . import views 

app_name = 'asistencias'

urlpatterns = [
    path('', views.home, name='home'),

    # --- NIVEL 1: ALUMNO ---
    path('perfil/', views.perfil, name='perfil'),
    path('diplomaturas/', views.listar_diplomaturas, name='listar_diplomaturas'),
    path('diplomaturas/<int:diplomatura_id>/calendario/', views.calendario_diplomatura, name='calendario_diplomatura'),
    path('materias/', views.listar_materias, name='listar_materias'),
    path('inscribirse/diplomatura/', views.insc_diplomatura_por_codigo, name='insc_diplomatura_codigo'),
    path('inscribirse/materia/', views.insc_materia_por_codigo, name='insc_materia_codigo'),
    path('clases/<int:materia_id>/', views.ver_clases_materia, name='ver_clases'),
    path('clases/<int:clase_id>/presente/', views.marcar_presente, name='marcar_presente'),
    path('materias/<int:materia_id>/desinscribirse/', views.desinscribirse_materia, name='desinscribirse_materia'),
    path('mis-notas/', views.mis_notas, name='mis_notas'),

    # --- TOKENS ---
    path('token/usar/', views.usar_token, name='usar_token'),

    # --- NIVEL 2: DOCENTE ---
    path('clases/<int:clase_id>/editar/', views.editar_clase, name='editar_clase'),
    path('materias/<int:materia_id>/presentes/', views.listado_presentes, name='listado_presentes'),
    path('materias/<int:materia_id>/notas/', views.cargar_notas, name='cargar_notas'),
    path('materias/<int:materia_id>/promedios/', views.promedios_materia, name='promedios_materia'),
    # Nombre de función: detalle_asistencia_clase | Nombre de URL: ver_asistencia_clase
    path('clase/<int:clase_id>/detalle/', views.detalle_asistencia_clase, name='ver_asistencia_clase'),
    path('materia/<int:materia_id>/exportar/', views.exportar_asistencia_materia, name='exportar_asistencia'),

    # --- NIVEL 3: COORDINADOR ---
    path('materias/crear/', views.crear_materia, name='crear_materia'),
    path('diplomaturas/crear/', views.crear_diplomatura, name='crear_diplomatura'),
    path('diplomaturas/<int:diplo_id>/cargar-excel/', views.cargar_excel_inscripciones, name='cargar_excel'),
    path('diplomaturas/constancia-alumno-regular/', views.generar_constancia, name='generar_constancia'),
    path('reportes/exportar/', views.exportar_reportes, name='exportar_reportes'),

    # --- NIVEL 6: REFERENTE MUNICIPAL ---
    path('referente/dashboard/', views.dashboard, name='referente_dashboard'),
    path('referente/diplomaturas/<int:diplomatura_id>/calendario/', views.calendario_referente, name='calendario_referente'),
    path('referente/clases/<int:clase_id>/asistencia/', views.detalle_asistencia_clase, name='referente_asistencia'),
    path('referente/diplomaturas/<int:diplomatura_id>/materias/', views.listar_materias_referente, name='referente_materias'),
    path('referente/materias/<int:materia_id>/notas/', views.ver_notas_materia, name='ver_notas_materia'),
    
    # --- OTROS ---
    path('supervisor/switch-role/<int:role_id>/', views.switch_role, name='switch_role'),
    path('exportar/xlsx/', views.exportar_xlsx, name='exportar_xlsx'),
    path('materias/<int:materia_id>/exportar-asistencia/', views.exportar_asistencia_materia, name='exportar_asistencia_materia'),
    path('diplomaturas/<int:diplomatura_id>/exportar-asistencia/', views.exportar_asistencia_diplomatura, name='exportar_asistencia_diplomatura'),

    # --- ACCESO PÚBLICO ---
    path('publico/', views.publico, name='publico'),
    path('publico/consulta/', views.consulta_publica, name='consulta_publica'),
]
