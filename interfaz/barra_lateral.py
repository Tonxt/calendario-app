"""Barra lateral: botón Crear, mini calendario y los eventos de hoy."""

from datetime import date

import customtkinter as ctk

from interfaz.estilos import (
    ANCHO_BARRA_LATERAL,
    COLOR_ACENTO,
    COLOR_ACENTO_HOVER,
    COLOR_EVENTO,
    COLOR_EVENTO_HOVER,
    COLOR_FONDO,
    COLOR_SECUNDARIO,
    COLOR_TEXTO,
    COLOR_TEXTO_TENUE,
    boton_principal,
    fuente,
)
from interfaz.formato import (
    DIAS_CORTOS,
    fecha_larga,
    recortar,
    resumen_evento,
    titulo_mes,
)
from interfaz.vista_calendario import semanas_del_mes

FILAS = 6
COLUMNAS = 7
TAMANO_DIA = 28
RADIO_DIA = 7  # con más radio, el botón necesita más ancho y no entran los 7 días


class MiniCalendario(ctk.CTkFrame):
    """Calendario chico para saltar rápido a cualquier día.

    Tiene su propia navegación: se puede mirar otro mes sin mover la grilla
    principal. Los días que tienen eventos se muestran resaltados.
    """

    def __init__(self, master, al_elegir_dia, fechas_con_eventos):
        super().__init__(master, fg_color="transparent")
        self._al_elegir_dia = al_elegir_dia
        # Función que recibe (anio, mes) y devuelve el conjunto de fechas con
        # eventos. La provee la ventana principal, que es la que habla con el
        # backend.
        self._fechas_con_eventos = fechas_con_eventos
        self._anio = date.today().year
        self._mes = date.today().month

        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.grid(row=0, column=0, columnspan=COLUMNAS, sticky="ew", pady=(0, 6))
        encabezado.grid_columnconfigure(0, weight=1)
        self._titulo = ctk.CTkLabel(
            encabezado, text="", anchor="w", font=fuente(13, negrita=True)
        )
        self._titulo.grid(row=0, column=0, sticky="w", padx=(4, 0))
        for columna, (texto, comando) in enumerate(
            (("‹", self._mes_anterior), ("›", self._mes_siguiente)), start=1
        ):
            ctk.CTkButton(
                encabezado,
                text=texto,
                command=comando,
                width=26,
                height=26,
                corner_radius=RADIO_DIA,
                fg_color="transparent",
                hover_color=COLOR_SECUNDARIO,
                text_color=COLOR_TEXTO,
                font=fuente(16),
            ).grid(row=0, column=columna)

        for columna in range(COLUMNAS):
            ctk.CTkLabel(
                self,
                text=DIAS_CORTOS[columna][0],  # solo la inicial: L M M J V S D
                width=TAMANO_DIA,
                height=20,
                text_color=COLOR_TEXTO_TENUE,
                font=fuente(11),
            ).grid(row=1, column=columna, padx=1)

        # Igual que en la grilla principal: los 42 botones se crean una vez y
        # después solo se les cambia el texto y los colores.
        self._botones: list[list[ctk.CTkButton]] = []
        for fila in range(FILAS):
            botones_fila = []
            for columna in range(COLUMNAS):
                boton = ctk.CTkButton(
                    self,
                    text="",
                    width=TAMANO_DIA,
                    height=TAMANO_DIA,
                    corner_radius=RADIO_DIA,
                    fg_color="transparent",
                    hover_color=COLOR_SECUNDARIO,
                    font=fuente(12),
                )
                boton.grid(row=fila + 2, column=columna, padx=1, pady=1)
                botones_fila.append(boton)
            self._botones.append(botones_fila)

    def mostrar(self, anio: int, mes: int) -> None:
        self._anio = anio
        self._mes = mes
        self._dibujar()

    def _mes_anterior(self) -> None:
        if self._mes == 1:
            self.mostrar(self._anio - 1, 12)
        else:
            self.mostrar(self._anio, self._mes - 1)

    def _mes_siguiente(self) -> None:
        if self._mes == 12:
            self.mostrar(self._anio + 1, 1)
        else:
            self.mostrar(self._anio, self._mes + 1)

    def _dibujar(self) -> None:
        self._titulo.configure(text=titulo_mes(self._anio, self._mes))
        hoy = date.today()
        con_eventos = self._fechas_con_eventos(self._anio, self._mes)
        semanas = semanas_del_mes(self._anio, self._mes)

        for fila in range(FILAS):
            for columna in range(COLUMNAS):
                boton = self._botones[fila][columna]
                if fila >= len(semanas):
                    boton.grid_remove()
                    continue
                boton.grid()
                fecha = semanas[fila][columna]
                del_mes = fecha.month == self._mes
                tiene_eventos = del_mes and fecha in con_eventos

                if fecha == hoy:
                    color_fondo, color_hover, color_texto = (
                        COLOR_ACENTO,
                        COLOR_ACENTO_HOVER,
                        "white",
                    )
                elif tiene_eventos:
                    color_fondo, color_hover, color_texto = (
                        COLOR_EVENTO,
                        COLOR_EVENTO_HOVER,
                        COLOR_TEXTO,
                    )
                else:
                    color_fondo, color_hover = "transparent", COLOR_SECUNDARIO
                    color_texto = COLOR_TEXTO if del_mes else COLOR_TEXTO_TENUE

                boton.configure(
                    text=str(fecha.day),
                    fg_color=color_fondo,
                    hover_color=color_hover,
                    text_color=color_texto,
                    font=fuente(12, negrita=fecha == hoy or tiene_eventos),
                    command=lambda f=fecha: self._al_elegir_dia(f),
                )


class BarraLateral(ctk.CTkFrame):
    """Columna izquierda de la ventana principal."""

    def __init__(
        self, master, al_crear, al_elegir_dia, al_elegir_evento, fechas_con_eventos
    ):
        super().__init__(
            master, corner_radius=0, fg_color=COLOR_FONDO, width=ANCHO_BARRA_LATERAL
        )
        self._al_elegir_evento = al_elegir_evento
        self.grid_propagate(False)  # mantiene el ancho fijo
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # la lista de hoy ocupa lo que sobra

        boton_principal(
            self, "+  Crear evento", al_crear, height=42, corner_radius=21
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 20))

        self.mini_calendario = MiniCalendario(self, al_elegir_dia, fechas_con_eventos)
        self.mini_calendario.grid(row=1, column=0, padx=10, pady=(0, 18))

        self._titulo_hoy = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            justify="left",
            text_color=COLOR_TEXTO_TENUE,
            font=fuente(12, negrita=True),
        )
        self._titulo_hoy.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 4))

        self._lista_hoy = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            # La barra de desplazamiento solo se nota al pasar el mouse.
            scrollbar_button_color=COLOR_FONDO,
            scrollbar_button_hover_color=COLOR_SECUNDARIO,
        )
        self._lista_hoy.grid(row=3, column=0, sticky="nsew", padx=(10, 4), pady=(0, 10))
        self._lista_hoy.grid_columnconfigure(0, weight=1)

    def mostrar_eventos_de_hoy(self, eventos: list) -> None:
        hoy = date.today()
        self._titulo_hoy.configure(text=f"HOY · {fecha_larga(hoy)}")

        for widget in self._lista_hoy.winfo_children():
            widget.destroy()

        if not eventos:
            ctk.CTkLabel(
                self._lista_hoy,
                text="No tenés eventos para hoy.",
                anchor="w",
                text_color=COLOR_TEXTO_TENUE,
                font=fuente(12),
            ).grid(row=0, column=0, sticky="ew", padx=8, pady=4)
            return

        for fila, evento in enumerate(eventos):
            ctk.CTkButton(
                self._lista_hoy,
                text=recortar(resumen_evento(evento), 26),
                command=lambda e=evento: self._al_elegir_evento(e),
                height=30,
                corner_radius=8,
                anchor="w",
                font=fuente(12),
                fg_color=COLOR_EVENTO,
                hover_color=COLOR_EVENTO_HOVER,
                text_color=COLOR_TEXTO,
            ).grid(row=fila, column=0, sticky="ew", padx=6, pady=2)
