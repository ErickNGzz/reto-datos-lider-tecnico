{#-
    Regla 5 con la interpretación documentada (H8): el compromiso es una fecha sin hora,
    así que una entrega el mismo día del compromiso cuenta como a tiempo.
    Falla si alguien compara timestamps y el indicador cae ~17 puntos.
-#}
select id_viaje, fecha_entrega, fecha_compromiso, a_tiempo
from {{ ref('fct_embarques') }}
where tiene_pod
  and cast(fecha_entrega as date) = cast(fecha_compromiso as date)
  and not a_tiempo
