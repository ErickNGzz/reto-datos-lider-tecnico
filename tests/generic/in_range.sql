{#- Rango de negocio: un KPI fuera de rango es síntoma de un defecto aguas arriba. -#}
{% test in_range(model, column_name, min_value, max_value) %}
select {{ column_name }}
from {{ model }}
where {{ column_name }} < {{ min_value }} or {{ column_name }} > {{ max_value }}
{% endtest %}
