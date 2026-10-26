"""Construct supported topologies from component settings."""
from core.components import Component
from core.config_types import NodeConfig
from core.topology import SystemTopology, MofNTopology, WheatstoneTopology


class TopologyBuilder:
    @staticmethod
    def _get_config(name, config_dict, default_lam=0.001, default_mu=0.0):
        if name in config_dict:
            return config_dict[name]
        return NodeConfig(lam=default_lam, mu=default_mu)

    @staticmethod
    def create_series(node_configs, node_order):
        topology = SystemTopology('S', 'T')
        topology.add_component(Component('S', 0, 0))
        topology.add_component(Component('T', 0, 0))
        previous = 'S'
        for name in node_order:
            config = TopologyBuilder._get_config(name, node_configs)
            topology.add_component(Component(name, config.lam, config.mu, config.capacity))
            topology.add_connection(previous, name)
            previous = name
        topology.add_connection(previous, 'T')
        return topology

    @staticmethod
    def create_parallel(n_components, lam, mu=0.0):
        topology = SystemTopology('S', 'T')
        topology.add_component(Component('S', 0, 0))
        topology.add_component(Component('T', 0, 0))
        for i in range(n_components):
            name = f'C{i}'
            topology.add_component(Component(name, lam, mu))
            topology.add_connection('S', name)
            topology.add_connection(name, 'T')
        return topology

    @staticmethod
    def create_wheatstone_bridge(node_configs):
        topology = WheatstoneTopology()
        topology.add_component(Component('S', 0, 0))
        topology.add_component(Component('T', 0, 0))
        for name in ['C1', 'C2', 'C3', 'C4', 'C5']:
            config = TopologyBuilder._get_config(name, node_configs)
            topology.add_component(Component(name, config.lam, config.mu, config.capacity))
        return topology

    @staticmethod
    def create_m_of_n(m, n, lam, mu=0.0):
        topology = MofNTopology(m, n)
        for i in range(n):
            name = f'C{i}'
            topology.add_component(Component(name, lam, mu))
            topology.add_connection('S', name)
            topology.add_connection(name, 'T')
        return topology


def build_topology(topology_type, node_configs, **kwargs):
    names = sorted(node_configs)
    if topology_type == 'Series':
        if kwargs.get('n', len(names)) != len(names):
            raise ValueError('n must match the configured component count.')
        return TopologyBuilder.create_series(node_configs, names)
    if topology_type == 'Wheatstone Bridge':
        if set(names) != {'C1', 'C2', 'C3', 'C4', 'C5'}:
            raise ValueError('The bridge requires exactly C1 through C5.')
        return TopologyBuilder.create_wheatstone_bridge(node_configs)
    if topology_type == 'M-of-N':
        n = kwargs.get('n', len(names))
        if n != len(names):
            raise ValueError('n must match the configured component count.')
        topology = MofNTopology(kwargs.get('m', 1), n)
        for name in names:
            config = node_configs[name]
            topology.add_component(Component(name, config.lam, config.mu, config.capacity))
            topology.add_connection('S', name)
            topology.add_connection(name, 'T')
        return topology
    raise ValueError(f'Unsupported topology: {topology_type}')
