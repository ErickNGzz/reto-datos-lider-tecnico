with plantas as (
    {{ cdc_latest(source('landing_opc', 'opc_planta'), ['ClaPlanta']) }}
)

select
    cast(ClaPlanta as integer) as cla_planta,
    trim(NomPlanta) as nom_planta,
    {{ clean_code('ClaPais') }} as cla_pais,
    cast(_ab_cdc_lsn as bigint) as cdc_lsn,
    cast(_ab_cdc_updated_at as timestamp) as cdc_updated_at_utc
from plantas
