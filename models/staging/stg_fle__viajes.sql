with viajes as (
    {{ cdc_latest(source('landing_fle', 'fle_viaje'), ['IdViaje']) }}
)

select
    cast(IdViaje as integer) as id_viaje,
    cast(ClaPlanta as integer) as cla_planta,
    {{ source_timestamp('FechaCompromiso') }} as fecha_compromiso,
    {{ source_timestamp('FechaRealEmbarque') }} as fecha_real_embarque,
    {{ source_timestamp('FechaEmbarqueFinal') }} as fecha_embarque_final,
    {{ clean_code('Estatus') }} as estatus,
    cast(CostoFlete as decimal(18, 2)) as costo_flete_mxn,
    cast(_ab_cdc_lsn as bigint) as cdc_lsn,
    cast(_ab_cdc_updated_at as timestamp) as cdc_updated_at_utc
from viajes
