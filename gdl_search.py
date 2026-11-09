"""Suche nach einem besseren verteilten Protokoll (kleine Fälle, lokale Suche, kein Beweis für ein Optimum).

Ein Protokoll legt für jeden Spieler fest, was er tut, und zwar nur aus seinem EIGENEN Gedächtnis und öffentlichen Angaben:
  * Aktion, wenn er k nicht kennt: einen zufälligen unbekannten Platz aufdecken ("E") oder eine selbst gemerkte Karte x aufdecken (("F", x)),
    was sie allen zeigt, aber nie trifft;
  * Speichern nach einem Fehlversuch j: aus seinem Gedächtnis M und j ein neues M' mit höchstens m Nummern wählen (M' = M heißt: ignorieren).
Die Entscheidungstabelle ist der Suchraum. Bewertet wird jedes Protokoll exakt über die Markov-Kette (Zustand: k, wer dran ist, Gedächtnis aller
Spieler). Start: die einfachen Regeln "alle merken dasselbe" und "aufgeteilt nach Nummer mod p"; danach Koordinatenabstieg über die Entscheidungen,
die im Protokoll mit Gewicht vorkommen, bis keine einzelne Änderung mehr verbessert."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
from scipy.sparse import csr_matrix, identity
from scipy.sparse.linalg import spsolve

import gdl_exact as E

STATE_CAP = 300000


def _store_options(mem, j, m):
    pool = set(mem) | {j}
    options = {frozenset(mem)}
    size = min(m, len(pool))
    for c in combinations(sorted(pool), size):
        options.add(frozenset(c))
    return sorted(options, key=lambda s: sorted(s))


def _act_options(mem):
    return ["E"] + [("F", x) for x in sorted(mem)]


class Policy:
    def __init__(self, n: int, m: int, p: int, start: str):
        self.n, self.m, self.p, self.start = n, m, p, start     # start: "team" oder "split"
        self.act: dict = {}
        self.store: dict = {}

    def get_act(self, player, mem, k):
        return self.act.get((player, mem, k), "E")

    def get_store(self, player, mem, j, k, flipper):
        key = (player, mem, j, k, flipper)
        if key in self.store:
            return self.store[key]
        if self.start == "split" and j % self.p != player:
            return frozenset(mem)
        return E._evict(set(mem) | {j}, self.m, "max")


def evaluate(pol: Policy, want_weights: bool = False):
    n, p = pol.n, pol.p
    start = (1, 0, tuple(frozenset() for _ in range(p)))
    idx = {start: 0}
    order = [start]
    rows, cols, vals, uses = [], [], [], []
    i = 0
    while i < len(order):
        k, turn, mems = order[i]
        if k > n:
            i += 1
            continue
        nxt = (turn + 1) % p
        mine = mems[turn]
        outs = []
        if k in mine:
            outs.append((1.0, (k + 1, nxt, tuple(frozenset(x for x in mem if x > k) for mem in mems)), []))
        else:
            action = pol.get_act(turn, mine, k)
            act_key = ("act", turn, mine, k)
            if action == "E":
                unknown = [j for j in range(k, n + 1) if j not in mine]
                revealed = [(1.0 / len(unknown), j) for j in unknown]
            else:
                revealed = [(1.0, action[1])]
            for prob, j in revealed:
                if j == k:
                    outs.append((prob, (k + 1, nxt, tuple(frozenset(x for x in mem if x > k) for mem in mems)), [act_key]))
                else:
                    keys = [act_key]
                    new = []
                    for q in range(p):
                        mem_q = frozenset(x for x in mems[q] if x >= k)
                        new.append(pol.get_store(q, mem_q, j, k, turn))
                        keys.append(("store", q, mem_q, j, k, turn))
                    outs.append((prob, (k, nxt, tuple(new)), keys))
        for prob, t, keys in outs:
            if t not in idx:
                idx[t] = len(order)
                order.append(t)
                if len(order) > STATE_CAP:
                    raise E.TooLarge("zu viele Zustände")
            rows.append(i)
            cols.append(idx[t])
            vals.append(prob)
            for key in keys:
                uses.append((i, prob, key))
        i += 1
    size = len(order)
    p_matrix = csr_matrix((vals, (rows, cols)), shape=(size, size))
    cost = np.array([1.0 if s[0] <= n else 0.0 for s in order])
    a_matrix = (identity(size, format="csc") - p_matrix).tocsc()
    value = float(spsolve(a_matrix, cost)[0])
    if not want_weights:
        return value, None
    e0 = np.zeros(size)
    e0[0] = 1.0
    visits = spsolve(a_matrix.T.tocsc(), e0)
    weights: dict = {}
    for state, prob, key in uses:
        weights[key] = weights.get(key, 0.0) + visits[state] * prob
    return value, weights


def optimize(pol: Policy, rounds: int = 8, min_weight: float = 0.003) -> float:
    value, weights = evaluate(pol, True)
    for _ in range(rounds):
        improved = False
        for key, weight in sorted(weights.items(), key=lambda kv: -kv[1]):
            if weight < min_weight:
                continue
            if key[0] == "act":
                _, player, mem, k = key
                current = pol.get_act(player, mem, k)
                best = (value, current)
                for option in _act_options(mem):
                    if option == current:
                        continue
                    pol.act[(player, mem, k)] = option
                    v, _ = evaluate(pol)
                    if v < best[0] - 1e-9:
                        best = (v, option)
                pol.act[(player, mem, k)] = best[1]
            else:
                _, player, mem, j, k, flipper = key
                store_key = (player, mem, j, k, flipper)
                current = pol.get_store(player, mem, j, k, flipper)
                best = (value, current)
                for option in _store_options(mem, j, pol.m):
                    if option == current:
                        continue
                    pol.store[store_key] = option
                    v, _ = evaluate(pol)
                    if v < best[0] - 1e-9:
                        best = (v, option)
                pol.store[store_key] = best[1]
            if best[1] != current:
                improved = True
                value = best[0]
        value, weights = evaluate(pol, True)
        if not improved:
            break
    return value


@dataclass
class SearchResult:
    n: int
    m: int
    p: int
    team: float                 # einfache Regel: alle merken dasselbe
    split: float                # einfache Regel: aufgeteilt nach Nummer mod p
    best: float                 # bestes gefundenes Protokoll
    best_start: str             # von welcher Regel aus gefunden
    lower: float                # untere Schranke: gemeinsames Gedächtnis mit p·m Paaren
    uses_share: bool            # kommt im besten Protokoll irgendwo ein Aufdecken eigener Karten zur Mitteilung vor?
    lines: list = field(default_factory=list)   # die wichtigsten Entscheidungen als Text


def search(n: int, m: int, p: int, rounds: int = 8, min_weight: float = 0.003, top: int = 12) -> SearchResult:
    start_values, results = {}, {}
    for start in ("team", "split"):
        pol = Policy(n, m, p, start)
        start_values[start] = evaluate(pol)[0]
        optimize(pol, rounds, min_weight)
        results[start] = (evaluate(pol)[0], pol)
    best_start = min(results, key=lambda s: results[s][0])
    best_value, best_pol = results[best_start]
    _, weights = evaluate(best_pol, True)
    lines = []
    uses_share = any(action != "E" for action in best_pol.act.values())        # über ALLE geänderten Aktionsentscheidungen, nicht nur die wichtigsten
    for key, weight in sorted(weights.items(), key=lambda kv: -kv[1])[:25]:
        if key[0] == "act":
            _, player, mem, k = key
            action = best_pol.get_act(player, mem, k)
            if len(lines) < top:
                text = "zufälligen unbekannten Platz aufdecken" if action == "E" else f"die selbst gemerkte Karte {action[1]} aufdecken"
                lines.append(f"Spieler {player + 1} ist dran, sucht {k}, merkt {sorted(mem) or 'nichts'}: {text} (Gewicht {weight:.2f})".replace("'", ""))
        elif len(lines) < top:
            _, player, mem, j, k, flipper = key
            new = sorted(best_pol.get_store(player, mem, j, k, flipper))
            lines.append(f"Spieler {player + 1} sieht die {j} (sucht {k}, aufgedeckt von Spieler {flipper + 1}), merkt {sorted(mem) or 'nichts'}, danach {new or 'nichts'} (Gewicht {weight:.2f})".replace("'", ""))
    lower = E.team(n, min(p * m, n - 1))
    return SearchResult(n, m, p, start_values["team"], start_values["split"], best_value, best_start, lower, uses_share, lines)
