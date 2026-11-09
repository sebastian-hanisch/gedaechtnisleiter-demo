"""Orakel (DEMO-PLAYBOOK §12): die exakten Ketten aus gdl_exact.py gegen einen unabhängigen Rechenweg.

Das Orakel rechnet über AUSGELEGTE PLÄTZE: Für jede der n! Anordnungen wird die Kette über (gesuchte Nummer, wer dran ist, gemerkte PLÄTZE) aufgestellt und gelöst, die
Zufallswahl ist gleichverteilt unter den verdeckten, dem Spieler unbekannten Plätzen; danach wird über alle Anordnungen gemittelt. gdl_exact.py rechnet dagegen über
Nummern ohne Anordnung. Das prüft die Annahme, dass die Nummer an einem unbekannten Platz gleichverteilt unter den unbekannten Nummern ist, und den Code der Ketten
(Übergänge, Vergessen, Besitzer, Fenster) in einer zweiten, anders gebauten Fassung. Außerdem die Ränder n(n+1)/2 und 2n − H(n) in exakter Bruchrechnung."""

import itertools
from fractions import Fraction

import numpy as np
import pytest

import gdl_exact as E


def _layout_value(layout, kind, m, p, r):
    """Erwartete Aufdeckungen für eine feste Anordnung (layout[platz] = Nummer). kind: split (r Besitzer je Karte von p Spielern, r = p heißt alle) oder window."""
    n = len(layout)
    where = {num: pos for pos, num in enumerate(layout)}

    def evict(positions):
        positions = list(positions)
        while len(positions) > m:
            positions.remove(max(positions, key=lambda q: layout[q]))   # höchste Nummer zuerst
        return frozenset(positions)

    def transitions(state):
        k, turn, mem = state
        if k > n:
            return None
        nxt = (turn + 1) % p
        if kind == "split":
            mine = mem[turn]
            known = set(mine)
        else:
            known = {pos for pos in mem if layout[pos] >= k}          # offene Karten gelten als bekannt, belegen aber im Fenster einen Platz
        def after_hit(memory):
            if kind == "split":
                return tuple(frozenset(q for q in x if layout[q] > k) for x in memory)
            return memory
        if where[k] in known:
            return [(1.0, (k + 1, nxt, after_hit(mem) if kind == "split" else ((where[k],) + mem)[:m]))]
        candidates = [pos for pos in range(n) if layout[pos] >= k and pos not in known]       # verdeckt und unbekannt
        out = []
        for pos in candidates:
            number = layout[pos]
            if number == k:
                new = after_hit(mem) if kind == "split" else ((pos,) + mem)[:m]
                out.append((1.0 / len(candidates), (k + 1, nxt, new)))
            elif kind == "split":
                new = list(mem)
                for s in range(r):
                    owner = (number + s) % p
                    new[owner] = evict(set(new[owner]) | {pos})
                out.append((1.0 / len(candidates), (k, nxt, tuple(new))))
            else:
                out.append((1.0 / len(candidates), (k, nxt, ((pos,) + mem)[:m])))
        return out

    start = (1, 0, tuple(frozenset() for _ in range(p)) if kind == "split" else ())
    index, order, edges = {start: 0}, [start], []
    i = 0
    while i < len(order):
        outs = transitions(order[i])
        if outs is not None:
            for prob, nxt_state in outs:
                if nxt_state not in index:
                    index[nxt_state] = len(order)
                    order.append(nxt_state)
                edges.append((i, index[nxt_state], prob))
        i += 1
    size = len(order)
    a = np.eye(size)
    b = np.array([1.0 if s[0] <= n else 0.0 for s in order])
    for src, dst, prob in edges:
        a[src, dst] -= prob
    return float(np.linalg.solve(a, b)[0])


def oracle(n, kind, m, p=2, r=1):
    values = [_layout_value(layout, kind, m, p, r) for layout in itertools.permutations(range(1, n + 1))]
    return sum(values) / len(values)


@pytest.mark.parametrize("n", [2, 3, 4])
def test_team_matches_the_oracle_for_every_m(n):
    for m in range(0, n):
        assert E.expected("team", n, m) == pytest.approx(oracle(n, "split", m, p=2, r=2), abs=1e-9), (n, m)


def test_team_matches_the_oracle_at_n5():
    for m in (1, 2, 3):
        assert E.expected("team", 5, m) == pytest.approx(oracle(5, "split", m, p=2, r=2), abs=1e-9), m


@pytest.mark.parametrize("p,r", [(2, 1), (3, 1), (3, 2)])
def test_split_matches_the_oracle(p, r):
    for n in (3, 4):
        for m in range(1, n):
            assert E.expected("split", n, m, p, r) == pytest.approx(oracle(n, "split", m, p=p, r=r), abs=1e-9), (n, m, p, r)


def test_split_matches_the_oracle_at_n5():
    for m in (1, 2):
        assert E.expected("split", 5, m, 2, 1) == pytest.approx(oracle(5, "split", m, p=2, r=1), abs=1e-9), m


def test_team_and_split_match_the_oracle_at_n6():
    """720 Anordnungen: Team m = 2, aufgeteilt (2 Spieler) m = 1 (das Fenster hat je Anordnung zu viele Zustände für die dichte Lösung)."""
    assert E.expected("team", 6, 2) == pytest.approx(oracle(6, "split", 2, p=2, r=2), abs=1e-9)
    assert E.expected("split", 6, 1, 2, 1) == pytest.approx(oracle(6, "split", 1, p=2, r=1), abs=1e-9)


def test_window_matches_the_oracle():
    for n, ms in ((3, (1, 2)), (4, (1, 2, 3)), (5, (1,))):      # bei n = 5 und m >= 2 hat das Fenster je Anordnung zu viele Zustände für die dichte Lösung (m = 2: Minuten)
        for m in ms:
            assert E.expected("window", n, m) == pytest.approx(oracle(n, "window", m, p=2, r=1), abs=1e-9), (n, m)


def test_team_equals_split_with_every_player_as_owner_in_the_oracle():
    """Im Orakel gibt es keine Abkürzung r = p: alle Spieler als Besitzer rechnen dasselbe wie ein Team mit p = 2 und p = 3 (die Zahl der Spieler ändert dann nichts)."""
    for n, m in ((4, 1), (4, 2), (4, 3)):
        assert oracle(n, "split", m, p=3, r=3) == pytest.approx(oracle(n, "split", m, p=2, r=2), abs=1e-9)


@pytest.mark.parametrize("n", range(1, 9))
def test_the_edges_are_exact_in_fractions(n):
    """kein Gedächtnis: n(n+1)/2; volles Gedächtnis: 2n − H(n) (Bruchrechnung), die Kette trifft beide."""
    h = sum(Fraction(1, i) for i in range(1, n + 1))
    assert Fraction(E.expected_none(n)) == Fraction(n * (n + 1), 2)
    assert E.expected("team", n, 0) == pytest.approx(float(Fraction(n * (n + 1), 2)), abs=1e-9)
    assert E.expected("team", n, max(0, n - 1)) == pytest.approx(float(2 * n - h), abs=1e-9)
    assert E.expected_full(n) == pytest.approx(float(2 * n - h), abs=1e-12)


def test_the_full_memory_value_equals_the_mean_over_all_orders_of_n_plus_misses():
    """Unabhängige Zählung für n = 5: bei fester Suchreihenfolge der Plätze (Permutation der Plätze) sind die Fehlversuche n minus die Zahl der Rekorde der Platzfolge;
    Mittel über alle 120 Reihenfolgen. Das ist dieselbe Zahl wie 2n − H(n)."""
    n = 5
    total = 0
    count = 0
    for order in itertools.permutations(range(n)):          # order[i] = Position der Karte i+1 in der Suchreihenfolge
        records = sum(1 for i in range(n) if all(order[i] > order[j] for j in range(i)))
        total += n + (n - records)
        count += 1
    assert Fraction(total, count) == 2 * n - sum(Fraction(1, i) for i in range(1, n + 1))


def test_forgetting_the_highest_number_first_is_optimal_in_every_gridcell():
    """Wertiteration (das Team wählt, was es vergisst) gegen die feste Regel „höchste zuerst“: gleiche Werte; „kleinste zuerst“ ist nie besser."""
    for n in range(3, 8):
        for m in range(1, n):
            assert E.team(n, m, "max") == pytest.approx(E.team_optimal(n, m), abs=1e-9), (n, m)
            assert E.team(n, m, "min") >= E.team_optimal(n, m) - 1e-9, (n, m)


def test_the_expectation_does_not_depend_on_the_layout():
    """Die Spieler wählen unbekannte Plätze zufällig, die Vergessensregel hängt nur an Nummern: für jede der 24 Anordnungen bei n = 4 ist die erwartete Zahl der Aufdeckungen dieselbe."""
    for kind, m, p, r in (("split", 2, 2, 2), ("split", 1, 2, 1), ("split", 1, 3, 2), ("window", 2, 2, 1)):
        values = [_layout_value(layout, kind, m, p, r) for layout in itertools.permutations(range(1, 5))]
        assert max(values) - min(values) < 1e-9, (kind, m, p, r)
