"""Base de las ventanas emergentes (formulario, detalle, lista del día)."""

import customtkinter as ctk

from interfaz.estilos import COLOR_PANEL


class VentanaModal(ctk.CTkToplevel):
    """Ventana emergente centrada sobre la principal.

    Mientras está abierta, la ventana principal no responde a los clics
    (eso es lo que significa "modal"). Se cierra con Escape.
    """

    def __init__(self, master, titulo: str, ancho: int, alto: int):
        super().__init__(master, fg_color=COLOR_PANEL)
        self.title(titulo)
        self.resizable(False, False)
        self.transient(master)  # siempre por encima de la ventana principal
        self._centrar_sobre(master, ancho, alto)
        self.bind("<Escape>", lambda evento: self.destroy())
        # En Windows la ventana tarda un instante en estar lista: si se le da
        # el foco enseguida, lo pierde. Por eso se espera unos milisegundos.
        self.after(150, self._tomar_foco)

    def _centrar_sobre(self, master, ancho: int, alto: int) -> None:
        master.update_idletasks()
        escala = ctk.ScalingTracker.get_window_scaling(self)
        x = master.winfo_rootx() + (master.winfo_width() - int(ancho * escala)) // 2
        y = master.winfo_rooty() + (master.winfo_height() - int(alto * escala)) // 3
        self.geometry(f"{ancho}x{alto}+{max(x, 0)}+{max(y, 0)}")

    def _tomar_foco(self) -> None:
        if not self.winfo_exists():
            return
        self.lift()
        self.focus_force()
        self.grab_set()
        self.al_abrir()

    def al_abrir(self) -> None:
        """Para que cada ventana elija dónde poner el cursor al abrirse."""
