"""Continuous-time Markov solver for system reliability and service reward."""
import numpy as np
from scipy.sparse.linalg import expm_multiply

from core.topology_builder import build_topology


class ExactMarkovSolver:
    def __init__(self, system_config, topology_type, load_sharing_factor=1.0, **kwargs):
        self.cfg = system_config
        self.names = sorted(system_config.nodes)
        self.topology = build_topology(topology_type, system_config.nodes, **kwargs)
        if not np.isfinite(load_sharing_factor) or load_sharing_factor < 1:
            raise ValueError('The load-sharing multiplier must be finite and >= 1.')
        if load_sharing_factor != 1 and not (
                topology_type == 'M-of-N' and kwargs.get('m', 1) == 1
                and len(self.names) == 2):
            raise ValueError('Load sharing supports only a 1-of-2 topology.')
        n = len(self.names)
        size = 1 << n
        self.generator = np.zeros((size, size))
        self.up = np.zeros(size, dtype=bool)
        self.reward = np.zeros(size)
        masks = [sum(1 << self.names.index(name) for name in group.affected_nodes)
                 for group in system_config.ccf_groups]

        for state in range(size):
            for i, name in enumerate(self.names):
                active = bool(state & (1 << i))
                self.topology.components[name].is_working = active
                cfg = system_config.nodes[name]
                multiplier = load_sharing_factor if state.bit_count() == 1 else 1.0
                rate = cfg.lam * multiplier if active else cfg.mu
                self.generator[state, state ^ (1 << i)] += rate
            self.up[state], self.reward[state] = self.topology.check_system_state()
            for group, mask in zip(system_config.ccf_groups, masks):
                destination = state & ~mask
                if destination != state:
                    self.generator[state, destination] += group.common_rate
            self.generator[state, state] = -self.generator[state].sum()

    @staticmethod
    def _distributions(generator, times):
        initial = np.zeros(len(generator))
        initial[-1] = 1.0  # All components initially working.
        if len(times) > 1 and times[-1] > times[0] and np.allclose(
                times, np.linspace(times[0], times[-1], len(times)),
                rtol=0, atol=1e-12):
            return expm_multiply(generator.T, initial, start=times[0],
                                 stop=times[-1], num=len(times))
        return np.array([expm_multiply(generator.T*t, initial) for t in times])

    def solve(self, t_values):
        times = np.asarray(t_values, dtype=float)
        if times.ndim != 1 or not len(times) or np.any(~np.isfinite(times)) or np.any(times < 0):
            raise ValueError('Provide a nonempty sequence of finite nonnegative times.')
        distribution = self._distributions(self.generator, times)
        # Keep the original diagonal: exits to failed states kill probability.
        # Repairs between functioning states remain in this subgenerator.
        transient = self.generator[np.ix_(self.up, self.up)]
        surviving = self._distributions(transient, times)
        return {'reliability': surviving.sum(axis=1),
                'availability': distribution @ self.up,
                'performability': distribution @ self.reward}
