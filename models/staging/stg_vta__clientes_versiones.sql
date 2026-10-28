{#- Historial: una fila por versión distinta del cliente (insumo del SCD2 de segmento). -#}
with versiones as (
    {{ cdc_versions(source('landing_vta', 'vta_cliente'), ['ClaCliente']) }}
)

select
    cast(ClaCliente as integer) as cla_cliente,
    trim(NomCliente) as nom_cliente,
    {{ clean_code('Segmento') }} as segmento,
    {{ clean_code('ClaEstado') }} as cla_estado,
    cast(_ab_cdc_lsn as bigint) as cdc_lsn,
    cast(_ab_cdc_updated_at as timestamp) as cdc_updated_at_utc,
    cast(_ab_cdc_deleted_at as timestamp) as cdc_deleted_at_utc
from versiones
