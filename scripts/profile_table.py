"""Perfila una tabla (CSV de réplica CDC o tabla de la base) y devuelve un resumen JSON compacto.

Uso:
    python scripts/profile_table.py <archivo.csv | esquema.tabla> --pk Col1[,Col2] [--lsn _ab_cdc_lsn]
"""
import argparse
import json
import duckdb

from base import ruta

SENTINELS = ["1900-01-01", "0", "-1", "9999-12-31", "N/A", "NULL", "null", ""]
LOW_CARDINALITY = 30
DB = ruta()


def profile(path, pk, lsn, db=DB):
    con = duckdb.connect()
    if path.endswith(".csv"):
        con.execute(f"create view t as select * from read_csv('{path}', all_varchar=true, header=true)")
    else:
        con.execute(f"attach '{db}' as base (read_only)")
        con.execute(f"create view t as select columns(*)::varchar from base.{path}")
    cols = [r[0] for r in con.execute("describe t").fetchall()]
    keys = ", ".join(pk)
    has_lsn = lsn in cols
    has_del = "_ab_cdc_deleted_at" in cols

    out = {"table": path, "pk": pk}
    if not path.endswith(".csv"):
        out["base"] = db
    out["rows"], out["distinct_rows"], out["keys"] = con.execute(
        f"select count(*), (select count(*) from (select distinct * from t)), count(distinct ({keys})) from t"
    ).fetchone()
    out["exact_duplicate_rows"] = out["rows"] - out["distinct_rows"]
    out["extra_versions"] = out["rows"] - out["keys"]

    if has_lsn:
        out["lsn_out_of_order_vs_updated_at"] = con.execute(f"""
            select count(*) from (
              select _ab_cdc_updated_at u,
                lag(_ab_cdc_updated_at) over (partition by {keys} order by {lsn}::bigint) p
              from t) where u < p""").fetchone()[0]
        latest = f"select * from t qualify row_number() over (partition by {keys} order by {lsn}::bigint desc) = 1"
    else:
        latest = "select * from t"
    if has_del:
        out["deleted_keys"] = con.execute(
            f"select count(*) from ({latest}) where _ab_cdc_deleted_at is not null").fetchone()[0]
    if "_airbyte_extracted_at" in cols:
        out["distinct_extractions"] = con.execute(
            "select count(distinct _airbyte_extracted_at) from t").fetchone()[0]

    out["columns"] = {}
    for c in cols:
        q = f'"{c}"'
        nulls, distinct, numeric, ts, mn, mx = con.execute(f"""
            select count(*) filter (where {q} is null), count(distinct {q}),
              count(try_cast({q} as double)), count(try_cast({q} as timestamp)),
              min({q}), max({q}) from t""").fetchone()
        non_null = out["rows"] - nulls
        info = {"nulls": nulls, "distinct": distinct}
        if non_null and numeric == non_null:
            info["type"] = "numeric"
            info["min"], info["max"], info["non_positive"] = con.execute(
                f"select min({q}::double), max({q}::double), count(*) filter (where {q}::double <= 0) from t").fetchone()
        elif non_null and ts == non_null:
            info["type"] = "timestamp"
            info["min"], info["max"] = mn, mx
            info["midnight_only"] = con.execute(
                f"select count(*) filter (where strftime({q}::timestamp, '%H:%M:%S') <> '00:00:00') = 0 from t where {q} is not null").fetchone()[0]
        else:
            info["type"] = "text"
            info["whitespace_padded"] = con.execute(
                f"select count(*) from t where {q} <> trim({q})").fetchone()[0]
            if distinct <= LOW_CARDINALITY:
                info["values"] = dict(con.execute(
                    f"select {q}, count(*) from t group by 1 order by 2 desc").fetchall())
                info["variants_after_upper_trim"] = con.execute(
                    f"select count(distinct upper(trim({q}))) from t").fetchone()[0]
        sentinels = {}
        for s in SENTINELS:
            n = con.execute(f"select count(*) from t where trim({q}) = ? or (? <> '' and {q} like ? || ' %')", [s, s, s]).fetchone()[0]
            if n:
                sentinels[s] = n
        if sentinels:
            info["sentinels"] = sentinels
        out["columns"][c] = info
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--pk", required=True)
    p.add_argument("--lsn", default="_ab_cdc_lsn")
    a = p.parse_args()
    print(json.dumps(profile(a.path, a.pk.split(","), a.lsn), ensure_ascii=False, indent=1, default=str))
