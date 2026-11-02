select
    cast(e.anio_mes as varchar) as anio_mes,
    cast(e.cla_planta as integer) as cla_planta,
    cast(e.nom_planta as varchar) as nom_planta,
    cast(e.tipo_incidencia as varchar) as tipo_incidencia,
    cast(count(*) as integer) as num_incidencias,
    cast(count(distinct e.id_viaje) as integer) as viajes_afectados,
    cast(round(sum(e.toneladas_afectadas), 3) as decimal(18, 3)) as toneladas_afectadas
from {{ ref('fct_incidencias') }} e
where e.anio_mes is not null
group by e.anio_mes, e.cla_planta, e.nom_planta, e.tipo_incidencia
