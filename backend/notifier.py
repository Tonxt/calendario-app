from plyer import notification


def notificar(titulo: str, mensaje: str) -> None:
    notification.notify(
        title=titulo, message=mensaje, app_name="Calendario", timeout=10
    )
