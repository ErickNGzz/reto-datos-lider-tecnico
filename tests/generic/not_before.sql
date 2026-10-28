{#- Falla si hay fechas anteriores al mínimo: detecta centinelas tipo 1900-01-01 que se colaron. -#}
{% test not_before(model, column_name, min_date) %}
select {{ column_name }}
from {{ model }}
where {{ column_name }} < cast('{{ min_date }}' as timestamp)
{% endtest %}
