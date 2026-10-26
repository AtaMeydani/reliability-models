import numpy as np

class AnalyticalSolver:
    @staticmethod
    def parallel_load_sharing(t, lam, k):
        """
        Calculates reliability for a 2-component Load Sharing system.
        """
        t = np.asarray(t, dtype=float)
        if np.any(~np.isfinite(t)) or np.any(t < 0) or not np.isfinite(lam) or lam < 0:
            raise ValueError('Time and failure rate must be finite and nonnegative.')
        if not np.isfinite(k) or k < 1:
            raise ValueError('Stress multiplier must be finite and >= 1.')
        base = np.exp(-2 * lam * t)
        delta = k - 2
        if delta == 0:
            return base * (1 + 2 * lam * t)
        # expm1 avoids cancellation near k=2; use the slower exponential as
        # the prefactor so that very long missions do not produce 0 * inf.
        if delta > 0:
            extra = base * (-np.expm1(-delta * lam * t)) / delta
        else:
            extra = np.exp(-k * lam * t) * np.expm1(delta * lam * t) / delta
        return base + 2 * extra
