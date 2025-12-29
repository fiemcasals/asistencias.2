# Re-exporta las vistas para mantener compatibilidad con "from . import views" en urls.py
    home, perfil, listar_diplomaturas, listar_materias,
    insc_diplomatura_por_codigo, insc_materia_por_codigo,
    ver_clases_materia, marcar_presente, desinscribirse_materia,
)
from .referente import dashboard, calendario_referente, ver_asistencia_clase, listar_materias_referente, ver_notas_materia
from .supervisor import switch_role
from .tokens import usar_token
from .docente import crear_materia, crear_clase, listado_presentes, generar_token_adjunto, editar_clase, eliminar_clase
from .coordinador import crear_diplomatura, cargar_excel_inscripciones
from .reportes import exportar_reportes
from .reportes_constancia import generar_constancia
from .publico import publico, consulta_publica
from .exportar import exportar_xlsx, exportar_asistencia_materia, exportar_asistencia_diplomatura
from .notas import cargar_notas, mis_notas, promedios_materia

__all__ = [
    # alumno
    "home", "perfil", "listar_diplomaturas", "listar_materias",
    "insc_diplomatura_por_codigo", "insc_materia_por_codigo",
    "ver_clases_materia", "marcar_presente", "desinscribirse_materia",
    # tokens
    "usar_token",
    # docente
    "crear_materia", "crear_clase", "listado_presentes", "generar_token_adjunto",
    # coordinador
    "crear_diplomatura", "cargar_excel_inscripciones", "generar_constancia",
    # reportes
    "exportar_reportes",
    # público
    "publico", "consulta_publica",
     # exportar
    "exportar_xlsx", "exportar_asistencia_materia",
    # notas
    "cargar_notas", "mis_notas", "promedios_materia",
]
