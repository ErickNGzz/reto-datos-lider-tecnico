PY := .venv/bin/python
DBT := .venv/bin/dbt --no-use-colors
export DBT_PROFILES_DIR := .

SELECT ?= marts

.PHONY: setup ingest build run counts full-refresh reset-landing

setup:
	python3 -m venv .venv
	$(PY) -m pip install -r requirements.txt

ingest:
	$(PY) scripts/ingest.py

build:
	$(DBT) build

run: ingest build counts

# Destructivos: solo corren con la variable que entrega el environment production aprobado.
full-refresh:
	$(DBT) build --full-refresh --select $(SELECT)

reset-landing:
	@test "$$APROBACION_DESTRUCTIVA" = production || { \
		echo "reset-landing bloqueado: borra landing y el manifiesto; requiere aprobación en el environment production."; exit 1; }
	$(PY) -c "import duckdb; c = duckdb.connect('deacero.duckdb'); \
	[c.execute(f'drop schema {s} cascade') for (s,) in c.execute(\"select schema_name from information_schema.schemata where schema_name like 'landing%'\").fetchall()]"
	$(MAKE) run

counts:
	@$(PY) -c "import duckdb; c = duckdb.connect('deacero.duckdb', read_only=True); \
	[print(f'{s}.{t}: {c.execute(f\"select count(*) from {s}.{t}\").fetchone()[0]}') \
	 for s, t in c.execute(\"select table_schema, table_name from information_schema.tables where table_schema not in ('information_schema','pg_catalog') order by 1, 2\").fetchall()]"
