from django.urls import path, include
from . import views 


app_name = 'asistencias'

urlpatterns = [
    path('', views.home, name='home'),

    # Alumno / nivel 1
    path('perfil/', views.perfil, name='perfil'),
    path('diplomaturas/', views.listar_diplomaturas, name='listar_diplomaturas'),
    path('diplomaturas/<int:diplomatura_id>/calendario/', views.calendario_diplomatura, name='calendario_diplomatura'),
    path('materias/', views.listar_materias, name='listar_materias'),
    path('inscribirse/diplomatura/', views.insc_diplomatura_por_codigo, name='insc_diplomatura_codigo'),
    path('inscribirse/materia/', views.insc_materia_por_codigo, name='insc_materia_codigo'),
    path('clases/<int:materia_id>/', views.ver_clases_materia, name='ver_clases'),
    path('clases/<int:clase_id>/presente/', views.marcar_presente, name='marcar_presente'),

    # Tokens
    path('token/usar/', views.usar_token, name='usar_token'),

    # Docente / nivel 2
    path('materias/crear/', views.crear_materia, name='crear_materia'),
    path('materias/<int:materia_id>/crear-clase/', views.crear_clase, name='crear_clase'),
    path('materias/<int:materia_id>/presentes/', views.listado_presentes, name='listado_presentes'),
    path('clases/<int:clase_id>/editar/', views.editar_clase, name='editar_clase'),
    path('clases/<int:clase_id>/eliminar/', views.eliminar_clase, name='eliminar_clase'),
    path('materias/<int:materia_id>/generar-token-adjunto/', views.generar_token_adjunto, name='token_adjunto'),

    # Coordinador / nivel 3
    path('diplomaturas/crear/', views.crear_diplomatura, name='crear_diplomatura'),
    path('diplomaturas/<int:diplo_id>/cargar-excel/', views.cargar_excel_inscripciones, name='cargar_excel'),
    path('diplomaturas/constancia-alumno-regular/', views.generar_constancia, name='generar_constancia'),

    # Reportes
    path('reportes/exportar/', views.exportar_reportes, name='exportar_reportes'),

    # Público
    path('publico/', views.publico, name='publico'),
    path('publico/consulta/', views.consulta_publica, name='consulta_publica'),

    #desincribirse de una materia
    path('materias/<int:materia_id>/desinscribirse/', views.desinscribirse_materia, name='desinscribirse_materia'),

    #exportar datos
    path('exportar/xlsx/', views.exportar_xlsx, name='exportar_xlsx'),
    path('materias/<int:materia_id>/exportar-asistencia/', views.exportar_asistencia_materia, name='exportar_asistencia_materia'),

    path('materias/<int:materia_id>/exportar-asistencia/', views.exportar_asistencia_materia, name='exportar_asistencia_materia'),

    # Notas
    path('materias/<int:materia_id>/notas/', views.cargar_notas, name='cargar_notas'),
    path('mis-notas/', views.mis_notas, name='mis_notas'),
    path('materias/<int:materia_id>/promedios/', views.promedios_materia, name='promedios_materia'),

]
