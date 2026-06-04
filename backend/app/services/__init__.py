"""
Paquete de servicios (lógica de negocio).

Separa la lógica de los routers (que solo manejan HTTP) de la integración con los
servicios externos. No hay base de datos: todo es en vivo.
- udea_horarios_service.py  : grupos/cupos/horarios EN VIVO del portal UdeA.
- udea_pensum_service.py    : catálogo y prerrequisitos (pensum) del portal Cursum.
- gemini_service.py         : agente Gemini con tool-calling sobre esos servicios.
"""
