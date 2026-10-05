# Punto de entrada: arranca el backend y abre la interfaz.
import sys

from backend.database import crear_tablas
from backend.scheduler import iniciar
from interfaz.app import App

# Con esta opción la aplicación arranca directamente en la bandeja, sin
# mostrar la ventana. Es la que va a usar el arranque automático del sistema.
OPCION_SEGUNDO_PLANO = "--segundo-plano"


def main():
    crear_tablas()
    scheduler = iniciar()  # revisa los avisos ahora y después cada 5 minutos
    app = App()
    hay_bandeja = app.activar_segundo_plano()
    if hay_bandeja and OPCION_SEGUNDO_PLANO in sys.argv:
        app.ocultar(avisar=False)
    app.mainloop()  # el programa queda acá hasta que se elige Salir
    scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
