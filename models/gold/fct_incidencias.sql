{#-
    Grano: una incidencia de viaje vigente.
    Regla 1: solo versión vigente y no borradas (manejado en staging).
    Regla 3: si el viaje no existe, la incidencia no se pierde: planta NO_IDENTIFICADO.
-#}
select
    i.id_incidencia,
    i.id_viaje,
    i.tipo_incidencia,
    i.fecha_incidencia,
    strftime(i.fecha_incidencia, '%Y-%m') as anio_mes,
    coalesce(v.cla_planta, -1) as cla_planta,
    coalesce(p.nom_planta, 'NO_IDENTIFICADO') as nom_planta,
    i.toneladas_afectadas
from {{ ref('stg_fle__incidencias') }} i
left join {{ ref('stg_fle__viajes') }} v on v.id_viaje = i.id_viaje
left join {{ ref('stg_opc__plantas') }} p on p.cla_planta = v.cla_planta
