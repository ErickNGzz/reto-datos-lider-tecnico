with entregas as (
    {{ cdc_latest(source('landing_fle', 'fle_entrega'), ['IdViaje']) }}
)

select
    cast(IdViaje as integer) as id_viaje,
    {{ source_timestamp('FechaEntrega') }} as fecha_entrega,
    cast(_ab_cdc_lsn as bigint) as cdc_lsn,
    cast(_ab_cdc_updated_at as timestamp) as cdc_updated_at_utc
from entregas
