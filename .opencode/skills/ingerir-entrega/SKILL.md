---
name: ingerir-entrega
description: Ingiere una entrega nueva de la réplica CDC, reconstruye las capas y reporta qué cambió en los marts. Usar cuando llega una carga o carpeta nueva en data/replica.
---

# Ingerir una entrega

La ingesta es idempotente: reingerir una entrega o correr todo dos veces no duplica nada.

1. **Antes:** `make counts` y guarda los conteos de `staging.*` y `mart_logistica.*`.
2. Verifica con `ls data/replica/*/` que la entrega esté en `data/replica/<entrega>/` con archivos `<prefijo>_<tabla>.csv`. Si está en otra ruta: `python scripts/ingest.py <ruta>`; si no, `make ingest`.
3. Lee el reporte JSON:
   - `cargado` → filas nuevas; revisa `columnas_nuevas` (schema drift).
   - `omitido` → ya se había cargado (mismo hash): normal en reenvíos.
   - `error` → detente y aplica `diagnosticar-falla`. La ingesta hizo rollback de ese archivo.
   - Un archivo cargado con 0 filas o sin las columnas de llave/CDC es sospechoso: perfílalo.
4. `make diagnose`. Si hay fallas → `diagnosticar-falla`.
5. **Después:** `make counts` y reporta deltas.

## Reporte

| Capa | Antes | Después | Δ |
|---|---|---|---|

Más: archivos cargados/omitidos, columnas nuevas, resultado de tests y **qué cambió para el negocio** (meses afectados, toneladas, % a tiempo) consultando los marts con `scripts/query.py`. Si una entrega cambia meses ya cerrados (versiones CDC tardías), dilo explícitamente.
