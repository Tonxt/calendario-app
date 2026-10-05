# Calendario App

Aplicación de escritorio en Python para agendar eventos y recibir recordatorios en la computadora.

## Estructura

```
calendario-app/
├── main.py                  # Punto de entrada
├── backend/                 # Lógica y datos (no sabe nada de la interfaz)
│   ├── models.py            # Entidad Evento
│   ├── database.py          # Conexión y tablas SQLite
│   ├── repository.py        # CRUD de eventos
│   ├── service.py           # Reglas de negocio (puerta de entrada al backend)
│   ├── scheduler.py         # Programación de recordatorios
│   └── notifier.py          # Notificaciones del sistema
├── interfaz/                # Todo lo visual
│   ├── app.py               # Ventana principal: coordina todo y habla con el service
│   ├── barra_lateral.py     # Botón Crear, mini calendario y eventos de hoy
│   ├── bandeja.py           # Ícono en la bandeja del sistema (segundo plano)
│   ├── vista_calendario.py  # Grilla del mes con los eventos de cada día
│   ├── formulario_evento.py # Crear / editar eventos
│   ├── dialogos.py          # Detalle de un evento y lista de un día
│   ├── modal.py             # Base de las ventanas emergentes
│   ├── formato.py           # Conversión entre fechas/horas y textos
│   └── estilos.py           # Colores, medidas y fuentes
├── data/                    # Acá vive la base de datos (ignorada por git)
└── tests/                   # Pruebas automáticas (pytest)
```

## Reglas de arquitectura

1. `interfaz/` solo habla con `backend/service.py` (y usa la clase `Evento` de `models.py`), nunca con el repositorio ni con la base de datos.
2. `backend/` nunca importa nada de `interfaz/`.
3. El flujo es: interfaz → service → repository → database.

## Cómo ejecutarla

```
python -m venv .venv
.venv\Scripts\activate        # en Ubuntu: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

En Ubuntu hace falta además `sudo apt install python3-tk libnotify-bin`.

Al cerrar la ventana, la aplicación queda en la bandeja del sistema y sigue avisando; para cerrarla del todo, clic derecho en el ícono y "Salir". Con `python main.py --segundo-plano` arranca directamente en la bandeja. Si el sistema no tiene bandeja, funciona como una ventana común.

## Pruebas

```
python -m pytest
```

Corre todas las pruebas de `tests/` (backend, formato e interfaz). Usan una base de datos temporal: nunca tocan `data/calendario.db`. Las de la interfaz abren la ventana de verdad durante un minuto, más o menos; para saltearlas: `python -m pytest --ignore=tests/test_interfaz.py`.

## Etapas

- [x] 1. Backend por consola: agregar, listar y borrar eventos en SQLite
- [x] 2. Recordatorios con notificaciones del sistema
- [x] 3. Interfaz gráfica
- [ ] 4. Segundo plano (bandeja del sistema y arranque automático)
- [ ] 5. Extras (eventos repetidos, categorías, exportar a .ics)
