from datetime import date, time

from backend.database import crear_tablas
from backend.models import Evento
from backend.repository import (
    guardar,
    buscar_avisos_previos_pendientes,
    buscar_avisos_dia_pendientes,
    marcar_aviso_previo_enviado,
    marcar_aviso_dia_enviado,
    eliminar,
)

crear_tablas()

fecha_prueba = date(2026, 12, 15)

# Preparación: crear un evento nuevo para la prueba
evento = guardar(Evento("prueba avisos", fecha_prueba, hora=time(10, 0)))
print(f"Evento creado con id {evento.id}")

# Paso 1: el aviso previo debería estar pendiente
previos = buscar_avisos_previos_pendientes(fecha_prueba)
print("1. Previos pendientes:", [e.nombre for e in previos])

# Paso 2: marcar el aviso previo como enviado
marcar_aviso_previo_enviado(evento.id)
print("2. Aviso previo marcado como enviado")

# Paso 3: el aviso previo ya no debería aparecer
previos = buscar_avisos_previos_pendientes(fecha_prueba)
print("3. Previos pendientes:", [e.nombre for e in previos])

# Paso 4: el aviso del día sigue pendiente
del_dia = buscar_avisos_dia_pendientes(fecha_prueba)
print("4. Del día pendientes:", [e.nombre for e in del_dia])

# Paso 5 (extra): marcar el aviso del día y verificar
marcar_aviso_dia_enviado(evento.id)
del_dia = buscar_avisos_dia_pendientes(fecha_prueba)
print("5. Del día pendientes:", [e.nombre for e in del_dia])

# Limpieza: borrar el evento de prueba
eliminar(evento.id)
print("Evento de prueba eliminado")