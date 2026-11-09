"""Die ▶-Knöpfe der Experimente und der Protokollsuche (der Rauchtest in test_app.py lässt Knöpfe mit ▶ aus): Klick, Ergebnis, Verdikt."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app(n=8) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    if n != 8:
        at.sidebar.slider(key="n_slider").set_value(n)
        at.sidebar.slider(key="games_slider").set_value(100)
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return [m.value for m in (list(at.success) + list(at.info) + list(at.warning))]


def test_up_to_n_8_the_experiments_run_without_a_button():
    at = _app()
    assert not [b for b in at.button if b.label.startswith("▶ Leiter") or b.label.startswith("▶ Teilen")]
    assert any("Das erste gemerkte Paar spart" in t for t in _texts(at))
    assert any("ist Aufteilen bis m" in t or "Aufteilen in" in t for t in _texts(at))


def test_above_n_8_the_ladder_waits_for_the_click_and_then_shows_a_verdict():
    at = _app(n=9)
    assert not any("Das erste gemerkte Paar spart" in t for t in _texts(at))
    at.button(key="run_ladder").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("Das erste gemerkte Paar spart" in t for t in _texts(at))
    at.run(timeout=TIMEOUT)                                          # das Ergebnis bleibt im nächsten Lauf stehen
    assert any("Das erste gemerkte Paar spart" in t for t in _texts(at))


def test_above_n_8_the_share_experiment_waits_for_the_click_and_then_shows_a_verdict():
    at = _app(n=9)
    assert not any("ist Aufteilen bis m" in t or "Aufteilen in" in t for t in _texts(at))
    at.button(key="run_share").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("ist Aufteilen bis m" in t or "Aufteilen in" in t for t in _texts(at))


def test_changing_the_settings_hides_the_old_result_again():
    at = _app(n=9)
    at.button(key="run_ladder").click().run(timeout=TIMEOUT)
    at.sidebar.slider(key="p_slider").set_value(3).run(timeout=TIMEOUT)
    assert not any("Das erste gemerkte Paar spart" in t for t in _texts(at))


def test_the_protocol_search_shows_the_result_for_the_first_case():
    at = _app()
    assert not any("bestes gefundenes Protokoll" in t for t in _texts(at))
    at.button(key="run_search").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    found = [t for t in _texts(at) if "bestes gefundenes Protokoll" in t]
    assert found and "n = 6, m = 1, 2 Spieler" in found[0] and "**13,63**" in found[0]
