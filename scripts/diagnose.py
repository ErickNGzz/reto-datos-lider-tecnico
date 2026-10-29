"""Corre dbt build y resume las fallas en JSON compacto para diagnosticar el mecanismo.

Por cada test o modelo que falla devuelve la regla que protege, la capa, el linaje aguas arriba
y una muestra de filas que rompen la regla; además, los archivos con cambios sin commit.
El log completo de dbt queda en logs/diagnose_dbt.log.

Uso:
    python scripts/diagnose.py [--select <selector>] [--no-run]
"""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

import duckdb

DB = "deacero.duckdb"
TARGET = Path("target")
LOG = Path("logs/diagnose_dbt.log")
LAYERS = ["staging", "silver", "gold", "marts"]
SAMPLE = 5


def run_dbt(select):
    LOG.parent.mkdir(exist_ok=True)
    cmd = [".venv/bin/dbt", "--no-use-colors", "build"] + (["--select", select] if select else [])
    with LOG.open("w") as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env={**os.environ, "DBT_PROFILES_DIR": "."})


def layer(node):
    return next((l for l in node.get("fqn", []) if l in LAYERS), node.get("resource_type"))


def rule(node):
    header = re.search(r"\{#-?(.*?)-?#\}", node.get("raw_code", ""), re.S)
    if header:
        return " ".join(header.group(1).split())[:400]
    meta = node.get("test_metadata") or {}
    if meta:
        kwargs = {k: v for k, v in meta.get("kwargs", {}).items() if k != "model"}
        return f"{meta['name']}({json.dumps(kwargs, ensure_ascii=False)})"
    return node.get("description") or None


def lineage(manifest, unique_id):
    parents, seen, out = manifest["parent_map"], set(), []
    stack = list(parents.get(unique_id, []))
    while stack:
        uid = stack.pop()
        if uid in seen:
            continue
        seen.add(uid)
        if uid.startswith(("model.", "source.")):
            out.append(uid.split(".", 2)[-1])
        stack.extend(parents.get(uid, []))
    return out


def sample(sql):
    try:
        con = duckdb.connect(DB, read_only=True)
        cur = con.execute(f"select * from ({sql}) limit {SAMPLE}")
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        con.close()
        return rows
    except Exception as e:
        return [{"no_disponible": str(e).splitlines()[0]}]


def changed_files():
    out = subprocess.run(["git", "status", "--porcelain", "--", "models", "macros", "tests", "data", "dbt_project.yml"],
                         capture_output=True, text=True).stdout
    return [line[3:] for line in out.splitlines()]


def diagnose():
    results = json.loads((TARGET / "run_results.json").read_text())
    manifest = json.loads((TARGET / "manifest.json").read_text())
    nodes = manifest["nodes"]
    summary, failures, skipped = {}, [], []

    for r in results["results"]:
        status = r["status"]
        summary[status] = summary.get(status, 0) + 1
        node = nodes.get(r["unique_id"], {})
        if status == "skipped":
            skipped.append(node.get("name"))
            continue
        if status not in ("fail", "error"):
            continue
        attached = [nodes[u] for u in node.get("depends_on", {}).get("nodes", []) if u in nodes]
        if node.get("resource_type") == "model" or not attached:
            target = node
        else:
            target = max(attached, key=lambda n: LAYERS.index(layer(n)) if layer(n) in LAYERS else -1)
        item = {
            "tipo": node.get("resource_type"),
            "nombre": node.get("name"),
            "estado": status,
            "capa": layer(target),
            "modelo": target.get("name"),
            "archivo": node.get("original_file_path"),
            "regla": rule(node),
            "linaje": lineage(manifest, r["unique_id"]),
        }
        if status == "fail":
            item["filas_falla"] = r.get("failures")
            item["muestra"] = sample(r["compiled_code"]) if r.get("compiled_code") else []
        else:
            lines = [l for l in (r.get("message") or "").splitlines() if l.strip() and not l.strip().startswith(">")]
            item["mensaje"] = "\n".join(lines[:15])
        failures.append(item)

    return {
        "resumen": summary,
        "fallas": failures,
        "omitidos_por_falla_previa": skipped,
        "cambios_sin_commit": changed_files(),
        "log": str(LOG),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--select")
    p.add_argument("--no-run", action="store_true")
    a = p.parse_args()
    if not a.no_run:
        run_dbt(a.select)
    print(json.dumps(diagnose(), ensure_ascii=False, indent=1, default=str))
