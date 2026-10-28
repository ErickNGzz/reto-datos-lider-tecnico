{#-
    Grano: un viaje embarcado.
    Regla 2: solo TRA y ENT. Regla 1: fecha real, si no la final (hora local de planta).
    Regla 5: a tiempo si la fecha de entrega del POD es menor o igual a la fecha compromiso,
    comparando fechas: el compromiso no trae hora (H8).
-#}
with viajes as (
    select * from {{ ref('stg_fle__viajes') }}
    where estatus in ('TRA', 'ENT')
),

partidas as (
    select id_viaje, sum(peso_kg) / 1000 as toneladas, count(*) as num_partidas
    from {{ ref('stg_fle__viaje_partidas') }}
    group by id_viaje
)

select
    v.id_viaje,
    v.cla_planta,
    v.estatus,
    coalesce(v.fecha_real_embarque, v.fecha_embarque_final) as fecha_embarque,
    strftime(coalesce(v.fecha_real_embarque, v.fecha_embarque_final), '%Y-%m') as anio_mes,
    v.fecha_real_embarque is null as fecha_embarque_es_final,
    v.fecha_compromiso,
    v.costo_flete_mxn,
    coalesce(p.toneladas, 0) as toneladas,
    coalesce(p.num_partidas, 0) as num_partidas,
    e.fecha_entrega,
    e.id_viaje is not null as tiene_pod,
    case when e.id_viaje is not null then cast(e.fecha_entrega as date) <= cast(v.fecha_compromiso as date) end as a_tiempo
from viajes v
left join partidas p on p.id_viaje = v.id_viaje
left join {{ ref('stg_fle__entregas') }} e on e.id_viaje = v.id_viaje
