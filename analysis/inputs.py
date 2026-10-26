"""Read scenario data and reject invalid inputs before solving."""
import json
from math import isfinite
from pathlib import Path

from core.config_types import CCFGroupConfig, NodeConfig, SystemConfig
from core.topology_builder import build_topology


def system_config(scenario):
    nodes = {name: NodeConfig(**values) for name, values in scenario['nodes'].items()}
    groups = [CCFGroupConfig(**values) for values in scenario.get('ccf_groups', [])]
    return SystemConfig(nodes, groups)


def read_input(path, simulations=None):
    document = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    settings = document['settings']
    if simulations is not None:
        settings['simulations'] = simulations
    for name, minimum in [('simulations', 1), ('time_points', 2)]:
        value = settings[name]
        if type(value) is not int or value < minimum:
            raise ValueError(f'{name} must be an integer >= {minimum}.')
    horizon, mission = settings['horizon'], settings['mission_time']
    if not isfinite(horizon) or horizon <= 0:
        raise ValueError('horizon must be positive and finite.')
    if not isfinite(mission) or not 0 <= mission <= horizon:
        raise ValueError('mission_time must lie between zero and horizon.')
    scenarios = document['scenarios']
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError('Provide a nonempty scenarios list.')
    names = set()
    for scenario in scenarios:
        name = scenario['name']
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError('Scenario names must be nonempty and unique.')
        names.add(name)
        config = system_config(scenario)
        parameters = scenario.get('parameters', {})
        build_topology(scenario['topology'], config.nodes, **parameters)
        factor = scenario.get('load_sharing_factor', 1.0)
        if not isfinite(factor) or factor < 1:
            raise ValueError('load_sharing_factor must be finite and >= 1.')
        if factor != 1 and not (scenario['topology'] == 'M-of-N'
                                and parameters.get('m', 1) == 1 and len(config.nodes) == 2):
            raise ValueError('Load sharing supports only a 1-of-2 topology.')
    return document
