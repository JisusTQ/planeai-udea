"""
Agente Gemini con tool-calling sobre datos en vivo de la UdeA.

Se le entregan dos herramientas (`consultar_pensum` y `consultar_horarios_udea`)
y el modelo decide cuándo invocarlas; el SDK ejecuta el bucle agéntico
automáticamente (enable_automatic_function_calling).
"""
import google.generativeai as genai

from app.config import get_settings
from app.services import udea_horarios_service as udea
from app.services import udea_pensum_service as pensum

settings = get_settings()

# Instrucción de sistema: define el rol y las reglas del asistente.
SYSTEM_PROMPT = """Eres "PlaneAI", un asistente de planeación académica para estudiantes \
del programa de Ingeniería de Sistemas de la Universidad de Antioquia (UdeA).

Tu objetivo es ayudar a armar horarios y recomendar materias. Reglas estrictas:
1. Cuando el estudiante mencione un SEMESTRE o NIVEL (p. ej. "soy de primer
   semestre"), PRIMERO usa la herramienta `consultar_pensum` con ese nivel para
   saber qué materias le corresponden (nivel = semestre: 1=primero, 2=segundo…)
   y sus prerrequisitos.
2. LUEGO consulta los grupos de esas materias con `consultar_horarios_udea`
   pasándolas TODAS en UNA sola llamada, separadas por punto y coma ";"
   (no la llames una vez por materia). Solo recomienda materias que correspondan
   al nivel del estudiante y que tengan cupos disponibles.
3. Para CUALQUIER dato de grupos, cupos, horarios o profesores DEBES usar
   `consultar_horarios_udea`. NUNCA inventes grupos, cupos, horarios ni profesores.
4. Puedes llamar las herramientas varias veces. Cruza pensum y oferta por el
   NOMBRE de la materia; algunas materias del pensum pueden no estar ofertadas
   este semestre (dilo con honestidad).
5. Si pide algo "en la mañana", filtra horarios antes de las 12:00; "en la tarde",
   de 12:00 en adelante.
6. Si un grupo tiene 0 cupos disponibles, adviértelo y sugiere otro grupo.
7. Respeta los prerrequisitos que entrega `consultar_pensum`: si una materia exige
   prerrequisitos, menciónalo.
8. Al proponer un horario, evita CHOQUES (dos materias el mismo día a la misma hora).
9. Responde en español, de forma clara, breve y organizada (usa listas cuando ayude).
10. Si una herramienta devuelve un error o no encuentra datos, dilo con honestidad."""


def _formatear_materia(m) -> list[str]:
    lineas = [f"{m.nombre} (código {m.codigo}):"]
    for g in m.grupos:
        sesiones = (
            "; ".join(f"{s.dia} {s.hora_inicio}-{s.hora_fin}" for s in g.horario)
            or "sin horario"
        )
        lineas.append(
            f"  - Grupo {g.numero}: cupos {g.cupos_disponibles}/"
            f"{g.cupos_totales}, profesor {g.profesor}, "
            f"horario [{sesiones}], aula {g.aula}."
        )
    return lineas


def consultar_horarios_udea(materia: str = "") -> str:
    """Consulta EN VIVO los grupos, cupos, horarios y profesores de la oferta
    académica vigente del programa de Ingeniería de Sistemas de la UdeA.

    Úsala siempre que necesites información de grupos, cupos disponibles,
    horarios o profesores de una o varias materias.

    Args:
        materia: Nombre (o parte) de la materia. Para consultar VARIAS materias
            de una sola vez (recomendado, p. ej. todas las de un semestre),
            sepáralas con punto y coma ";", por ejemplo
            "cálculo diferencial; álgebra y trigonometría; geometría vectorial".
            Si se deja vacío, devuelve la lista de materias disponibles.

    Returns:
        Texto con los grupos encontrados de cada materia (cupos, horario,
        profesor y aula) o la lista de materias disponibles.
    """
    try:
        if not materia.strip():
            nombres = "; ".join(m.nombre for m in udea.obtener_oferta())
            return f"Materias disponibles en la oferta vigente:\n{nombres}"

        terminos = [t.strip() for t in materia.split(";") if t.strip()]
        bloques: list[str] = []
        for termino in terminos:
            materias = udea.buscar_materias(termino)
            if not materias:
                bloques.append(
                    f"'{termino}': no se encontró en la oferta vigente "
                    "(puede no estar ofertada este semestre)."
                )
                continue
            for m in materias:
                bloques.append("\n".join(_formatear_materia(m)))
        return "\n\n".join(bloques)
    except Exception as exc:  # noqa: BLE001 — degradar con elegancia para el modelo
        return f"Error al consultar el portal de la UdeA: {exc}"


def consultar_pensum(nivel: int = 0) -> str:
    """Consulta el PENSUM oficial (plan de estudios) de Ingeniería de Sistemas:
    qué materias corresponden a cada nivel y sus prerrequisitos, donde NIVEL =
    SEMESTRE (nivel 1 = primer semestre, nivel 2 = segundo, etc.).

    Úsala SIEMPRE que necesites saber qué materias le tocan a un estudiante según
    su semestre, antes de revisar cupos y horarios.

    Args:
        nivel: número de semestre (1, 2, 3, ...). Usa 99 para las electivas.
            Si se deja en 0, devuelve un resumen con cuántas materias hay por nivel.

    Returns:
        Texto con las materias del nivel solicitado (nombre, código, créditos,
        tipo y prerrequisitos) o un resumen de los niveles disponibles.
    """
    try:
        if not nivel:
            niveles = pensum.niveles_disponibles()
            partes = []
            for n in niveles:
                etiqueta = "electivas" if n == pensum.NIVEL_ELECTIVAS else f"semestre {n}"
                partes.append(f"nivel {n} ({etiqueta}): {len(pensum.materias_por_nivel(n))} materias")
            return "Niveles disponibles en el pensum:\n" + "\n".join(partes)

        materias = pensum.materias_por_nivel(nivel)
        if not materias:
            return f"No hay materias registradas para el nivel {nivel} en el pensum."

        etiqueta = "electivas" if nivel == pensum.NIVEL_ELECTIVAS else f"semestre {nivel}"
        lineas = [f"Materias del nivel {nivel} ({etiqueta}):"]
        for m in materias:
            req = ""
            if m.requisitos:
                detalle = ", ".join(
                    f"{pensum.nombre_de(r.codigo)} ({r.tipo.lower()})" for r in m.requisitos
                )
                req = f" Requisitos: {detalle}."
            lineas.append(
                f"  - {m.nombre} (código {m.codigo}, {m.creditos} créditos, {m.tipo}).{req}"
            )
        return "\n".join(lineas)
    except Exception as exc:  # noqa: BLE001 — degradar con elegancia para el modelo
        return f"Error al consultar el pensum de la UdeA: {exc}"


def _api_key_valida() -> bool:
    """Comprueba que la GEMINI_API_KEY esté configurada (no es el placeholder)."""
    key = settings.GEMINI_API_KEY or ""
    return bool(key) and not key.startswith("tu_api_key")


def _a_history_gemini(historial: list[dict]) -> list[dict]:
    """Convierte el historial del frontend al formato de Gemini, que exige que
    la conversación empiece con un turno 'user' y alterne los roles."""
    h: list[dict] = []
    for m in historial:
        role = "user" if m.get("rol") == "user" else "model"
        if not h and role != "user":
            continue  # descarta el saludo inicial del asistente
        texto = (m.get("texto") or "").strip()
        if texto:
            h.append({"role": role, "parts": [texto]})
    return h


def _extraer_pasos(chat) -> list[dict]:
    """Lista las herramientas que el agente decidió invocar durante el turno."""
    pasos: list[dict] = []
    for content in chat.history:
        for part in getattr(content, "parts", []):
            fc = getattr(part, "function_call", None)
            if fc and getattr(fc, "name", None):
                args = {}
                try:
                    for k, v in fc.args.items():
                        args[k] = str(v)
                except Exception:  # noqa: BLE001
                    pass
                pasos.append({"herramienta": fc.name, "args": args})
    return pasos


def responder(mensaje: str, historial: list[dict] | None = None) -> tuple[str, list[dict]]:
    """
    Responde al estudiante con el agente Gemini sobre datos en vivo de la UdeA.

    Recibe el historial previo (memoria multi-turno) y devuelve la respuesta y
    la traza de herramientas que el agente invocó. Lanza ValueError si la API
    key no está configurada.
    """
    if not _api_key_valida():
        raise ValueError(
            "La GEMINI_API_KEY no está configurada en el .env. "
            "Agrega tu clave real para habilitar el chat."
        )

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        tools=[consultar_pensum, consultar_horarios_udea],
    )
    chat = model.start_chat(
        history=_a_history_gemini(historial or []),
        enable_automatic_function_calling=True,
    )
    respuesta = chat.send_message(mensaje)
    return respuesta.text, _extraer_pasos(chat)


_PROMPT_SUGERENCIAS = (
    "Con base en la conversación anterior, propón TRES preguntas de seguimiento "
    "breves (máximo 9 palabras), en primera persona, que el estudiante podría "
    "hacerle al asistente de planeación académica. Una por línea, sin numeración "
    "ni viñetas. Si no hay conversación previa, propón preguntas generales de "
    "planeación de semestre."
)


def sugerencias(historial: list[dict]) -> list[str]:
    """Genera hasta 3 preguntas de seguimiento contextuales (sin herramientas)."""
    if not _api_key_valida():
        return []
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
        chat = model.start_chat(history=_a_history_gemini(historial))
        texto = chat.send_message(_PROMPT_SUGERENCIAS).text
        opciones = [linea.strip(" -•*\t").strip() for linea in texto.splitlines()]
        return [o for o in opciones if len(o) > 4][:3]
    except Exception:  # noqa: BLE001 — las sugerencias son un extra opcional
        return []
