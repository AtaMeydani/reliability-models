"""Static Bayesian inference for independent snapshots and nonrepairable shocks."""
import numpy as np
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination

from core.config_types import SystemConfig
from core.topology_builder import build_topology
from models.bayesian_tables import component_cpd, system_table


class AdvancedBayesianSolver:
    def __init__(self, system_config: SystemConfig, time_mission: float):
        if not np.isfinite(time_mission) or time_mission < 0:
            raise ValueError('Mission time must be finite and nonnegative.')
        self.cfg = system_config
        self.t = time_mission

    def _component_probability(self, name):
        node = self.cfg.nodes[name]
        total_rate = node.lam + node.mu
        if total_rate == 0:
            return 1.0
        return node.mu / total_rate + (node.lam / total_rate) * np.exp(-total_rate * self.t)

    def _validate_metric(self, metric):
        if metric not in ('availability', 'reliability', 'performability'):
            raise ValueError(f'Unsupported metric: {metric}')
        repairable = any(node.mu > 0 for node in self.cfg.nodes.values())
        if repairable and (metric == 'reliability' or
                           any(group.common_rate > 0 for group in self.cfg.ccf_groups)):
            raise ValueError('Static BN cannot represent first passage with repairs '
                             'or recurring shocks with repairs; use ExactMarkovSolver.')

    def _add_shocks(self, model):
        for group in self.cfg.ccf_groups:
            internal_name = f'CCF_{group.name}'
            while internal_name in model.nodes:
                internal_name = '_' + internal_name
            model.add_node(internal_name)
            for name in group.affected_nodes:
                model.add_edge(internal_name, name)
            # In the supported static model this root means no shock has occurred.
            probability = np.exp(-group.common_rate * self.t)
            model.add_cpds(TabularCPD(internal_name, 2, [[1 - probability], [probability]]))

    def solve(self, topology_type, **kwargs):
        self._validate_metric(kwargs.pop('metric', 'availability'))
        build_topology(topology_type, self.cfg.nodes, **kwargs)
        names = sorted(self.cfg.nodes)
        model = DiscreteBayesianNetwork([(name, 'System') for name in names])
        self._add_shocks(model)
        for name in names:
            model.add_cpds(component_cpd(name, self._component_probability(name),
                                         model.get_parents(name)))
        system_cpd, rewards = system_table(self.cfg, names, topology_type, **kwargs)
        model.add_cpds(system_cpd)
        inference = VariableElimination(model)
        availability = inference.query(variables=['System'], show_progress=False).values[1]
        joint = inference.query(variables=names, show_progress=False)
        axes = [joint.variables.index(name) for name in names]
        probabilities = np.transpose(joint.values, axes).ravel()
        return availability, probabilities @ rewards
