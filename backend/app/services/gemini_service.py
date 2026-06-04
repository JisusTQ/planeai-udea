"""
Servicio de IA AGÉNTICA: integra Google Gemini con datos en vivo de la UdeA.

Cambio de arquitectura: los grupos, cupos y horarios YA NO salen de la base de
datos. Gemini funciona como un AGENTE con tool-calling: se le entrega la
herramienta `consultar_horarios_udea`, y el propio modelo DECIDE cuándo
invocarla para consultar EN VIVO el portal oficial de Admisiones y Registro.

  - Horarios / cupos / grupos / profesores -> herramienta en vivo (UdeA).
  - Catálogo (créditos y prerrequisitos)     -> contexto desde la BD.

La librería google-generativeai ejecuta el bucle agéntico automáticamente
(`enable_automatic_function_calling=True`): envía la pregunta, recibe la
petición de herramienta del modelo, ejecuta la función Python, le devuelve el
resultado y obtiene la respuesta final, todo en una sola llamada.
"""
import google.generativeai as genai

from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.models import Curso
from app.services import udea_horarios_service as udea

settings = get_settings()

# Instrucción de sistema: define el rol y las reglas del asistente.
SYSTEM_PROMPT = """Eres "PlaneAI", un asistente de planeación académica para estudiantes \
del programa de Ingeniería de Sistemas de la Universidad de Antioquia (UdeA).

Tu objetivo es ayudar a armar horarios y recomendar materias. Reglas estrictas:
1. Para CUALQUIER dato de grupos, cupos, horarios o profesores DEBES usar la
   herramienta `consultar_horarios_udea`, que consulta la oferta REAL y vigente
   del portal oficial. NUNCA inventes grupos, cupos, horarios ni profesores.
2. La herramienta puede recibir el nombre (o parte) de una materia. Si el
   estudiante menciona varias materias, consúltalas (puedes llamar la
   herramienta varias veces).
3. Los créditos y prerrequisitos vienen en el CATÁLOGO que se te entrega como
   contexto (proviene de la base de datos). Crúzalo con la oferta en vivo por el
   NOMBRE de la materia: los códigos del portal y del catálogo pueden diferir.
4. Si un grupo tiene 0 cupos disponibles, adviértelo y sugiere otro grupo.
5. Respeta los prerrequisitos: si el estudiante quiere un curso, menciona qué
   prerrequisitos exige (según el catálogo).
6. Al proponer un horario, evita CHOQUES (dos materias el mismo día a la misma hora).
7. Responde en español, de forma clara, breve y organizada (usa listas cuando ayude).
8. Si la herramienta devuelve un error o no encuentra la materia, dilo con honestidad."""


def consultar_horarios_udea(materia: str = "") -> str:
    """Consulta EN VIVO los grupos, cupos, horarios y profesores de la oferta
    académica vigente del programa de Ingeniería de Sistemas de la UdeA.

    Úsala siempre que necesites información de grupos, cupos disponibles,
    horarios o profesores de una materia.

    Args:
        materia: Nombre (o parte del nombre) de la materia a consultar,
            por ejemplo "cálculo" o "álgebra lineal". Si se deja vacío,
            devuelve la lista de todas las materias disponibles para que
            puedas elegir y volver a consultar con una en concreto.

    Returns:
        Texto con los grupos encontrados (cupos, horario, profesor y aula) o la
        lista de materias disponibles.
    """
    try:
        if not materia.strip():
            nombres = "; ".join(m.nombre for m in udea.obtener_oferta())
            return f"Materias disponibles en la oferta vigente:\n{nombres}"

        materias = udea.buscar_materias(materia)
        if not materias:
            return (
                f"No se encontraron materias que coincidan con '{materia}' "
                "en la oferta vigente."
            )

        lineas: list[str] = []
        for m in materias:
            lineas.append(f"{m.nombre} (código {m.codigo}):")
            for g in m.grupos:
                sesiones = (
                    "; ".join(
                        f"{s.dia} {s.hora_inicio}-{s.hora_fin}" for s in g.horario
                    )
                    or "sin horario"
                )
                lineas.append(
                    f"  - Grupo {g.numero}: cupos {g.cupos_disponibles}/"
                    f"{g.cupos_totales}, profesor {g.profesor}, "
                    f"horario [{sesiones}], aula {g.aula}."
                )
        return "\n".join(lineas)
    except Exception as exc:  # noqa: BLE001 — degradar con elegancia para el modelo
        return f"Error al consultar el portal de la UdeA: {exc}"


def _contexto_catalogo(db: Session) -> tuple[str, int]:
    """
    Arma el contexto del CATÁLOGO (nombre, código, créditos, semestre y
    prerrequisitos) desde la BD. NO incluye grupos ni horarios: esos los obtiene
    el modelo en vivo mediante la herramienta.
    Devuelve (texto_contexto, numero_de_cursos).
    """
    cursos = (
        db.query(Curso)
        .options(selectinload(Curso.prerrequisitos))
        .order_by(Curso.semestre, Curso.nombre)
        .all()
    )

    lineas: list[str] = []
    for c in cursos:
        prereq = ", ".join(p.nombre for p in c.prerrequisitos) or "ninguno"
        lineas.append(
            f"- {c.nombre} (código {c.codigo}, {c.creditos} créditos, "
            f"semestre {c.semestre}). Prerrequisitos: {prereq}."
        )

    return "\n".join(lineas), len(cursos)


def _api_key_valida() -> bool:
    """Comprueba que la GEMINI_API_KEY esté configurada (no es el placeholder)."""
    key = settings.GEMINI_API_KEY or ""
    return bool(key) and not key.startswith("tu_api_key")


def responder(db: Session, mensaje: str) -> tuple[str, int]:
    """
    Genera la respuesta del asistente para el mensaje del estudiante usando un
    agente Gemini con tool-calling automático.
    Devuelve (respuesta, numero_de_cursos_de_catalogo_considerados).

    Lanza ValueError si la API key no está configurada.
    """
    if not _api_key_valida():
        raise ValueError(
            "La GEMINI_API_KEY no está configurada en el .env. "
            "Agrega tu clave real para habilitar el chat."
        )

    genai.configure(api_key=settings.GEMINI_API_KEY)
    catalogo, num_cursos = _contexto_catalogo(db)

    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        tools=[consultar_horarios_udea],
    )
    # El SDK ejecuta automáticamente el bucle agéntico (llamar la herramienta y
    # devolver su resultado al modelo) hasta producir la respuesta final.
    chat = model.start_chat(enable_automatic_function_calling=True)

    prompt = (
        "CATÁLOGO DE CURSOS (créditos y prerrequisitos; fuente: base de datos):\n"
        f"{catalogo}\n\n"
        "Recuerda: para grupos, cupos, horarios y profesores usa la herramienta "
        "`consultar_horarios_udea` (datos en vivo).\n\n"
        f"PREGUNTA DEL ESTUDIANTE:\n{mensaje}"
    )

    respuesta = chat.send_message(prompt)
    return respuesta.text, num_cursos
