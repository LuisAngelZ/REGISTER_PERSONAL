"""
Script para detectar y limpiar registros con fechas invalidas en la BD.

Uso:
    cd backend
    python scripts/fix_fechas.py

Detecta personal con fecha_inicio cuyo año < 2000 (ej: año 2, 20, 202)
y los lista. Ofrece limpiar esos campos para que el admin los corrija
manualmente desde la UI.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db import SessionLocal
from sqlalchemy import text


def main():
    db = SessionLocal()
    try:
        rows = db.execute(text(
            "SELECT id, nombre, apellido, fecha_inicio, fecha_fin FROM personal"
        )).fetchall()

        invalidos = [r for r in rows if r.fecha_inicio and int(r.fecha_inicio[:4]) < 2000]

        if not invalidos:
            print("OK — No se encontraron fechas invalidas.")
            return

        print(f"\nSe encontraron {len(invalidos)} registros con fecha_inicio invalida:\n")
        print(f"  {'ID':<5} {'Nombre':<25} {'fecha_inicio':<15} {'fecha_fin'}")
        print("  " + "-" * 65)
        for r in invalidos:
            nombre = f"{r.nombre} {r.apellido}"[:24]
            print(f"  {r.id:<5} {nombre:<25} {str(r.fecha_inicio):<15} {r.fecha_fin}")

        print()
        resp = input("¿Limpiar fecha_inicio y fecha_fin de estos registros? (s/n): ").strip().lower()
        if resp == 's':
            ids = [r.id for r in invalidos]
            placeholders = ",".join(str(i) for i in ids)
            db.execute(text(
                f"UPDATE personal SET fecha_inicio = NULL, fecha_fin = NULL WHERE id IN ({placeholders})"
            ))
            db.commit()
            print(f"\nListo — se limpiaron {len(invalidos)} registros.")
            print("Editalos desde la seccion 'Editar' en la app para ingresar la fecha correcta.")
        else:
            print("Operacion cancelada.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
