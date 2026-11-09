"""Einstellungen, Kennzahlen und Kurven (gdl_evaluation.py) und die Grenzen der Regler (gdl_presets.py)."""

import pytest

import gdl_constants as C
import gdl_evaluation as ev
import gdl_exact as E
import gdl_presets as P


def test_settings_clamp_r_and_m_and_name_the_reading():
    s = ev.Settings(n=8, p=3, r=4, m=50)
    assert (s.r_eff, s.m_eff, s.kind) == (3, 7, "team")                                 # r über p: alle merken dasselbe; m über n − 1: n − 1
    assert ev.Settings(n=8, p=3, r=1, m=2).kind == "split" and ev.Settings(n=8, p=3, r=2, m=2).kind == "split"
    assert ev.Settings(n=8, p=2, r=2, m=0).m_eff == 0
    assert ev.Settings().kind == "team" and ev.Settings().m == 3


def test_the_grid_over_m():
    assert ev.curve_ms(8) == [0, 1, 2, 3, 4, 5, 6, 7]
    assert ev.curve_ms(30) == [0, 1, 2, 3, 5, 8, 12, 20, 29]
    assert ev.curve_ms(100) == [0, 1, 2, 3, 5, 8, 12, 20, 30, 40, 50, 75, 99]


def test_curve_cells_use_exact_values_for_small_n_and_the_edges_for_large_n():
    assert ev.curve_cell("split", 8, 2, 2, 1, 100, 7) == (E.split(8, 2, 2, 1), 0.0)
    for kind in ("team", "split", "window"):
        assert ev.curve_cell(kind, 100, 0, 3, 1, 100, 7) == (5050.0, 0.0)               # ohne Gedächtnis sind alle Deutungen gleich
    assert ev.curve_cell("team", 100, 99, 3, 3, 100, 7) == (E.expected_full(100), 0.0)
    mean, se = ev.curve_cell("team", 20, 3, 3, 3, 200, 7)
    assert se > 0 and 80 < mean < 240


def test_analyse_small_n_has_the_exact_value_and_no_team_reference_when_everybody_remembers():
    a = ev.analyse(ev.Settings(n=8, p=2, r=2, m=3, games=2000, seed=7))
    assert a.exact == pytest.approx(16.5816, abs=1e-4) and a.team_mean is None and a.pooled_mean is None
    assert abs(a.mean - a.exact) < 4 * a.se
    assert (a.none, round(a.full, 2)) == (36, 13.28)


def test_analyse_split_has_the_team_reference_and_the_lower_bound():
    a = ev.analyse(ev.Settings(n=8, p=3, r=1, m=2, games=2000, seed=7))
    assert a.exact == pytest.approx(E.split(8, 2, 3, 1), abs=1e-9)
    assert a.team_mean is not None and a.pooled_mean is not None
    assert abs(a.team_mean - E.team(8, 2)) < 4 * a.team_se
    assert abs(a.pooled_mean - E.team(8, 6)) < 4 * a.pooled_se                           # untere Schranke: gemeinsames Gedächtnis mit p·m = 6 Paaren
    assert a.pooled_mean < a.mean                                                         # und sie liegt unter dem aufgeteilten Wert


def test_analyse_has_no_exact_value_above_n_8():
    a = ev.analyse(ev.Settings(n=9, p=2, r=2, m=3, games=100, seed=7))
    assert a.exact is None and a.mean > 0


def test_ladder_and_share_rows_have_the_edges_and_the_series():
    rows = ev.ladder_rows(8, 2, 100, 7)
    assert [r["m"] for r in rows] == list(range(8))
    assert [rows[0][k] for k in ("team", "split", "window")] == [pytest.approx(36.0, abs=1e-9)] * 3
    assert rows[7]["team"] == pytest.approx(E.expected_full(8), abs=1e-9)
    srows = ev.share_rows(8, 3, 100, 7)
    assert set(srows[1]) >= {"m", "team", "r1", "r2", "bound"} and "r2" not in ev.share_rows(8, 2, 100, 7)[1]
    assert srows[7]["bound"] == pytest.approx(E.expected_full(8), abs=1e-9)             # 3·7 über n − 1: volles Gedächtnis
    assert all(r["bound"] <= r["team"] + 1e-9 for r in srows)                            # die Schranke liegt nie über dem Team


def test_forget_rows_are_exact_and_ordered():
    rows = ev.forget_rows(6)
    assert [r["m"] for r in rows] == [1, 2, 3, 4, 5]
    assert all(r["opt"] <= r["min"] + 1e-9 and r["opt"] == pytest.approx(r["max"], abs=1e-9) for r in rows)


# --- Presets und Reglergrenzen -----------------------------------------------------------------------------------------------------------

def test_every_preset_has_help_and_only_known_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) <= set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_and_the_memory_fits_the_cards():
    for name, preset in C.PRESETS.items():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.P_MIN <= preset["p"] <= C.P_MAX and C.R_MIN <= preset["r"] <= C.R_MAX, name
        assert 0 <= preset["m"] <= preset["n"] - 1 and 0 <= preset["seed"] <= C.SEED_MAX, name


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS))
    assert ev.Settings(**C.PRESETS[first]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    assert all(preset["games"] == C.DEFAULT_GAMES for preset in C.PRESETS.values())       # ein Preset stellt auch die Zahl der Partien auf den Standard zurück


def test_the_memory_slider_upper_bound_follows_n():
    assert [P.m_upper(n) for n in (4, 8, 100)] == [3, 7, 99]
    assert P.m_upper(2) == 1                                                              # nie gleich der Untergrenze (Regler mit min == max stürzt ab)
