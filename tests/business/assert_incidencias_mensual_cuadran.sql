{#-
    Regla 1 + 3: el mart de incidencias mensual coincide con el recálculo independiente desde staging.
    Valida que no se pierdan incidencias (viajes no existentes van a NO_IDENTIFICADO) y solo cuenta vigentes no borradas.
-#}
with esperado as (
    select
        strftime(i.fecha_incidencia, '%Y-%m') as anio_mes,
        coalesce(v.cla_planta, -1) as cla_planta,
        i.tipo_incidencia,
        count(*) as num_incidencias,
        count(distinct i.id_viaje) as viajes_afectados,
        sum(i.toneladas_afectadas) as toneladas_afectadas
    from {{ ref('stg_fle__incidencias') }} i
    left join {{ ref('stg_fle__viajes') }} v on v.id_viaje = i.id_viaje
    group by 1, 2, 3
),

publicado as (
    select
        anio_mes,
        cla_planta,
        tipo_incidencia,
        num_incidencias,
        viajes_afectados,
        toneladas_afectadas
    from {{ ref('incidencias_mensual') }}
)

select
    coalesce(e.anio_mes, p.anio_mes) as anio_mes,
    coalesce(e.cla_planta, p.cla_planta) as cla_planta,
    coalesce(e.tipo_incidencia, p.tipo_incidencia) as tipo_incidencia,
    e.num_incidencias as esperado_num,
    p.num_incidencias as publicado_num
from esperado e
full outer join publicado p
    on p.anio_mes = e.anio_mes
    and p.cla_planta = e.cla_planta
    and p.tipo_incidencia = e.tipo_incidencia
where coalesce(e.num_incidencias, 0) <> coalesce(p.num_incidencias, 0)
   or abs(coalesce(e.toneladas_afectadas, 0) - coalesce(p.toneladas_afectadas, 0)) > 0.001
