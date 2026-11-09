"""Die Partie mit ausgelegten Plätzen (gdl_game.py): Regeln als Invarianten an vielen Partien, eine Partie von Hand."""

import pytest

import gdl_game as G
from gdl_rng import SplitMix64

CASES = [("team", 9, 3, 2, 2), ("split", 9, 2, 3, 1), ("split", 7, 1, 4, 2), ("window", 8, 3, 2, 1), ("team", 6, 0, 3, 3), ("split", 10, 9, 2, 1)]


def test_the_layout_is_a_permutation_of_the_numbers():
    for seed in range(20):
        assert sorted(G.layout_for(12, SplitMix64(seed))) == list(range(1, 13))


@pytest.mark.parametrize("kind,n,m,p,r", CASES)
def test_rules_hold_in_every_game(kind, n, m, p, r):
    for seed in range(60):
        game = G.play(kind, n, m, seed, p, r)
        hits = [f.number for f in game.flips if f.hit]
        assert hits == list(range(1, n + 1))                                    # die Nummern werden der Reihe nach offen
        assert game.length >= n
        assert game.flips[-1].hit
        opened = set()
        for f in game.flips:
            assert f.number == game.layout[f.position]
            assert f.position not in opened                                     # offene Karten werden nicht mehr aufgedeckt
            assert f.player == (f.step - 1) % p                                 # reihum
            assert f.hit == (f.number == f.needed)
            if f.targeted:
                assert f.hit                                                    # wer den Platz von k kennt, trifft
            if f.hit:
                opened.add(f.position)
        if m == 0 or (kind == "window" and m == 0):
            assert not any(f.targeted for f in game.flips)                      # ohne Gedächtnis nie gezielt
        if kind in ("team", "split"):
            for f in game.flips:
                assert all(len(mem) <= m for mem in f.memory)                   # nie mehr als m gemerkt


def test_with_full_memory_a_card_seen_before_is_flipped_exactly_when_it_is_needed():
    """Alle merken alles (m = n − 1, Team): eine Karte, die einmal als Fehlversuch aufgedeckt wurde, wird danach nur noch gezielt aufgedeckt."""
    for seed in range(40):
        game = G.play("team", 8, 7, seed, 2, 2)
        seen = set()
        for f in game.flips:
            if not f.hit:
                seen.add(f.number)
            elif f.number in seen:
                assert f.targeted
            else:
                assert not f.targeted


def test_the_same_seed_gives_the_same_game():
    assert G.play("split", 8, 2, 4, 3, 1) == G.play("split", 8, 2, 4, 3, 1)
    assert G.play("split", 8, 2, 4, 3, 1) != G.play("split", 8, 2, 5, 3, 1)


def test_state_at_follows_the_flips():
    game = G.play("team", 6, 2, 3, 2, 2)
    assert G.state_at(game, 0)["needed"] == 1 and G.state_at(game, 0)["next_player"] == 0 and G.state_at(game, 0)["last"] is None
    for step in range(1, game.length + 1):
        state = G.state_at(game, step)
        hits = sum(1 for f in game.flips[:step] if f.hit)
        assert state["needed"] == hits + 1
        assert state["next_player"] == step % 2
        assert state["last"] is game.flips[step - 1]
    assert G.state_at(game, game.length)["done"] and not G.state_at(game, game.length - 1)["done"]


def test_one_game_by_hand_with_one_player_pair_and_two_cards():
    """n = 2: Anordnung (2, 1) heißt Platz 0 trägt die 2. Die erste Aufdeckung ist entweder Platz 0 (Fehlversuch, dann wird Platz 1 gesucht) oder Platz 1 (Treffer).
    Mit m = 1 und einem Team: nach dem Fehlversuch merkt das Team die 2, danach 1 aufdecken (Treffer), dann die gemerkte 2 gezielt: 3 Aufdeckungen."""
    for seed in range(200):
        game = G.play("team", 2, 1, seed, 2, 2)
        if game.layout == (2, 1):
            first = game.flips[0]
            if first.position == 0:
                assert [f.hit for f in game.flips] == [False, True, True] and [f.targeted for f in game.flips] == [False, False, True]
            else:
                assert [f.hit for f in game.flips] == [True, True] and not any(f.targeted for f in game.flips)
