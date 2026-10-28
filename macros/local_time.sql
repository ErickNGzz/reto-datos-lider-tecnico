{#- Las fechas del origen están en hora de Monterrey, UTC-6 fijo para todas las plantas (H9). -#}
{% macro utc_to_local(column) -%}
    ({{ column }} - interval 6 hour)
{%- endmacro %}
