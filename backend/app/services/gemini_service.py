"""
Servicio de IA AGÉNTICA: integra Google Gemini con datos en vivo de la UdeA.

El backend NO usa base de datos: toda la información proviene en vivo de los
portales oficiales de la UdeA. Gemini funciona como un AGENTE con tool-calling:
se le entregan dos herramientas y el propio modelo DECIDE cuándo invocarlas.

  - `consultar_pensum`        -> materias por nivel/semestre + prerrequisitos.
  - `consultar_horarios_udea` -> grupos, cupos, horarios y profesores en vivo.

La librería google-generativeai ejecuta el bucle agéntico automáticamente
(`enable_automatic_function_calling=True`): envía la pregunta, recibe la
petición de herramienta del modelo, ejecuta la función Python, le devuelve el
resultado y obtiene la respuesta final.
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


def responder(mensaje: str) -> str:
    """
    Genera la respuesta del asistente para el mensaje del estudiante usando un
    agente Gemini con tool-calling automático sobre datos en vivo de la UdeA.

    Lanza ValueError si la API key no está configurada.
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
    # El SDK ejecuta automáticamente el bucle agéntico (llamar la herramienta y
    # devolver su resultado al modelo) hasta producir la respuesta final.
    chat = model.start_chat(enable_automatic_function_calling=True)

    prompt = (
        "Recuerda el flujo: si hay un semestre/nivel, primero `consultar_pensum` "
        "para saber las materias del nivel y sus prerrequisitos, y luego "
        "`consultar_horarios_udea` para sus cupos y horarios reales.\n\n"
        f"PREGUNTA DEL ESTUDIANTE:\n{mensaje}"
    )

    respuesta = chat.send_message(prompt)
    return respuesta.text
