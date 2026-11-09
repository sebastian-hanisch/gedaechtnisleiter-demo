"""Kennzahlen, Kurven und Verdikte. Jedes Verdikt ist eine reine Funktion (Art, Text); die App ruft st.<Art>(Text)."""

from __future__ import annotations

from dataclasses import dataclass

import gdl_constants as C
import gdl_exact as E
import gdl_simulation as S


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma und Punkt als Tausendertrenner (5.050; 13,28)."""
    return f"{x:,.{digits}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def de_auto(x: float) -> str:
    """Eine Nachkommastelle, ab 1.000 ganze Zahlen."""
    return de(x, 0 if abs(x) >= 1000 else 1)


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    p: int = C.DEFAULT_P
    r: int = C.DEFAULT_R
    m: int = C.DEFAULT_M
    games: int = C.DEFAULT_GAMES
    seed: int = C.DEFAULT_SEED

    @property
    def r_eff(self) -> int:
        return max(1, min(self.r, self.p))

    @property
    def m_eff(self) -> int:
        return max(0, min(self.m, self.n - 1))

    @property
    def kind(self) -> str:
        return "team" if self.r_eff >= self.p else "split"


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    mean: float
    se: float
    exact: float | None            # nur für n <= EXACT_N_MAX
    team_mean: float | None        # gemeinsames Merken bei gleichem m (nur wenn aufgeteilt wird)
    team_se: float | None
    pooled_mean: float | None      # untere Schranke: gemeinsames Gedächtnis mit p·m Paaren
    pooled_se: float | None
    none: int
    full: float


def analyse(settings: Settings) -> Analysis:
    s = settings
    flips = S.simulate(s.kind, s.n, s.m_eff, s.games, s.seed, s.p, s.r_eff)
    mean, se = S.mean_se(flips)
    exact = E.expected(s.kind, s.n, s.m_eff, s.p, s.r_eff) if s.n <= C.EXACT_N_MAX else None
    team_mean = team_se = pooled_mean = pooled_se = None
    if s.kind == "split":
        team_mean, team_se = S.mean_se(S.simulate("team", s.n, s.m_eff, s.games, s.seed))
        pooled_mean, pooled_se = S.mean_se(S.simulate("team", s.n, min(s.p * s.m_eff, s.n - 1), s.games, s.seed))
    return Analysis(s, mean, se, exact, team_mean, team_se, pooled_mean, pooled_se, E.expected_none(s.n), E.expected_full(s.n))


def curve_ms(n: int) -> list[int]:
    """Gitter über m: bei kleinem n alle m, sonst CURVE_MS_LARGE (nur Werte unter n − 1) und n − 1."""
    if n <= C.EXACT_N_MAX:
        return list(range(0, n))
    return [m for m in C.CURVE_MS_LARGE if m < n - 1] + [n - 1]


def curve_cell(kind: str, n: int, m: int, p: int, r: int, games: int, seed: int) -> tuple[float, float]:
    """(Mittel, Standardfehler); bei n <= EXACT_N_MAX exakt (Standardfehler 0), sonst Simulation."""
    if n <= C.EXACT_N_MAX:
        return E.expected(kind, n, m, p, r), 0.0
    if m == 0:
        return float(E.expected_none(n)), 0.0           # ohne Gedächtnis sind alle Deutungen gleich: n(n+1)/2
    if kind == "team" and m >= n - 1:
        return E.expected_full(n), 0.0                  # volles Gedächtnis: 2n − H(n)
    return S.mean_se(S.simulate(kind, n, m, games, seed, p, r))


def ladder_rows(n: int, p: int, games: int, seed: int) -> list[dict]:
    """E1: Team, aufgeteilt (r = 1) und Fenster über m."""
    rows = []
    for m in curve_ms(n):
        row = {"m": m}
        for name, kind, r in (("team", "team", p), ("split", "split", 1), ("window", "window", 1)):
            row[name], row[name + "_se"] = curve_cell(kind, n, m, p, r, games, seed)
        rows.append(row)
    return rows


def share_rows(n: int, p: int, games: int, seed: int) -> list[dict]:
    """E4: Team, Aufteilen mit r = 1 und (bei p >= 3) r = 2, dazu die untere Schranke (Team mit p·m Paaren)."""
    rows = []
    for m in curve_ms(n):
        row = {"m": m}
        specs = [("team", "team", p), ("r1", "split", 1)]
        if p >= 3:
            specs.append(("r2", "split", 2))
        specs.append(("bound", "team", None))
        for name, kind, r in specs:
            if name == "bound":
                row[name], row[name + "_se"] = curve_cell("team", n, min(p * m, n - 1), p, p, games, seed)
            else:
                row[name], row[name + "_se"] = curve_cell(kind, n, m, p, r, games, seed)
        rows.append(row)
    return rows


def forget_rows(n: int) -> list[dict]:
    """E3 (exakt): Vergessen der höchsten Nummer zuerst, der kleinsten zuerst und das optimale Vergessen, über m = 1 .. n − 1."""
    return [{"m": m, "max": E.team(n, m, "max"), "min": E.team(n, m, "min"), "opt": E.team_optimal(n, m)} for m in range(1, n)]


# --- Verdikte (rein) ----------------------------------------------------------------------------------------------------------------------

def verdict_main(n: int, m: int, mean: float, se: float, none: float, full: float, team_mean: float | None = None, team_se: float | None = None,
                 p: int | None = None, r: int | None = None) -> tuple[str, str]:
    """Kernfrage der Hauptansicht: wo liegt die Einstellung zwischen keinem und vollem Gedächtnis, und (bei Aufteilen) gegenüber gemeinsamem Merken?"""
    if m <= 0:
        return "warning", f"Ohne Gedächtnis sind es im Mittel **{de(none, 0)}** Aufdeckungen, n(n+1)/2 bei n = {n}: für jede gesuchte Nummer ist jede verdeckte Karte gleich wahrscheinlich."
    if m >= n - 1 and team_mean is None:
        return "success", f"Mit m = n − 1 = {n - 1} Paaren merken sich alle alles, was sie brauchen: **{de(full, 2)}** Aufdeckungen im Mittel (2n − H(n) bei n = {n}), mehr Gedächtnis hilft nicht."
    if m >= n - 1:
        if mean > full + 2 * (se or 0.0):
            return "warning", (f"Mit m = n − 1 = {n - 1} Paaren je Spieler bleibt Aufteilen (jede Karte merken {r} von {p} Spielern) bei **{de(mean, 1)}** Aufdeckungen (± {de(se, 1)} Standardfehler); "
                               f"gemeinsames Merken käme auf {de(full, 2)} (2n − H(n) bei n = {n}). Mehr Gedächtnis ändert hier nichts mehr: der Abstand liegt an der Aufteilung, nicht am Gedächtnis.")
        return "info", f"Mit m = n − 1 = {n - 1} Paaren je Spieler sind es **{de(mean, 1)}** Aufdeckungen (± {de(se, 1)} Standardfehler), von gemeinsamem Merken ({de(full, 2)}) nicht zu unterscheiden."
    share = 100.0 * (none - mean) / (none - full) if none > full else 0.0
    text = (f"Bei n = {n} und m = {m} Paaren sind es im Mittel **{de(mean, 1)}** Aufdeckungen (± {de(se, 1)} Standardfehler): {de(share, 0)} % des Wegs von {de(none, 0)} ohne "
            f"Gedächtnis bis {de(full, 1)} bei vollem Gedächtnis.")
    if team_mean is None:
        return "info", text
    diff = team_mean - mean
    se_diff = ((se or 0.0) ** 2 + (team_se or 0.0) ** 2) ** 0.5
    if diff > 2 * se_diff:
        return "success", text + f" Jede Karte merken nur {r} von {p} Spielern: das spart **{de(diff, 1)}** gegenüber gemeinsamem Merken ({de(team_mean, 1)}), also {de(100.0 * diff / team_mean, 0)} % von dessen Aufdeckungen."
    if diff < -2 * se_diff:
        return "warning", text + f" Aufteilen (jede Karte merken {r} von {p} Spielern) kostet **{de(-diff, 1)}** mehr als gemeinsames Merken ({de(team_mean, 1)}); vermutlich liegt das Wissen beim Zuständigen, der nicht immer dran ist (Deutung, nicht gemessen)."
    return "info", text + f" Aufteilen und gemeinsames Merken ({de(team_mean, 1)}) unterscheiden sich um {de(abs(diff), 1)}, weniger als zwei Standardfehler ({de(2 * se_diff, 1)}): kein Unterschied erkennbar."


def verdict_ladder(n: int, rows: list[dict]) -> tuple[str, str]:
    """E1: das erste Paar, das Fenster gegen das Team."""
    by_m = {r["m"]: r for r in rows}
    first = by_m[1]
    first_saving = 100.0 * (by_m[0]["team"] - first["team"]) / by_m[0]["team"]
    worse = [r for r in rows if r["m"] >= 1 and r["window"] > r["team"]]
    if worse:
        gap = max(worse, key=lambda r: (r["window"] - r["team"]) / r["team"])
        gap_pct = 100.0 * (gap["window"] - gap["team"]) / gap["team"]
        window_text = (f"Das Fenster der letzten m Aufdeckungen liegt in {len(worse)} von {sum(1 for r in rows if r['m'] >= 1)} Zellen über dem Team, "
                       f"am weitesten bei m = {gap['m']} ({de_auto(gap['window'])} gegen {de_auto(gap['team'])}, {de(gap_pct, 0)} % darüber).")
    else:
        window_text = "Das Fenster der letzten m Aufdeckungen liegt in keiner Zelle über dem Team."
    return "info", f"Das erste gemerkte Paar spart {de(first_saving, 0)} % ({de_auto(by_m[0]['team'])} → {de_auto(first['team'])}). {window_text}"


def _tolerance(row: dict) -> float:
    """Unterschiede unter zwei Standardfehlern der Differenz (bei exakter Rechnung unter 0,01) zählen als gleichauf."""
    se = ((row.get("team_se", 0.0) or 0.0) ** 2 + (row.get("r1_se", 0.0) or 0.0) ** 2) ** 0.5
    return max(2.0 * se, 0.01)


def crossing(rows: list[dict]) -> tuple[int | None, int | None]:
    """Letztes m des Gitters, in dem Aufteilen (r1) das Team deutlich schlägt (um mehr als die Toleranz), und erstes m danach, in dem das Team besser oder gleichauf ist
    (None, falls es das nicht gibt)."""
    better = [r["m"] for r in rows if r["m"] >= 1 and r["r1"] < r["team"] - _tolerance(r)]
    last_better = max(better) if better else None
    after = [r["m"] for r in rows if r["m"] >= 1 and (last_better is None or r["m"] > last_better) and r["team"] <= r["r1"] + _tolerance(r)]
    return last_better, (min(after) if after else None)


def verdict_share(n: int, p: int, rows: list[dict]) -> tuple[str, str]:
    """E4: wo kreuzen sich Aufteilen und gemeinsames Merken, wie hoch ist das Plateau."""
    last_better, first_team = crossing(rows)
    plateau = rows[-1]["r1"]
    if last_better is None:
        return "info", f"Bei n = {n} und {p} Spielern ist Aufteilen in keiner Zelle des Gitters deutlich besser als gemeinsames Merken."
    if first_team is None:
        return "info", f"Bei n = {n} und {p} Spielern ist Aufteilen in jeder Zelle bis m = {last_better} deutlich besser als gemeinsames Merken (Gitter endet dort)."
    return "info", (f"Bei n = {n} und {p} Spielern ist Aufteilen bis m = {last_better} deutlich besser als gemeinsames Merken, ab m = {first_team} ist das Team besser oder gleichauf "
                    f"(die Kreuzung liegt auf dem Gitter zwischen diesen Werten). Mit n − 1 Paaren je Spieler bleibt Aufteilen bei {de_auto(plateau)}, "
                    f"gemeinsam sind es {de_auto(rows[-1]['team'])}.")


def verdict_forget(rows: list[dict]) -> tuple[str, str]:
    """E3: ist „höchste Nummer zuerst vergessen“ in jeder Zelle optimal, wie viel kostet „kleinste zuerst“?"""
    opt_cells = [r for r in rows if abs(r["max"] - r["opt"]) < 1e-9]
    worst = max(rows, key=lambda r: r["min"] - r["opt"])
    text = (f"„Höchste Nummer zuerst vergessen“ ist in {len(opt_cells)} von {len(rows)} Zellen so gut wie das optimale Vergessen. „Kleinste zuerst“ kostet bis zu "
            f"{de(worst['min'] - worst['opt'], 1)} mehr (bei m = {worst['m']}: {de(worst['min'], 1)} gegen {de(worst['opt'], 1)}).")
    return ("success" if len(opt_cells) == len(rows) else "warning"), text


def verdict_search(n: int, m: int, p: int, team: float, split: float, best: float, lower: float, uses_share: bool) -> tuple[str, str]:
    """E5: wie viel besser ist das gefundene Protokoll als die beste einfache Regel, wie weit ist die untere Schranke weg?"""
    simple = min(team, split)
    gain = 100.0 * (simple - best) / simple
    share_text = ("Im besten gefundenen Protokoll kommt ein Aufdecken eigener Karten zur Mitteilung vor." if uses_share else
                  "Im besten gefundenen Protokoll kommt kein Aufdecken eigener Karten zur Mitteilung vor; die Suche startet aber nur von Regeln ohne Mitteilung, ein Beweis, dass Zeichen nie helfen, ist das nicht.")
    return "info", (f"Für n = {n}, m = {m}, {p} Spieler: bestes gefundenes Protokoll **{de(best, 2)}**, beste einfache Regel {de(simple, 2)} (gemeinsam {de(team, 2)}, aufgeteilt "
                    f"{de(split, 2)}): {de(gain, 1)} % weniger als die beste einfache Regel. Untere Schranke (gemeinsames Gedächtnis mit {p * m} Paaren) {de(lower, 2)}. {share_text}")
