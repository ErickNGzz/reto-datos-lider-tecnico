{#- Grano: la combinación de columnas es única. -#}
{% test unique_combination(model, columns) %}
select {{ columns | join(', ') }}, count(*) as filas
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
