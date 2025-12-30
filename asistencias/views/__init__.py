# FILE: asistencias/views/__init__.py
from .referente import dashboard, calendario_referente, ver_asistencia_clase, listar_materias_referente, ver_notas_materia
# IMPORTANTE: switch_role sale de supervisor.py
from .supervisor import switch_role 
from .tokens import usar_token
from .reportes import exportar_reportes
from .reportes_constancia import generar_constancia
from .publico import publico, consulta_publica
from .exportar import exportar_xlsx, exportar_asistencia_materia, exportar_asistencia_diplomatura
from .notas import cargar_notas, mis_notas, promedios_materia

from .docente import editar_clase, listado_presentes, detalle_asistencia_clase
from .alumno import (
    home, perfil, listar_materias, listar_diplomaturas, 
    ver_clases_materia, insc_materia_por_codigo,
    insc_diplomatura_por_codigo, marcar_presente, desinscribirse_materia
)

from .coordinador import (
    crear_materia, crear_diplomatura, cargar_excel_inscripciones, calendario_diplomatura
)

__all__ = [
    "home", "perfil", "listar_diplomaturas", "listar_materias",
    "insc_diplomatura_por_codigo", "insc_materia_por_codigo",
    "ver_clases_materia", "marcar_presente", "desinscribirse_materia",
    "editar_clase", "listado_presentes", "switch_role",
    "crear_materia", "crear_diplomatura", "cargar_excel_inscripciones", "calendario_diplomatura",
    "usar_token", "generar_constancia", "exportar_reportes", "publico", "consulta_publica",
    "exportar_xlsx", "exportar_asistencia_materia", "exportar_asistencia_diplomatura",
    "cargar_notas", "mis_notas", "promedios_materia",
    "dashboard", "calendario_referente", "ver_asistencia_clase","detalle_asistencia_clase", 
    "listar_materias_referente", "ver_notas_materia"
]
