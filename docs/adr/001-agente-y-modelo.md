# ADR 001 · Agente y modelo de lenguaje

- **Estado:** aceptada
- **Fecha:** 2026-10-29

## Contexto

El workspace necesita un agente que una persona del equipo use en lenguaje natural para ingerir entregas, diagnosticar fallas, perfilar tablas, modelar fuentes nuevas y abrir PRs. Restricciones: costo cero sin tarjeta, reproducible en un fork con la llave de quien evalúa, y que el estándar no dependa de que el modelo "se acuerde" de las reglas.

## Decisión

- **Agente:** opencode, configurado en el repo (`opencode.json`, `AGENTS.md`, `.opencode/skills/`). Se arranca con `make agent`.
- **Modelo:** `google/gemini-3.5-flash-lite` como modelo principal y como modelo secundario (`small_model`, que opencode usa para tareas internas como titular la sesión). Versión fija, no un alias `latest`.
- **Reparto del trabajo:** el modelo razona; los datos los producen scripts que siempre responden igual y en JSON compacto (`make diagnose`, `make profile`, `scripts/query.py`). Las reglas críticas viven en tests, contratos y la frontera (ADR 003), no en el prompt.
- **Contexto mínimo:** `AGENTS.md` corto y siempre cargado; los procedimientos van en skills que se cargan solo cuando la tarea las pide.
- **Aislamiento:** `make agent` desactiva la carga de contexto y skills globales de la máquina (`OPENCODE_DISABLE_CLAUDE_CODE=1`) y `opencode.json` solo permite las skills del repo. El agente ve el mismo contexto en cualquier máquina.

## Por qué este modelo: el cuello de botella son las peticiones por día

Cada paso del agente (leer una skill, correr un comando, consultar datos) es una petición al modelo. Un diagnóstico completo usa de 15 a 30 peticiones, y cada una pesa de 15K a 19K tokens de entrada. Límites del plan gratuito revisados en la consola del proveedor el 2026-10-29:

| Modelo | Peticiones/min | Tokens/min | Peticiones/día | Resultado |
|---|---|---|---|---|
| Gemini 3.8 Flash | 5 | 250K | 20 | Agotado a mitad del primer diagnóstico |
| Gemini 2.5 Flash | — | — | — | No disponible para cuentas nuevas |
| Gemma 4 31B | 30 | 16K | 14.4K | Una petición del agente no cabe en el límite por minuto |
| Groq gpt-oss-120b | 30 | 8K | 1K | Igual: no cabe una petición |
| **Gemini 3.5 Flash Lite** | **15** | **250K** | **500** | Diagnóstico completo en menos de 2 minutos |

## Alternativas consideradas

- **El Flash más reciente (`gemini-flash-latest`).** Descartada: 20 peticiones al día no alcanzan para una tarea; además el alias cambia de modelo sin que nadie lo decida, y en la prueba coincidió con saturación del proveedor.
- **Groq como proveedor principal.** Descartada: el límite de tokens por minuto es menor que el tamaño de una petición del agente.
- **Modelo local (Ollama).** Descartada: obliga a quien evalúa a descargar varios GB y a tener hardware suficiente.
- **Construir un servidor MCP propio.** Pospuesta: los scripts con permisos explícitos dan las mismas herramientas con menos piezas; queda como mejora.

## Consecuencias

- Un modelo pequeño razona menos. Se compensa con herramientas que ya entregan la regla rota, la muestra de filas y el archivo cambiado, y con una plantilla de respuesta en la skill.
- 500 peticiones al día alcanzan para unas 15 a 25 tareas completas. Para un equipo real se usaría un plan de pago o un modelo con mayor cuota.
- Quien evalúa puede usar otro modelo sin tocar el repo: `opencode -m <proveedor>/<modelo>`, o cambiar `model` en `opencode.json`. La llave se lee de `GEMINI_API_KEY` o `GOOGLE_GENERATIVE_AI_API_KEY`.
- Cuando el proveedor se satura o se agota la cuota, opencode reintenta en silencio y parece que sigue trabajando. Diagnóstico: el log de opencode (`~/.local/share/opencode/log/opencode.log`) y la consola de límites del proveedor.
