"""Sample simulation intervals at the requested result times."""
import numpy as np


def sample_timelines(timelines, t_values, performance=False, horizon=None):
    """Use half-open intervals and include the supplied censoring horizon."""
    times = np.asarray(t_values, dtype=float)
    if times.ndim != 1 or len(times) == 0 or not np.all(np.isfinite(times)):
        raise ValueError('Provide a nonempty finite time axis.')
    if np.any(times < 0) or (horizon is not None and np.any(times > horizon)):
        raise ValueError('Sample times must lie within the simulation horizon.')
    samples = np.zeros((len(timelines), len(times)))
    for row, intervals in enumerate(timelines):
        for interval in intervals:
            start, end = interval[:2]
            mask = (times >= start) & (times < end)
            if horizon is not None:
                mask |= (times == horizon) & (end == horizon) & (times >= start)
            samples[row, mask] = interval[2] if performance else 1.0
    return samples
