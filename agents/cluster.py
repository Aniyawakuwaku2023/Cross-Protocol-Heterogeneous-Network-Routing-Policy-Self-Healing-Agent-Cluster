import networkx as nx
import random
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict


class RiskLevel(Enum):
    NORMAL = 0
    WARNING = 1
    CRITICAL = 2


class KnowledgeSource(Enum):
    PERCEPTOR = "perceptor"
    REASONER = "reasoner"
    VALIDATOR = "validator"
    CAUSAL = "causal"
    ENVIRONMENT = "environment"


@dataclass
class RiskPattern:
    """检测到的风险模式"""
    risk_type: str
    location: Tuple[int, int]
    severity: RiskLevel
    confidence: float
    metrics: Dict[str, float]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RoutingStrategy:
    """路由策略"""
    path: List[int]
    constraints: Dict[str, float]
    score: float
    protocol_path: List[str]
    estimated_delay: float
    estimated_loss: float
    reasoning_chain: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """可解释的验证结果"""
    passed: bool
    rejection_reasons: List[str]
    improvement_suggestions: List[str]
    detailed_checks: Dict[str, Any]
    score: float


@dataclass
class CausalLink:
    """因果链中的链接"""
    source: Tuple[str, Any]
    target: Tuple[str, Any]
    relationship: str
    strength: float


class BlackBoard:
    """
    黑板共享系统 - Agent 间知识共享
    存储全局状态、推理历史、因果关系
    """
    
    def __init__(self):
        self.shared_context: Dict[str, Any] = {
            'current_faults': [],
            'current_risks': [],
            'proposed_strategies': [],
            'rejected_strategies': [],
            'successful_strategies': [],
            'causal_chains': [],
            'network_state': {},
            'execution_trace': []
        }
        self.agent_observations: Dict[str, List[Dict]] = defaultdict(list)
        self.knowledge_base: Dict[str, List[Dict]] = defaultdict(list)
        self.publish_count: int = 0
    
    def publish(self, source: KnowledgeSource, knowledge_type: str, data: Any):
        """发布知识到黑板"""
        self.knowledge_base[knowledge_type].append({
            'source': source.value,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'id': self.publish_count
        })
        self.publish_count += 1
        self.shared_context['execution_trace'].append({
            'source': source.value,
            'type': knowledge_type,
            'timestamp': datetime.now().isoformat()
        })
    
    def query(self, knowledge_type: str, latest: bool = True) -> List[Any]:
        """查询知识"""
        entries = self.knowledge_base.get(knowledge_type, [])
        if latest and entries:
            return [entries[-1]['data']]
        return [e['data'] for e in entries]
    
    def query_by_source(self, source: KnowledgeSource) -> List[Dict]:
        """按来源查询知识"""
        results = []
        for knowledge_type, entries in self.knowledge_base.items():
            for entry in entries:
                if entry['source'] == source.value:
                    results.append(entry)
        return results
    
    def get_latest_risks(self) -> List[RiskPattern]:
        """获取最新风险列表"""
        return self.shared_context.get('current_risks', [])
    
    def get_network_state_summary(self) -> Dict:
        """获取网络状态摘要"""
        return self.shared_context.get('network_state', {})
    
    def update_network_state(self, state: Dict):
        """更新网络状态"""
        self.shared_context['network_state'].update(state)
    
    def get_execution_history(self) -> List[Dict]:
        """获取执行历史"""
        return self.shared_context.get('execution_trace', [])


class CausalReasoner:
    """
    因果推理引擎 - 故障传播分析
    分析故障如何影响相邻节点和链路
    """
    
    def __init__(self, blackboard: BlackBoard):
        self.blackboard = blackboard
        self.propagation_depth: int = 2
    
    def analyze_fault_propagation(self, fault: RiskPattern, 
                                  graph: nx.Graph) -> List[CausalLink]:
        """
        分析故障传播链
        返回故障如何影响相邻节点和链路
        """
        causal_links: List[CausalLink] = []
        u, v = fault.location
        
        if fault.risk_type == 'LINK_FAILURE':
            affected_nodes = [u, v]
            
            for node in affected_nodes:
                neighbors = list(graph.neighbors(node))
                for neighbor in neighbors:
                    edge = (node, neighbor)
                    edge_data = graph.get_edge_data(*edge)
                    
                    if edge_data and edge_data.get('status') == 'UP':
                        delay_impact = edge_data.get('delay', 0) * 0.1
                        load_increase = 0.15
                        
                        causal_links.append(CausalLink(
                            source=('fault', fault),
                            target=('edge', edge),
                            relationship='traffic_redistribution',
                            strength=load_increase
                        ))
                        
                        causal_links.append(CausalLink(
                            source=('fault', fault),
                            target=('node', neighbor),
                            relationship='increased_load',
                            strength=delay_impact
                        ))
        
        elif fault.risk_type == 'NODE_CONGESTION':
            location = fault.metrics.get('node', u)
            neighbors = list(graph.neighbors(location))
            
            for neighbor in neighbors:
                edge = (location, neighbor)
                edge_data = graph.get_edge_data(*edge)
                
                if edge_data:
                    causal_links.append(CausalLink(
                        source=('node', location),
                        target=('edge', edge),
                        relationship='congestion_propagation',
                        strength=0.8
                    ))
        
        self.blackboard.publish(
            KnowledgeSource.CAUSAL,
            'causal_analysis',
            causal_links
        )
        
        return causal_links
    
    def predict_secondary_failures(self, fault: RiskPattern, 
                                   graph: nx.Graph) -> List[Tuple[int, int]]:
        """
        预测由当前故障可能引发的二次故障
        基于负载重分配和级联效应
        """
        secondary_risks: List[Tuple[int, int]] = []
        u, v = fault.location
        
        if fault.risk_type == 'LINK_FAILURE':
            for node in [u, v]:
                neighbors = list(graph.neighbors(node))
                
                for neighbor in neighbors:
                    edge = (node, neighbor)
                    edge_data = graph.get_edge_data(*edge)
                    
                    if edge_data:
                        current_util = edge_data.get('bandwidth_utilization', 0)
                        if current_util > 0.75:
                            score = (current_util - 0.75) * 4
                            if score > 0.5:
                                secondary_risks.append((node, neighbor))
        
        return secondary_risks
    
    def build_reasoning_chain(self, fault: RiskPattern,
                             secondary_risks: List[Tuple[int, int]],
                             proposed_path: List[int]) -> List[str]:
        """
        构建推理链解释
        说明为什么选择这条路径
        """
        chain = []
        
        chain.append(f"观察到 {fault.risk_type} @ {fault.location}")
        
        if secondary_risks:
            chain.append(f"预测可能的二次故障: {len(secondary_risks)} 条高风险链路")
            for risk in secondary_risks[:3]:
                chain.append(f"  - 链路 {risk} 负载过高")
        
        chain.append(f"选择路径 {'->'.join(map(str, proposed_path))}")
        
        affected_by_fault = set()
        for edge in proposed_path[:-1]:
            for risk in secondary_risks:
                if edge in risk:
                    affected_by_fault.add(edge)
        
        if affected_by_fault:
            safe_edges = len(proposed_path) - 1 - len(affected_by_fault)
            chain.append(f"路径中 {safe_edges}/{len(proposed_path)-1} 条链路不受故障影响")
        else:
            chain.append("路径完全避开已知故障区域")
        
        return chain


class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.execution_history: List[Dict] = []
        self.blackboard: Optional[BlackBoard] = None
    
    def attach_blackboard(self, blackboard: BlackBoard):
        """连接到黑板系统"""
        self.blackboard = blackboard
    
    def log_execution(self, action: str, details: Dict):
        """记录执行历史"""
        self.execution_history.append({
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details
        })


class PerceptionAgent(BaseAgent):
    """
    感知 Agent：多模态分析，识别潜在风险模式
    支持：时延异常、丢包率飙升、拥塞检测、协议不匹配
    """
    
    def __init__(self, name: str, threshold_delay: float = 0.035,
                 threshold_loss: float = 0.015,
                 threshold_util: float = 0.85):
        super().__init__(name)
        self.threshold_delay = threshold_delay
        self.threshold_loss = threshold_loss
        self.threshold_util = threshold_util
        self.baseline_metrics: Dict = {}
    
    def monitor(self, env_graph: nx.Graph, 
                telemetry: Dict = None) -> List[RiskPattern]:
        """
        多模态感知：分析网络遥测数据，识别风险模式
        """
        faults: List[RiskPattern] = []
        
        for u, v, attr in env_graph.edges(data=True):
            if attr['status'] == 'DOWN':
                faults.append(RiskPattern(
                    risk_type='LINK_FAILURE',
                    location=(u, v),
                    severity=RiskLevel.CRITICAL,
                    confidence=1.0,
                    metrics={'delay': attr.get('delay', 0), 
                            'protocol': attr.get('protocol', 'Unknown')}
                ))
                continue
            
            risk_score = 0
            risk_factors: Dict[str, float] = {}
            
            if attr.get('delay', 0) > self.threshold_delay:
                risk_score += 0.3
                risk_factors['high_delay'] = attr['delay']
            
            if attr.get('packet_loss', 0) > self.threshold_loss:
                risk_score += 0.3
                risk_factors['high_loss'] = attr['packet_loss']
            
            if attr.get('bandwidth_utilization', 0) > self.threshold_util:
                risk_score += 0.25
                risk_factors['congestion'] = attr['bandwidth_utilization']
            
            if risk_score >= 0.3:
                severity = RiskLevel.CRITICAL if risk_score >= 0.6 else RiskLevel.WARNING
                faults.append(RiskPattern(
                    risk_type='DEGRADATION',
                    location=(u, v),
                    severity=severity,
                    confidence=risk_score,
                    metrics=risk_factors
                ))
        
        self.log_execution('monitor', {
            'detected_risks': len(faults),
            'critical_count': sum(1 for f in faults if f.severity == RiskLevel.CRITICAL),
            'warning_count': sum(1 for f in faults if f.severity == RiskLevel.WARNING)
        })
        
        if self.blackboard:
            self.blackboard.shared_context['current_risks'] = faults
            self.blackboard.publish(KnowledgeSource.PERCEPTOR, 'risk_detection', faults)
        
        return faults
    
    def detect_protocol_mismatch(self, path: List[int], 
                                 graph: nx.Graph) -> List[str]:
        """检测路径中的协议不匹配情况"""
        mismatches = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            protocol = graph[u][v].get('protocol', 'Unknown')
            if i > 0:
                prev_protocol = graph[path[i-1]][path[i]].get('protocol', 'Unknown')
                if protocol != prev_protocol:
                    if not graph.check_protocol_compatibility(prev_protocol, protocol):
                        mismatches.append(
                            f"Protocol incompatibility: {prev_protocol}->{protocol} @ ({u},{v})"
                        )
        return mismatches


class ReasoningAgent(BaseAgent):
    """
    推理 Agent：长链推理，多约束条件下的最优路由策略生成
    支持：K-最短路径、Dijkstra、A*、业务权重感知
    """
    
    def __init__(self, name: str, max_candidates: int = 10):
        super().__init__(name)
        self.max_candidates = max_candidates
        self.causal_reasoner: Optional[CausalReasoner] = None
    
    def attach_causal_reasoner(self, causal_reasoner: CausalReasoner):
        """连接因果推理引擎"""
        self.causal_reasoner = causal_reasoner
    
    def compute_reroute(self, graph: nx.Graph, source: int, target: int,
                       business_weight: float = 1.0,
                       max_hops: int = None,
                       avoid_edges: List[Tuple[int, int]] = None) -> Optional[RoutingStrategy]:
        """
        长链推理：综合考虑时延、丢包、带宽、业务权重生成最优路径
        """
        active_view = self._filter_active_edges(graph, avoid_edges or [])
        
        if max_hops is None:
            try:
                max_hops = nx.diameter(active_view) + 5
            except nx.NetworkXError:
                max_hops = 20
        
        candidates = self._generate_candidate_paths(active_view, source, target, max_hops)
        
        if not candidates:
            self.log_execution('compute_reroute', {
                'source': source, 'target': target,
                'result': 'NO_PATH'
            })
            return None
        
        best_strategy = self._select_best_strategy(candidates, business_weight)
        
        if best_strategy and self.causal_reasoner:
            risks = self.blackboard.get_latest_risks() if self.blackboard else []
            if risks:
                fault = risks[0]
                secondary = self.causal_reasoner.predict_secondary_failures(fault, graph)
                best_strategy.reasoning_chain = self.causal_reasoner.build_reasoning_chain(
                    fault, secondary, best_strategy.path
                )
        
        self.log_execution('compute_reroute', {
            'source': source, 'target': target,
            'candidates_evaluated': len(candidates),
            'selected_score': best_strategy.score if best_strategy else None
        })
        
        if self.blackboard and best_strategy:
            self.blackboard.publish(
                KnowledgeSource.REASONER, 
                'routing_strategy', 
                best_strategy
            )
        
        return best_strategy
    
    def compute_reroute_batch(self, graph: nx.Graph, 
                             requests: List[Tuple[int, int, float]]) -> Dict[Tuple[int, int], RoutingStrategy]:
        """批量路由计算"""
        results = {}
        for src, dst, weight in requests:
            strategy = self.compute_reroute(graph, src, dst, weight)
            if strategy:
                results[(src, dst)] = strategy
        return results
    
    def _filter_active_edges(self, graph: nx.Graph, 
                            avoid_edges: List[Tuple[int, int]]) -> nx.Graph:
        """过滤活跃链路"""
        active_view = graph.copy()
        
        avoid_set = set(avoid_edges)
        dead_edges = []
        for u, v, d in active_view.edges(data=True):
            if d.get('status') == 'DOWN' or (u, v) in avoid_set or (v, u) in avoid_set:
                dead_edges.append((u, v))
        
        active_view.remove_edges_from(dead_edges)
        return active_view
    
    def _generate_candidate_paths(self, graph: nx.Graph, source: int, target: int,
                                  max_hops: int) -> List[RoutingStrategy]:
        """生成多条候选路径（K-最短路径变体）"""
        candidates = []
        
        try:
            k_paths = list(nx.shortest_simple_paths(graph, source, target, weight='delay'))
        except nx.NetworkXNoPath:
            return []
        
        for path in k_paths[:self.max_candidates]:
            if len(path) - 1 > max_hops:
                continue
            
            constraints = self._calculate_path_constraints(graph, path)
            score = self._calculate_strategy_score(constraints)
            protocol_path = self._extract_protocols(graph, path)
            
            candidates.append(RoutingStrategy(
                path=path,
                constraints=constraints,
                score=score,
                protocol_path=protocol_path,
                estimated_delay=constraints['total_delay'],
                estimated_loss=constraints['total_loss']
            ))
        
        return candidates
    
    def _calculate_path_constraints(self, graph: nx.Graph, path: List[int]) -> Dict[str, float]:
        """计算路径约束条件"""
        total_delay = 0.0
        total_loss = 0.0
        max_util = 0.0
        total_jitter = 0.0
        protocol_transitions = 0
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            attr = graph[u][v]
            total_delay += attr.get('delay', 0)
            total_loss += attr.get('packet_loss', 0)
            max_util = max(max_util, attr.get('bandwidth_utilization', 0))
            total_jitter += attr.get('jitter', 0)
            
            if i > 0:
                prev_protocol = graph[path[i-1]][path[i]].get('protocol', '')
                curr_protocol = attr.get('protocol', '')
                if prev_protocol != curr_protocol:
                    protocol_transitions += 1
        
        return {
            'total_delay': total_delay,
            'total_loss': total_loss,
            'max_utilization': max_util,
            'avg_jitter': total_jitter / max(len(path) - 1, 1),
            'hop_count': len(path) - 1,
            'protocol_transitions': protocol_transitions
        }
    
    def _calculate_strategy_score(self, constraints: Dict[str, float],
                                  delay_weight: float = 0.35,
                                  loss_weight: float = 0.25,
                                  util_weight: float = 0.20,
                                  hop_weight: float = 0.10,
                                  protocol_weight: float = 0.10) -> float:
        """多约束综合评分（分数越高越好）"""
        delay_score = max(0, 1 - constraints['total_delay'] / 0.1)
        loss_score = max(0, 1 - constraints['total_loss'] / 0.1)
        util_score = max(0, 1 - constraints['max_utilization'])
        hop_score = max(0, 1 - constraints['hop_count'] / 20)
        protocol_score = max(0, 1 - constraints['protocol_transitions'] / 5)
        
        return (delay_weight * delay_score + 
                loss_weight * loss_score + 
                util_weight * util_score + 
                hop_weight * hop_score +
                protocol_weight * protocol_score)
    
    def _extract_protocols(self, graph: nx.Graph, path: List[int]) -> List[str]:
        """提取路径协议序列"""
        return [graph[path[i]][path[i+1]].get('protocol', 'Unknown') 
                for i in range(len(path) - 1)]
    
    def _select_best_strategy(self, candidates: List[RoutingStrategy],
                              business_weight: float) -> Optional[RoutingStrategy]:
        """选择最优策略"""
        if not candidates:
            return None
        
        for candidate in sorted(candidates, key=lambda x: x.score, reverse=True):
            if (candidate.estimated_delay < 0.06 and 
                candidate.estimated_loss < 0.05):
                return candidate
        
        return candidates[0] if candidates else None


class ValidationAgent(BaseAgent):
    """
    验证 Agent：闭环验证，确保策略安全性
    支持：路由环路检测、性能回退检测、协议一致性验证
    """
    
    def __init__(self, name: str, delay_threshold: float = 0.06,
                 loss_threshold: float = 0.05,
                 enable_sandbox: bool = True):
        super().__init__(name)
        self.delay_threshold = delay_threshold
        self.loss_threshold = loss_threshold
        self.enable_sandbox = enable_sandbox
        self.validation_count = 0
    
    def validate(self, strategy: Optional[RoutingStrategy], 
                 graph: nx.Graph,
                 baseline_performance: Dict = None) -> ValidationResult:
        """
        可解释验证：检查策略是否满足所有约束，并提供详细的验证报告
        """
        self.validation_count += 1
        
        rejection_reasons: List[str] = []
        improvement_suggestions: List[str] = []
        detailed_checks: Dict[str, Any] = {}
        
        if not strategy or not strategy.path:
            rejection_reasons.append("策略无效：路径为空")
            improvement_suggestions.append("请提供有效的路由路径")
            return ValidationResult(
                passed=False,
                rejection_reasons=rejection_reasons,
                improvement_suggestions=improvement_suggestions,
                detailed_checks={},
                score=0.0
            )
        
        detailed_checks['loop_free'] = self._check_no_loop(strategy.path)
        if not detailed_checks['loop_free']:
            rejection_reasons.append(f"检测到路由环路: {self._get_loop_nodes(strategy.path)}")
            improvement_suggestions.append("重新规划路径以消除环路")
        
        detailed_checks['path_valid'] = self._check_path_exists(strategy.path, graph)
        if not detailed_checks['path_valid']:
            rejection_reasons.append("路径包含不存在的边或已故障的链路")
            improvement_suggestions.append("检查所有链路状态是否为 UP")
        
        detailed_checks['delay_ok'] = strategy.estimated_delay < self.delay_threshold
        detailed_checks['delay_value'] = strategy.estimated_delay
        detailed_checks['delay_threshold'] = self.delay_threshold
        if not detailed_checks['delay_ok']:
            diff = strategy.estimated_delay - self.delay_threshold
            rejection_reasons.append(
                f"时延超标: {strategy.estimated_delay:.4f}s > {self.delay_threshold:.4f}s (超出 {diff:.4f}s)"
            )
            improvement_suggestions.append(
                f"建议选择跳数更少或协议更高效的路径（当前路径 {len(strategy.path)-1} 跳）"
            )
        
        detailed_checks['loss_ok'] = strategy.estimated_loss < self.loss_threshold
        detailed_checks['loss_value'] = strategy.estimated_loss
        detailed_checks['loss_threshold'] = self.loss_threshold
        if not detailed_checks['loss_ok']:
            diff = strategy.estimated_loss - self.loss_threshold
            rejection_reasons.append(
                f"丢包率超标: {strategy.estimated_loss:.4f} > {self.loss_threshold:.4f}"
            )
            improvement_suggestions.append("建议规避高丢包率链路")
        
        detailed_checks['protocol_compatible'] = self._check_protocol_compatibility(
            strategy.path, graph
        )
        if not detailed_checks['protocol_compatible']:
            rejection_reasons.append("路径存在协议不兼容的链路转换")
            improvement_suggestions.append("确保相邻链路协议可互通（如 Optical 不能直接连 IP）")
        
        detailed_checks['no_regression'] = self._check_no_regression(
            strategy, baseline_performance
        )
        if not detailed_checks['no_regression']:
            rejection_reasons.append("策略性能相比基准有明显回退")
            improvement_suggestions.append("选择性能更优的路径")
        
        detailed_checks['load_balance'] = self._check_load_balance(strategy.path, graph)
        if not detailed_checks['load_balance']:
            improvement_suggestions.append("部分链路负载较高，建议考虑负载均衡")
        
        passed = len(rejection_reasons) == 0
        
        if not passed:
            print(f"\n[{self.name}] [FAIL] 验证失败")
            print(f"   原因: {rejection_reasons}")
            if improvement_suggestions:
                print(f"   建议: {improvement_suggestions}")
        else:
            print(f"\n[{self.name}] [PASS] 验证通过")
        
        if strategy.reasoning_chain:
            print(f"   推理链:")
            for step in strategy.reasoning_chain:
                print(f"     - {step}")
        
        score = self._calculate_validation_score(detailed_checks)
        
        self.log_execution('validate', {
            'validation_id': self.validation_count,
            'result': 'PASS' if passed else 'FAIL',
            'path': strategy.path,
            'rejection_reasons': rejection_reasons,
            'score': score
        })
        
        if self.blackboard and passed:
            self.blackboard.publish(
                KnowledgeSource.VALIDATOR,
                'validated_strategy',
                strategy
            )
        
        return ValidationResult(
            passed=passed,
            rejection_reasons=rejection_reasons,
            improvement_suggestions=improvement_suggestions,
            detailed_checks=detailed_checks,
            score=score
        )
    
    def _check_no_loop(self, path: List[int]) -> bool:
        """检测路由环路"""
        return len(path) == len(set(path))
    
    def _get_loop_nodes(self, path: List[int]) -> List[int]:
        """找出环路中的重复节点"""
        seen = set()
        loop_nodes = []
        for node in path:
            if node in seen:
                loop_nodes.append(node)
            seen.add(node)
        return loop_nodes
    
    def _check_path_exists(self, path: List[int], graph: nx.Graph) -> bool:
        """验证路径在图中存在"""
        for i in range(len(path) - 1):
            if not graph.has_edge(path[i], path[i + 1]):
                return False
            if graph[path[i]][path[i + 1]].get('status') == 'DOWN':
                return False
        return True
    
    def _check_protocol_compatibility(self, path: List[int], graph: nx.Graph) -> bool:
        """检查路径协议兼容性"""
        if not path or len(path) < 2:
            return True
        
        prev_protocol = None
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            try:
                if not graph.has_edge(u, v):
                    continue
                curr_protocol = graph[u][v].get('protocol', '')
                if prev_protocol and curr_protocol:
                    if not graph.check_protocol_compatibility(prev_protocol, curr_protocol):
                        return False
                prev_protocol = curr_protocol
            except (KeyError, AttributeError):
                continue
        return True
    
    def _check_no_regression(self, strategy: RoutingStrategy,
                             baseline: Dict = None) -> bool:
        """检查性能是否回退"""
        if baseline is None:
            return True
        
        if strategy.estimated_delay > baseline.get('max_delay', float('inf')):
            return False
        if strategy.estimated_loss > baseline.get('max_loss', float('inf')):
            return False
        return True
    
    def _check_load_balance(self, path: List[int], graph: nx.Graph) -> bool:
        """检查路径负载均衡"""
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            util = graph[u][v].get('bandwidth_utilization', 0)
            if util > 0.9:
                return False
        return True
    
    def _calculate_validation_score(self, checks: Dict[str, Any]) -> float:
        """计算验证分数"""
        weights = {
            'loop_free': 0.25,
            'path_valid': 0.25,
            'delay_ok': 0.20,
            'loss_ok': 0.15,
            'protocol_compatible': 0.10,
            'no_regression': 0.05
        }
        
        score = 0.0
        for key, weight in weights.items():
            if checks.get(key, False):
                score += weight
        
        return score
    
    def sandbox_validate(self, strategy: RoutingStrategy,
                        env_simulation) -> Dict:
        """仿真沙箱验证"""
        if not self.enable_sandbox:
            return {'safe': True, 'simulated': False}
        
        results = {
            'safe': True,
            'simulated': True,
            'test_iterations': 100,
            'issues': []
        }
        
        for _ in range(100):
            delay_sim = sum(random.gauss(strategy.estimated_delay, 0.005)
                          for _ in range(len(strategy.path) - 1))
            if delay_sim > self.delay_threshold * 1.5:
                results['issues'].append('High delay variance detected')
                results['safe'] = False
                break
        
        return results


class AgentCluster:
    """
    Agent 集群管理器：协调三个 Agent 的协作
    集成黑板系统和因果推理引擎
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.blackboard = BlackBoard()
        self.causal_reasoner = CausalReasoner(self.blackboard)
        
        self.perceptor = PerceptionAgent(
            name=config.get('perceptor_name', 'Perceptor-01'),
            threshold_delay=config.get('delay_threshold', 0.035),
            threshold_loss=config.get('loss_threshold', 0.015),
            threshold_util=config.get('util_threshold', 0.85)
        )
        self.perceptor.attach_blackboard(self.blackboard)
        
        self.reasoner = ReasoningAgent(
            name=config.get('reasoner_name', 'Reasoner-01'),
            max_candidates=config.get('max_candidates', 10)
        )
        self.reasoner.attach_blackboard(self.blackboard)
        self.reasoner.attach_causal_reasoner(self.causal_reasoner)
        
        self.validator = ValidationAgent(
            name=config.get('validator_name', 'Validator-01'),
            delay_threshold=config.get('delay_threshold', 0.06),
            loss_threshold=config.get('loss_threshold', 0.05)
        )
        self.validator.attach_blackboard(self.blackboard)
        
        self.self_healing_attempts = 0
    
    def execute_self_healing(self, env, src: int, dst: int,
                            business_weight: float = 1.0,
                            max_retries: int = 3) -> Tuple[bool, Optional[RoutingStrategy]]:
        """
        执行完整的自愈流程
        返回: (成功标志, 路由策略)
        """
        self.self_healing_attempts += 1
        print(f"\n{'='*70}")
        print(f"[Cluster] 自愈流程 #{self.self_healing_attempts}")
        print(f"[Cluster] 路由请求: {src} -> {dst}, 业务权重: {business_weight}")
        print(f"{'='*70}")
        
        faults = self.perceptor.monitor(env.get_topology())
        print(f"[Cluster] 感知到 {len(faults)} 个风险")
        for fault in faults:
            print(f"  [{fault.severity.name}] {fault.risk_type} @ {fault.location}")
        
        for fault in faults:
            causal_links = self.causal_reasoner.analyze_fault_propagation(fault, env.get_topology())
            if causal_links:
                print(f"[Cluster] 因果分析: 发现 {len(causal_links)} 条关联影响")
        
        avoid_edges = [(f.location) for f in faults if f.risk_type == 'LINK_FAILURE']
        
        for attempt in range(max_retries):
            strategy = self.reasoner.compute_reroute(
                env.get_topology(), src, dst, business_weight,
                avoid_edges=avoid_edges
            )
            
            if not strategy:
                print(f"[Cluster] 未找到有效路径 (尝试 {attempt + 1}/{max_retries})")
                continue
            
            print(f"[Cluster] 推理引擎提议: {'->'.join(map(str, strategy.path))}")
            print(f"[Cluster] 策略评分: {strategy.score:.3f}")
            print(f"[Cluster] 协议序列: {'->'.join(strategy.protocol_path)}")
            
            result = self.validator.validate(strategy, env.get_topology())
            
            if result.passed:
                env.apply_routing_policy(strategy.path)
                return True, strategy
            
            print(f"[Cluster] 验证失败，重试中 ({attempt + 1}/{max_retries})...")
        
        return False, None
    
    def get_execution_summary(self) -> Dict:
        """获取执行摘要"""
        return {
            'total_attempts': self.self_healing_attempts,
            'perceptor_executions': len(self.perceptor.execution_history),
            'reasoner_executions': len(self.reasoner.execution_history),
            'validator_executions': len(self.validator.execution_history),
            'blackboard_publishes': self.blackboard.publish_count,
            'execution_trace': self.blackboard.get_execution_history()
        }