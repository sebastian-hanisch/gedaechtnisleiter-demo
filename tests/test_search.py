"""Protokollsuche (gdl_search.py): die einfachen Startregeln gegen die exakten Ketten, die gefundenen Protokolle gegen die Zahlen der README und die untere Schranke."""

import math

import pytest

import gdl_exact as E
import gdl_search as SR


def half_up(x, digits=0):
    f = 10 ** digits
    return math.floor(x * f + 0.5) / f


@pytest.mark.parametrize("n,m,p", [(5, 1, 2), (6, 2, 2), (6, 1, 3)])
def test_the_start_rules_evaluate_to_the_exact_chains(n, m, p):
    """Die Auswertung beliebiger Entscheidungstabellen (gdl_search.evaluate) ist ein zweiter Code zu den Ketten in gdl_exact: gleiche Werte für die einfachen Regeln."""
    assert SR.evaluate(SR.Policy(n, m, p, "team"))[0] == pytest.approx(E.team(n, m), abs=1e-9)
    assert SR.evaluate(SR.Policy(n, m, p, "split"))[0] == pytest.approx(E.split(n, m, p, 1), abs=1e-9)


def test_a_changed_decision_changes_the_value_as_a_hand_computed_case():
    """n = 2, m = 1, zwei Spieler; Spieler 2 merkt nie etwas. Handrechnung: Spieler 1 deckt zuerst auf.
    Die 1 (Wkt. 1/2): Spieler 2 deckt den einzigen verdeckten Platz auf, die 2: 2 Aufdeckungen.
    Die 2 (Wkt. 1/2): nur Spieler 1 merkt sie. Spieler 2 sucht die 1 und kennt nichts, er deckt einen der zwei Plätze auf: die 1 (Wkt. 1/2), dann deckt Spieler 1 die gemerkte 2 auf:
    3 Aufdeckungen; oder die 2 (Wkt. 1/2), ein Fehlversuch: Spieler 1 deckt den Platz der 1 auf (die eigene 2 scheidet aus), Spieler 2 den Platz der 2: 4 Aufdeckungen.
    Zusammen 0,5 · 2 + 0,5 · (0,5 · 3 + 0,5 · 4) = 2,75; mit gemeinsamem Merken sind es 2n − H(2) = 2,5."""
    pol = SR.Policy(2, 1, 2, "team")
    assert SR.evaluate(pol)[0] == pytest.approx(2.5, abs=1e-12)
    for k in (1, 2):
        for flipper in (0, 1):
            pol.store[(1, frozenset(), 2, k, flipper)] = frozenset()                       # Spieler 2 merkt die 2 nie
    assert SR.evaluate(pol)[0] == pytest.approx(0.5 * 2 + 0.5 * (0.5 * 3 + 0.5 * 4), abs=1e-12)


def test_the_found_protocol_for_n6_m1_two_players_matches_the_readme():
    res = SR.search(6, 1, 2)
    assert (half_up(res.best, 2), half_up(res.split, 2), half_up(res.team, 2), half_up(res.lower, 2)) == (13.63, 13.97, 14.21, 11.70)
    assert half_up(100 * (res.split - res.best) / res.split, 1) == 2.5
    assert res.best >= res.lower and res.best <= min(res.team, res.split)
    assert not res.uses_share and len(res.lines) == 12


def test_the_found_protocol_for_n6_m2_two_players_matches_the_readme():
    res = SR.search(6, 2, 2)
    assert (half_up(res.best, 2), half_up(res.team, 2), half_up(res.lower, 2)) == (11.41, 11.70, 9.72)
    assert res.best >= res.lower and res.best <= min(res.team, res.split)
    assert not res.uses_share
