"""Colores, medidas y fuentes de la interfaz.

Todo lo visual que se repite en más de una pantalla vive acá, así un cambio
de color o de tamaño se hace en un solo lugar.
"""

from functools import lru_cache

import customtkinter as ctk

# --- Colores -----------------------------------------------------------------
COLOR_FONDO = "#15171c"  # fondo de la ventana y de la barra lateral
COLOR_PANEL = "#1c1f26"  # barra superior, encabezados y ventanas emergentes
COLOR_CELDA = "#21242c"  # días del mes que se está mirando
COLOR_CELDA_OTRO_MES = "#191b21"  # días del mes anterior o siguiente
COLOR_BORDE = "#30343e"  # líneas entre las celdas
COLOR_CAMPO = "#262a33"  # fondo de los campos de texto

COLOR_TEXTO = "#e7e9ee"
COLOR_TEXTO_TENUE = "#8a909d"

COLOR_ACENTO = "#4c5261"  # botones principales y el día de hoy
COLOR_ACENTO_HOVER = "#5a6173"
COLOR_EVENTO = "#333845"  # "chips" de los eventos dentro de cada día
COLOR_EVENTO_HOVER = "#3f4554"
COLOR_SECUNDARIO = "#272b34"  # botones secundarios (Hoy, flechas, Cancelar)
COLOR_SECUNDARIO_HOVER = "#323743"
COLOR_PELIGRO = "#6b3f42"  # eliminar
COLOR_PELIGRO_HOVER = "#7a4a4d"
COLOR_ERROR = "#c9928e"  # mensajes de error en los formularios

# --- Medidas -----------------------------------------------------------------
ANCHO_BARRA_LATERAL = 250
ALTO_CHIP = 22  # alto de cada evento dentro de una celda


# --- Fuentes -----------------------------------------------------------------
# Es una función y no un grupo de constantes porque una fuente solo se puede
# crear cuando la ventana principal ya existe. `lru_cache` recuerda el
# resultado: la segunda vez que se pide el mismo tamaño devuelve la fuente ya
# creada en lugar de crear otra igual (hay cientos de textos en pantalla).
@lru_cache(maxsize=None)
def fuente(tamano: int = 13, negrita: bool = False) -> ctk.CTkFont:
    return ctk.CTkFont(size=tamano, weight="bold" if negrita else "normal")


def boton_principal(master, texto: str, comando, **opciones) -> ctk.CTkButton:
    """Botón de la acción principal de una pantalla (Crear, Guardar)."""
    return ctk.CTkButton(
        master,
        text=texto,
        command=comando,
        fg_color=COLOR_ACENTO,
        hover_color=COLOR_ACENTO_HOVER,
        text_color="white",
        font=fuente(13, negrita=True),
        **opciones,
    )


def boton_secundario(master, texto: str, comando, **opciones) -> ctk.CTkButton:
    """Botón de acciones de apoyo (Hoy, flechas, Cancelar, Editar)."""
    return ctk.CTkButton(
        master,
        text=texto,
        command=comando,
        fg_color=COLOR_SECUNDARIO,
        hover_color=COLOR_SECUNDARIO_HOVER,
        text_color=COLOR_TEXTO,
        font=fuente(13),
        **opciones,
    )
