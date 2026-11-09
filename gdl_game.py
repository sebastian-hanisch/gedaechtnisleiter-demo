"""Eine Partie mit ausgelegten Plätzen, Zug für Zug (für die Zugansicht und als zweiter Rechenweg zu gdl_simulation.py).

Karten 1..n liegen zufällig auf den Plätzen 0..n−1. Reihum deckt ein Spieler einen verdeckten Platz auf: Kennt er die gesuchte Nummer k, deckt er genau
diese Karte auf; sonst deckt er einen zufälligen Platz auf, von dem er nicht weiß, welche Karte dort liegt (Plätze offener Karten und eigene gemerkte Plätze
scheiden aus). Ist es k, bleibt die Karte offen, sonst wird sie zurückgedreht; alle sehen jede Aufdeckung.

Gedächtnis: `team`/`split` wie in gdl_exact.py (jede Karte merken r der p Spieler, höchste Nummer zuerst vergessen; `team` heißt r = p), `window` die
letzten m Aufdeckungen des Teams. Zufall: SplitMix64 aus gdl_rng (erst die Anordnung, dann die Wahl der unbekannten Plätze)."""

from __future__ import annotations

from dataclasses import dataclass

from gdl_rng import SplitMix64


@dataclass(frozen=True)
class Flip:
    step: int            # laufende Nummer der Aufdeckung, ab 1
    player: int          # wer aufdeckt, 0 bis p−1
    position: int
    number: int
    needed: int          # gesuchte Nummer vor dieser Aufdeckung
    hit: bool
    targeted: bool       # True: der Spieler kannte den Platz von k; False: zufälliger unbekannter Platz
    memory: tuple        # gemerkte Nummern nach dieser Aufdeckung: je Spieler eine sortierte Liste (window: eine Liste für das Team)


@dataclass(frozen=True)
class Game:
    kind: str
    n: int
    m: int
    p: int
    r: int
    layout: tuple        # layout[position] = Nummer
    flips: tuple

    @property
    def length(self) -> int:
        return len(self.flips)


def layout_for(n: int, rng: SplitMix64) -> list[int]:
    """Fisher-Yates: gleichverteilte Anordnung der Nummern 1..n auf die Plätze."""
    cards = list(range(1, n + 1))
    for i in range(n - 1, 0, -1):
        j = min(int(rng.uniform() * (i + 1)), i)
        cards[i], cards[j] = cards[j], cards[i]
    return cards


def play(kind: str, n: int, m: int, seed: int, p: int = 2, r: int = 1) -> Game:
    m = max(0, min(m, n - 1))
    r = min(r, p)
    if kind == "team":
        kind, r = "split", p
    rng = SplitMix64(seed)
    layout = layout_for(n, rng)
    where = {number: pos for pos, number in enumerate(layout)}
    opened: set[int] = set()
    mems = [dict() for _ in range(p)]      # je Spieler: Nummer -> Platz (split)
    window: list[tuple[int, int]] = []     # (Nummer, Platz), neueste zuerst (window)
    flips = []
    k = 1
    step = 0
    cap = 20 * n * n + 1000
    while k <= n:
        step += 1
        if step > cap:
            raise RuntimeError("Partie endet nicht")
        player = (step - 1) % p
        needed = k
        if kind == "split":
            known = mems[player]
            known_pos = set(known.values())
            target = known.get(k)
        else:
            known_pos = {pos for (_, pos) in window if pos not in opened}
            target = next((pos for (num, pos) in window if num == k and pos not in opened), None)
        targeted = target is not None
        if not targeted:
            candidates = [pos for pos in range(n) if pos not in opened and pos not in known_pos]
            target = candidates[min(int(rng.uniform() * len(candidates)), len(candidates) - 1)]
        number = layout[target]
        hit = number == k
        if hit:
            opened.add(target)
            k += 1
            for mem in mems:
                mem.pop(number, None)
        elif kind == "split":
            for s in range(r):
                mem = mems[(number + s) % p]
                mem[number] = target
                while len(mem) > m:
                    del mem[max(mem)]
        if kind == "window" and m > 0:
            window.insert(0, (number, target))
            del window[m:]
        if kind == "split":
            snapshot = tuple(tuple(sorted(mem)) for mem in mems)
        else:
            snapshot = (tuple(sorted(num for (num, pos) in window if pos not in opened)),)
        flips.append(Flip(step, player, target, number, needed, hit, targeted, snapshot))
    return Game(kind, n, m, p, r, tuple(layout), tuple(flips))



def state_at(game: Game, step: int) -> dict:
    """Stand nach `step` Aufdeckungen: offene Plätze, zuletzt aufgedeckter Platz, gesuchte Nummer, gemerkte Nummern, wer als Nächster dran ist."""
    opened = {f.position for f in game.flips[:step] if f.hit}
    last = game.flips[step - 1] if step > 0 else None
    needed = 1 + len(opened)
    memory = last.memory if last else tuple(() for _ in range(game.p if game.kind == "split" else 1))
    return {"opened": opened, "last": last, "needed": needed, "memory": memory, "next_player": step % game.p, "done": needed > game.n}
