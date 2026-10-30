"""Genera una entrega simulada de la réplica (carga_2) a partir de carga_1, con lo que traen las réplicas reales.

Determinista: misma entrada, mismos archivos y mismo hash. Escribe en data/simulada/carga_2/ (fuera de git)
y deja un resumen de lo inyectado en _resumen.json para verificar el efecto en los marts.

Uso:
    python scripts/simular_entrega.py [--salida data/simulada/carga_2]
"""
import argparse
import csv
import json
from pathlib import Path

ORIGEN = Path("data/replica/carga_1")
EXTRAIDO = "2026-08-01T08:00:00.000Z"
CDC = ["_ab_cdc_lsn", "_ab_cdc_updated_at", "_ab_cdc_deleted_at", "_airbyte_extracted_at"]


def leer(nombre):
    with open(ORIGEN / nombre, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def escribir(carpeta, nombre, columnas, filas):
    with open(carpeta / nombre, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)


def vigentes(filas, llave):
    ultimo = {}
    for r in filas:
        k = tuple(r[c] for c in llave)
        if k not in ultimo or int(r["_ab_cdc_lsn"]) > int(ultimo[k]["_ab_cdc_lsn"]):
            ultimo[k] = r
    return {k: r for k, r in ultimo.items() if not r["_ab_cdc_deleted_at"]}


class Lsn:
    def __init__(self, inicio):
        self.n = inicio

    def __call__(self):
        self.n += 17
        return str(self.n)


def main(salida):
    viajes, partidas, entregas, clientes = (leer(f"{t}.csv") for t in ("fle_viaje", "fle_viaje_det", "fle_entrega", "vta_cliente"))
    col_viaje = list(viajes[0].keys()) + ["ClaTransportista"]
    col_det, col_ent, col_cli = list(partidas[0].keys()), list(entregas[0].keys()), list(clientes[0].keys())
    lsn = Lsn(7000300000)
    out_v, out_d, out_e, out_c = [], [], [], []
    resumen = {}

    def version(base, **cambios):
        r = {**base, "ClaTransportista": base.get("ClaTransportista", ""), **cambios}
        r["_ab_cdc_lsn"] = lsn()
        r["_airbyte_extracted_at"] = EXTRAIDO
        return r

    # 1. Viajes nuevos de julio con ciclo PRO -> TRA -> ENT; algunos sin fecha real (centinela) y algunos tarde.
    activos = sorted(int(k[0]) for k, r in vigentes(clientes, ["ClaCliente"]).items())
    nuevos = list(range(251906, 251936))
    for i, idv in enumerate(nuevos):
        dia = 1 + i % 24
        base = {"IdViaje": str(idv), "ClaPlanta": str(1 + i % 4), "FechaCompromiso": f"2026-07-{dia + 2:02d} 00:00:00.000",
                "FechaRealEmbarque": "", "FechaEmbarqueFinal": "", "Estatus": "PRO", "CostoFlete": "",
                "_ab_cdc_updated_at": f"2026-07-{dia:02d}T14:00:00.000Z", "_ab_cdc_deleted_at": "",
                "ClaTransportista": str(10 + i % 5)}
        out_v.append(version(base))
        sale = f"2026-07-{dia:02d} 09:30:00.000"
        real = "1900-01-01 00:00:00.000" if i % 6 == 0 else sale
        out_v.append(version(base, Estatus="TRA", FechaRealEmbarque=real, FechaEmbarqueFinal=sale,
                             CostoFlete=f"{9000 + 137 * i:.2f}", _ab_cdc_updated_at=f"2026-07-{dia:02d}T15:30:00.000Z"))
        if i % 7 == 0:
            cliente = "1903"
        elif i == 26:
            cliente = "9999"
        elif i in (1, 19, 20):
            cliente = str(activos[1])
        else:
            cliente = str(activos[i % len(activos)])
        for p in (1, 2) if i % 3 else (1,):
            out_d.append({"IdViaje": str(idv), "IdPartida": str(p), "ClaCliente": cliente, "ClaArticulo": "130410",
                          "PesoKg": str(12000 + 251 * i + 400 * p), "_ab_cdc_lsn": lsn(),
                          "_ab_cdc_updated_at": f"2026-07-{dia:02d}T14:00:01.000Z", "_ab_cdc_deleted_at": "",
                          "_airbyte_extracted_at": EXTRAIDO})
        if i % 5 != 4:
            entrega_dia = dia + (4 if i % 4 == 0 else 1)
            out_v.append(version(out_v[-1], Estatus="ENT", _ab_cdc_updated_at=f"2026-07-{entrega_dia:02d}T20:00:00.000Z"))
            out_e.append({"IdViaje": str(idv), "FechaEntrega": f"2026-07-{entrega_dia:02d} 13:00:00.000", "_ab_cdc_lsn": lsn(),
                          "_ab_cdc_updated_at": f"2026-07-{entrega_dia:02d}T19:00:00.000Z", "_ab_cdc_deleted_at": "",
                          "_airbyte_extracted_at": EXTRAIDO})
    resumen["viajes_nuevos"] = {"ids": f"{nuevos[0]}-{nuevos[-1]}", "con_cliente_nuevo_1903": sum(1 for i in range(30) if i % 7 == 0),
                                "con_cliente_inexistente_9999": [nuevos[26]],
                                "cliente_que_cambia_segmento": {"antes_del_cambio": [nuevos[1]], "despues_del_cambio": [nuevos[19], nuevos[20]]}, "sin_entregar": [nuevos[i] for i in range(30) if i % 5 == 4],
                                "fecha_real_centinela": [nuevos[i] for i in range(30) if i % 6 == 0]}

    # 2. Versiones tardías: el costo de 10 viajes entregados de enero se corrige en julio (mes ya cerrado).
    vig = vigentes(viajes, ["IdViaje"])
    enero = [r for k, r in sorted(vig.items()) if r["Estatus"].strip().upper() == "ENT" and r["CostoFlete"]
             and (r["FechaRealEmbarque"] or r["FechaEmbarqueFinal"]).startswith("2026-01")
             and not r["FechaRealEmbarque"].startswith("1900")][:10]
    for r in enero:
        out_v.append(version(r, CostoFlete=f"{float(r['CostoFlete']) * 1.10:.2f}", _ab_cdc_updated_at="2026-07-15T16:00:00.000Z"))
    resumen["costo_corregido_enero"] = {"viajes": [r["IdViaje"] for r in enero],
                                        "delta_mxn": round(sum(float(r["CostoFlete"]) * 0.10 for r in enero), 2)}

    # 3. Borrados en el origen: 3 viajes entregados de marzo.
    marzo = [r for k, r in sorted(vig.items()) if r["Estatus"].strip().upper() == "ENT"
             and (r["FechaEmbarqueFinal"] or "").startswith("2026-03")][:3]
    for r in marzo:
        out_v.append(version(r, _ab_cdc_updated_at="2026-07-20T12:00:00.000Z", _ab_cdc_deleted_at="2026-07-20T12:00:00.000Z"))
    resumen["viajes_borrados_marzo"] = [r["IdViaje"] for r in marzo]

    # 4. Reenvío: 20 filas de carga_1 que vuelven a llegar idénticas (mismo LSN), sin la columna nueva.
    for r in viajes[:20]:
        out_v.append({**r, "ClaTransportista": ""})
    resumen["filas_reenviadas_de_carga_1"] = 20

    # 5. Duplicados exactos dentro de la entrega.
    out_v.extend(dict(r) for r in out_v[:5])
    resumen["duplicados_exactos"] = 5

    # 6. Maestro de clientes: cliente nuevo y cambio de segmento a mitad de julio (SCD2).
    out_c.append({"ClaCliente": "1903", "NomCliente": "Aceros del Bajio 1903, SA de CV", "Segmento": "Industrial ",
                  "ClaEstado": "GTO", "_ab_cdc_lsn": "7000299000", "_ab_cdc_updated_at": "2026-06-30T12:00:00.000Z",
                  "_ab_cdc_deleted_at": "", "_airbyte_extracted_at": EXTRAIDO})
    cambia = vigentes(clientes, ["ClaCliente"])[(str(activos[1]),)]
    out_c.append({**cambia, "Segmento": "CONSTRUCTORA", "_ab_cdc_lsn": lsn(), "_ab_cdc_updated_at": "2026-07-15T15:00:00.000Z",
                  "_airbyte_extracted_at": EXTRAIDO})
    resumen["clientes"] = {"nuevo": "1903 (Segmento con espacio y minúsculas)",
                           "cambio_segmento": {"cliente": cambia["ClaCliente"], "de": cambia["Segmento"], "a": "CONSTRUCTORA",
                                               "desde_utc": "2026-07-15T15:00:00Z"}}

    resumen["columna_nueva"] = "fle_viaje.ClaTransportista"
    resumen["filas"] = {"fle_viaje": len(out_v), "fle_viaje_det": len(out_d), "fle_entrega": len(out_e), "vta_cliente": len(out_c)}

    salida.mkdir(parents=True, exist_ok=True)
    escribir(salida, "fle_viaje.csv", col_viaje, out_v)
    escribir(salida, "fle_viaje_det.csv", col_det, out_d)
    escribir(salida, "fle_entrega.csv", col_ent, out_e)
    escribir(salida, "vta_cliente.csv", col_cli, out_c)
    (salida / "_resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    print(json.dumps(resumen, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--salida", default="data/simulada/carga_2")
    main(Path(p.parse_args().salida))
