"""Regression tests for percentile statistics on the monitoring dashboard.

Small samples must report true interpolated percentiles (previously p50/p95
collapsed onto the minimum, so latency alerts never fired), the result must
stay within [min, max], and a fraction passed outside [0, 1] must raise
instead of crashing with an IndexError.
"""
import math

import pytest

from aegisrover.analysis.metrics import MetricSeries, Registry
from aegisrover.analysis.observability import percentile, summary
from aegisrover.runtime.diagnostics import latency_budget


def reference_percentile(values, p):
    """Independent CPS linear-interpolation reference."""
    xs = sorted(map(float, values))
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    rank = p * (len(xs) - 1)
    low = math.floor(rank)
    if low == len(xs) - 1:
        return xs[-1]
    return xs[low] + (xs[low + 1] - xs[low]) * (rank - low)


def test_metric_series_small_sample_shows_real_percentiles():
    series = MetricSeries('latency')
    for value in (10, 20, 30, 40, 50):
        series.observe(value)
    result = series.summary()
    assert result['count'] == 5
    assert result['p50'] == 30.0
    assert result['p95'] == pytest.approx(48.0)
    assert result['p99'] == pytest.approx(49.6)
    # tail latency must be visible so threshold alerts can fire
    assert result['p95'] > result['min']


def test_metric_series_single_sample():
    series = MetricSeries('latency')
    series.observe(42)
    result = series.summary()
    assert result['p50'] == result['p95'] == result['p99'] == 42.0


def test_metric_series_two_samples_interpolate():
    series = MetricSeries('latency')
    series.observe(10)
    series.observe(20)
    result = series.summary()
    assert result['p50'] == pytest.approx(15.0)
    assert result['p95'] == pytest.approx(19.5)
    assert result['p99'] == pytest.approx(19.9)


def test_metric_series_empty_reports_count_only():
    assert MetricSeries('latency').summary() == {'count': 0}


@pytest.mark.parametrize('n', list(range(1, 50)))
def test_percentile_matches_reference_and_stays_bounded(n):
    xs = [((n * 7 + i * 13) % 97) - 48 for i in range(n)]
    lo, hi = min(xs), max(xs)
    for p in (0.0, 0.25, 0.5, 0.95, 0.99, 1.0):
        value = percentile(xs, p)
        assert value == pytest.approx(reference_percentile(xs, p))
        assert lo - 1e-12 <= value <= hi + 1e-12


def test_percentile_endpoints_are_min_and_max():
    assert percentile([3, 1, 2], 0.0) == 1.0
    assert percentile([3, 1, 2], 1.0) == 3.0


def test_percentile_empty_returns_none():
    assert percentile([], 0.95) is None


@pytest.mark.parametrize('bad', (-0.01, 1.01, 95, 100))
def test_percentile_out_of_range_raises_value_error(bad):
    with pytest.raises(ValueError):
        percentile([1, 2, 3], bad)


def test_observability_summary_p95():
    result = summary([10, 20, 30, 40, 50])
    assert result['count'] == 5
    assert result['mean'] == 30.0
    assert result['p95'] == pytest.approx(48.0)
    assert summary([])['p95'] is None


def test_latency_budget_uses_interpolated_p95():
    assert latency_budget([], 15) == {'count': 0, 'over': 0, 'p95': None}
    result = latency_budget([10, 20, 30, 40, 50], 45)
    assert result == {'count': 5, 'over': 1, 'p95': pytest.approx(48.0)}
    # two samples used to report the minimum (10.0)
    assert latency_budget([10, 20], 15)['p95'] == pytest.approx(19.5)


def test_registry_snapshot_tail_visible_for_alerts():
    registry = Registry()
    for value in (100, 102, 98, 500, 101):
        registry.observe('request_ms', value)
    snapshot = registry.snapshot()
    assert snapshot['request_ms']['p95'] > 102
