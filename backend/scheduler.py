import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from backend.notifier import notificar
from backend.repository import (
    buscar_avisos_previos_pendientes,
    buscar_avisos_dia_pendientes,
    marcar_aviso_dia_enviado,
    marcar_aviso_previo_enviado,
)

# El logger anota los errores (por defecto, en la terminal) sin cortar el programa.
logger = logging.getLogger(__name__)


def _avisar(evento, mensaje: str, marcar_enviado) -> None:
    """Muestra la notificación de un evento y, si salió bien, la marca como enviada.

    Si la notificación falla (por ejemplo, porque el sistema no las admite),
    el error se anota y el aviso queda pendiente: la próxima revisión lo
    vuelve a intentar. Así un aviso con problemas no frena a los demás ni
    impide que la aplicación abra.
    """
    try:
        notificar(titulo=evento.nombre, mensaje=mensaje)
    except Exception:
        logger.exception("No se pudo mostrar el aviso del evento %s", evento.id)
        return
    marcar_enviado(evento.id)


def revisar_avisos() -> None:
    hoy = date.today()
    manana = hoy + timedelta(days=1)
    avisos_previos = buscar_avisos_previos_pendientes(manana)
    pendientes_hoy = buscar_avisos_dia_pendientes(hoy)
    for previo in avisos_previos:
        _avisar(
            previo,
            f"Mañana, {previo.fecha.strftime('%d/%m')}",
            marcar_aviso_previo_enviado,
        )
    for pendiente in pendientes_hoy:
        _avisar(
            pendiente,
            f"Hoy, {pendiente.fecha.strftime('%d/%m')}",
            marcar_aviso_dia_enviado,
        )


def iniciar() -> BackgroundScheduler:
    # Si la revisión inicial falla, la aplicación tiene que abrir igual.
    try:
        revisar_avisos()
    except Exception:
        logger.exception("No se pudo hacer la revision inicial de avisos")
    scheduler = BackgroundScheduler()
    scheduler.add_job(revisar_avisos, "interval", minutes=5)
    scheduler.start()
    return scheduler
