from dataclasses import dataclass, field
import statistics

from aegisrover.analysis.observability import percentile


@dataclass
class MetricSeries:
    name: str
    values: list = field(default_factory=list)

    def observe(self, value):
        self.values.append(float(value))

    def summary(self):
        if not self.values:
            return {'count': 0}
        xs = sorted(self.values)
        return {'count': len(xs), 'min': xs[0], 'max': xs[-1],
                'mean': statistics.fmean(xs),
                'p50': percentile(xs, 0.50),
                'p95': percentile(xs, 0.95),
                'p99': percentile(xs, 0.99)}


class Registry:

    def __init__(self):
        self.series = {}

    def observe(self, name, value):
        self.series.setdefault(name, MetricSeries(name)).observe(value)

    def snapshot(self):
        return {k: v.summary() for k, v in self.series.items()}
