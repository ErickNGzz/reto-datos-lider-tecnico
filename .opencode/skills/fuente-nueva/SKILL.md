---
name: fuente-nueva
description: Lleva una tabla replicada que nunca se ha modelado, más un requerimiento de negocio, hasta un mart con contrato y tests de negocio siguiendo el estándar. Usar cuando llega una fuente o tabla nueva con un pedido.
---

# De fuente nueva a mart

Trabaja en una rama `feature/<fuente>-<entidad>` y avanza capa por capa; corre `make diagnose` al cerrar cada una.

## 1. Entender
- Lee el requerimiento. Lista las reglas de negocio numeradas, el grano del mart y las columnas pedidas. Lo ambiguo → supuesto explícito.
- Ubica los CSV y perfílalos (skill `perfilar-tabla`). Identifica PK, columnas CDC, códigos, fechas, centinelas, llaves hacia otras tablas.

## 2. Landing
- Nombre de archivo `<prefijo>_<tabla>.csv` → `landing_<prefijo>.<prefijo>_<tabla>`. `make ingest`.
- Declara la tabla en `models/staging/_sources.yml`.

## 3. Staging — `models/staging/stg_<fuente>__<entidad>.sql`
- `{{ cdc_latest(source(...), ['<pk>']) }}` (o `cdc_versions` si necesitas historia para SCD2).
- Renombra a `snake_case` en español; castea estricto; `clean_code` en códigos; `source_timestamp` en fechas; expón `cdc_lsn` y `cdc_updated_at_utc`.
- Tests en `_staging.yml`: PK `unique`+`not_null`, `accepted_values` en códigos, `relationships` hacia dimensiones existentes, `not_before` en fechas.
- Compara conteos con el perfil (llaves − borrados).

## 4. Silver / gold
- Lógica reutilizable en `int_<entidad>__<detalle>` (por ejemplo vigencias SCD2 con `[vigente_desde, vigente_hasta)`).
- Hechos `fct_<proceso>` al grano más fino útil; joins a dimensiones con `left join` + `NO_IDENTIFICADO`. Test de grano con `unique_combination`.

## 5. Mart — `models/marts/<nombre_de_negocio>.sql`
- Castea cada columna al tipo del contrato (texto → varchar, entero → integer, toneladas → decimal(18,3), dinero y % → decimal(18,2)).
- Documéntalo en `_marts.yml` con `data_type` por columna, `not_null` y grano. El contrato queda `enforced` por la carpeta.

## 6. Tests de negocio — `tests/business/assert_<regla>.sql`
- Al menos uno por regla del requerimiento que **pueda fallar**: recalcula el resultado por un camino independiente desde staging y compáralo con el mart (conservación de totales, casos frontera, consistencia entre indicadores).
- Demuéstralo: rompe el modelo a propósito, confirma que el test falla y restaura.

## 7. Cerrar
- `make run` dos veces: conteos idénticos.
- PR con skill `abrir-pr`: reglas → dónde se implementó cada una → qué test la protege; hallazgos de datos y supuestos. Un mart nuevo pasa por el check `aprobacion`.
