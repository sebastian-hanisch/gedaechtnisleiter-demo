"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 4, 100, 8                # Zahl der Karten
P_MIN, P_MAX, DEFAULT_P = 2, 4, 2                  # Zahl der Spieler am Tisch
R_MIN, R_MAX, DEFAULT_R = 1, 4, 2                  # Besitzer je Karte; wirksam ist min(r, p), r = p heißt: alle merken dasselbe
M_MIN, M_MAX, DEFAULT_M = 0, 99, 3                 # Gedächtnis in Paaren Nummer -> Platz; wirksam ist min(m, n - 1), die Obergrenze des Reglers folgt n
GAMES_MIN, GAMES_MAX, DEFAULT_GAMES, GAMES_STEP = 100, 2000, 300, 100   # simulierte Partien je Zelle
SEED_MAX, DEFAULT_SEED = 999999, 7

EXACT_N_MAX = 8                                    # bis hierher rechnet die App die Erwartung exakt (Markov-Kette), darüber nur per Simulation
GAME_VIEW_N_MAX = 30                               # bis hierher zeigt die App eine Partie Zug für Zug (Raster)
SEARCH_CASES = ((6, 1, 2), (6, 2, 2))                # (n, m, p) der Protokollsuche, die die App live rechnet (3 bis 20 Sekunden)
CURVE_MS_LARGE = (0, 1, 2, 3, 5, 8, 12, 20, 30, 40, 50, 75)   # Gitter über m für n > EXACT_N_MAX (dazu n - 1)

COLOR_OPEN = "#2F6B65"
COLOR_FLIP = "#E1A23B"
COLOR_HIDDEN = "rgba(150,150,150,0.45)"
COLOR_TEAM = "#4c78a8"
COLOR_SPLIT = "#d1495b"
COLOR_WINDOW = "#8d7b68"
COLOR_BOUND = "rgba(120,120,120,0.9)"

PRESETS = {
    "Standardtisch (n = 8, alle merken dasselbe)": {"n": DEFAULT_N, "p": 2, "r": 2, "m": 3, "games": DEFAULT_GAMES, "seed": DEFAULT_SEED},
    "Nichts merken (m = 0)": {"n": DEFAULT_N, "p": 2, "r": 2, "m": 0, "games": DEFAULT_GAMES, "seed": DEFAULT_SEED},
    "Alles merken (m = n − 1)": {"n": DEFAULT_N, "p": 2, "r": 2, "m": DEFAULT_N - 1, "games": DEFAULT_GAMES, "seed": DEFAULT_SEED},
    "Teilen lohnt (n = 100, 4 Spieler, m = 5)": {"n": 100, "p": 4, "r": 1, "m": 5, "games": DEFAULT_GAMES, "seed": DEFAULT_SEED},
    "Kreuzung (n = 100, 2 Spieler, m = 40)": {"n": 100, "p": 2, "r": 1, "m": 40, "games": DEFAULT_GAMES, "seed": DEFAULT_SEED},
    "Teilen stagniert (n = 100, 4 Spieler, m = 75)": {"n": 100, "p": 4, "r": 1, "m": 75, "games": DEFAULT_GAMES, "seed": DEFAULT_SEED},
    "Zwischenstufe (n = 100, 3 Spieler, r = 2, m = 40)": {"n": 100, "p": 3, "r": 2, "m": 40, "games": DEFAULT_GAMES, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Standardtisch (n = 8, alle merken dasselbe)": "8 Karten, 2 Spieler, jeder merkt dieselben 3 Paare (die kleinsten Nummern). Dafür rechnet die App die Erwartung exakt.",
    "Nichts merken (m = 0)": "Niemand merkt sich eine aufgedeckte Karte: n(n+1)/2 Aufdeckungen im Mittel, bei 8 Karten 36.",
    "Alles merken (m = n − 1)": "Alle merken alles, was sie sehen: 2n − H(n) Aufdeckungen im Mittel, bei 8 Karten 13,28. Die Grenze nach unten.",
    "Teilen lohnt (n = 100, 4 Spieler, m = 5)": "100 Karten, 4 Spieler, jeder merkt 5 Paare, und jede Karte merkt nur einer (nach Nummer mod 4): so merkt das Team insgesamt bis zu 20 Paare. Simulation.",
    "Kreuzung (n = 100, 2 Spieler, m = 40)": "Bei 2 Spielern, 100 Karten und 40 Paaren je Spieler liegen Aufteilen und gemeinsames Merken gleichauf (Messung dieser Demo mit 800 Partien: 371 gegen 372). Bei 3 oder 4 Spielern kreuzen sie sich früher. Simulation.",
    "Teilen stagniert (n = 100, 4 Spieler, m = 75)": "Wer 75 Paare merken kann, gewinnt nicht mehr durch Aufteilen: ab 25 Paaren wird nie mehr vergessen, und Aufteilen bleibt schlechter als gemeinsames Merken; vermutlich liegt das Wissen beim Zuständigen, der nicht immer dran ist (Deutung, nicht gemessen). Simulation.",
    "Zwischenstufe (n = 100, 3 Spieler, r = 2, m = 40)": "Jede Karte merken zwei der drei Spieler: zwischen Aufteilen (r = 1) und gemeinsamem Merken (r = 3). Simulation.",
}
