from math import isfinite
import numpy as np

from core.config_types import SystemConfig
from core.topology import MofNTopology


class GeneralMonteCarloSimulator:
    """DES with recurring Poisson shocks and independent component repairs.

    A shock fails every working member; already failed members keep their repair
    clocks. Repairs are parallel, as-good-as-new, and exponential. Events at the
    censoring horizon are excluded (a probability-zero case for these clocks).
    """

    def __init__(self, topology, system_config: SystemConfig, mission_time: float,
                 load_sharing_factor=1.0):
        if not isfinite(mission_time) or mission_time <= 0:
            raise ValueError('The simulation horizon must be positive and finite.')
        if not isfinite(load_sharing_factor) or load_sharing_factor < 1:
            raise ValueError('The load-sharing multiplier must be finite and >= 1.')
        if load_sharing_factor != 1 and not (
                isinstance(topology, MofNTopology) and topology.m_req == 1
                and topology.n_total == 2):
            raise ValueError('Load sharing supports only a 1-of-2 topology.')
        if set(topology.components) - {'S', 'T'} != set(system_config.nodes):
            raise ValueError('Topology components must match the system configuration.')
        for name, cfg in system_config.nodes.items():
            comp = topology.components[name]
            if (comp.lam, comp.mu, comp.capacity) != (cfg.lam, cfg.mu, cfg.capacity):
                raise ValueError(f'Topology/configuration mismatch for {name}.')
        self.topology = topology
        self.config = system_config
        self.mission_time = mission_time
        self.load_sharing_factor = load_sharing_factor
        self.rng = np.random.default_rng()

    def run_single_simulation(self):
        components = list(self.topology.components.values())
        for comp in components:
            comp.reset(self.rng)
        shock_times = [self.rng.exponential(1 / g.common_rate)
                       if g.common_rate else float('inf')
                       for g in self.config.ccf_groups]
        up_intervals, perf_intervals = [], []
        current_time, last_up_start = 0.0, 0.0
        was_up, performance = self.topology.check_system_state()
        first_failure = float('inf') if was_up else 0.0

        while True:
            comp = min(components, key=lambda c: c.next_event_time)
            shock_index = min(range(len(shock_times)), key=shock_times.__getitem__) \
                if shock_times else None
            shock_time = shock_times[shock_index] if shock_index is not None else float('inf')
            next_time = min(comp.next_event_time, shock_time)
            if next_time >= self.mission_time:
                break
            if next_time > current_time:
                perf_intervals.append((current_time, next_time, performance))
            current_time = next_time

            if shock_time <= comp.next_event_time:
                group = self.config.ccf_groups[shock_index]
                for name in group.affected_nodes:
                    member = self.topology.components[name]
                    if member.is_working:
                        member.is_working = False
                        member.schedule_next_event(current_time, self.rng)
                shock_times[shock_index] = current_time + self.rng.exponential(1/group.common_rate)
            else:
                comp.toggle_state()
                comp.schedule_next_event(current_time, self.rng)

            if self.load_sharing_factor != 1:
                active = [self.topology.components[name] for name in self.config.nodes
                          if self.topology.components[name].is_working]
                multiplier = self.load_sharing_factor if len(active) == 1 else 1.0
                # Exponential clocks can be restarted after a load change.
                for member in active:
                    member.schedule_next_event(current_time, self.rng, multiplier)

            is_up, performance = self.topology.check_system_state()
            if was_up and not is_up:
                up_intervals.append((last_up_start, current_time))
                first_failure = min(first_failure, current_time)
            elif not was_up and is_up:
                last_up_start = current_time
            was_up = is_up

        if was_up:
            up_intervals.append((last_up_start, self.mission_time))
        perf_intervals.append((current_time, self.mission_time, performance))
        return {'ttf': first_failure,
                'uptime': sum(end-start for start, end in up_intervals),
                'timeline': up_intervals, 'perf_intervals': perf_intervals}

    def run_batch(self, num_simulations, seed=None):
        if not isinstance(num_simulations, int) or num_simulations <= 0:
            raise ValueError('num_simulations must be a positive integer.')
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        results = [self.run_single_simulation() for _ in range(num_simulations)]
        return {'failure_times': np.array([r['ttf'] for r in results]),
                'availabilities': np.array([r['uptime']/self.mission_time for r in results]),
                'timelines': [r['timeline'] for r in results],
                'perf_timelines': [r['perf_intervals'] for r in results]}
