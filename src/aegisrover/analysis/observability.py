import math


def percentile(values, p):
    """Return the p percentile using linear interpolation between ranks.

    ``p`` is a fraction in the closed interval [0, 1].  Sorting once and
    interpolating keeps small samples informative while guaranteeing that the
    result remains within the observed [min, max] range.
    """
    xs = sorted(float(value) for value in values)
    if not xs:
        return None
    if not math.isfinite(p) or not 0.0 <= p <= 1.0:
        raise ValueError('p must be in [0, 1]')
    if len(xs) == 1:
        return xs[0]

    position = (len(xs) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return xs[lower]
    fraction = position - lower
    return xs[lower] * (1.0 - fraction) + xs[upper] * fraction

def summary(values):
    xs = list(map(float, values))
    return {'count': len(xs), 'min': min(xs) if xs else None, 'max': max(xs) if xs else None, 'mean': sum(xs) / len(xs) if xs else None, 'p95': percentile(xs, 0.95)}

def rate(count, seconds):
    return 0.0 if seconds <= 0 else count / seconds

def error_budget(total, failures, objective):
    allowed = total * (1 - objective)
    remaining = allowed - failures
    return {'allowed': allowed, 'remaining': remaining, 'exhausted': remaining < 0}
