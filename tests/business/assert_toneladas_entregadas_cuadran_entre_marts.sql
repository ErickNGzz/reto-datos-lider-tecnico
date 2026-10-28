{#-
    Reglas 5, 6 y 7: el reparto por segmento no crea ni pierde toneladas.
    Por mes, las toneladas entregadas del mart de cumplimiento (con NO_IDENTIFICADO) deben ser
    las toneladas de las partidas cuyo viaje tiene POD, calculadas desde staging.
    Falla si el SCD2 de segmento duplica una partida (vigencias traslapadas) o si un cliente
    inexistente se pierde en un join interno.
-#}
with esperado as (
    select
        strftime(coalesce(v.fecha_real_embarque, v.fecha_embarque_final), '%Y-%m') as anio_mes,
        sum(p.peso_kg) / 1000 as toneladas
    from {{ ref('stg_fle__viaje_partidas') }} p
    join {{ ref('stg_fle__viajes') }} v on v.id_viaje = p.id_viaje
    join {{ ref('stg_fle__entregas') }} e on e.id_viaje = p.id_viaje
    where v.estatus in ('TRA', 'ENT')
    group by 1
),

publicado as (
    select anio_mes, sum(toneladas_entregadas) as toneladas
    from {{ ref('cumplimiento_entrega') }}
    group by 1
)

select coalesce(e.anio_mes, p.anio_mes) as anio_mes, e.toneladas as esperado, p.toneladas as publicado
from esperado e
full outer join publicado p on p.anio_mes = e.anio_mes
where abs(coalesce(e.toneladas, 0) - coalesce(p.toneladas, 0)) > 0.01
