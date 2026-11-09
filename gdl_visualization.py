"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

from __future__ import annotations

import math

import plotly.graph_objects as go

import gdl_constants as C
import gdl_exact as E


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def grid_shape(n: int) -> tuple[int, int]:
    """(Zeilen, Spalten) des Rasters: möglichst quadratisch."""
    cols = math.ceil(math.sqrt(n))
    return math.ceil(n / cols), cols


def build_grid(layout, opened, last_position, show_all=False):
    """Das Raster der Karten: offene Karten grün mit Nummer, die zuletzt aufgedeckte gelb mit Nummer, verdeckte grau (mit `show_all` mit Nummer, für Neugierige)."""
    n = len(layout)
    rows, cols = grid_shape(n)
    z, text = [], []
    for r in range(rows):
        z_row, t_row = [], []
        for c in range(cols):
            pos = r * cols + c
            if pos >= n:
                z_row.append(None)
                t_row.append("")
            elif pos == last_position:
                z_row.append(2)
                t_row.append(str(layout[pos]))
            elif pos in opened:
                z_row.append(1)
                t_row.append(str(layout[pos]))
            else:
                z_row.append(0)
                t_row.append(str(layout[pos]) if show_all else "")
        z.append(z_row)
        text.append(t_row)
    fig = go.Figure(go.Heatmap(
        z=z, showscale=False, xgap=3, ygap=3, colorscale=[[0.0, C.COLOR_HIDDEN], [0.5, C.COLOR_OPEN], [1.0, C.COLOR_FLIP]], zmin=0, zmax=2,
        hovertemplate="Platz %{y}, %{x}<extra></extra>",
    ))
    # Beschriftungen als Annotationen: der Text eines Heatmap-Traces (texttemplate) meldet beim ersten Zeichnen im noch ungemessenen Container Konsolenfehler (y = -Infinity)
    for r_, t_row in enumerate(text):
        for c_, label in enumerate(t_row):
            if label:
                fig.add_annotation(x=c_, y=r_, text=label, showarrow=False, font=dict(size=14, color="#222222" if z[r_][c_] == 2 else "#ffffff"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")
    return _base(fig, height=max(200, min(420, 58 * rows + 20)))


def build_curves(n, rows, series, y_title="Aufdeckungen im Mittel"):
    """Kurven über m. series: Liste (Schlüssel in rows, Name, Farbe). Mit Fehlerbalken ±1 Standardfehler (bei exakter Rechnung ohne), die Ränder n(n+1)/2 und 2n − H(n) als gestrichelte Linien."""
    fig = go.Figure()
    ms = [r["m"] for r in rows]
    for key, name, color in series:
        se = [r.get(key + "_se", 0.0) or 0.0 for r in rows]
        fig.add_trace(go.Scatter(
            x=ms, y=[r[key] for r in rows], mode="lines+markers", name=name, line=dict(color=color, width=3),
            error_y=dict(type="data", array=se, visible=any(se), thickness=1, width=2),
            hovertemplate="m = %{x}: %{y:.1f}<extra>" + name + "</extra>",
        ))
    # Die Ränder als Linien-Spuren mit Legendeneintrag, nicht als add_hline: Formen und Beschriftungen auf einer logarithmischen Achse erwarten den Zehnerlogarithmus
    # (die Achse würde bis 10^194 aufgezogen).
    none, full = E.expected_none(n), E.expected_full(n)
    for value, name, dash in ((none, "kein Gedächtnis n(n+1)/2", "dot"), (full, "volles Gedächtnis 2n − H(n)", "dash")):
        fig.add_trace(go.Scatter(x=[min(ms), max(ms)], y=[value, value], mode="lines", name=name, line=dict(color=C.COLOR_BOUND, dash=dash, width=2),
                                 hovertemplate=name + ": %{y:.1f}<extra></extra>"))
    fig.update_xaxes(title_text="Gedächtnis m (Paare je Spieler bzw. im Team)")
    fig.update_yaxes(title_text=y_title, type="log" if n > 30 else "linear")
    return _base(fig, height=400)
