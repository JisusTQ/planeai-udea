"""
Paquete de ingesta de datos (scraping + carga semilla).

Estrategia de ingesta "batch" (programada), no en tiempo real:
1. `scraper.py`     intenta extraer la oferta de cursos de las fuentes
                    oficiales de la Facultad de Ingeniería UdeA.
2. Si la extracción falla (las fuentes oficiales bloquean el scraping
   automatizado), se usa `seed_data.json` como dataset semilla de respaldo
   para garantizar que la aplicación SIEMPRE tenga datos con los que operar.
3. `run_scraper.py` orquesta el proceso y persiste los datos en PostgreSQL.

Se implementará tras la aprobación del diseño de la base de datos.
"""
