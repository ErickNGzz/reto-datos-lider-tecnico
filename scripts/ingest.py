"""Ingesta idempotente de entregas de la réplica a la capa landing de DuckDB.

Cada CSV se agrega (append) a landing_<sistema>.<tabla> con su entrega y hash.
Un manifiesto registra el hash por tabla: la misma entrega, o el mismo archivo con
otro nombre de carpeta, no se vuelve a cargar. Si una entrega trae columnas nuevas,
se agregan a la tabla; las que falten llegan como nulo.

Uso:
    python scripts/ingest.py [carpeta_entrega ...]   (por defecto: data/replica/*)
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

DB = "deacero.duckdb"
REPLICA = Path("data/replica")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def target(csv):
    table = csv.stem.lower()
    return f"landing_{table.split('_')[0]}", table


def ingest(folders, db=DB):
    con = duckdb.connect(db)
    con.execute("create schema if not exists landing")
    con.execute("""create table if not exists landing.ingest_manifest (
        entrega varchar, archivo varchar, tabla varchar, sha256 varchar,
        filas bigint, ingested_at timestamp)""")
    report = []
    for folder in folders:
        for csv in sorted(Path(folder).glob("*.csv")):
            schema, table = target(csv)
            fqn = f"{schema}.{table}"
            digest = sha256(csv)
            done = con.execute(
                "select entrega from landing.ingest_manifest where tabla = ? and sha256 = ?", [fqn, digest]
            ).fetchone()
            if done:
                report.append({"archivo": str(csv), "tabla": fqn, "estado": "omitido", "ya_cargado_en": done[0]})
                continue

            con.execute("begin")
            try:
                con.execute(f"create schema if not exists {schema}")
                con.execute(f"create temp table _nuevo as select * from read_csv('{csv}', all_varchar=true, header=true)")
                con.execute(f"""create table if not exists {fqn} as
                    select *, ''::varchar _entrega, ''::varchar _archivo_sha256 from _nuevo limit 0""")
                existing = {r[0] for r in con.execute(f"describe {fqn}").fetchall()}
                new_cols = [r[0] for r in con.execute("describe _nuevo").fetchall() if r[0] not in existing]
                for c in new_cols:
                    con.execute(f'alter table {fqn} add column "{c}" varchar')
                con.execute(f"insert into {fqn} by name select *, ? _entrega, ? _archivo_sha256 from _nuevo",
                            [Path(folder).name, digest])
                rows = con.execute("select count(*) from _nuevo").fetchone()[0]
                con.execute("insert into landing.ingest_manifest values (?, ?, ?, ?, ?, ?)",
                            [Path(folder).name, csv.name, fqn, digest, rows, datetime.now(timezone.utc).replace(tzinfo=None)])
                con.execute("drop table _nuevo")
                con.execute("commit")
            except Exception as e:
                con.execute("rollback")
                report.append({"archivo": str(csv), "tabla": fqn, "estado": "error", "detalle": str(e).splitlines()[0]})
                continue
            item = {"archivo": str(csv), "tabla": fqn, "estado": "cargado", "filas": rows}
            if new_cols:
                item["columnas_nuevas"] = new_cols
            report.append(item)
    con.close()
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("folders", nargs="*")
    a = p.parse_args()
    folders = a.folders or sorted(str(d) for d in REPLICA.iterdir() if d.is_dir())
    print(json.dumps(ingest(folders), ensure_ascii=False, indent=1))
