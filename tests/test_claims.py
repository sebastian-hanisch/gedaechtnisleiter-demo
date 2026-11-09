"""Jede Zahl der Tabelle „Befunde“ in der README wird hier nachgerechnet, über dieselben Funktionen wie in der App.

Exakte Werte (n = 8) sind Markov-Ketten und plattformfest. Zahlen für n = 100 sind Simulationen mit Zufalls-Seed 7 und 800 Partien: Der Zufallsstrom ist reine
Ganzzahl-Arithmetik (SplitMix64), die Messung ist deshalb reproduzierbar; verglichen wird auf die in der README genannte Stelle (Mittel auf die ganze Zahl, Standardfehler
auf die ganze Zahl, Prozentwerte auf ganze Prozent)."""

import math

import pytest

import gdl_evaluation as V
import gdl_exact as E
import gdl_simulation as S

SEED, GAMES = 7, 800


def half_up(x, digits=0):
    f = 10 ** digits
    return math.floor(x * f + 0.5) / f


def cell(kind, m, p=4, r=1, n=100):
    return S.mean_se(S.simulate(kind, n, m, GAMES, SEED, p, r))


def test_claim_edges():
    assert E.expected_none(8) == 36 and half_up(E.expected_full(8), 2) == 13.28
    assert E.expected_none(100) == 5050 and half_up(E.expected_full(100), 2) == 194.81


def test_claim_team_ladder_n8():
    assert [half_up(E.team(8, m), 2) for m in range(1, 8)] == [23.79, 19.09, 16.58, 14.93, 13.90, 13.41, 13.28]
    assert half_up(100 * (36 - E.team(8, 1)) / 36) == 34


def test_claim_team_n100():
    expected = {1: (3182, 14), 5: (1538, 9), 40: (372, 2), 50: (323, 2)}
    for m, (mean, se) in expected.items():
        got = cell("team", m)
        assert (half_up(got[0]), half_up(got[1])) == (mean, se), (m, got)
    assert half_up(100 * (5050 - cell("team", 1)[0]) / 5050) == 37


def test_claim_forgetting():
    for n in range(3, 9):
        for m in range(1, n):
            assert E.team(n, m, "max") == pytest.approx(E.team_optimal(n, m), abs=1e-9), (n, m)
    rows = V.forget_rows(8)
    worst = max(rows, key=lambda r: r["min"] - r["opt"])
    assert worst["m"] == 1 and half_up(worst["min"] - worst["opt"], 1) == 5.2
    assert (half_up(worst["min"], 1), half_up(worst["opt"], 1)) == (29.0, 23.8)


def test_claim_window_n8():
    assert half_up(E.window(8, 1), 2) == 30.72 and half_up(E.team(8, 1), 2) == 23.79
    assert half_up(E.window(8, 7), 2) == 14.11 and half_up(E.team(8, 7), 2) == 13.28
    assert all(E.window(8, m) > E.team(8, m) for m in range(1, 8))                     # 7 von 7 Zellen


def test_claim_window_n100():
    mean1, se1 = cell("window", 1, 4, 1)
    assert (half_up(mean1), half_up(se1)) == (4927, 20)
    mean30, se30 = cell("window", 30, 4, 1)
    assert (half_up(mean30), half_up(se30)) == (1755, 11)
    assert (half_up(cell("team", 30)[0]), half_up(cell("team", 30)[1])) == (468, 3)


def test_claim_split_n8():
    p2 = [E.split(8, m, 2, 1) for m in range(1, 8)]
    assert half_up(p2[0], 2) == 22.56 and half_up(p2[1], 2) == 19.08 and half_up(E.team(8, 2), 2) == 19.09
    assert half_up(p2[2], 2) == 17.93 and half_up(E.team(8, 3), 2) == 16.58
    assert all(abs(x - 17.81) < 0.0051 for x in p2[3:]) and max(p2[3:]) - min(p2[3:]) < 1e-9          # ab m = 4 gleich
    p3 = [E.split(8, m, 3, 1) for m in range(1, 8)]
    assert half_up(p3[0], 2) == 22.11 and all(half_up(x, 2) == 19.69 for x in p3[2:]) and max(p3[2:]) - min(p3[2:]) < 1e-9


def test_claim_split_n100():
    expected = {1: (1919, 10), 5: (821, 5), 30: (440, 3), 40: (440, 3)}
    for m, (mean, se) in expected.items():
        got = cell("split", m)
        assert (half_up(got[0]), half_up(got[1])) == (mean, se), (m, got)
    team = {m: cell("team", m)[0] for m in (1, 5, 30, 40)}
    split = {m: cell("split", m)[0] for m in (1, 5, 30, 40)}
    assert half_up(100 * (1 - split[1] / team[1])) == 40
    assert half_up(100 * (1 - split[5] / team[5])) == 47
    assert half_up(100 * (1 - split[30] / team[30])) == 6
    assert half_up(100 * (split[40] / team[40] - 1)) == 18


def test_claim_split_plateau_is_where_nothing_is_forgotten():
    """n = 100, p = 4, r = 1: jeder Besitzer hat höchstens 25 Nummern; ab m = 25 wird nie vergessen, die Partien sind Zug für Zug dieselben."""
    base = S.simulate("split", 100, 25, 200, SEED, 4, 1)
    for m in (30, 40, 75, 99):
        assert (S.simulate("split", 100, m, 200, SEED, 4, 1) == base).all(), m



def test_claim_window_at_full_memory():
    """README: Fenster bei m = n − 1: n = 8 6 % darüber (exakt), n = 100 35 % darüber (Messung: 263 ± 0,4 gegen 194,8)."""
    assert half_up(100 * (E.window(8, 7) / E.expected_full(8) - 1)) == 6
    mean, se = cell("window", 99, 4, 1)
    assert half_up(mean) == 263 and half_up(se, 1) == 0.4
    assert half_up(100 * (mean / E.expected_full(100) - 1)) == 35


def test_claim_split_saving_at_m30_across_seeds():
    """README: bei m = 30 (n = 100, p = 4) spart Aufteilen 6,1 % mit Zufalls-Seed 7, bei den Zufalls-Seeds 1, 2, 3 und 11 zwischen 4,6 und 6,1 %."""
    savings = []
    for seed in (1, 2, 3, 11, 7):
        team = S.mean_se(S.simulate("team", 100, 30, GAMES, seed, 4, 4))[0]
        split = S.mean_se(S.simulate("split", 100, 30, GAMES, seed, 4, 1))[0]
        savings.append(100 * (1 - split / team))
    assert half_up(savings[-1], 1) == 6.1
    assert half_up(min(savings), 1) == 4.6 and half_up(max(savings), 1) == 6.1


def test_claim_crossing_preset_two_players_equal_three_players_worse():
    """Preset „Kreuzung“: bei 2 Spielern, m = 40: Aufteilen 371 gegen 372 gemeinsam (gleichauf); bei 3 Spielern kostet Aufteilen mehr (414 gegen 372)."""
    team = cell("team", 40, 2, 2)
    split2 = cell("split", 40, 2, 1)
    assert (half_up(split2[0]), half_up(team[0])) == (371, 372)
    assert abs(split2[0] - team[0]) < 2 * (split2[1] ** 2 + team[1] ** 2) ** 0.5
    split3 = cell("split", 40, 3, 1)
    assert half_up(split3[0]) == 414 and split3[0] - team[0] > 2 * (split3[1] ** 2 + team[1] ** 2) ** 0.5
