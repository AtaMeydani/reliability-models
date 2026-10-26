"""Conditional probability and reward tables for static Bayesian inference."""
import itertools

import numpy as np
from pgmpy.factors.discrete import TabularCPD


def component_cpd(name, probability, parents):
    if not parents:
        return TabularCPD(name, 2, [[1 - probability], [probability]])
    success = [probability if all(states) else 0.0
               for states in itertools.product([0, 1], repeat=len(parents))]
    return TabularCPD(name, 2, [[1 - value for value in success], success],
                      evidence=parents, evidence_card=[2] * len(parents))


def system_table(config, names, topology_type, **kwargs):
    success, rewards = [], []
    for states in itertools.product([0, 1], repeat=len(names)):
        working = dict(zip(names, states))
        if topology_type == 'Wheatstone Bridge':
            is_up = ((working['C1'] and working['C4']) or
                     (working['C2'] and working['C5']) or
                     (working['C1'] and working['C3'] and working['C5']) or
                     (working['C2'] and working['C3'] and working['C4']))
        elif topology_type == 'Series':
            is_up = all(states)
        else:  # M-of-N; topology and threshold are validated before table creation.
            is_up = sum(states) >= kwargs.get('m', 1)
        success.append(int(bool(is_up)))
        rewards.append(sum(config.nodes[name].capacity * state
                           for name, state in working.items()) if is_up else 0.0)
    cpd = TabularCPD('System', 2, [[1 - value for value in success], success],
                    evidence=names, evidence_card=[2] * len(names))
    return cpd, np.asarray(rewards)
