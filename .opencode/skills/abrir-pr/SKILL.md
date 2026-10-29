---
name: abrir-pr
description: Publica un cambio terminado como Pull Request siguiendo el flujo del equipo (rama, commit convencional, descripción con mecanismo y validación). Nunca hace merge.
---

# Abrir un PR

1. Rama desde `main` actualizado: `git switch main && git pull`, luego `git switch -c fix/<desc>` (corrección) o `feature/<desc>` (nuevo). Si ya estás en la rama del cambio, sigue.
2. Valida antes de publicar: `make diagnose` sin fallas. Si cambiaste ingesta, también `make run` dos veces con los mismos conteos.
3. `git add <archivos>` — solo los del cambio; nunca `deacero.duckdb`, `target/`, `logs/`.
4. Commit en inglés, Conventional Commits: `fix: keep unmatched customers as NO_IDENTIFICADO`.
5. `git push -u origin <rama>`.
6. `gh pr create --base main --title "<mismo estilo>" --body "<cuerpo>"` con este cuerpo:

```
## Mecanismo
## Evidencia
## Impacto en el negocio
## Cambio
## Validación
(resumen de make diagnose: N pass, 0 fail; conteos si aplica)
## Supuestos
## ¿Toca contrato de mart o frontera?
Sí/No. Si sí, el check `aprobacion` pedirá aprobación humana antes del merge.
```

7. Responde con la URL del PR y `gh pr checks <n>` cuando terminen. **No hagas merge**: lo decide una persona.
