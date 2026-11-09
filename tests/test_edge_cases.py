"""Randfälle (DEMO-PLAYBOOK §12): n = 1, n = 2, kein und volles Gedächtnis, Gleichstände von Aufteilen und Team, Reglerränder."""

import numpy as np
import pytest

import gdl_constants as C
import gdl_evaluation as ev
import gdl_exact as E
import gdl_game as G
import gdl_simulation as S


def test_one_card_always_costs_one_flip():
    assert E.expected("team", 1, 0) == 1.0 and E.expected_none(1) == 1 and E.expected_full(1) == 1.0
    assert (S.simulate("team", 1, 0, 50, 3) == 1).all()
    assert G.play("team", 1, 0, 3, 2, 2).length == 1


def test_two_cards_by_hand():
    """n = 2, Handrechnung. Ohne Gedächtnis: zuerst die 1 (Wkt. 1/2): 2 Aufdeckungen; sonst Fehlversuch und dasselbe Spiel von vorn, also E = 1/2 · 2 + 1/2 · (1 + E), E = 3.
    Mit Gedächtnis (Team, m = 1): die 1 zuerst: 2; sonst merken sie die 2, die 1 ist der einzige unbekannte Platz, dann die gemerkte 2: 3; Mittel 2,5 = 2n − H(2).
    Fenster m = 1: nach dem Fehlversuch steht die 2 im Fenster, die nächste Aufdeckung (die 1) schiebt sie hinaus, die 2 ist dann der einzige unbekannte Platz: ebenfalls 3, Mittel 2,5.
    Aufteilen (2 Spieler, r = 1, Besitzer der 2 ist Spieler 1): die 1 zuerst: 2. Sonst weiß nur Spieler 1 von der 2; Spieler 2 sucht die 1 unter beiden Plätzen: die 1 (Wkt. 1/2), dann die
    gemerkte 2 von Spieler 1: 3; oder die 2 (Fehlversuch), dann Spieler 1 die 1, Spieler 2 die 2: 4. Mittel 1/2 · 2 + 1/2 · (1/2 · 3 + 1/2 · 4) = 2,75."""
    assert E.expected("team", 2, 0) == pytest.approx(3.0, abs=1e-12)
    assert E.expected("team", 2, 1) == pytest.approx(2.5, abs=1e-12)
    assert E.expected("window", 2, 1) == pytest.approx(2.5, abs=1e-12)
    assert E.expected("split", 2, 1, 2, 1) == pytest.approx(2.75, abs=1e-12)


def test_split_with_one_owner_and_one_player_is_the_team():
    assert E.expected("split", 6, 2, 1, 1) == E.expected("team", 6, 2)
    assert E.expected("split", 6, 2, 3, 3) == E.expected("team", 6, 2)                    # r = p
    assert E.expected("split", 6, 2, 3, 4) == E.expected("team", 6, 2)                    # r über p wird auf p begrenzt


def test_memory_over_n_minus_one_is_the_same_as_n_minus_one():
    for kind in ("team", "split", "window"):
        assert E.expected(kind, 6, 5, 2, 1) == E.expected(kind, 6, 40, 2, 1)


def test_window_with_zero_memory_is_no_memory():
    assert E.window(6, 0) == E.team(6, 0)                                                 # gleicher Code-Pfad ...
    assert E.window(6, 0) == pytest.approx(21.0, abs=1e-9)                                # ... und n(n+1)/2


def test_the_smallest_app_instance_runs_for_every_player_count_and_owner_count():
    for p in range(C.P_MIN, C.P_MAX + 1):
        for r in range(C.R_MIN, C.R_MAX + 1):
            a = ev.analyse(ev.Settings(n=C.N_MIN, p=p, r=r, m=2, games=C.GAMES_MIN, seed=1))
            assert a.exact is not None and a.mean >= C.N_MIN
            assert a.exact >= E.expected_full(C.N_MIN) - 1e-9 and a.exact <= E.expected_none(C.N_MIN) + 1e-9      # zwischen den Rändern


def test_every_reading_stays_between_the_edges_for_every_m_at_n8():
    lo, hi = E.expected_full(8), E.expected_none(8)
    for m in range(8):
        for value in (E.team(8, m), E.split(8, m, 3, 1), E.split(8, m, 3, 2), E.window(8, m)):
            assert lo - 1e-9 <= value <= hi + 1e-9


def test_games_are_never_shorter_than_n_and_the_slider_edges_run():
    flips = S.simulate("window", C.N_MAX, 99, C.GAMES_MIN, C.SEED_MAX, C.P_MAX, C.R_MAX)
    assert flips.min() >= C.N_MAX and np.isfinite(flips).all()
