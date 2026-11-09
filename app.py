"""Gedächtnisleiter: Wie viel Merken braucht ein Team? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Nummerierte Karten liegen verdeckt auf einem Raster; reihum deckt jeder eine auf, nur die nächste Nummer bleibt offen. Gemessen wird, wie viele
Aufdeckungen das Team braucht, wenn es sich nur begrenzt viele aufgedeckte Karten merken kann und nicht reden darf.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import gdl_constants as C
import gdl_evaluation as V
import gdl_game as G
import gdl_search as SR
from gdl_evaluation import Settings, de
from gdl_layout import dunkles_design, kopf_css
from gdl_presets import (
    bounds,
    clamp_m_state,
    init_session_state_defaults,
    load_permalink_settings,
    m_upper,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from gdl_visualization import build_curves, build_grid

st.set_page_config(page_title="Gedächtnisleiter – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return V.analyse(settings)


@st.cache_data(show_spinner=False)
def _game(kind, n, m, seed, p, r):
    return G.play(kind, n, m, seed, p, r)


@st.cache_data(show_spinner=False)
def _ladder(n, p, games, seed):
    return V.ladder_rows(n, p, games, seed)


@st.cache_data(show_spinner=False)
def _share(n, p, games, seed):
    return V.share_rows(n, p, games, seed)


@st.cache_data(show_spinner=False)
def _forget(n):
    return V.forget_rows(n)


@st.cache_data(show_spinner=False)
def _search(n, m, p):
    return SR.search(n, m, p)


def gated(key, params, label, seconds, compute):
    """Bis n = EXACT_N_MAX rechnet das Experiment sofort (exakt); darüber erst nach Klick, mit Hinweis auf die Rechenzeit; das Ergebnis bleibt, solange die Einstellungen gleich sind."""
    if params["n"] <= C.EXACT_N_MAX:
        return compute()
    token = tuple(sorted(params.items()))
    if st.button(label, key=f"run_{key}"):
        st.session_state[f"done_{key}"] = token
    if st.session_state.get(f"done_{key}") != token:
        st.caption(f"Simulation mit den Einstellungen der Seitenleiste, etwa {seconds} Sekunden; das Ergebnis bleibt stehen, solange sie gleich bleiben.")
        return None
    with st.spinner(f"Rechne … (etwa {seconds} Sekunden)"):
        return compute()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in gdl_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🃏 Gedächtnisleiter: Wie viel Merken braucht ein Team?")
st.markdown(
    """
Nummerierte Karten liegen verdeckt und zufällig auf einem Raster. **Reihum** deckt jeder eine Karte auf: Ist es die **nächste Nummer** (zuerst die 1), bleibt sie offen,
sonst wird sie wieder umgedreht. Alle sehen jede Aufdeckung, **reden oder zeigen** darf niemand. Die Frage: Wie wenige Aufdeckungen braucht das Team, und wie sehr hängt das davon ab,
**wie viele aufgedeckte Karten es sich merken kann** (Gedächtnis m), ob **alle dasselbe** merken oder jede Karte nur **einer**, und ob das Gedächtnis nach Wichtigkeit oder nach Zeit vergisst?
Teil der Reihe „Teamrätsel: Strategie ohne Verständigung“.

Weiter unten: eine **Partie Zug für Zug**, vier **🔬 Experimente**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Gedächtnisleiter", expanded=True):
    st.markdown(
        """
1. **Wer die gesuchte Nummer k kennt, deckt genau diese Karte auf:** sicherer Treffer, die Karte bleibt offen, k wird um eins größer.
2. **Sonst deckt er einen zufälligen Platz auf, von dem er nicht weiß, was dort liegt.** Trifft er k, bleibt die Karte offen. Sonst wird sie zurückgedreht, aber alle haben sie gesehen und merken sie sich,
   soweit ihr Gedächtnis reicht: höchstens m Paare „Nummer → Platz“. Beim Überlauf wird die **höchste Nummer zuerst vergessen**, weil sie am spätesten gebraucht wird.
3. **Wer merkt was:** *alle dasselbe* (Team) oder *aufgeteilt*: jede Karte merken nur r der p Spieler (nach Nummer mod p). Dann merkt das Team insgesamt mehr, aber nur der Zuständige kennt die Karte,
   und der ist nicht immer dran; reden darf er nicht.
4. **Gezählt werden alle Aufdeckungen:** n Treffer (jede Karte wird einmal offen, gezielt oder durch Zufall beim Suchen) plus jeder Fehlversuch. Ganz ohne Gedächtnis sind es n(n+1)/2, bei vollem Gedächtnis 2n − H(n).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Spiel**")
    n = st.slider("Karten n", *bounds("n_slider"), key="n_slider", help="Wie viele Karten auf dem Raster liegen. Bis n = 8 rechnet die App exakt, darüber per Simulation.")
    p = st.slider("Spieler p", *bounds("p_slider"), key="p_slider", help="Wie viele Spieler am Tisch sitzen; es geht reihum.")
    st.markdown("**Gedächtnis**")
    clamp_m_state(int(n))
    m = st.slider("Gedächtnis m (Paare je Spieler)", C.M_MIN, m_upper(int(n)), key="m_slider",
                  help="Wie viele aufgedeckte Karten (Nummer und Platz) sich jeder merken kann. Mit n − 1 Paaren merkt das Team alles, was es braucht.")
    r = st.slider("Besitzer je Karte r", *bounds("r_slider"), key="r_slider",
                  help="Wie viele der p Spieler sich eine aufgedeckte Karte merken. r = p: alle merken dasselbe (Team). r = 1: aufgeteilt nach Nummer mod p. Wirksam ist min(r, p).")
    st.caption(f"Wirksam: r = {min(int(r), int(p))} von {int(p)} Spielern merken jede Karte" + (" (alle dasselbe)." if int(r) >= int(p) else " (aufgeteilt)."))
    st.markdown("**Rechnung**")
    games = st.slider("Simulierte Partien", C.GAMES_MIN, C.GAMES_MAX, step=C.GAMES_STEP, key="games_slider",
                      help="Wie viele Partien für Mittelwerte simuliert werden (ab n = 9). Mehr Partien: kleinerer Standardfehler, längere Rechenzeit.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1, help="Legt Anordnung und Zufallswahlen fest; gleicher Zufalls-Seed, gleiche Ergebnisse.")
    st.button("🎲 Neuen Zufalls-Seed würfeln", width="stretch", on_click=randomize_seed)

sync_query_params({"n_slider": int(n), "p_slider": int(p), "r_slider": int(r), "m_slider": int(m), "games_slider": int(games), "seed_input": int(seed)})

settings = Settings(int(n), int(p), int(r), int(m), int(games), int(seed))
a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Aufdeckungen im Mittel", de(a.mean, 1), delta=f"± {de(a.se, 1)} Standardfehler, {settings.games} Partien", delta_color="off",
          help="Mittel über die simulierten Partien; der Standardfehler gibt die Streuung dieses Mittels an.")
c2.metric("Exakt (Markov-Kette)", de(a.exact, 2) if a.exact is not None else "–", delta="nur bis n = 8" if a.exact is None else "ohne Simulationsfehler", delta_color="off")
c3.metric("Kein Gedächtnis", de(a.none, 0), delta="n(n+1)/2", delta_color="off")
c4.metric("Volles Gedächtnis", de(a.full, 1), delta="2n − H(n)", delta_color="off")
if a.team_mean is not None:
    d1, d2 = st.columns(2)
    # Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
    d1.metric("Gemeinsames Merken (alle dasselbe, gleiches m)", de(a.team_mean, 1), delta=f"{de(a.mean - a.team_mean, 1)} Aufteilen gegen gemeinsam", delta_color="inverse",
              help="Alle Spieler merken dieselben m Paare. Vergleichswert zur gewählten Aufteilung, gleicher Zufalls-Seed.")
    d2.metric(f"Untere Schranke (gemeinsames Gedächtnis mit {settings.p * settings.m_eff} Paaren)", de(a.pooled_mean, 1), delta="mehr kann das Team nicht wissen", delta_color="off",
              help="So schnell wäre das Team, wenn alle alles wüssten, was die p Spieler zusammen merken, ohne dass der Zuständige dran sein muss. In den gerechneten Fällen lag kein gefundenes Protokoll darunter; bewiesen ist das nicht.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viel bringt das Gedächtnis, und lohnt es sich, es aufzuteilen?")
kind, text = V.verdict_main(settings.n, settings.m_eff, a.mean, a.se, a.none, a.full, a.team_mean, a.team_se, settings.p, settings.r_eff)
getattr(st, kind)(text)

st.markdown("---")

# --- Partie Zug für Zug --------------------------------------------------------------------------------------------------------------------

st.subheader("🎞️ Eine Partie Zug für Zug")
if settings.n > C.GAME_VIEW_N_MAX:
    st.info(f"Die Zugansicht zeigt das Raster bis n = {C.GAME_VIEW_N_MAX}; bei n = {settings.n} wären es mehrere hundert Aufdeckungen. Für große n zeigen die Experimente unten die Mittelwerte.")
else:
    game = _game(settings.kind, settings.n, settings.m_eff, settings.seed, settings.p, settings.r_eff)
    st.caption(f"Eine Partie mit den Einstellungen der Seitenleiste (ausgelegte Plätze, Zufalls-Seed {settings.seed}): {game.length} Aufdeckungen; "
               f"der Mittelwert über {settings.games} simulierte Partien ist {de(a.mean, 1)}.")
    st.session_state["game_step"] = min(st.session_state.get("game_step", 0), game.length)
    step = st.slider("Zug", 0, game.length, key="game_step", help="Wie viele Aufdeckungen dieser Partie angezeigt werden.")
    state = G.state_at(game, step)
    left, right = st.columns([3, 2])
    with left:
        st.plotly_chart(build_grid(game.layout, state["opened"], state["last"].position if state["last"] else None), width="stretch", key="grid_chart")
        st.caption("Grün: offen, gelb: eben aufgedeckt, grau: verdeckt. Die Karten liegen zeilenweise auf den Plätzen 0 bis n − 1.")
    with right:
        if state["done"]:
            st.success(f"Alle {settings.n} Karten sind offen, nach {step} Aufdeckungen.")
        else:
            st.markdown(f"**Gesucht:** Nummer {state['needed']}  \n**Als Nächster dran:** Spieler {state['next_player'] + 1}")
        last = state["last"]
        if last:
            how = "gezielt (kannte den Platz)" if last.targeted else "zufälliger unbekannter Platz"
            result = "Treffer, bleibt offen" if last.hit else "Fehlversuch, wird zurückgedreht"
            st.markdown(f"**Zug {last.step}:** Spieler {last.player + 1} deckt Platz {last.position} auf, dort liegt die **{last.number}** (gesucht: {last.needed}). {result}; {how}.")
        if game.kind == "split":
            for q, mem in enumerate(state["memory"]):
                st.markdown(f"Spieler {q + 1} merkt: {', '.join(map(str, mem)) if mem else '–'}")
        else:
            mem = state["memory"][0] if state["memory"] else ()
            st.markdown(f"Das Team merkt (letzte {game.m} Aufdeckungen, nur noch verdeckte): {', '.join(map(str, mem)) if mem else '–'}")
    with st.expander("Alle Aufdeckungen dieser Partie"):
        st.dataframe(
            [{"Zug": f.step, "Spieler": f.player + 1, "Platz": f.position, "Nummer": f.number, "Gesucht": f.needed,
              "Ergebnis": "Treffer" if f.hit else "Fehlversuch", "Wahl": "gezielt" if f.targeted else "zufällig"} for f in game.flips],
            hide_index=True, width="stretch",
        )

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Die Leiter")
st.caption("Aufdeckungen über das Gedächtnis m: alle merken dasselbe (Team, nach Wichtigkeit), aufgeteilt (jede Karte merkt einer, nach Nummer mod p) und das Fenster der letzten m Aufdeckungen. "
           f"Bis n = 8 exakt, darüber Simulation ({settings.games} Partien je Zelle, Fehlerbalken ± ein Standardfehler); Spieler p wie in der Seitenleiste.")
rows = gated("ladder", dict(n=settings.n, p=settings.p, games=settings.games, seed=settings.seed), "▶ Leiter rechnen", 15, lambda: _ladder(settings.n, settings.p, settings.games, settings.seed))
if rows:
    st.plotly_chart(build_curves(settings.n, rows, [("team", "alle merken dasselbe", C.COLOR_TEAM), ("split", "aufgeteilt (r = 1)", C.COLOR_SPLIT), ("window", "Fenster der letzten m", C.COLOR_WINDOW)]),
                    width="stretch", key="ladder_chart")
    kind, text = V.verdict_ladder(settings.n, rows)
    getattr(st, kind)(text)

st.markdown("---")
n_forget = min(settings.n, C.EXACT_N_MAX)
st.subheader("🔬 Experiment 2: Was wird zuerst vergessen?")
st.caption(f"Exakt für n = {n_forget} (größer als {C.EXACT_N_MAX} rechnet die App hier nicht): alle merken dasselbe, beim Überlauf fällt die höchste Nummer weg, die kleinste, oder das Team wählt das beste Vergessen (Wertiteration).")
frows = _forget(n_forget)
fig_rows = [{"m": r_["m"], "max": r_["max"], "min": r_["min"], "opt": r_["opt"]} for r_ in frows]
st.plotly_chart(build_curves(n_forget, fig_rows, [("max", "höchste Nummer zuerst", C.COLOR_TEAM), ("min", "kleinste zuerst", C.COLOR_SPLIT), ("opt", "optimales Vergessen", C.COLOR_WINDOW)]),
                width="stretch", key="forget_chart")
kind, text = V.verdict_forget(frows)
getattr(st, kind)(text)

st.markdown("---")
st.subheader("🔬 Experiment 3: Teilen lohnt, bis das Gedächtnis reicht")
st.caption("Aufteilen (jede Karte merkt einer, bei p ≥ 3 auch zwei) gegen gemeinsames Merken, dazu die untere Schranke (gemeinsames Gedächtnis mit p·m Paaren). "
           "Bis n = 8 exakt, darüber Simulation; Spieler p wie in der Seitenleiste.")
rows = gated("share", dict(n=settings.n, p=settings.p, games=settings.games, seed=settings.seed), "▶ Teilen rechnen", 15, lambda: _share(settings.n, settings.p, settings.games, settings.seed))
if rows:
    series = [("team", "alle merken dasselbe", C.COLOR_TEAM), ("r1", "aufgeteilt (r = 1)", C.COLOR_SPLIT)]
    if settings.p >= 3:
        series.append(("r2", "jede Karte merken zwei (r = 2)", C.COLOR_WINDOW))
    series.append(("bound", f"untere Schranke (Team mit {settings.p}·m Paaren)", C.COLOR_BOUND))
    st.plotly_chart(build_curves(settings.n, rows, series), width="stretch", key="share_chart")
    kind, text = V.verdict_share(settings.n, settings.p, rows)
    getattr(st, kind)(text)

st.markdown("---")
st.subheader("🔬 Experiment 4: Gibt es ein besseres Protokoll?")
st.caption("Suche nach der besten Entscheidungstabelle, wenn jeder nur aus seinem eigenen Gedächtnis und den öffentlichen Angaben entscheidet (lokale Suche, exakt bewertet). "
           "Nur kleine Fälle; die Einstellungen der Seitenleiste gelten hier nicht.")
labels = [f"n = {c[0]}, m = {c[1]}, {c[2]} Spieler" for c in C.SEARCH_CASES]
choice = st.selectbox("Fall", labels, key="search_case", help="Die Suche läuft im Browser der App; größere Fälle brauchen Minuten.")
case = C.SEARCH_CASES[labels.index(choice)]
if st.button("▶ Suche starten (3 bis 20 Sekunden)", key="run_search"):
    st.session_state["done_search"] = case
if st.session_state.get("done_search") == case:
    with st.spinner("Suche läuft …"):
        res = _search(*case)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Bestes gefundenes Protokoll", de(res.best, 2))
    s2.metric("Gemeinsam merken", de(res.team, 2))
    s3.metric("Aufgeteilt (mod p)", de(res.split, 2))
    s4.metric("Untere Schranke", de(res.lower, 2), help="Gemeinsames Gedächtnis mit p·m Paaren.")
    kind, text = V.verdict_search(res.n, res.m, res.p, res.team, res.split, res.best, res.lower, res.uses_share)
    getattr(st, kind)(text)
    with st.expander("Die wichtigsten Entscheidungen des gefundenen Protokolls"):
        st.markdown("\n".join(f"- {line}" for line in res.lines))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Gemessen? |
|---|---|---|
| **Alle sehen jede Aufdeckung und passen perfekt auf, niemand macht Fehler** | Mit Unaufmerksamkeit oder Fehlern ist es ein anderes Modell. | Nein |
| **Reden, Zeigen und Zeichen sind verboten** | Mit Reden könnte das Team Gedächtnis auslagern („die 7 liegt links oben“) und käme dem vollen Gedächtnis näher. Auch die Wahl der Aufdeckung kann ein Zeichen sein (kostet einen Versuch). | Nein; im besten gefundenen Protokoll von Experiment 4 kam kein Aufdecken eigener Karten zur Mitteilung vor (die Suche startet nur von Regeln ohne Mitteilung, kein Beweis) |
| **Gedächtnis = m Paare Nummer → Platz, Vergessen nach fester Regel** | Das Fenster der letzten m Aufdeckungen ist schlechter als das Merken nach Wichtigkeit (Experiment 1): bei kleinem bis mittlerem m um ein Vielfaches (n = 100), bei m = n − 1 noch 6 % (n = 8) bis 35 % (n = 100) darüber. Eine Zahl nur ohne Platz oder ein Platz ohne Nummer wurde nicht gerechnet. | Fenster und Reihenfolge ja, andere Gedächtnisformen nein |
| **Aufteilen nach Nummer mod p mit r Besitzern** | Eine einfache Wahl, kein bestes Protokoll; bei knappem Gedächtnis gut, bei reichlichem schlechter als gemeinsames Merken (Experiment 3). | Für die gewählten Einstellungen |
| **Die Suche nach Protokollen (Experiment 4)** | Nur n ≤ 6, lokale Suche, kein Beweis, dass kein besseres Protokoll existiert; für große n wurde nicht gesucht. | Nur die gezeigten Fälle |
| **Anordnung zufällig, und die Spieler wählen unbekannte Plätze zufällig** | Die Zahlen hängen im Modell nicht von der Anordnung ab (für n = 4 über alle Anordnungen geprüft). Würden die Spieler nach fester Regel aufdecken, etwa von links, könnte ein Muster in der Anordnung eine Rolle spielen. | Nur das Modell; feste Aufdeckregeln nein |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** $n$ Karten mit den Nummern $1, \dots, n$ liegen gleichverteilt zufällig auf $n$ Plätzen. Gesucht ist die Nummer $k$ (zuerst $k = 1$). Eine Aufdeckung kostet 1; trifft sie $k$, wird $k$ um 1 größer, sonst
wird die Karte zurückgedreht. Wer $k$ nicht kennt, deckt einen Platz auf, von dem er nicht weiß, was dort liegt; bei zufälliger Anordnung ist die dort liegende Nummer gleichverteilt unter den Nummern $k, \dots, n$, die er nicht kennt.

**Kein Gedächtnis.** Für jedes $k$ sind $n-k+1$ Nummern gleich wahrscheinlich, die Trefferwahrscheinlichkeit ist $1/(n-k+1)$, im Mittel braucht es $n-k+1$ Aufdeckungen:

$$E_0 = \sum_{k=1}^{n} (n-k+1) = \frac{n(n+1)}{2}$$

**Volles Gedächtnis.** Jede Karte wird einmal offen, wenn ihre Nummer gesucht ist (gezielt oder durch Zufall beim Suchen), das sind $n$ Treffer. Dazu kommt ein Fehlversuch für jede Karte, die beim Suchen nicht genau dann aufgedeckt wird, wenn ihre Nummer gesucht ist. Das Suchen entspricht einem Durchgehen der Plätze in zufälliger Reihenfolge; Karte $k$ wird genau dann beim Suchen getroffen, wenn ihr Platz in dieser Reihenfolge hinter den Plätzen aller Karten $1, \dots, k-1$ liegt (ein Rekord). Im Mittel gibt es $H_n$ Rekorde, also:

$$E_\infty = n + (n - H_n) = 2n - H_n, \qquad H_n = \sum_{i=1}^{n} \frac{1}{i}$$

**Begrenztes Gedächtnis (Markov-Kette).** Der Zustand ist $(k, M)$ mit der Menge $M$ der gemerkten Nummern (höchstens $m$); bei aufgeteiltem Gedächtnis kommen die Mengen aller Spieler und die Nummer des Spielers am Zug hinzu. Mit $U = \{k, \dots, n\} \setminus M$ gilt: Ist $k \in M$, wird $k$ gezielt aufgedeckt, und man geht nach $(k+1, M \setminus \{k\})$. Sonst ist die aufgedeckte Nummer $j$ gleichverteilt auf $U$: $j = k$ führt nach $(k+1, M)$, jedes andere $j$ nach $(k, M \cup \{j\})$, bei mehr als $m$ Einträgen fällt die höchste Nummer weg. Die erwartete Zahl der Schritte bis $k = n+1$ löst das lineare Gleichungssystem

$$(I - P)\,e = \mathbf{1}_{\text{Zustände mit } k \le n}$$

**Literatur.** Die Formeln für $E_0$ und $E_\infty$ sind Lehrbuchwissen (Rekorde in Zufallspermutationen, harmonische Zahlen); keine Quelle im Volltext gelesen.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Teamrätsel: Strategie ohne Verständigung](https://sebastianhanisch.net/konzepte-teamraetsel.html)."
)
