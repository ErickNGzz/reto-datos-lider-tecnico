"""Ruta de la base DuckDB: DUCKDB_PATH, o la copia de pruebas si existe .sandbox, o la base real."""
import os
from pathlib import Path

REAL = "deacero.duckdb"
MARCA = Path(".sandbox")


def ruta():
    if os.environ.get("DUCKDB_PATH"):
        return os.environ["DUCKDB_PATH"]
    if MARCA.exists():
        return MARCA.read_text().strip()
    return REAL
