with incidencias as (
    {{ cdc_latest(source('landing_fle', 'fle_incidencia'), ['IdIncidencia']) }}
)

select
    cast(IdIncidencia as integer) as id_incidencia,
    cast(IdViaje as integer) as id_viaje,
    case
        when upper(trim(TipoIncidencia)) in ('RETRASO') then 'RETRASO'
        when upper(trim(TipoIncidencia)) in ('DANO', 'DAÑO') then 'DANO'
        when upper(trim(TipoIncidencia)) in ('FALTANTE') then 'FALTANTE'
        else upper(trim(TipoIncidencia))
    end as tipo_incidencia,
    coalesce({{ source_timestamp('FechaIncidencia') }}, cast(_ab_cdc_updated_at as timestamp)) as fecha_incidencia,
    cast(TonsAfectadas as decimal(18, 3)) as toneladas_afectadas,
    cast(_ab_cdc_lsn as bigint) as cdc_lsn,
    cast(_ab_cdc_updated_at as timestamp) as cdc_updated_at_utc
from incidencias
