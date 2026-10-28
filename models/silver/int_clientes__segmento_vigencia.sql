{#-
    SCD2 del segmento del cliente.
    Regla 6: el cambio aplica desde el día en que se registra, en hora local (H10).
    Si hay varias versiones el mismo día, gana la última (mayor LSN).
    La primera versión conocida aplica también hacia atrás.
    Una versión borrada cierra la vigencia: segmento nulo, que aguas abajo es NO_IDENTIFICADO.
-#}
with versiones as (
    select
        cla_cliente,
        case when cdc_deleted_at_utc is null then segmento end as segmento,
        cast({{ utc_to_local('cdc_updated_at_utc') }} as date) as dia_registro,
        cdc_lsn
    from {{ ref('stg_vta__clientes_versiones') }}
),

por_dia as (
    select *
    from versiones
    qualify row_number() over (partition by cla_cliente, dia_registro order by cdc_lsn desc) = 1
)

select
    cla_cliente,
    segmento,
    case
        when row_number() over (partition by cla_cliente order by dia_registro) = 1 then date '1900-01-01'
        else dia_registro
    end as vigente_desde,
    lead(dia_registro) over (partition by cla_cliente order by dia_registro) as vigente_hasta,
    cdc_lsn
from por_dia
