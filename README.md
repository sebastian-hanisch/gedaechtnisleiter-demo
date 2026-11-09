# Gedächtnisleiter: Wie viel Merken braucht ein Team? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-gedaechtnisleiter-demo.streamlit.app/)**

Teil der Linie **Teamrätsel: Strategie ohne Verständigung** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Ein Team hat **ein gemeinsames Ziel**, legt vorher eine Strategie fest und handelt dann mit **beschränkter Information**; hier ist die beschränkte Größe das **Gedächtnis**. Schwesterstücke: `informationsleiter-demo` (Leiter über das Wissen, hier über das Gedächtnis) und `gluehbirne-demo` (dort ist der Schalter ein Gedächtnis von einem Bit; in beiden Demos kommt die harmonische Zahl H(n) vor).

## Warum dieses Problem

*Nummerierte Karten liegen verdeckt und zufällig auf einem Raster. Reihum deckt jeder eine Karte auf. Ist es die nächste Nummer (zuerst die 1), bleibt sie offen, sonst wird sie zurückgedreht. Alle sehen jede Aufdeckung, reden oder zeigen darf niemand.* Die Aufgabe stammt aus einem Seminar. Mit perfektem Gedächtnis ist sie fast trivial: wer die gesuchte Nummer kennt, deckt sie auf, sonst wird erkundet. Die Frage der Demo ist, **wie viel das Team verliert, wenn es sich nur begrenzt viele aufgedeckte Karten merken kann**, und ob es sich lohnt, das Gedächtnis auf die Spieler **aufzuteilen**, wenn niemand reden darf.

## Modell

Voraussetzungen, wo nichts anderes steht: **n Karten**, die Nummern 1 bis n gleichverteilt zufällig auf n Plätzen; **p Spieler** reihum; jede Aufdeckung kostet 1; **alle sehen jede Aufdeckung** und passen perfekt auf, niemand macht Fehler; **kein Reden, Zeigen oder Zeichen** außer den Aufdeckungen selbst.

- **Wer k kennt**, deckt genau diese Karte auf (sicherer Treffer). **Sonst** deckt er einen zufälligen Platz auf, von dem er nicht weiß, was dort liegt; die dort liegende Nummer ist gleichverteilt unter den Nummern ab k, die er nicht kennt.
- **Gedächtnis m:** höchstens m Paare „Nummer → Platz“, beim Überlauf fällt die **höchste Nummer zuerst** weg (sie wird am spätesten gebraucht). Aufgedeckte Karten, die offen bleiben, sind frei sichtbar.
- **Wer merkt was (r von p Spielern je Karte):** *alle dasselbe* (r = p, „Team“) oder *aufgeteilt* (r = 1: Besitzer der Nummer j ist der Spieler mit Index j mod p, Index ab 0, in der App „Spieler 1“ = Index 0; r = 2 bei p ≥ 3 als Zwischenstufe). Wer die Karte nicht merkt, kennt sie nicht.
- **Fenster:** das Team merkt die letzten m Aufdeckungen (statt nach Wichtigkeit zu vergessen, nach Zeit).
- **Kein Gedächtnis:** n(n+1)/2 Aufdeckungen im Mittel; **volles Gedächtnis (m = n − 1):** 2n − H(n), H(n) die harmonische Zahl.

Formeln stehen im Expander „📐 Mathematische Formulierung“ der App. Bekannt sind die beiden Ränder (Lehrbuchwissen, keine Quelle im Volltext gelesen); die Deutungen, die Aufteilungsregel und alle Messungen sind eigene Fassung. Dass „höchste Nummer zuerst“ optimal ist, ist hier für die gemessenen n gerechnet, nicht allgemein bewiesen.

## Methodik

- **Exakt (n ≤ 8):** Markov-Ketten über (gesuchte Nummer, gemerkte Nummern, wer dran ist) in `gdl_exact.py`, gelöst als lineares Gleichungssystem; das optimale Vergessen per Wertiteration.
- **Simulation:** `gdl_simulation.py` spielt viele Partien nebeneinander über Nummern statt Plätze; `gdl_game.py` spielt eine Partie mit ausgelegten Plätzen (für die Zugansicht). Zufall: SplitMix64 (feste Zufalls-Seeds), alle Deutungen mit demselben Zufalls-Seed lesen dieselben Zufallszahlen.
- **Protokollsuche (Experiment 4):** jeder Spieler entscheidet nur aus eigenem Gedächtnis und öffentlichen Angaben; Suchraum ist die Entscheidungstabelle (zufälligen unbekannten Platz aufdecken oder eine selbst gemerkte Karte aufdecken; was nach einem Fehlversuch gemerkt wird). Koordinatenabstieg über die Entscheidungen mit Gewicht, jede Tabelle exakt bewertet. Lokale Suche, kein Beweis für ein Optimum.

## Befunde (gemessen, keine Behauptungen)

Exakte Zahlen sind Markov-Ketten (n ≤ 8). Zahlen für n = 100 sind **Messungen dieser Demo** mit Zufalls-Seed 7 und 800 Partien je Zelle (Mittel ± Standardfehler); `tests/test_claims.py` rechnet sie neu und vergleicht auf die genannte Stelle.

| Frage | Befund | Beleg |
|---|---|---|
| Ränder | n = 8: kein Gedächtnis **36**, volles Gedächtnis **13,28**; n = 100: **5.050** und **194,81** | `test_claim_edges` |
| Was bringt das erste gemerkte Paar? (n = 8, Team) | 36 → **23,79**, also **34 %** weniger; Team m = 1 bis 7: 23,79 / 19,09 / 16,58 / 14,93 / 13,90 / 13,41 / 13,28 | `test_claim_team_ladder_n8` |
| Dasselbe bei n = 100 (Messung, Team) | m = 1: **3.182** ± 14 (37 % weniger als 5.050); m = 5: 1.538 ± 9; m = 40: 372 ± 2; m = 50: 323 ± 2 | `test_claim_team_n100` |
| Ist „höchste Nummer zuerst vergessen“ optimal? | Ja für alle gerechneten Zellen: n = 3 bis 8, jedes m (Wertiteration); „kleinste zuerst“ kostet bei n = 8 bis zu **5,2** mehr (m = 1: 29,0 gegen 23,8) | `test_claim_forgetting`, Orakel-Test |
| Fenster der letzten m Aufdeckungen (n = 8, exakt) | m = 1: **30,72** (Team 23,79); m = 7: 14,11 (Team 13,28); in **7 von 7** Zellen über dem Team | `test_claim_window_n8` |
| Fenster bei n = 100 (Messung) | m = 1: **4.927** ± 20 gegen 5.050 ohne Gedächtnis; m = 30: 1.755 ± 11 gegen 468 ± 3 für das Team; m = 99: 263 ± 0,4 gegen 194,8 (35 % darüber) | `test_claim_window_n100` |
| Aufteilen bei n = 8, p = 2 (exakt) | m = 1: **22,56** (Team 23,79); m = 2: 19,08 gegen 19,09 (gleichauf); m = 3: 17,93 gegen 16,58; **ab m = 4 bleibt es bei 17,81**. p = 3: m = 1 22,11, dann **19,69** ab m = 3 | `test_claim_split_n8` |
| Aufteilen bei n = 100, p = 4, r = 1 (Messung) | m = 1: **1.919** ± 10 gegen 3.182 (40 % weniger als das Team); m = 5: 821 ± 5 gegen 1.538 (47 % weniger); m = 30: 440 ± 3 gegen 468 (etwa 6 % weniger, bei anderen Zufalls-Seeds 4,6 bis 6,1 %); m = 40: 440 ± 3 gegen 372 (**18 % mehr**) | `test_claim_split_n100` |
| Warum hört das Aufteilen auf zu helfen? | Bei r = 1 hat jeder Besitzer höchstens ⌈n/p⌉ Nummern zu merken (n = 100, p = 4: 25); ab dort wird nie mehr vergessen, und mehr Gedächtnis ändert die Partien nicht: die Partien für m = 25, 30, 40, 75 und 99 sind **identisch** (gleicher Zufalls-Seed; geprüft nur für n = 100, p = 4) | `test_claim_split_plateau_is_where_nothing_is_forgotten` |
| Gibt es ein besseres Protokoll? (Experiment 4) | Für n = 6, m = 1, 2 Spieler: bestes gefundenes **13,63** gegen 13,97 (aufgeteilt) und 14,21 (gemeinsam), also **2,5 %** weniger als die beste einfache Regel (hier aufgeteilt); untere Schranke (gemeinsames Gedächtnis mit 2 Paaren) 11,70. n = 6, m = 2: 11,41 gegen 11,70 (hier ist gemeinsam die beste einfache Regel, aufgeteilt 12,49), ebenfalls 2,5 % weniger, Schranke 9,72. In beiden Fällen liegt das gefundene Protokoll nicht unter der Schranke (bewiesen ist das nicht). Im besten gefundenen Protokoll kommt kein Aufdecken eigener Karten zur Mitteilung vor; die Suche startet nur von Regeln ohne Mitteilung, ein Beweis, dass Zeichen nie helfen, ist das nicht | `test_search.py` |

Jede Zahl der Tabelle steht in dem genannten Test; Zahlen aus der Vormessung zum Plan (`teamraetsel-planung/vormessung/`, andere n und andere Zufallsströme) stehen nicht in dieser README.

## Ehrliche Grenzen

- **Nur das Modell oben.** Perfekte Aufmerksamkeit, kein Reden, zufällige Anordnung; mit Reden wäre es leichter, mit Fehlern ein anderes Modell. Zeichen über die Wahl der Aufdeckung (sie kostet einen Versuch) sind im Modell zugelassen, aber nur in Experiment 4 untersucht: im besten gefundenen Protokoll der gezeigten kleinen Fälle kommen sie nicht vor, die Suche startet aber nur von Regeln ohne Mitteilung.
- **Die Aufteilung nach Nummer mod p ist eine einfache Regel**, kein bestes Protokoll. Die Protokollsuche ist **lokal** (kein Beweis, dass kein besseres existiert) und nur für n ≤ 6 live in der App; für n = 100 wurde nicht gesucht.
- **Gemessen** sind n = 8 (exakt) und n = 100 (Simulation, ein Zufalls-Seed, 800 Partien); Zahlen dazwischen oder für mehr als 4 Spieler stehen nicht in dieser README. Die Kurven der App für n ≥ 9 sind Simulationen mit der gewählten Zahl von Partien.
- **Gedächtnis als „Paare Nummer → Platz“.** Eine Zahl ohne Platz oder ein Platz ohne Nummer wurde nicht gerechnet.
- **Ursachen** wie „das Wissen liegt beim Zuständigen, der nicht immer dran ist“ sind Deutungen der Messung, nicht eigens gemessen (der Befund zum Plateau, `test_claim_split_plateau_is_where_nothing_is_forgotten`, stützt nur, dass Vergessen dort keine Rolle mehr spielt).

## Verifikation

- **Orakel:** `tests/test_oracle_gedaechtnisleiter.py` rechnet die Ketten über **ausgelegte Plätze** für alle n! Anordnungen (Team: n = 2 bis 4 alle m, n = 5 mit m = 1 bis 3, n = 6 mit m = 2; Aufteilen: n = 3 und 4 alle m für p = 2, 3, n = 5 mit m = 1, 2, n = 6 mit m = 1; Fenster: n = 3 und 4 alle m, n = 5 mit m = 1) und vergleicht auf 1e-9; dazu die Ränder in Bruchrechnung und eine Zählung der Rekorde.
- **Simulation:** gegen die exakten Ketten innerhalb von vier Standardfehlern (sechs Zellen), Zufallsstrom reproduzierbar, die Partie mit Plätzen und die Simulation über Nummern stimmen statistisch überein (`tests/test_simulation.py`).
- **Regeln der Partie:** Invarianten an je 60 Partien in sechs Einstellungen (`tests/test_game.py`).
- **Verdikte:** reine Funktionen, die Schwellen und die Zahlen im Text an handgesetzten Werten (`tests/test_verdicts.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button außer den ▶-Knöpfen, jeder Regler am Minimum und Maximum; die ▶-Knöpfe der Experimente und der Protokollsuche haben eigene Tests in `tests/test_app_experimente.py`), Footer-Test, Layout-Test (Schnellstart oben, fester Kopf, aktives Preset hervorgehoben, jeder Regler hebt die Markierung auf).
- Frühere Erfahrung beim Bau: im ersten Lauf wich das Fenster-Orakel von den Ketten ab; der Fehler lag im Orakel (Treffer auf einer bekannten Karte rückte das Fenster nicht weiter), nicht im Code.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Ergebnis, Kernfrage, Partie Zug für Zug, vier Experimente, Grenzen, Formeln |
| `gdl_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Schnellstart-Szenarien |
| `gdl_exact.py` | Exakte Erwartung (Markov-Ketten, Wertiteration) |
| `gdl_simulation.py` | Simulation vieler Partien nebeneinander (numpy) |
| `gdl_game.py` | Eine Partie mit ausgelegten Plätzen, Zug für Zug |
| `gdl_search.py` | Suche nach besseren verteilten Protokollen (lokal, exakt bewertet) |
| `gdl_evaluation.py` | Kennzahlen, Kurven über m, Verdikte als reine Funktionen |
| `gdl_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `gdl_presets.py` | Permalink (Begrenzen), Schnellstart in der Seitenleiste, Zufalls-Seed-Button |
| `gdl_layout.py` | Fester Kopf (Stylesheet) |
| `gdl_rng.py` | SplitMix64, wörtliche Kopie aus `ab-test-demo/abt_rng.py` |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Orakel, Simulation, Partie, Suche, Kennzahlen, Verdikte, Abbildungen, Befunde der README, Schnellstart, Layout, Oberfläche, Footer, Laufzeit-Importe, Randfälle |

## Bewusst nicht umgesetzt

- **Memory mit Paaren** (zwei gleiche Karten aufdecken): eine andere Aufgabe.
- **Gedächtnis in Bits** statt Paaren und **Fehler der Spieler**: nicht gerechnet.
- **Protokollsuche für große n:** nicht gemacht; der Regler r (r Besitzer je Karte) und Experiment 3 zeigen die Zwischenstufe, ihre Befunde stehen aber nur in der Vormessung zum Plan, nicht in dieser README.
- **PDF-Export:** nicht vorhanden.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Teamrätsel: Strategie ohne Verständigung](https://sebastianhanisch.net/konzepte-teamraetsel.html).
