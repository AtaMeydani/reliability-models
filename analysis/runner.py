"""Solve configured scenarios and return their numerical results."""
import numpy as np

from analysis.inputs import system_config
from core.simulator import GeneralMonteCarloSimulator
from core.topology_builder import build_topology
from models.analytical import AnalyticalSolver
from models.bayesian import AdvancedBayesianSolver
from models.markov import ExactMarkovSolver
from utils.helpers import sample_timelines

METRICS = ('reliability', 'availability', 'performability')


def bayesian_curves(config, topology, times, factor, parameters):
    repairable = any(node.mu > 0 for node in config.nodes.values())
    if factor != 1 or (repairable and config.ccf_groups):
        return {}
    pairs = np.array([AdvancedBayesianSolver(config, time).solve(topology, **parameters)
                      for time in times])
    curves = {'availability': pairs[:, 0], 'performability': pairs[:, 1]}
    if not repairable:
        curves['reliability'] = pairs[:, 0]
    return curves


def analytical_curves(config, topology, times, factor, parameters):
    nodes = list(config.nodes.values())
    if (topology != 'M-of-N' or parameters.get('m', 1) != 1 or len(nodes) != 2
            or config.ccf_groups or any(node.mu > 0 for node in nodes)
            or nodes[0].lam != nodes[1].lam):
        return {}
    reliability = AnalyticalSolver.parallel_load_sharing(times, nodes[0].lam, factor)
    curves = {'reliability': reliability, 'availability': reliability}
    if nodes[0].capacity == nodes[1].capacity:
        both_healthy = np.exp(-2 * nodes[0].lam * times)
        curves['performability'] = nodes[0].capacity * (reliability + both_healthy)
    return curves


def solve_scenario(scenario, settings, seed):
    config = system_config(scenario)
    parameters = scenario.get('parameters', {})
    factor = scenario.get('load_sharing_factor', 1.0)
    topology_type = scenario['topology']
    horizon = settings['horizon']
    times = np.unique(np.r_[np.linspace(0, horizon, settings['time_points']),
                            settings['mission_time']])
    topology = build_topology(topology_type, config.nodes, **parameters)
    simulator = GeneralMonteCarloSimulator(topology, config, horizon, factor)
    simulation = simulator.run_batch(settings['simulations'], seed)
    monte_carlo = {
        'reliability': (simulation['failure_times'][:, None] > times).mean(axis=0),
        'availability': sample_timelines(simulation['timelines'], times,
                                         horizon=horizon).mean(axis=0),
        'performability': sample_timelines(simulation['perf_timelines'], times,
                                           True, horizon=horizon).mean(axis=0),
    }
    markov = ExactMarkovSolver(config, topology_type, factor, **parameters).solve(times)
    bayesian = bayesian_curves(config, topology_type, times, factor, parameters)
    analytical = analytical_curves(config, topology_type, times, factor, parameters)
    rows = []
    for metric in METRICS:
        for index, time in enumerate(times):
            rows.append({
                'scenario': scenario['name'], 'metric': metric, 'time': time,
                'markov': markov[metric][index], 'monte_carlo': monte_carlo[metric][index],
                'bayesian': bayesian[metric][index] if metric in bayesian else '',
                'analytical': analytical[metric][index] if metric in analytical else '',
            })
    return rows
