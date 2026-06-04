"""
Smoke test de la API de PlaneAI UdeA.

Ejecuta peticiones reales contra la app (con TestClient, en proceso) para
verificar rápidamente que los endpoints responden y que los datos fluyen desde
PostgreSQL. Útil como verificación manual antes de una demostración.

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

    print("\n=== GET /cursos (lista) ===")
    cursos = client.get("/cursos").json()
    print(f"{len(cursos)} cursos:")
    for cu in cursos:
        print(f"   {cu['codigo']}  {cu['nombre']}  (sem {cu['semestre']}, {cu['creditos']} cr)")

    print("\n=== GET /cursos?semestre=1 (filtro) ===")
    print(len(client.get("/cursos", params={"semestre": 1}).json()), "cursos de semestre 1")

    print("\n=== GET /cursos/{id} (detalle con prerrequisitos) ===")
    cid = next(x["id"] for x in cursos if x["codigo"] == "2521201")
    d = client.get(f"/cursos/{cid}").json()
    print("curso:", d["nombre"])
    print("   prerrequisitos:", [p["nombre"] for p in d["prerrequisitos"]])
    print("   nº grupos:", len(d["grupos"]))

    print("\n=== GET /cursos/{id}/grupos (cupos y horarios) ===")
    for gr in client.get(f"/cursos/{cid}/grupos").json():
        prof = gr["profesor"]["nombre"] if gr["profesor"] else "N/A"
        print(f"   Grupo {gr['numero']}: {gr['cupos_disponibles']}/{gr['cupos_totales']} cupos | prof {prof}")
        for s in gr["horario"]:
            print(f"       {s['dia']} {s['hora_inicio']}-{s['hora_fin']}")

    print("\n=== GET /cursos/9999 (inexistente -> 404 esperado) ===")
    r = client.get("/cursos/9999")
    print(r.status_code, r.json())

    print("\n=== POST /chat (sin API key -> 503 esperado) ===")
    r = client.post("/chat", json={"mensaje": "Hola"})
    print(r.status_code, r.json())


if __name__ == "__main__":
    main()
