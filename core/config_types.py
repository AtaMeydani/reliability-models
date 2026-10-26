from dataclasses import dataclass
from typing import List, Dict
from math import isfinite


def _nonnegative(value, name):
    if not isfinite(value) or value < 0:
        raise ValueError(f'{name} must be finite and nonnegative.')

@dataclass
class NodeConfig:
    lam: float   
    mu: float
    capacity: float = 1.0

    def __post_init__(self):
        for name in ('lam', 'mu', 'capacity'):
            _nonnegative(getattr(self, name), name)

@dataclass
class CCFGroupConfig:
    """
    Configuration for a Common Cause Failure Group.
    """
    name: str 
    affected_nodes: List[str]
    common_rate: float

    def __post_init__(self):
        _nonnegative(self.common_rate, 'common_rate')
        if not self.name or not self.affected_nodes:
            raise ValueError('A CCF group needs a name and affected nodes.')
        if len(set(self.affected_nodes)) != len(self.affected_nodes):
            raise ValueError('CCF members must be unique.')

class SystemConfig:
    def __init__(self, node_configs: Dict[str, NodeConfig], ccf_groups: List[CCFGroupConfig] = None):
        self.nodes = node_configs
        self.ccf_groups = ccf_groups if ccf_groups else []
        if not self.nodes or {'S', 'T', 'System'} & self.nodes.keys():
            raise ValueError('Provide components with names other than S, T, System.')
        if len({g.name for g in self.ccf_groups}) != len(self.ccf_groups):
            raise ValueError('CCF group names must be unique.')
        for group in self.ccf_groups:
            if not set(group.affected_nodes) <= self.nodes.keys():
                raise ValueError(f'Unknown components in CCF group {group.name}.')
