{#-
    Frontera humana en dbt: un full-refresh recrea tablas publicadas, así que solo corre
    dentro del job aprobado del environment `production`, el único que recibe la variable.
-#}
{% macro guardia_destructiva() -%}
    {%- if execute and flags.FULL_REFRESH and env_var('APROBACION_DESTRUCTIVA', '') != 'production' -%}
        {{ exceptions.raise_compiler_error(
            "full-refresh bloqueado: recrea tablas publicadas y requiere aprobación humana. "
            ~ "Propónlo con el workflow 'destructive' (gh workflow run destructive.yml), "
            ~ "que espera la aprobación en el environment production."
        ) }}
    {%- endif -%}
{%- endmacro %}
