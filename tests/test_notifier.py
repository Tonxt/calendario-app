"""Pruebas del notifier. No muestran notificaciones reales: se reemplaza plyer."""

import pytest

from backend import notifier


@pytest.fixture
def llamadas(monkeypatch):
    """Reemplaza la función de plyer por una que solo anota cómo la llamaron."""
    registro = []
    monkeypatch.setattr(
        notifier.notification, "notify", lambda **datos: registro.append(datos)
    )
    return registro


def test_notificar_le_pasa_titulo_y_mensaje_a_plyer(llamadas):
    notifier.notificar("Dentista", "Mañana, 20/10")

    assert len(llamadas) == 1
    assert llamadas[0]["title"] == "Dentista"
    assert llamadas[0]["message"] == "Mañana, 20/10"
    assert llamadas[0]["app_name"] == "Calendario"
    assert llamadas[0]["timeout"] > 0


@pytest.mark.parametrize("titulo", ["", "ñ 日本語 🎉", "a" * 500])
def test_notificar_acepta_titulos_raros(llamadas, titulo):
    notifier.notificar(titulo, "mensaje")

    assert llamadas[0]["title"] == titulo


def test_si_plyer_falla_el_error_no_se_esconde(monkeypatch):
    # El notifier no decide qué hacer con el error: lo deja pasar para que
    # lo maneje quien lo llamó (el scheduler).
    def falla(**datos):
        raise NotImplementedError("este sistema no tiene notificaciones")

    monkeypatch.setattr(notifier.notification, "notify", falla)

    with pytest.raises(NotImplementedError):
        notifier.notificar("x", "y")
