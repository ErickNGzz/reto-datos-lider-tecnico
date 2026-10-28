PY := .venv/bin/python
DBT := .venv/bin/dbt --no-use-colors
export DBT_PROFILES_DIR := .

.PHONY: setup ingest build run counts

setup:
	python3 -m venv .venv
	$(PY) -m pip install -r requirements.txt

ingest:
	$(PY) scripts/ingest.py

build:
	$(DBT) build

run: ingest build counts

counts:
	@$(PY) -c "import duckdb; c = duckdb.connect('deacero.duckdb', read_only=True); \
	[print(f'{s}.{t}: {c.execute(f\"select count(*) from {s}.{t}\").fetchone()[0]}') \
	 for s, t in c.execute(\"select table_schema, table_name from information_schema.tables where table_schema not in ('information_schema','pg_catalog') order by 1, 2\").fetchall()]"
