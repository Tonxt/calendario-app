"""Vista del calendario mensual con los eventos dentro de cada día."""

import calendar
from datetime import date

import customtkinter as ctk

from interfaz.estilos import (
    ALTO_CHIP,
    COLOR_ACENTO,
    COLOR_BORDE,
    COLOR_CELDA,
    COLOR_CELDA_OTRO_MES,
    COLOR_EVENTO,
    COLOR_EVENTO_HOVER,
    COLOR_PANEL,
    COLOR_SECUNDARIO,
    COLOR_TEXTO,
    COLOR_TEXTO_TENUE,
    fuente,
)
from interfaz.formato import DIAS_CORTOS, recortar, resumen_evento

FILAS = 6  # un mes ocupa como máximo 6 semanas
COLUMNAS = 7
ALTO_NUMERO = 36  # espacio que ocupa el número del día dentro de la celda
ANCHO_LETRA = 6.6  # ancho promedio de una letra en los chips, en píxeles
CHIPS_POR_DEFECTO = 2  # mientras todavía no se conoce el tamaño de las celdas
LETRAS_POR_DEFECTO = 14


def semanas_del_mes(anio: int, mes: int) -> list[list[date]]:
    """El mes como lista de semanas; cada semana, 7 fechas de lunes a domingo.

    Incluye los días del mes anterior y del siguiente que completan la
    primera y la última semana.
    """
    return calendar.Calendar(firstweekday=0).monthdatescalendar(anio, mes)


class CeldaDia(ctk.CTkFrame):
    """Un día del calendario: su número y los eventos que entran."""

    def __init__(self, master, al_elegir_dia, al_elegir_evento, al_ver_mas):
        # bg_color es el color de lo que queda "detrás" del widget. Se pone
        # igual al de la celda porque customtkinter dibuja en tamaños pares:
        # sin esto, en las celdas de tamaño impar asomaría una línea de 1 píxel
        # del color del fondo y la grilla se vería despareja.
        super().__init__(
            master, corner_radius=0, fg_color=COLOR_CELDA, bg_color=COLOR_CELDA
        )
        self._al_elegir_dia = al_elegir_dia
        self._al_elegir_evento = al_elegir_evento
        self._al_ver_mas = al_ver_mas
        self.fecha: date | None = None
        self._chips: list[ctk.CTkButton] = []

        # Sin esto, la celda crecería según su contenido y las columnas
        # quedarían de anchos distintos.
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        self._numero = ctk.CTkLabel(
            self, text="", width=26, height=26, corner_radius=8, font=fuente(12)
        )
        self._numero.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 3))

        # Un clic en cualquier parte vacía de la celda elige ese día.
        self.bind("<Button-1>", self._clic)
        self._numero.bind("<Button-1>", self._clic)

    def _clic(self, _evento_tk) -> None:
        if self.fecha is not None:
            self._al_elegir_dia(self.fecha)

    def mostrar(
        self,
        fecha: date,
        del_mes: bool,
        es_hoy: bool,
        eventos: list,
        max_chips: int,
        max_letras: int,
    ) -> None:
        self.fecha = fecha
        color_celda = COLOR_CELDA if del_mes else COLOR_CELDA_OTRO_MES
        self.configure(fg_color=color_celda, bg_color=color_celda)

        if es_hoy:
            self._numero.configure(
                text=str(fecha.day),
                fg_color=COLOR_ACENTO,
                text_color="white",
                font=fuente(12, negrita=True),
            )
        else:
            self._numero.configure(
                text=str(fecha.day),
                fg_color="transparent",
                text_color=COLOR_TEXTO if del_mes else COLOR_TEXTO_TENUE,
                font=fuente(12),
            )

        for chip in self._chips:
            chip.destroy()
        self._chips = []

        # Si no entran todos, el último lugar se usa para el "+N más".
        if len(eventos) > max_chips:
            visibles = eventos[: max(max_chips - 1, 0)]
        else:
            visibles = eventos
        ocultos = len(eventos) - len(visibles)

        for evento in visibles:
            self._agregar_chip(
                texto=recortar(resumen_evento(evento), max_letras),
                color=COLOR_EVENTO if del_mes else COLOR_SECUNDARIO,
                color_hover=COLOR_EVENTO_HOVER,
                color_texto=COLOR_TEXTO,
                comando=lambda e=evento: self._al_elegir_evento(e),
            )
        if ocultos > 0:
            self._agregar_chip(
                texto=f"+{ocultos} más",
                color="transparent",
                color_hover=COLOR_SECUNDARIO,
                color_texto=COLOR_TEXTO_TENUE,
                comando=lambda: self._al_ver_mas(self.fecha),
            )

    def _agregar_chip(self, texto, color, color_hover, color_texto, comando) -> None:
        chip = ctk.CTkButton(
            self,
            text=texto,
            command=comando,
            height=ALTO_CHIP,
            corner_radius=6,
            anchor="w",
            font=fuente(12),
            fg_color=color,
            hover_color=color_hover,
            text_color=color_texto,
        )
        chip.grid(row=len(self._chips) + 1, column=0, sticky="ew", padx=4, pady=1)
        self._chips.append(chip)


class VistaCalendario(ctk.CTkFrame):
    """Grilla del mes: encabezado con los días y una celda por cada fecha.

    No habla con el backend: recibe los eventos ya buscados y avisa a la
    ventana principal, mediante funciones que se le pasan al crearla, cuando
    el usuario hace clic en un día, en un evento o en un "+N más".
    """

    def __init__(self, master, al_elegir_dia, al_elegir_evento, al_ver_mas):
        # El color de fondo se ve en la separación de 1 píxel que queda entre
        # las celdas: así se dibujan las líneas de la grilla.
        super().__init__(master, corner_radius=0, fg_color=COLOR_BORDE)
        self._anio = 0
        self._mes = 0
        self._semanas: list[list[date]] = []
        self._eventos_por_fecha: dict[date, list] = {}
        self._medidas = (CHIPS_POR_DEFECTO, LETRAS_POR_DEFECTO)
        self._redibujo_pendiente = None

        for columna in range(COLUMNAS):
            self.grid_columnconfigure(columna, weight=1, uniform="dia")
            ctk.CTkLabel(
                self,
                text=DIAS_CORTOS[columna],
                height=30,
                corner_radius=0,
                fg_color=COLOR_PANEL,
                bg_color=COLOR_PANEL,
                text_color=COLOR_TEXTO_TENUE,
                font=fuente(11, negrita=True),
            ).grid(row=0, column=columna, sticky="nsew", padx=(0, 1), pady=(1, 1))

        # Las 42 celdas se crean una sola vez y después se reutilizan: al
        # cambiar de mes solo se les cambia el contenido, que es mucho más
        # rápido que destruirlas y crearlas de nuevo.
        self._celdas: list[list[CeldaDia]] = []
        for fila in range(FILAS):
            celdas_fila = []
            for columna in range(COLUMNAS):
                celda = CeldaDia(self, al_elegir_dia, al_elegir_evento, al_ver_mas)
                celda.grid(
                    row=fila + 1,
                    column=columna,
                    sticky="nsew",
                    padx=(0, 1),
                    pady=(0, 1),
                )
                celdas_fila.append(celda)
            self._celdas.append(celdas_fila)

        self.bind("<Configure>", self._al_cambiar_tamano)

    def mostrar(self, anio: int, mes: int, eventos_por_fecha: dict[date, list]) -> None:
        """Dibuja el mes indicado con los eventos de cada fecha."""
        self._anio = anio
        self._mes = mes
        self._eventos_por_fecha = eventos_por_fecha
        self._semanas = semanas_del_mes(anio, mes)

        # Un mes puede ocupar 4, 5 o 6 semanas: las filas que sobran se ocultan.
        for fila in range(FILAS):
            visible = fila < len(self._semanas)
            self.grid_rowconfigure(
                fila + 1,
                weight=1 if visible else 0,
                uniform="semana" if visible else "",
            )
            for celda in self._celdas[fila]:
                if visible:
                    celda.grid()
                else:
                    celda.grid_remove()

        self.update_idletasks()  # para que las celdas ya tengan su tamaño nuevo
        self._medidas = self._calcular_medidas()
        self._dibujar_celdas()

    def _dibujar_celdas(self) -> None:
        hoy = date.today()
        max_chips, max_letras = self._medidas
        for fila, semana in enumerate(self._semanas):
            for columna, fecha in enumerate(semana):
                self._celdas[fila][columna].mostrar(
                    fecha=fecha,
                    del_mes=fecha.month == self._mes,
                    es_hoy=fecha == hoy,
                    eventos=self._eventos_por_fecha.get(fecha, []),
                    max_chips=max_chips,
                    max_letras=max_letras,
                )

    def _calcular_medidas(self) -> tuple[int, int]:
        """Cuántos eventos y cuántas letras entran en una celda ahora mismo."""
        celda = self._celdas[0][0]
        ancho, alto = celda.winfo_width(), celda.winfo_height()
        if ancho <= 1 or alto <= 1:  # la ventana todavía no se dibujó
            return CHIPS_POR_DEFECTO, LETRAS_POR_DEFECTO
        # En pantallas con zoom, Windows informa píxeles reales: se pasan a
        # las mismas unidades que usan los tamaños de los widgets.
        escala = ctk.ScalingTracker.get_widget_scaling(self)
        ancho, alto = ancho / escala, alto / escala
        max_chips = max(1, int((alto - ALTO_NUMERO) // (ALTO_CHIP + 2)))
        max_letras = max(4, int((ancho - 26) // ANCHO_LETRA))
        return max_chips, max_letras

    def _al_cambiar_tamano(self, _evento_tk) -> None:
        # Mientras se arrastra el borde de la ventana llegan decenas de avisos
        # por segundo. Se espera a que el usuario termine para redibujar una
        # sola vez (esta técnica se llama "debounce").
        if self._redibujo_pendiente is not None:
            self.after_cancel(self._redibujo_pendiente)
        self._redibujo_pendiente = self.after(120, self._ajustar_al_tamano)

    def _ajustar_al_tamano(self) -> None:
        self._redibujo_pendiente = None
        medidas = self._calcular_medidas()
        if medidas != self._medidas and self._semanas:
            self._medidas = medidas
            self._dibujar_celdas()
