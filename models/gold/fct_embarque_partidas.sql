{#-
    Grano: una partida de un viaje embarcado.
    Regla 6: segmento vigente el día del embarque. Regla 7: cliente sin segmento -> NO_IDENTIFICADO.
    Regla 5: cada partida hereda la puntualidad de su viaje.
-#}
select
    p.id_viaje,
    p.id_partida,
    p.cla_cliente,
    p.cla_articulo,
    e.cla_planta,
    e.fecha_embarque,
    e.anio_mes,
    coalesce(s.segmento, 'NO_IDENTIFICADO') as segmento_cliente,
    p.peso_kg / 1000 as toneladas,
    e.tiene_pod,
    e.a_tiempo
from {{ ref('stg_fle__viaje_partidas') }} p
inner join {{ ref('fct_embarques') }} e on e.id_viaje = p.id_viaje
left join {{ ref('int_clientes__segmento_vigencia') }} s
    on s.cla_cliente = p.cla_cliente
    and cast(e.fecha_embarque as date) >= s.vigente_desde
    and (s.vigente_hasta is null or cast(e.fecha_embarque as date) < s.vigente_hasta)
