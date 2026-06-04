"""
Servicio de IA: integra Google Gemini con los datos reales de la BD.

Idea central (y punto clave del proyecto): la IA NO inventa cursos ni cupos.
El backend consulta la oferta en PostgreSQL, la convierte en un CONTEXTO de
texto y se lo entrega a Gemini junto con la pregunta del estudiante. Así las
respuestas se basan en datos reales y verificables.
"""
import google.generativeai as genai

from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.models import Curso

settings = get_settings()

# Instrucción de sistema: define el rol y las reglas del asistente.
SYSTEM_PROMPT = """Eres "PlaneAI", un asistente de planeación académica para estudiantes \
de la Facultad de Ingeniería de la Universidad de Antioquia (UdeA).

Tu objetivo es ayudar a armar horarios y recomendar materias. Reglas estrictas:
1. Usa ÚNICAMENTE los cursos, grupos, cupos y horarios que se te proporcionan en el
   contexto. NUNCA inventes cursos, códigos, cupos ni horarios.
2. Si un grupo tiene 0 cupos disponibles, adviértelo y sugiere otro grupo si existe.
3. Respeta los prerrequisitos: si el estudiante quiere un curso, menciona qué
   prerrequisitos exige.
4. Al proponer un horario, evita CHOQUES (dos materias el mismo día a la misma hora).
5. Responde en español, de forma clara, breve y organizada (usa listas cuando ayude).
6. Si te preguntan algo que no está en los datos, dilo con honestidad."""


def _construir_contexto(db: Session) -> tuple[str, int]:
    """
    Arma un texto legible con toda la oferta (cursos, grupos, cupos, horarios y
    prerrequisitos) para entregárselo a Gemini como contexto.
    Devuelve (texto_contexto, numero_de_cursos).
    """
    cursos = (
        db.query(Curso)
        .options(
            selectinload(Curso.grupos),
            selectinload(Curso.prerrequisitos),
        )
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
        for g in c.grupos:
            prof = g.profesor.nombre if g.profesor else "Sin asignar"
            sesiones = "; ".join(
                f"{s.get('dia')} {s.get('hora_inicio')}-{s.get('hora_fin')}"
                for s in (g.horario or [])
            ) or "sin horario"
            lineas.append(
                f"    · Grupo {g.numero}: cupos {g.cupos_disponibles}/{g.cupos_totales}, "
                f"profesor {prof}, horario [{sesiones}], aula {g.aula or 'N/D'}."
            )

    return "\n".join(lineas), len(cursos)


def _api_key_valida() -> bool:
    """Comprueba que la GEMINI_API_KEY esté configurada (no es el placeholder)."""
    key = settings.GEMINI_API_KEY or ""
    return bool(key) and not key.startswith("tu_api_key")


def responder(db: Session, mensaje: str) -> tuple[str, int]:
    """
    Genera la respuesta del asistente para el mensaje del estudiante.
    Devuelve (respuesta, numero_de_cursos_considerados).

    Lanza ValueError si la API key no está configurada.
    """
    if not _api_key_valida():
        raise ValueError(
            "La GEMINI_API_KEY no está configurada en el .env. "
            "Agrega tu clave real para habilitar el chat."
        )

    genai.configure(api_key=settings.GEMINI_API_KEY)
    contexto, num_cursos = _construir_contexto(db)

    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
    )

    prompt = (
        "OFERTA DE CURSOS DISPONIBLE (única fuente de verdad):\n"
        f"{contexto}\n\n"
        f"PREGUNTA DEL ESTUDIANTE:\n{mensaje}"
    )

    respuesta = model.generate_content(prompt)
    return respuesta.text, num_cursos
