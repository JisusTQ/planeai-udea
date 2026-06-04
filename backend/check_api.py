"""
Smoke test de la API de PlaneAI UdeA.

Ejecuta peticiones reales contra la app (con TestClient, en proceso) para
verificar que los endpoints responden y que los datos fluyen desde los portales
EN VIVO de la UdeA (no hay base de datos). Útil como verificación rápida.

Requiere httpx (incluido en requirements.txt).
Uso:  cd backend && python check_api.py
"""
from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    client = TestClient(app)

    print("=== GET /health ===")
    r = client.get("/health")
    print(r.status_code, r.json())

    print("\n=== GET /cursos (catálogo / pensum en vivo) ===")
    cursos = client.get("/cursos").json()
    print(f"{len(cursos)} materias en el pensum")

    print("\n=== GET /cursos?nivel=1 (materias de primer semestre) ===")
    nivel1 = client.get("/cursos", params={"nivel": 1}).json()
    for m in nivel1:
        print(f"   {m['codigo']}  {m['nombre']}  ({m['creditos']} cr, {m['tipo']})")

    print("\n=== GET /cursos/{codigo}/grupos (cupos/horarios EN VIVO) ===")
    # Cálculo Diferencial (código compartido entre pensum y portal de cupos).
    codigo = "2555131"
    grupos = client.get(f"/cursos/{codigo}/grupos").json()
    print(f"código {codigo}: {len(grupos)} grupos")
    for g in grupos[:3]:
        prof = g["profesor"]["nombre"] if g["profesor"] else "N/A"
        print(f"   Grupo {g['numero']}: {g['cupos_disponibles']}/{g['cupos_totales']} cupos | prof {prof}")
        for s in g["horario"]:
            print(f"       {s['dia']} {s['hora_inicio']}-{s['hora_fin']}")

    print("\n=== GET /cursos/en-vivo (oferta completa) ===")
    print(len(client.get("/cursos/en-vivo").json()), "materias ofertadas")

    print("\n=== POST /chat (consulta el agente) ===")
    r = client.post("/chat", json={"mensaje": "Hola, ¿qué puedes hacer?"})
    print(r.status_code, str(r.json())[:200])


if __name__ == "__main__":
    main()
