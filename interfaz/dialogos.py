"""Ventanas emergentes de consulta: el detalle de un evento y la lista de un día."""

from datetime import date

import customtkinter as ctk

from backend import service
from backend.models import Evento
from interfaz.estilos import (
    COLOR_ERROR,
    COLOR_EVENTO,
    COLOR_EVENTO_HOVER,
    COLOR_PANEL,
    COLOR_PELIGRO,
    COLOR_PELIGRO_HOVER,
    COLOR_SECUNDARIO,
    COLOR_TEXTO,
    COLOR_TEXTO_TENUE,
    boton_principal,
    boton_secundario,
    fuente,
)
from interfaz.formato import fecha_larga, hora_a_texto, recortar, resumen_evento
from interfaz.modal import VentanaModal


class DetalleEvento(VentanaModal):
    """Muestra todos los datos de un evento y permite editarlo o eliminarlo."""

    def __init__(self, master, evento: Evento, al_editar, al_eliminar):
        super().__init__(master, "Evento", ancho=420, alto=330)
        self._evento = evento
        self._al_editar = al_editar
        self._al_eliminar = al_eliminar
        self._confirmando = False

        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=24, pady=20)
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_rowconfigure(2, weight=1)  # la descripción ocupa lo que sobra

        ctk.CTkLabel(
            cuerpo,
            text=evento.nombre,
            anchor="w",
            justify="left",
            wraplength=370,
            font=fuente(18, negrita=True),
        ).grid(row=0, column=0, sticky="ew")

        cuando = fecha_larga(evento.fecha)
        if evento.hora is not None:
            cuando += f" · {hora_a_texto(evento.hora)} hs"
        ctk.CTkLabel(
            cuerpo,
            text=cuando,
            anchor="w",
            text_color=COLOR_TEXTO_TENUE,
            font=fuente(13),
        ).grid(row=1, column=0, sticky="ew", pady=(4, 12))

        descripcion = ctk.CTkTextbox(
            cuerpo,
            fg_color="transparent",
            text_color=COLOR_TEXTO if evento.descripcion else COLOR_TEXTO_TENUE,
            font=fuente(13),
            wrap="word",
        )
        descripcion.insert("1.0", evento.descripcion or "Sin descripción.")
        descripcion.configure(state="disabled")  # solo lectura
        descripcion.grid(row=2, column=0, sticky="nsew")

        self._error = ctk.CTkLabel(
            cuerpo, text="", anchor="w", text_color=COLOR_ERROR, font=fuente(12)
        )
        self._error.grid(row=3, column=0, sticky="ew")

        botones = ctk.CTkFrame(cuerpo, fg_color="transparent")
        botones.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        botones.grid_columnconfigure(1, weight=1)  # empuja Editar y Cerrar a la derecha
        self._boton_eliminar = ctk.CTkButton(
            botones,
            text="Eliminar",
            command=self._eliminar,
            width=100,
            fg_color="transparent",
            hover_color=COLOR_PELIGRO_HOVER,
            border_width=1,
            border_color=COLOR_PELIGRO,
            text_color=COLOR_TEXTO,
            font=fuente(13),
        )
        self._boton_eliminar.grid(row=0, column=0)
        boton_secundario(botones, "Editar", self._editar, width=90).grid(
            row=0, column=2, padx=(0, 8)
        )
        boton_principal(botones, "Cerrar", self.destroy, width=90).grid(row=0, column=3)

    def _editar(self) -> None:
        self.destroy()
        self._al_editar(self._evento)

    def _eliminar(self) -> None:
        # Eliminar no se puede deshacer, así que pide un segundo clic: el
        # primero cambia el botón a "¿Confirmar?" y el segundo borra.
        if not self._confirmando:
            self._confirmando = True
            self._boton_eliminar.configure(
                text="¿Confirmar?", fg_color=COLOR_PELIGRO, text_color="white"
            )
            return
        try:
            service.eliminar_evento(self._evento.id)
        except service.ErrorValidacion as error:
            self._error.configure(text=str(error))
            return
        self.destroy()
        self._al_eliminar()


class EventosDelDia(VentanaModal):
    """Lista todos los eventos de un día (se abre desde "+N más")."""

    def __init__(self, master, fecha: date, eventos: list, al_elegir_evento, al_crear):
        super().__init__(master, "Eventos del día", ancho=380, alto=420)
        self._fecha = fecha
        self._al_elegir_evento = al_elegir_evento
        self._al_crear = al_crear

        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=20, pady=20)
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            cuerpo, text=fecha_larga(fecha), anchor="w", font=fuente(16, negrita=True)
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 10))

        lista = ctk.CTkScrollableFrame(
            cuerpo,
            fg_color="transparent",
            scrollbar_button_color=COLOR_PANEL,
            scrollbar_button_hover_color=COLOR_SECUNDARIO,
        )
        lista.grid(row=1, column=0, sticky="nsew")
        lista.grid_columnconfigure(0, weight=1)

        if not eventos:
            ctk.CTkLabel(
                lista,
                text="No hay eventos este día.",
                anchor="w",
                text_color=COLOR_TEXTO_TENUE,
                font=fuente(13),
            ).grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        for fila, evento in enumerate(eventos):
            ctk.CTkButton(
                lista,
                text=recortar(resumen_evento(evento), 40),
                command=lambda e=evento: self._elegir(e),
                height=34,
                corner_radius=8,
                anchor="w",
                font=fuente(13),
                fg_color=COLOR_EVENTO,
                hover_color=COLOR_EVENTO_HOVER,
                text_color=COLOR_TEXTO,
            ).grid(row=fila, column=0, sticky="ew", padx=2, pady=3)

        botones = ctk.CTkFrame(cuerpo, fg_color="transparent")
        botones.grid(row=2, column=0, sticky="e", pady=(12, 0))
        boton_secundario(botones, "Cerrar", self.destroy, width=90).grid(
            row=0, column=0, padx=(0, 8)
        )
        boton_principal(botones, "+  Nuevo evento", self._crear, width=140).grid(
            row=0, column=1
        )

    def _elegir(self, evento: Evento) -> None:
        self.destroy()
        self._al_elegir_evento(evento)

    def _crear(self) -> None:
        self.destroy()
        self._al_crear(self._fecha)
