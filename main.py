from backend.models import Evento
from datetime import date

fecha = date(2026, 9, 12)
dentista = Evento("dentista", fecha)


print(vars(dentista))
