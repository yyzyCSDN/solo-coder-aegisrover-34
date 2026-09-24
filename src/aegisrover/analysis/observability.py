def percentile(values, p):
    """Linear-interpolated percentile (CPS / numpy 'linear' convention).

    ``p`` is a fraction in ``[0, 1]``; ``percentile(xs, 0.5)`` is the median.
    Works for any sample size, including a single sample, and the result always
    lies within the observed ``[min, max]`` range.  Returns ``None`` when there
    are no samples.
    """
    if not 0.0 <= p <= 1.0:
        raise ValueError('p must be within [0, 1], got %r' % (p,))
    xs = sorted(map(float, values))
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    rank = p * (len(xs) - 1)
    low = int(rank)
    frac = rank - low
    if low >= len(xs) - 1:
        return xs[-1]
    return xs[low] + (xs[low + 1] - xs[low]) * frac


def summary(values):
    xs = list(map(float, values))
    return {'count': len(xs), 'min': min(xs) if xs else None, 'max': max(xs) if xs else None, 'mean': sum(xs) / len(xs) if xs else None, 'p95': percentile(xs, 0.95)}


def rate(count, seconds):
    return 0.0 if seconds <= 0 else count / seconds


def error_budget(total, failures, objective):
    allowed = total * (1 - objective)
    remaining = allowed - failures
    return {'allowed': allowed, 'remaining': remaining, 'exhausted': remaining < 0}
