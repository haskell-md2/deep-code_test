import statistics
import pytest

from app.services.analytics import _compute_stats


def test_compute_stats_normal():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    stats = _compute_stats(values)
    assert stats.min == 1.0
    assert stats.max == 5.0
    assert stats.count == 5
    assert stats.sum == 15.0
    assert stats.median == 3.0


def test_compute_stats_empty():
    stats = _compute_stats([])
    assert stats.min is None
    assert stats.max is None
    assert stats.count == 0
    assert stats.sum is None
    assert stats.median is None


def test_compute_stats_single():
    stats = _compute_stats([42.0])
    assert stats.min == 42.0
    assert stats.max == 42.0
    assert stats.count == 1
    assert stats.sum == 42.0
    assert stats.median == 42.0


def test_compute_stats_negative():
    values = [-5.0, -3.0, 0.0, 3.0, 5.0]
    stats = _compute_stats(values)
    assert stats.min == -5.0
    assert stats.max == 5.0
    assert stats.sum == 0.0
    assert stats.median == 0.0


def test_compute_stats_even_count():
    values = [1.0, 2.0, 3.0, 4.0]
    stats = _compute_stats(values)
    assert stats.median == statistics.median(values)  # 2.5
