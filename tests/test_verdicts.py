"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Schwelle und jede Zahl im Text steht hier."""

import gdl_evaluation as ev


def test_de_formats_with_decimal_comma_and_thousands_dots():
    assert ev.de(13.28, 2) == "13,28" and ev.de(5050, 0) == "5.050" and ev.de(3181.858, 1) == "3.181,9" and ev.de(0.5, 1) == "0,5"
    assert ev.de_auto(23.7928) == "23,8" and ev.de_auto(999.94) == "999,9" and ev.de_auto(1000.4) == "1.000" and ev.de_auto(3181.858) == "3.182"


def test_main_without_memory_is_a_warning_with_the_edge_value():
    kind, text = ev.verdict_main(8, 0, 36.0, 0.0, 36, 13.28)
    assert kind == "warning" and "**36** Aufdeckungen, n(n+1)/2 bei n = 8" in text


def test_main_with_full_memory_is_a_success_with_the_edge_value():
    kind, text = ev.verdict_main(8, 7, 13.3, 0.1, 36, 13.28)
    assert kind == "success" and "m = n − 1 = 7" in text and "**13,28**" in text and "2n − H(n) bei n = 8" in text
    assert ev.verdict_main(8, 9, 13.3, 0.1, 36, 13.28)[0] == "success"                  # m über n − 1 gilt wie n − 1


def test_main_team_names_mean_se_and_share_of_the_way():
    kind, text = ev.verdict_main(8, 3, 16.6, 0.3, 36, 13.28)                            # (36 − 16,6) / (36 − 13,28) = 85,4 %
    assert kind == "info"
    assert "n = 8 und m = 3 Paaren" in text and "**16,6**" in text and "(± 0,3 Standardfehler)" in text and "85 % des Wegs von 36 ohne Gedächtnis bis 13,3" in text


def test_main_split_better_is_a_success_above_two_standard_errors_of_the_difference():
    # se_diff = sqrt(0,5² + 0,5²) = 0,7071; zwei Standardfehler = 1,414
    kind, text = ev.verdict_main(8, 3, 18.5, 0.5, 36, 13.28, 20.0, 0.5, 3, 1)           # Differenz 1,5 > 1,414
    assert kind == "success"
    assert "Jede Karte merken nur 1 von 3 Spielern" in text and "spart **1,5** gegenüber gemeinsamem Merken (20,0)" in text and "also 8 % von dessen Aufdeckungen" in text
    assert ev.verdict_main(8, 3, 18.6, 0.5, 36, 13.28, 20.0, 0.5, 3, 1)[0] == "info"   # Differenz 1,4 < 1,414


def test_main_split_worse_is_a_warning():
    kind, text = ev.verdict_main(8, 3, 22.0, 0.5, 36, 13.28, 20.0, 0.5, 3, 2)           # Differenz −2,0
    assert kind == "warning" and "kostet **2,0** mehr als gemeinsames Merken (20,0)" in text and "jede Karte merken 2 von 3 Spielern" in text
    assert "vermutlich liegt das Wissen beim Zuständigen" in text and "(Deutung, nicht gemessen)" in text
    assert ev.verdict_main(8, 3, 21.4, 0.5, 36, 13.28, 20.0, 0.5, 3, 2)[0] == "info"   # Differenz −1,4


def test_main_split_equal_names_difference_and_two_standard_errors():
    kind, text = ev.verdict_main(8, 3, 20.5, 0.5, 36, 13.28, 20.0, 0.5, 3, 1)
    assert kind == "info" and "unterscheiden sich um 0,5, weniger als zwei Standardfehler (1,4)" in text and "kein Unterschied erkennbar" in text


def _ladder(window_worse=True):
    return [
        {"m": 0, "team": 36.0, "window": 36.0},
        {"m": 1, "team": 24.0, "window": 30.0 if window_worse else 20.0},
        {"m": 2, "team": 19.0, "window": 25.0 if window_worse else 18.0},
    ]


def test_ladder_names_the_first_pair_and_the_widest_window_gap():
    kind, text = ev.verdict_ladder(8, _ladder())
    assert kind == "info"
    assert "Das erste gemerkte Paar spart 33 % (36,0 → 24,0)" in text                    # (36 − 24) / 36
    assert "in 2 von 2 Zellen über dem Team, am weitesten bei m = 2 (25,0 gegen 19,0, 32 % darüber)" in text      # 6/19 = 31,6 % gegen 6/24 = 25 %
    assert "in keiner Zelle über dem Team" in ev.verdict_ladder(8, _ladder(False))[1]
    assert "(5.050 → 3.182)" in ev.verdict_ladder(100, [{"m": 0, "team": 5050.0, "window": 5050.0}, {"m": 1, "team": 3181.858, "window": 4927.4}])[1]


def _share(rows):
    return [{"m": m, "team": t, "r1": s, "team_se": 0.0, "r1_se": 0.0} for m, t, s in rows]


def test_crossing_uses_a_tolerance_of_two_standard_errors_of_the_difference():
    rows = _share([(1, 10.0, 8.0), (2, 9.0, 8.5), (3, 8.0, 8.2), (4, 7.5, 8.5)])
    assert ev.crossing(rows) == (2, 3)                                                  # m = 3: 8,0 gegen 8,2, Team besser oder gleich
    assert ev.crossing(_share([(1, 10.0, 9.995), (2, 9.0, 9.0)])) == (None, 1)           # Unterschied 0,005 < 0,01: gleichauf
    noisy = [{"m": 1, "team": 10.0, "r1": 9.0, "team_se": 0.6, "r1_se": 0.6}]           # Differenz 1,0 < 2 · 0,85 = 1,7: nicht deutlich
    assert ev.crossing(noisy) == (None, 1)
    clear = [{"m": 1, "team": 10.0, "r1": 8.0, "team_se": 0.6, "r1_se": 0.6}]           # Differenz 2,0 > 1,7: deutlich
    assert ev.crossing(clear) == (1, None)


def test_share_verdict_names_the_crossing_and_the_plateau():
    rows = _share([(1, 10.0, 8.0), (2, 9.0, 8.5), (3, 8.0, 8.2), (4, 7.5, 8.5)])
    kind, text = ev.verdict_share(10, 3, rows)
    assert kind == "info"
    assert "n = 10 und 3 Spielern ist Aufteilen bis m = 2 deutlich besser" in text and "ab m = 3 ist das Team besser oder gleichauf" in text
    assert "die Kreuzung liegt auf dem Gitter zwischen diesen Werten" in text and "%" not in text.split("Kreuzung")[1].split(".")[0] and "bleibt Aufteilen bei 8,5" in text and "gemeinsam sind es 7,5" in text
    assert "in keiner Zelle des Gitters deutlich besser" in ev.verdict_share(10, 3, _share([(1, 5.0, 6.0), (2, 4.0, 5.0)]))[1]
    assert "in jeder Zelle bis m = 2 deutlich besser" in ev.verdict_share(10, 3, _share([(1, 5.0, 3.0), (2, 4.0, 2.0)]))[1]


def test_forget_verdict_counts_optimal_cells_and_the_worst_alternative():
    rows = [{"m": 1, "max": 5.0, "min": 6.5, "opt": 5.0}, {"m": 2, "max": 4.0, "min": 4.25, "opt": 4.0}]
    kind, text = ev.verdict_forget(rows)
    assert kind == "success" and "in 2 von 2 Zellen so gut wie" in text and "bis zu 1,5 mehr (bei m = 1: 6,5 gegen 5,0)" in text
    kind, text = ev.verdict_forget([{"m": 1, "max": 5.2, "min": 6.5, "opt": 5.0}, {"m": 2, "max": 4.0, "min": 4.25, "opt": 4.0}])
    assert kind == "warning" and "in 1 von 2 Zellen" in text


def test_search_verdict_names_gain_bound_and_sharing():
    kind, text = ev.verdict_search(6, 1, 2, 14.2125, 13.9724, 13.6261, 11.7028, False)
    assert kind == "info"
    assert "n = 6, m = 1, 2 Spieler" in text and "**13,63**" in text and "beste einfache Regel 13,97" in text and "(gemeinsam 14,21, aufgeteilt 13,97)" in text
    assert "2,5 % weniger" in text and "mit 2 Paaren) 11,70" in text and "kommt kein Aufdecken eigener Karten zur Mitteilung vor" in text
    assert "kommt ein Aufdecken eigener Karten zur Mitteilung vor" in ev.verdict_search(6, 1, 2, 14.0, 13.0, 12.0, 11.0, True)[1]
    assert "beste einfache Regel 14,00" in ev.verdict_search(6, 1, 2, 14.0, 15.0, 12.0, 11.0, False)[1]      # die kleinere der beiden Regeln


def test_main_with_full_memory_and_split_does_not_claim_the_full_memory_value():
    """Bei m = n − 1 und Aufteilen bleibt der Wert auf dem Plateau (n = 8, p = 2, r = 1: 17,81 gegen 13,28); der Satz „alle merken alles“ gilt nur fürs Team."""
    kind, text = ev.verdict_main(8, 7, 17.9, 0.1, 36, 13.28, 13.3, 0.1, 2, 1)
    assert kind == "warning"
    assert "bleibt Aufteilen (jede Karte merken 1 von 2 Spielern) bei **17,9** Aufdeckungen (± 0,1 Standardfehler)" in text
    assert "gemeinsames Merken käme auf 13,28 (2n − H(n) bei n = 8)" in text and "nicht am Gedächtnis" in text
    assert "merken sich alle alles" not in text
    kind, text = ev.verdict_main(8, 7, 13.4, 0.1, 36, 13.28, 13.3, 0.1, 3, 2)           # Differenz 0,12 < 0,2 (zwei Standardfehler): nicht zu unterscheiden
    assert kind == "info" and "nicht zu unterscheiden" in text and "**13,4**" in text
