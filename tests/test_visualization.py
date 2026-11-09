"""Abbildungen: Aufbau der Kurven (Ränder als Spuren, Achsenart) und des Rasters."""

import pytest

import gdl_exact as E
import gdl_visualization as VZ


def _rows(n):
    return [{"m": 0, "a": float(E.expected_none(n)), "a_se": 0.0}, {"m": 1, "a": E.expected_none(n) * 0.6, "a_se": 2.0}, {"m": n - 1, "a": E.expected_full(n), "a_se": 0.0}]


def test_the_curves_carry_the_edges_as_traces_and_no_shapes():
    """Formen und Beschriftungen auf einer logarithmischen Achse brauchen den Zehnerlogarithmus: add_hline zog die Achse bei n = 100 bis 10^194 auf. Die Ränder sind deshalb Spuren."""
    fig = VZ.build_curves(100, _rows(100), [("a", "Reihe", "#000000")])
    assert len(fig.data) == 3 and not fig.layout.shapes and not fig.layout.annotations
    assert list(fig.data[1].y) == [5050, 5050] and fig.data[2].y[0] == pytest.approx(E.expected_full(100))
    assert list(fig.data[1].x) == [0, 99]
    assert fig.layout.yaxis.type == "log" and fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_the_axis_is_linear_up_to_n_30_and_log_above():
    assert VZ.build_curves(30, _rows(30), [("a", "Reihe", "#000")]).layout.yaxis.type == "linear"
    assert VZ.build_curves(31, _rows(31), [("a", "Reihe", "#000")]).layout.yaxis.type == "log"


def test_error_bars_only_where_there_is_a_standard_error():
    exact = VZ.build_curves(8, [{"m": 0, "a": 36.0}, {"m": 1, "a": 24.0}], [("a", "Reihe", "#000")])
    assert exact.data[0].error_y.visible is False
    noisy = VZ.build_curves(8, _rows(8), [("a", "Reihe", "#000")])
    assert noisy.data[0].error_y.visible is True and list(noisy.data[0].error_y.array) == [0.0, 2.0, 0.0]


def test_the_grid_shows_open_cards_the_last_flip_and_hides_the_rest():
    layout = (3, 1, 2, 5, 4)
    fig = VZ.build_grid(layout, opened={1}, last_position=3)
    z = fig.data[0].z
    assert VZ.grid_shape(5) == (2, 3)
    assert [z[0][0], z[0][1], z[0][2], z[1][0], z[1][1]] == [0, 1, 0, 2, 0] and z[1][2] is None
    labels = {(a.x, a.y): a.text for a in fig.layout.annotations}
    assert labels == {(1, 0): "1", (0, 1): "5"}                                           # offene und eben aufgedeckte Karte mit Nummer, verdeckte ohne
    assert len(VZ.build_grid(layout, set(), None, show_all=True).layout.annotations) == 5
