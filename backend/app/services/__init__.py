"""
Paquete de servicios (lógica de negocio).

Separa la lógica de los routers (que solo manejan HTTP) de las reglas del
dominio y la integración con servicios externos:
- curso_service.py          : consultas del catálogo de cursos (BD).
- udea_horarios_service.py  : grupos/cupos/horarios EN VIVO del portal UdeA.
- udea_pensum_service.py    : materias por nivel (pensum) del portal Cursum.
- gemini_service.py         : agente Gemini con tool-calling sobre los servicios.
"""
