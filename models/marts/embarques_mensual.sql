select
    cast(e.anio_mes as varchar) as anio_mes,
    cast(e.cla_planta as integer) as cla_planta,
    cast(p.nom_planta as varchar) as nom_planta,
    cast(count(*) as integer) as num_viajes,
    cast(round(sum(e.toneladas), 3) as decimal(18, 3)) as toneladas_embarcadas,
    cast(round(sum(e.costo_flete_mxn), 2) as decimal(18, 2)) as costo_flete_mxn,
    cast(round(sum(e.costo_flete_mxn) / nullif(sum(e.toneladas), 0), 2) as decimal(18, 2)) as costo_flete_por_ton
from {{ ref('fct_embarques') }} e
left join {{ ref('stg_opc__plantas') }} p on p.cla_planta = e.cla_planta
group by e.anio_mes, e.cla_planta, p.nom_planta
