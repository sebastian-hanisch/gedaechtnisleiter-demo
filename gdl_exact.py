"""Exakte Erwartung der Aufdeckungen für kleine Karten- und Spielerzahlen (Markov-Ketten über Nummern).

Die Anordnung der Karten ist zufällig. Wer die gesuchte Nummer k nicht kennt, deckt einen zufälligen Platz auf, der nach seinem Wissen nicht k
enthält; bei zufälliger Anordnung ist die dort liegende Nummer gleichverteilt unter den noch nicht bekannten Nummern k..n. Deshalb genügt der Zustand
(k, Gedächtnis aller Spieler, wer dran ist). Jede Aufdeckung kostet 1; der Endzustand k > n kostet 0 und hat keine Übergänge.

Deutungen: `team` (alle merken dieselben m Paare), `split` (jede Karte merken r der p Spieler, Besitzer von Nummer j sind (j + s) mod p für s < r,
Spieler reihum), `window` (das Team merkt die letzten m Aufdeckungen). Vergessen: höchste Nummer zuerst (`forget="max"`), kleinste zuerst
(`"min"`) oder das optimale (`team_optimal`, Wertiteration)."""

from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.sparse import csr_matrix, identity
from scipy.sparse.linalg import spsolve

STATE_CAP = 120000


class TooLarge(Exception):
    """Die Kette hat mehr Zustände als STATE_CAP."""


def harmonic(n: int) -> float:
    return sum(1.0 / i for i in range(1, n + 1))


def expected_none(n: int) -> int:
    """Kein Gedächtnis: n(n+1)/2 Aufdeckungen im Mittel (für k ist jede der n−k+1 noch verdeckten Nummern gleich wahrscheinlich)."""
    return n * (n + 1) // 2


def expected_full(n: int) -> float:
    """Volles Gedächtnis: 2n − H(n); n gezielte Aufdeckungen, dazu je ein Fehlversuch für jede Karte, die nicht beim Suchen getroffen wird (Rekorde: H(n))."""
    return 2 * n - harmonic(n)


def _evict(pool, m: int, forget: str) -> frozenset:
    pool = set(pool)
    while len(pool) > m:
        pool.discard(max(pool) if forget == "max" else min(pool))
    return frozenset(pool)


def _solve(start, transitions) -> float:
    """transitions(s) -> None (Endzustand) oder Liste (Wahrscheinlichkeit, Folgezustand). Gesucht: erwartete Zahl der Schritte bis zum Ende."""
    idx = {start: 0}
    order = [start]
    rows, cols, vals, cost = [], [], [], []
    i = 0
    while i < len(order):
        outs = transitions(order[i])
        if outs is None:
            cost.append(0.0)
        else:
            cost.append(1.0)
            for prob, t in outs:
                if t not in idx:
                    idx[t] = len(order)
                    order.append(t)
                    if len(order) > STATE_CAP:
                        raise TooLarge(f"mehr als {STATE_CAP} Zustände")
                rows.append(i)
                cols.append(idx[t])
                vals.append(prob)
        i += 1
    size = len(order)
    p_matrix = csr_matrix((vals, (rows, cols)), shape=(size, size))
    expected = spsolve((identity(size, format="csc") - p_matrix).tocsc(), np.array(cost))
    return float(expected[0])


def team(n: int, m: int, forget: str = "max") -> float:
    def trans(s):
        k, mem = s
        if k > n:
            return None
        if k in mem:
            return [(1.0, (k + 1, mem - {k}))]
        unknown = [j for j in range(k, n + 1) if j not in mem]
        out = []
        for j in unknown:
            if j == k:
                out.append((1.0 / len(unknown), (k + 1, mem)))
            else:
                out.append((1.0 / len(unknown), (k, _evict(set(mem) | {j}, m, forget))))
        return out

    return _solve((1, frozenset()), trans)


def team_optimal(n: int, m: int) -> float:
    """Wie `team`, aber das Team wählt beim Überlauf, welche Nummer es vergisst (Wertiteration je Stufe k, von n abwärts)."""
    value: dict = {}
    for k in range(n, 0, -1):
        nums = list(range(k, n + 1))
        states = [frozenset(c) for r in range(0, min(m, len(nums)) + 1) for c in combinations(nums, r)]
        for mem in states:
            value[(k, mem)] = 0.0
        nxt = (lambda mem: value[(k + 1, mem)]) if k < n else (lambda mem: 0.0)
        for _ in range(100000):
            delta = 0.0
            for mem in states:
                if k in mem:
                    v = 1.0 + nxt(mem - {k})
                else:
                    unknown = [j for j in range(k, n + 1) if j not in mem]
                    total = 0.0
                    for j in unknown:
                        if j == k:
                            total += nxt(mem)
                        else:
                            pool = set(mem) | {j}
                            if len(pool) > m:
                                total += min(value[(k, frozenset(pool - {x}))] for x in pool)
                            else:
                                total += value[(k, frozenset(pool))]
                    v = 1.0 + total / len(unknown)
                delta = max(delta, abs(v - value[(k, mem)]))
                value[(k, mem)] = v
            if delta < 1e-13:
                break
    return value[(1, frozenset())]


def split(n: int, m: int, p: int, r: int) -> float:
    r = min(r, p)
    if r >= p:
        return team(n, m)

    def trans(s):
        k, turn, mems = s
        if k > n:
            return None
        mine = mems[turn]
        next_turn = (turn + 1) % p
        if k in mine:
            return [(1.0, (k + 1, next_turn, tuple(x - {k} for x in mems)))]
        unknown = [j for j in range(k, n + 1) if j not in mine]
        out = []
        for j in unknown:
            if j == k:
                out.append((1.0 / len(unknown), (k + 1, next_turn, tuple(x - {k} for x in mems))))
            else:
                new = list(mems)
                for s_ in range(r):
                    owner = (j + s_) % p
                    new[owner] = _evict(set(new[owner]) | {j}, m, "max")
                out.append((1.0 / len(unknown), (k, next_turn, tuple(new))))
        return out

    return _solve((1, 0, tuple(frozenset() for _ in range(p))), trans)


def window(n: int, m: int) -> float:
    if m == 0:
        return team(n, 0)

    def trans(s):
        k, win = s
        if k > n:
            return None
        if k in win:
            cleared = tuple(0 if x == k else x for x in win)
            return [(1.0, (k + 1, ((0,) + cleared)[:m]))]
        live = {x for x in win if x}
        unknown = [j for j in range(k, n + 1) if j not in live]
        out = []
        for j in unknown:
            if j == k:
                out.append((1.0 / len(unknown), (k + 1, ((0,) + win)[:m])))
            else:
                out.append((1.0 / len(unknown), (k, ((j,) + win)[:m])))
        return out

    return _solve((1, ()), trans)


def expected(kind: str, n: int, m: int, p: int = 2, r: int = 1) -> float:
    """Erwartete Aufdeckungen exakt; m wird auf n − 1 begrenzt (mehr braucht das Team nie)."""
    m = max(0, min(m, n - 1))
    if kind == "team":
        return team(n, m)
    if kind == "split":
        return split(n, m, p, r)
    if kind == "window":
        return window(n, m)
    raise ValueError(kind)
