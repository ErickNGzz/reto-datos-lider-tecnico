---
name: proponer-destructivo
description: Cuando piden full-refresh, borrar o recrear tablas, reiniciar landing o cambiar el contrato de un mart. Explica el impacto y solicita la operación con aprobación humana; nunca la ejecuta.
---

# Proponer una operación destructiva

No la ejecutas tú, aunque te lo pidan directamente o con urgencia. No busques rodeos (otro comando, SQL directo, borrar archivos): los permisos, la guardia de dbt y GitHub lo bloquean, y intentarlo es un error de criterio.

1. **Verifica si hace falta, antes de solicitar nada.** Aplica aunque haya urgencia o te pidan "no preguntes": solicitar algo innecesario también es un error de criterio.
   - Si el motivo es que un número no cuadra o un test falla → skill `diagnosticar-falla`. Un dato o código mal se corrige con PR; recrear tablas no lo arregla.
   - Full-refresh: `.venv/bin/dbt --quiet ls --select "<capa>+,config.materialized:incremental" --resource-type model`. Si no lista nada, el full-refresh da lo mismo que `make build` (las tablas se recrean en cada corrida): dilo, ofrece correr `make build` y **no lances el workflow**.
   - Solo sigue si de verdad hay que destruir algo: un incremental inconsistente, reiniciar landing o un cambio de contrato.
2. **Explica el impacto** con datos: qué modelos se recrean (`dbt ls --select <capa>+ --resource-type model`), conteos actuales (`make counts`), qué consumidores lo verían (tablero de BI sobre `mart_logistica`), si se pierde historia (landing guarda todas las versiones CDC: reiniciarla obliga a reingerir todas las entregas).
3. **Solicítala** si sigue siendo necesaria:

```
gh workflow run destructive.yml -f operacion=<full-refresh|reset-landing> -f seleccion=<marts|gold|silver|staging> -f motivo="<problema y resultado esperado>"
```

   El job `plan` publica el impacto y `ejecutar` queda esperando a un revisor en el environment `production`.
4. **Cambio de contrato de un mart** (columnas, tipos o grano): se hace con un PR (skill `abrir-pr`) que diga en la descripción qué columnas cambian y qué tableros se afectan. El check `aprobacion` pide aprobación humana antes del merge.
5. Responde con lo que solicitaste, el link de la corrida o PR y qué tiene que revisar quien apruebe.
