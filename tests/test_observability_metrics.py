import pytest

from aegisrover.analysis.metrics import MetricSeries, Registry
from aegisrover.analysis.observability import percentile, summary
from aegisrover.runtime.diagnostics import latency_budget


def test_percentile_interpolates_small_samples():
    assert percentile([0.0, 10.0], 0.5) == 5.0
    assert percentile([0.0, 10.0], 0.95) == 9.5
    assert percentile([0.0, 10.0], 0.99) == 9.9


def test_percentile_boundaries_stay_within_sample_range():
    values = [4.0, 1.0, 3.0, 2.0]
    assert percentile(values, 0.0) == 1.0
    assert percentile(values, 1.0) == 4.0
    for p in (0.0, 0.25, 0.5, 0.75, 1.0):
        result = percentile(values, p)
        assert 1.0 <= result <= 4.0


def test_percentile_handles_empty_and_rejects_invalid_probability():
    assert percentile([], 0.95) is None
    with pytest.raises(ValueError):
        percentile([1.0, 2.0], 1.01)
    with pytest.raises(ValueError):
        percentile([1.0, 2.0], -0.01)


def test_metric_summary_reports_interpolated_percentiles_for_small_samples():
    series = MetricSeries('latency')
    series.observe(0)
    series.observe(10)

    result = series.summary()

    assert result['p50'] == 5.0
    assert result['p95'] == 9.5
    assert result['p99'] == 9.9


def test_empty_metric_and_registry_snapshot_do_not_interpolate_missing_data():
    assert MetricSeries('latency').summary() == {'count': 0}
    registry = Registry()
    registry.observe('latency', 2.0)
    assert registry.snapshot()['latency']['count'] == 1
    assert registry.snapshot()['latency']['p95'] == 2.0


def test_observability_and_latency_budget_use_same_percentile():
    assert summary([0.0, 10.0])['p95'] == 9.5
    assert latency_budget([0.0, 10.0], 9.0) == {'count': 2, 'over': 1, 'p95': 9.5}
    assert latency_budget([], 9.0) == {'count': 0, 'over': 0, 'p95': None}
