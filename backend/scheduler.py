from datetime import date, time, timedelta
from backend.repository import (
    buscar_avisos_previos_pendientes,
    buscar_avisos_dia_pendientes,
    marcar_aviso_dia_enviado,
    marcar_aviso_previo_enviado,
)
from backend.notifier import notificar
from apscheduler.schedulers.background import BackgroundScheduler


def revisar_avisos() -> None:
    hoy = date.today()
    manana = hoy + timedelta(days=1)
    avisos_previos = buscar_avisos_previos_pendientes(manana)
    pendientes_hoy = buscar_avisos_dia_pendientes(hoy)
    for previo in avisos_previos:
        notificar(
            titulo=previo.nombre, mensaje=f"Mañana, {previo.fecha.strftime('%d/%m')}"
        )
        marcar_aviso_previo_enviado(previo.id)
    for pendiente in pendientes_hoy:
        notificar(
            titulo=pendiente.nombre, mensaje=f"Hoy, {pendiente.fecha.strftime('%d/%m')}"
        )
        marcar_aviso_dia_enviado(pendiente.id)


def iniciar() -> BackgroundScheduler:
    revisar_avisos()
    scheduler = BackgroundScheduler()
    scheduler.add_job(revisar_avisos, "interval", minutes=5)
    scheduler.start()
    return scheduler
