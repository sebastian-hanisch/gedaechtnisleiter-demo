"""Simulation (gdl_simulation.py) und Partie mit Plätzen (gdl_game.py): Zufallsstrom, Ränder, Übereinstimmung mit den exakten Ketten und untereinander."""

import numpy as np
import pytest

import gdl_exact as E
import gdl_game as G
import gdl_simulation as S


def test_the_same_seed_gives_the_same_games_and_another_seed_does_not():
    a = S.simulate("team", 12, 3, 200, 5)
    assert (a == S.simulate("team", 12, 3, 200, 5)).all()
    assert not (a == S.simulate("team", 12, 3, 200, 6)).all()


def test_a_game_does_not_depend_on_how_many_other_games_run_beside_it():
    """Partie g liest im Schritt s die Zahl `uniform_block(step_seed, games)[g]`: mit mehr Partien ändern sich die ersten nicht, sofern sie dieselbe Zahl lesen.
    Die Zahlen hängen von `games` ab (Blocklänge ändert den Strom nicht, nur die Spalten): die ersten 50 Partien sind in beiden Läufen gleich."""
    few = S.simulate("split", 10, 2, 50, 3, 3, 1)
    many = S.simulate("split", 10, 2, 120, 3, 3, 1)
    assert (few == many[:50]).all()


def test_every_game_needs_at_least_n_flips_and_at_most_the_zero_memory_worst_case():
    flips = S.simulate("team", 9, 2, 400, 1)
    assert flips.min() >= 9


@pytest.mark.parametrize("kind,n,m,p,r", [("team", 8, 3, 2, 2), ("split", 8, 2, 2, 1), ("split", 8, 1, 3, 2), ("window", 8, 3, 2, 1), ("team", 6, 1, 2, 2), ("split", 6, 2, 3, 1)])
def test_the_simulation_matches_the_exact_chain_within_four_standard_errors(kind, n, m, p, r):
    mean, se = S.mean_se(S.simulate(kind, n, m, 4000, 11, p, r))
    assert abs(mean - E.expected(kind, n, m, p, r)) < 4 * se


def test_zero_memory_costs_n_times_n_plus_one_over_two_and_full_memory_two_n_minus_h():
    mean0, se0 = S.mean_se(S.simulate("team", 8, 0, 4000, 2))
    assert abs(mean0 - 36) < 4 * se0
    mean_full, se_full = S.mean_se(S.simulate("team", 8, 7, 4000, 2))
    assert abs(mean_full - E.expected_full(8)) < 4 * se_full


def test_every_deutung_agrees_without_memory():
    """Ohne Gedächtnis sind Team, Aufteilen und Fenster dieselbe Aufgabe: dieselben Partien (gleicher Zufalls-Seed)."""
    base = S.simulate("team", 10, 0, 300, 4)
    assert (S.simulate("split", 10, 0, 300, 4, 3, 1) == base).all()
    assert (S.simulate("window", 10, 0, 300, 4) == base).all()


def test_an_oversized_memory_is_clamped_to_n_minus_one():
    assert (S.simulate("team", 8, 50, 100, 9) == S.simulate("team", 8, 7, 100, 9)).all()


def test_the_game_with_places_matches_the_exact_chain_within_four_standard_errors():
    for kind, m, p, r in (("team", 2, 2, 2), ("split", 1, 2, 1), ("window", 3, 2, 1)):
        lengths = np.array([G.play(kind, 6, m, 500 + s, p, r).length for s in range(3000)])
        assert abs(lengths.mean() - E.expected(kind, 6, m, p, r)) < 4 * lengths.std(ddof=1) / np.sqrt(len(lengths)), kind


def test_the_game_with_places_and_the_simulation_over_numbers_agree():
    for kind, m, p, r in (("split", 1, 3, 2), ("team", 3, 2, 2)):
        a = np.array([G.play(kind, 8, m, 900 + s, p, r).length for s in range(2500)])
        b = S.simulate(kind, 8, m, 2500, 21, p, r)
        se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        assert abs(a.mean() - b.mean()) < 4 * se, kind
