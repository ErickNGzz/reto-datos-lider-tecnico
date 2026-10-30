"""Consulta de solo lectura contra la base: el agente confirma hipótesis sin poder modificar nada.

Uso:
    python scripts/query.py "select ..." [--limit 50]
"""
import argparse
import json

import duckdb

from base import ruta

DB = ruta()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("sql")
    p.add_argument("--limit", type=int, default=50)
    a = p.parse_args()
    con = duckdb.connect(DB, read_only=True)
    cur = con.execute(f"select * from ({a.sql.rstrip().rstrip(';')}) limit {min(a.limit, 50)}")
    cols = [d[0] for d in cur.description]
    print(json.dumps([dict(zip(cols, r)) for r in cur.fetchall()], ensure_ascii=False, indent=1, default=str))
