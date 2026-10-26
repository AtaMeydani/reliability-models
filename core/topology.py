"""Connectivity, voting, and bridge state/reward rules."""
import networkx as nx
from core.components import Component


class SystemTopology:
    def __init__(self, source_node_name, target_node_name):
        self.graph = nx.DiGraph()
        self.components = {}
        self.source = source_node_name
        self.target = target_node_name

    def add_component(self, component):
        self.components[component.name] = component
        self.graph.add_node(component.name)

    def add_connection(self, u_name, v_name):
        if u_name not in self.components or v_name not in self.components:
            raise ValueError(f'Components {u_name} or {v_name} not found in topology.')
        self.graph.add_edge(u_name, v_name)

    def check_system_state(self):
        working_nodes = [name for name, comp in self.components.items() if comp.is_working]
        active_subgraph = self.graph.subgraph(working_nodes)
        try:
            is_connected = nx.has_path(active_subgraph, self.source, self.target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            is_connected = False
        capacity = sum(self.components[name].capacity for name in working_nodes
                       if name not in [self.source, self.target])
        return is_connected, capacity if is_connected else 0.0

    def reset(self):
        for component in self.components.values():
            component.reset()


class MofNTopology(SystemTopology):
    def __init__(self, m, n):
        if not isinstance(m, int) or not isinstance(n, int) or not 1 <= m <= n:
            raise ValueError('M-of-N requires integers 1 <= m <= n.')
        super().__init__('S', 'T')
        self.m_req = m
        self.n_total = n
        self.add_component(Component('S', 0, 0))
        self.add_component(Component('T', 0, 0))

    def check_system_state(self):
        active = [comp for name, comp in self.components.items()
                  if name not in ['S', 'T'] and comp.is_working]
        is_up = len(active) >= self.m_req
        return is_up, sum(comp.capacity for comp in active) if is_up else 0.0


class WheatstoneTopology(SystemTopology):
    def __init__(self):
        super().__init__('S', 'T')

    def check_system_state(self):
        working = {name: comp.is_working for name, comp in self.components.items()}
        paths = [('C1', 'C4'), ('C2', 'C5'),
                 ('C1', 'C3', 'C5'), ('C2', 'C3', 'C4')]
        is_up = any(all(working.get(name, False) for name in path) for path in paths)
        capacity = sum(comp.capacity for name, comp in self.components.items()
                       if comp.is_working and name not in ['S', 'T'])
        return is_up, capacity if is_up else 0.0
