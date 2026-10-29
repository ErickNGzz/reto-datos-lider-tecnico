---
name: perfilar-tabla
description: Perfila una tabla (CSV de la réplica o tabla de cualquier capa) e interpreta las señales de calidad de datos. Usar cuando piden revisar una tabla o antes de modelar una fuente nueva.
---

# Perfilar una tabla

`make profile TABLE=<archivo.csv | esquema.tabla> PK=<col1,col2>`

Si no conoces la PK, búscala en `docs/diccionario-landing.md` o prueba candidatas: la PK correcta tiene `keys` = filas de la última versión.

## Cómo leer el JSON

| Campo | Señal |
|---|---|
| `exact_duplicate_rows` > 0 | La réplica repite filas idénticas → dedup obligatoria |
| `extra_versions` > 0 | Varias versiones CDC por llave → `cdc_latest` |
| `lsn_out_of_order_vs_updated_at` > 0 | El orden real es el LSN, no la fecha de actualización |
| `deleted_keys` | Llaves cuya última versión está borrada |
| `distinct_extractions` | Cuántas extracciones distintas hay en la entrega |
| columna `type` | Qué tipo castear en staging (numeric / timestamp / text) |
| `midnight_only` = true | La fecha no trae hora: compárala como fecha |
| `whitespace_padded`, `variants_after_upper_trim` < `distinct` | Códigos sucios → `clean_code` |
| `sentinels` | Valores que significan "sin dato" (1900-01-01, 0, -1, N/A) |
| `non_positive` | Pesos/montos ≤ 0: ¿válidos o error de captura? |
| `values` | Dominio real de códigos → `accepted_values` |

## Reporte

Tabla, filas, llaves, y una lista corta de **hallazgos con impacto** ("12% de los estatus vienen en minúsculas: sin limpiar, esos viajes no cuentan como embarcados"). Cada hallazgo con su tratamiento estándar y si hay que escalarlo al dueño del origen.
