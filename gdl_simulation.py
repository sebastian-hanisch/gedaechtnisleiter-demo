"""Simulation vieler Partien nebeneinander (numpy, Achse 0 = Partien) über Nummern statt Plätze.

Wer die gesuchte Nummer k nicht kennt, deckt einen zufälligen Platz auf, der nach seinem Wissen nicht k enthält; bei zufälliger Anordnung ist die dort
liegende Nummer gleichverteilt unter den Nummern k..n, die er nicht kennt (gleiche Annahme wie in gdl_exact.py; gdl_game.py spielt dieselben Regeln mit
ausgelegten Plätzen, tests/test_oracle_gedaechtnisleiter.py vergleicht beides).

Zufall: Partie g zieht im Schritt s die Gleichverteilte `uniform_block(step_seed(seed, s), games)[g]`. Eine Partie hängt damit nur von Seed, Schritt und
ihrer Nummer ab, nicht davon, wann andere Partien enden; alle Deutungen mit demselben Seed lesen dieselben Zufallszahlen."""

from __future__ import annotations

import numpy as np

from gdl_rng import uniform_block


def step_seed(seed: int, step: int) -> int:
    return (int(seed) << 24) + int(step)


def _evict_max(rows: np.ndarray, over: np.ndarray) -> None:
    """In den Zeilen mit over=True den größten gemerkten Wert (True-Eintrag mit größtem Index) löschen; `rows` wird verändert."""
    sub = rows[over]
    largest = sub.shape[-1] - 1 - sub[..., ::-1].argmax(-1)
    sub[np.arange(len(sub)), largest] = False
    rows[over] = sub


def _pick(allowed: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Je Zeile die ceil(u * Anzahl)-te erlaubte Spalte (gleichverteilt unter den erlaubten)."""
    count = allowed.sum(1)
    rank = (u * count).astype(np.int64) + 1
    return (allowed.cumsum(1) >= rank[:, None]).argmax(1)


def simulate(kind: str, n: int, m: int, games: int, seed: int, p: int = 2, r: int = 1) -> np.ndarray:
    """Aufdeckungen je Partie (Länge `games`). kind: "team", "split" (r Besitzer je Karte von p Spielern) oder "window"."""
    m = max(0, min(m, n - 1))
    r = min(r, p)
    if kind == "split" and r >= p:
        kind = "team"
    if kind == "window" and m == 0:
        kind = "team"
    cols = np.arange(n + 2)
    k = np.ones(games, dtype=np.int64)
    t = np.zeros(games, dtype=np.int64)
    ids = np.arange(games)
    out = np.zeros(games, dtype=np.int64)
    if kind == "team":
        mem = np.zeros((games, n + 2), dtype=bool)
    elif kind == "split":
        mem = np.zeros((games, p, n + 2), dtype=bool)
    else:
        win = np.zeros((games, m), dtype=np.int64)
    step = 0
    while len(ids):
        a = len(ids)
        row = np.arange(a)
        if kind == "team":
            known = mem
            known_hit = mem[row, k]
        elif kind == "split":
            known = mem[row, t % p]
            known_hit = known[row, k]
        else:
            known_hit = (win == k[:, None]).any(1)
            known = np.zeros((a, n + 2), dtype=bool)
            known[row[:, None], win] = True
            known[:, 0] = False
        allowed = (~known) & (cols[None, :] >= k[:, None]) & (cols[None, :] <= n)
        u = uniform_block(step_seed(seed, step), games)[ids]
        j = np.where(known_hit, k, _pick(allowed, u))
        hit = j == k
        miss = ~hit
        t = t + 1
        if kind == "team":
            mem[hit, k[hit]] = False
            rows = np.nonzero(miss)[0]
            mem[rows, j[rows]] = True
            over = mem[rows].sum(1) > m
            if over.any():
                sub = mem[rows]
                _evict_max(sub, over)
                mem[rows] = sub
        elif kind == "split":
            hit_rows = np.nonzero(hit)[0]
            if len(hit_rows):
                mem[hit_rows[:, None], np.arange(p)[None, :], k[hit_rows][:, None]] = False
            rows = np.nonzero(miss)[0]
            for s_ in range(r):
                owner = (j[rows] + s_) % p
                mem[rows, owner, j[rows]] = True
                sub = mem[rows, owner]
                over = sub.sum(1) > m
                if over.any():
                    _evict_max(sub, over)
                    mem[rows, owner] = sub
        else:
            known_rows = np.nonzero(known_hit)[0]
            if len(known_rows):
                sub = win[known_rows]
                sub[sub == k[known_rows][:, None]] = 0
                win[known_rows] = sub
            newest = np.where(hit, 0, j)
            win = np.concatenate([newest[:, None], win[:, :-1]], axis=1)
        k = k + hit
        done = k > n
        if done.any():
            out[ids[done]] = t[done]
            keep = ~done
            ids, k, t = ids[keep], k[keep], t[keep]
            if kind == "window":
                win = win[keep]
            else:
                mem = mem[keep]
        step += 1
    return out


def mean_se(flips: np.ndarray) -> tuple[float, float]:
    """Mittel und Standardfehler des Mittels."""
    games = len(flips)
    se = float(flips.std(ddof=1) / np.sqrt(games)) if games > 1 else 0.0
    return float(flips.mean()), se
