select anio_mes, segmento_cliente, toneladas_a_tiempo, toneladas_entregadas
from {{ ref('cumplimiento_entrega') }}
where toneladas_a_tiempo > toneladas_entregadas
