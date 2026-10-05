"""Ícono en la bandeja del sistema (al lado del reloj).

Permite que la aplicación siga funcionando, y avisando, con la ventana
cerrada. El ícono tiene un menú para volver a abrirla o para salir del todo.
"""

import logging

from PIL import Image, ImageDraw

from interfaz.estilos import COLOR_ACENTO, COLOR_PANEL, COLOR_TEXTO

logger = logging.getLogger(__name__)


def crear_imagen(tamano: int = 64) -> Image.Image:
    """Dibuja el ícono: una hoja de calendario sobre fondo oscuro.

    Se dibuja con código para no depender de un archivo de imagen aparte.
    """
    imagen = Image.new("RGBA", (tamano, tamano), (0, 0, 0, 0))  # transparente
    lapiz = ImageDraw.Draw(imagen)
    u = tamano / 16  # unidad: todo se dibuja sobre una cuadrícula de 16 x 16

    lapiz.rounded_rectangle(
        (0, 0, tamano - 1, tamano - 1), radius=3 * u, fill=COLOR_PANEL
    )
    # La hoja y su franja superior.
    lapiz.rounded_rectangle(
        (3 * u, 4 * u, 13 * u, 13 * u), radius=1.5 * u, fill=COLOR_TEXTO
    )
    lapiz.rounded_rectangle(
        (3 * u, 4 * u, 13 * u, 7 * u), radius=1.5 * u, fill=COLOR_ACENTO
    )
    lapiz.rectangle((3 * u, 6 * u, 13 * u, 7 * u), fill=COLOR_ACENTO)
    # Las dos anillas.
    for x in (5.5 * u, 10.5 * u):
        lapiz.rounded_rectangle(
            (x - 0.6 * u, 2.5 * u, x + 0.6 * u, 5.5 * u),
            radius=0.6 * u,
            fill=COLOR_TEXTO,
        )
    # Los días.
    for fila in range(2):
        for columna in range(3):
            x = (4.6 + columna * 2.6) * u
            y = (8.4 + fila * 2.3) * u
            lapiz.rectangle((x, y, x + 1.5 * u, y + 1.3 * u), fill=COLOR_PANEL)
    return imagen


class IconoBandeja:
    """Envuelve a la librería pystray.

    El ícono vive en su propio hilo: cuando el usuario elige algo del menú,
    las funciones `al_...` se llaman DESDE ESE HILO, no desde el de la
    ventana. Por eso quien las provee tiene que hacerlas seguras para hilos
    (la ventana principal lo resuelve con una cola).
    """

    def __init__(self, al_abrir, al_crear, al_salir):
        self._al_abrir = al_abrir
        self._al_crear = al_crear
        self._al_salir = al_salir
        self._icono = None

    def iniciar(self) -> bool:
        """Muestra el ícono. Devuelve False si este sistema no lo admite.

        Hay sistemas sin bandeja (algunos escritorios de Linux, por ejemplo).
        En ese caso la aplicación sigue funcionando como una ventana común.
        """
        try:
            self._icono = self._crear_icono()
            self._icono.run_detached()  # en su propio hilo, sin frenar la ventana
        except Exception:
            logger.exception("No se pudo mostrar el icono en la bandeja del sistema")
            self._icono = None
            return False
        return True

    def _crear_icono(self):
        # Se importa acá adentro y no arriba del archivo porque, en un sistema
        # sin bandeja, el solo hecho de importar pystray ya lanza un error.
        import pystray

        menu = pystray.Menu(
            # default=True: es lo que se ejecuta al hacer clic sobre el ícono.
            pystray.MenuItem(
                "Abrir calendario", lambda: self._al_abrir(), default=True
            ),
            pystray.MenuItem("Nuevo evento", lambda: self._al_crear()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", lambda: self._al_salir()),
        )
        icono = pystray.Icon("calendario", crear_imagen(), "Calendario", menu)
        # En Linux, pystray tiene un modo antiguo ("xorg") que casi ningún
        # escritorio actual muestra: el ícono se crearía pero no se vería, y
        # la ventana quedaría escondida sin forma de recuperarla. En ese caso
        # es preferible no usar la bandeja.
        if type(icono).__module__.endswith("_xorg"):
            raise RuntimeError("Este escritorio no tiene una bandeja compatible")
        return icono

    def avisar(self, mensaje: str) -> None:
        """Muestra un globo de texto junto al ícono (si el sistema lo admite)."""
        if self._icono is None:
            return
        try:
            self._icono.notify(mensaje, "Calendario")
        except Exception:
            logger.debug("Este sistema no admite avisos desde la bandeja")

    def detener(self) -> None:
        if self._icono is None:
            return
        try:
            self._icono.stop()
        except Exception:
            logger.exception("No se pudo quitar el icono de la bandeja")
        self._icono = None
