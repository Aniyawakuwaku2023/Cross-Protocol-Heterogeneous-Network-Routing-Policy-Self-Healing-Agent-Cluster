import networkx as nx
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime


@dataclass
class LinkMetrics:
    """链路多模态指标"""
    delay: float
    packet_loss: float
    bandwidth_utilization: float
    jitter: float
    protocol: str
    status: str


@dataclass
class ProtocolConstraint:
    """协议约束规则"""
    name: str
    can_connect_to: Set[str]
    min_delay: float
    max_delay: float
    supports_switching: bool = True


class NetworkEnvironment:
    """
    跨协议异构网络环境模拟器
    支持：OTN、IP、Optical 等多种传输协议
    包含真实的协议约束规则
    """
    
    PROTOCOLS = ['OTN', 'IP', 'Optical', 'MPLS', 'SDN']
    
    PROTOCOL_CONSTRAINTS: Dict[str, ProtocolConstraint] = {
        'OTN': ProtocolConstraint('OTN', {'OTN', 'IP', 'MPLS', 'SDN'}, 0.005, 0.015, True),
        'IP': ProtocolConstraint('IP', {'OTN', 'IP', 'Optical', 'MPLS', 'SDN'}, 0.015, 0.035, True),
        'Optical': ProtocolConstraint('Optical', {'Optical', 'OTN'}, 0.002, 0.008, False),
        'MPLS': ProtocolConstraint('MPLS', {'OTN', 'IP', 'MPLS', 'SDN'}, 0.010, 0.025, True),
        'SDN': ProtocolConstraint('SDN', {'OTN', 'IP', 'MPLS', 'SDN'}, 0.008, 0.020, True),
    }
    
    def __init__(self, num_nodes: int = 20, num_edges: int = 45, seed: int = None):
        if seed is not None:
            random.seed(seed)
        self.graph = nx.gnm_random_graph(n=num_nodes, m=num_edges, seed=seed)
        self.business_weights: Dict[int, float] = {}
        self.fault_history: List[Dict] = []
        self._init_topology()
    
    def _init_topology(self):
        for u, v in self.graph.edges():
            protocol = random.choice(self.PROTOCOLS)
            base_delay = self._get_protocol_delay(protocol)
            self.graph[u][v]['delay'] = base_delay
            self.graph[u][v]['packet_loss'] = random.uniform(0.001, 0.02)
            self.graph[u][v]['bandwidth_utilization'] = random.uniform(0.1, 0.8)
            self.graph[u][v]['jitter'] = random.uniform(0.001, 0.01)
            self.graph[u][v]['protocol'] = protocol
            self.graph[u][v]['status'] = 'UP'
        
        for node in self.graph.nodes():
            self.business_weights[node] = random.uniform(0.5, 1.0)
    
    def _get_protocol_delay(self, protocol: str) -> float:
        protocol_delays = {
            'OTN': (0.005, 0.015),
            'IP': (0.015, 0.035),
            'Optical': (0.002, 0.008),
            'MPLS': (0.010, 0.025),
            'SDN': (0.008, 0.020)
        }
        delay_range = protocol_delays.get(protocol, (0.010, 0.030))
        return random.uniform(*delay_range)
    
    def get_telemetry(self) -> Dict[Tuple[int, int], LinkMetrics]:
        """获取完整遥测数据"""
        telemetry = {}
        for u, v in self.graph.edges():
            attr = self.graph[u][v]
            telemetry[(u, v)] = LinkMetrics(
                delay=attr['delay'],
                packet_loss=attr['packet_loss'],
                bandwidth_utilization=attr['bandwidth_utilization'],
                jitter=attr['jitter'],
                protocol=attr['protocol'],
                status=attr['status']
            )
        return telemetry
    
    def get_node_business_weight(self, node: int) -> float:
        return self.business_weights.get(node, 1.0)
    
    def inject_fault(self, edge: Optional[Tuple[int, int]] = None) -> Tuple[int, int]:
        if edge is None:
            up_edges = [(u, v) for u, v in self.graph.edges() 
                       if self.graph[u][v]['status'] == 'UP']
            if not up_edges:
                raise RuntimeError("No available links to fail")
            edge = random.choice(up_edges)
        
        self.graph[edge[0]][edge[1]]['status'] = 'DOWN'
        self.fault_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'LINK_FAILURE',
            'edge': edge,
            'protocol': self.graph[edge[0]][edge[1]]['protocol']
        })
        print(f"[Env] Link {edge} FAILED (Protocol: {self.graph[edge[0]][edge[1]]['protocol']})")
        return edge
    
    def inject_congestion(self, node: int, congestion_level: float = 0.9):
        """模拟节点拥塞"""
        for u, v in self.graph.edges(node):
            self.graph[u][v]['bandwidth_utilization'] = congestion_level
            self.graph[u][v]['delay'] *= 1.5
        self.fault_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'NODE_CONGESTION',
            'node': node,
            'level': congestion_level
        })
        print(f"[Env] Node {node} congested (utilization: {congestion_level})")
    
    def apply_routing_policy(self, path: List[int]):
        """应用新路由策略到环境"""
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            self.graph[u][v]['bandwidth_utilization'] = min(
                self.graph[u][v]['bandwidth_utilization'] + 0.1, 1.0
            )
    
    def get_topology(self) -> nx.Graph:
        return self.graph
    
    def reset_link(self, edge: Tuple[int, int]):
        """恢复链路状态"""
        self.graph[edge[0]][edge[1]]['status'] = 'UP'
        self.graph[edge[0]][edge[1]]['delay'] = self._get_protocol_delay(
            self.graph[edge[0]][edge[1]]['protocol']
        )
        print(f"[Env] Link {edge} RESTORED")
    
    def get_neighbors(self, node: int) -> List[int]:
        """获取节点的所有邻居"""
        return list(self.graph.neighbors(node))
    
    def get_incident_edges(self, node: int) -> List[Tuple[int, int]]:
        """获取节点的所有关联边"""
        return [(node, v) for v in self.graph.neighbors(node)]
    
    def check_protocol_compatibility(self, protocol1: str, protocol2: str) -> bool:
        """检查两个协议是否兼容"""
        constraint1 = self.PROTOCOL_CONSTRAINTS.get(protocol1)
        constraint2 = self.PROTOCOL_CONSTRAINTS.get(protocol2)
        
        if not constraint1 or not constraint2:
            return True
        
        return (protocol2 in constraint1.can_connect_to and 
                protocol1 in constraint2.can_connect_to)
    
    def get_fault_history(self) -> List[Dict]:
        """获取故障历史"""
        return self.fault_history.copy()