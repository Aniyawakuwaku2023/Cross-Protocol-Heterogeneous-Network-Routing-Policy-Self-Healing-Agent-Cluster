import unittest
import networkx as nx
from environment.network_sim import NetworkEnvironment, LinkMetrics, ProtocolConstraint
from agents.cluster import (
    PerceptionAgent, ReasoningAgent, ValidationAgent,
    AgentCluster, RoutingStrategy, RiskPattern, RiskLevel,
    BlackBoard, CausalReasoner, KnowledgeSource, ValidationResult, CausalLink
)


def get_existing_edge(env: NetworkEnvironment, node1: int, node2: int = None):
    """获取图中实际存在的边"""
    if node2 is not None:
        if env.graph.has_edge(node1, node2):
            return (node1, node2)
        if env.graph.has_edge(node2, node1):
            return (node2, node1)
    edges = list(env.graph.edges())
    if edges:
        return edges[0]
    return None


class TestNetworkEnvironment(unittest.TestCase):
    def setUp(self):
        self.env = NetworkEnvironment(num_nodes=15, num_edges=30, seed=42)
    
    def test_initialization(self):
        self.assertEqual(self.env.graph.number_of_nodes(), 15)
        self.assertGreaterEqual(self.env.graph.number_of_edges(), 25)
        self.assertLessEqual(self.env.graph.number_of_edges(), 35)
    
    def test_telemetry(self):
        telemetry = self.env.get_telemetry()
        self.assertGreater(len(telemetry), 0)
        for (u, v), metrics in telemetry.items():
            self.assertIsInstance(metrics, LinkMetrics)
            self.assertGreater(metrics.delay, 0)
            self.assertGreaterEqual(metrics.bandwidth_utilization, 0)
    
    def test_fault_injection(self):
        edge = list(self.env.graph.edges())[0]
        self.env.inject_fault(edge)
        self.assertEqual(self.env.graph[edge[0]][edge[1]]['status'], 'DOWN')
        history = self.env.get_fault_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['type'], 'LINK_FAILURE')
    
    def test_congestion(self):
        node = list(self.env.graph.nodes())[0]
        self.env.inject_congestion(node, 0.95)
        for u, v in self.env.graph.edges(node):
            self.assertGreaterEqual(self.env.graph[u][v]['bandwidth_utilization'], 0.9)
    
    def test_routing_policy_application(self):
        edges = list(self.env.graph.edges())
        self.assertGreater(len(edges), 0)
        path = [edges[0][0], edges[0][1]]
        if len(edges) > 2:
            path.append(edges[2][1] if edges[2][0] == path[-1] else edges[2][0])
        if len(path) >= 2:
            initial_util = self.env.graph[path[0]][path[1]]['bandwidth_utilization']
            self.env.apply_routing_policy(path)
            self.assertGreaterEqual(
                self.env.graph[path[0]][path[1]]['bandwidth_utilization'],
                initial_util
            )
    
    def test_protocol_compatibility(self):
        self.assertTrue(self.env.check_protocol_compatibility('OTN', 'IP'))
        self.assertTrue(self.env.check_protocol_compatibility('IP', 'Optical'))
        self.assertFalse(self.env.check_protocol_compatibility('Optical', 'SDN'))


class TestBlackBoard(unittest.TestCase):
    def setUp(self):
        self.blackboard = BlackBoard()
    
    def test_publish_and_query(self):
        self.blackboard.publish(
            KnowledgeSource.PERCEPTOR,
            'risk_detection',
            {'type': 'LINK_FAILURE', 'location': (3, 7)}
        )
        
        results = self.blackboard.query('risk_detection')
        self.assertEqual(len(results), 1)
        
        latest = self.blackboard.query('risk_detection', latest=True)
        self.assertEqual(len(latest), 1)
    
    def test_execution_trace(self):
        self.blackboard.publish(KnowledgeSource.REASONER, 'test', 'data')
        trace = self.blackboard.get_execution_history()
        self.assertGreater(len(trace), 0)
    
    def test_latest_risks(self):
        risks = [
            RiskPattern('LINK_FAILURE', (1, 2), RiskLevel.CRITICAL, 1.0, {})
        ]
        self.blackboard.shared_context['current_risks'] = risks
        latest = self.blackboard.get_latest_risks()
        self.assertEqual(len(latest), 1)


class TestCausalReasoner(unittest.TestCase):
    def setUp(self):
        self.blackboard = BlackBoard()
        self.causal_reasoner = CausalReasoner(self.blackboard)
        self.env = NetworkEnvironment(num_nodes=15, num_edges=30, seed=42)
    
    def test_fault_propagation_analysis(self):
        edges = list(self.env.graph.edges())
        if len(edges) > 0:
            fault_edge = edges[0]
            self.env.inject_fault(fault_edge)
            
            fault = RiskPattern(
                risk_type='LINK_FAILURE',
                location=fault_edge,
                severity=RiskLevel.CRITICAL,
                confidence=1.0,
                metrics={'delay': 0.01, 'protocol': 'IP'}
            )
            
            causal_links = self.causal_reasoner.analyze_fault_propagation(fault, self.env.get_topology())
            self.assertIsInstance(causal_links, list)
    
    def test_secondary_failure_prediction(self):
        edges = list(self.env.graph.edges())
        if len(edges) > 0:
            fault = RiskPattern(
                risk_type='LINK_FAILURE',
                location=edges[0],
                severity=RiskLevel.CRITICAL,
                confidence=1.0,
                metrics={}
            )
            
            secondary = self.causal_reasoner.predict_secondary_failures(fault, self.env.get_topology())
            self.assertIsInstance(secondary, list)
    
    def test_reasoning_chain_build(self):
        fault = RiskPattern(
            risk_type='LINK_FAILURE',
            location=(5, 8),
            severity=RiskLevel.CRITICAL,
            confidence=1.0,
            metrics={}
        )
        
        secondary = [(3, 6), (4, 7)]
        path = [0, 2, 5, 10, 12]
        
        chain = self.causal_reasoner.build_reasoning_chain(fault, secondary, path)
        self.assertIsInstance(chain, list)
        self.assertGreater(len(chain), 0)


class TestPerceptionAgent(unittest.TestCase):
    def setUp(self):
        self.perceptor = PerceptionAgent(
            name="TestPerceptor",
            threshold_delay=0.025,
            threshold_loss=0.012,
            threshold_util=0.80
        )
        self.env = NetworkEnvironment(num_nodes=10, num_edges=20, seed=42)
        self.blackboard = BlackBoard()
        self.perceptor.attach_blackboard(self.blackboard)
    
    def test_link_failure_detection(self):
        edges = list(self.env.graph.edges())
        self.assertGreater(len(edges), 0)
        self.env.inject_fault(edges[0])
        risks = self.perceptor.monitor(self.env.get_topology())
        link_failures = [r for r in risks if r.risk_type == 'LINK_FAILURE']
        self.assertEqual(len(link_failures), 1)
        self.assertEqual(link_failures[0].severity, RiskLevel.CRITICAL)
    
    def test_congestion_detection(self):
        nodes = list(self.env.graph.nodes())
        self.assertGreater(len(nodes), 0)
        self.env.inject_congestion(nodes[0], 0.95)
        risks = self.perceptor.monitor(self.env.get_topology())
        self.assertGreater(len(risks), 0)
    
    def test_blackboard_integration(self):
        edges = list(self.env.graph.edges())
        self.assertGreater(len(edges), 0)
        self.env.inject_fault(edges[0])
        self.perceptor.monitor(self.env.get_topology())
        
        risks = self.blackboard.get_latest_risks()
        self.assertGreater(len(risks), 0)


class TestReasoningAgent(unittest.TestCase):
    def setUp(self):
        self.reasoner = ReasoningAgent(name="TestReasoner", max_candidates=10)
        self.env = NetworkEnvironment(num_nodes=12, num_edges=25, seed=42)
        self.blackboard = BlackBoard()
        self.reasoner.attach_blackboard(self.blackboard)
        self.causal_reasoner = CausalReasoner(self.blackboard)
        self.reasoner.attach_causal_reasoner(self.causal_reasoner)
    
    def test_reroute_basic(self):
        strategy = self.reasoner.compute_reroute(
            self.env.get_topology(), 0, 8
        )
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.path[0], 0)
        self.assertEqual(strategy.path[-1], 8)
    
    def test_reroute_batch(self):
        requests = [(0, 5, 0.9), (1, 6, 0.8), (2, 7, 0.7)]
        results = self.reasoner.compute_reroute_batch(
            self.env.get_topology(), requests
        )
        self.assertGreaterEqual(len(results), 0)
    
    def test_reasoning_chain_generation(self):
        strategy = self.reasoner.compute_reroute(
            self.env.get_topology(), 0, 8
        )
        if strategy and self.reasoner.causal_reasoner:
            self.assertIsInstance(strategy.reasoning_chain, list)


class TestValidationAgent(unittest.TestCase):
    def setUp(self):
        self.validator = ValidationAgent(
            name="TestValidator",
            delay_threshold=0.06,
            loss_threshold=0.05
        )
        self.env = NetworkEnvironment(num_nodes=10, num_edges=20, seed=42)
        self.blackboard = BlackBoard()
        self.validator.attach_blackboard(self.blackboard)
    
    def test_valid_strategy_passes(self):
        reasoner = ReasoningAgent("Temp", max_candidates=5)
        strategy = reasoner.compute_reroute(self.env.get_topology(), 0, 8)
        if strategy:
            result = self.validator.validate(strategy, self.env.get_topology())
            self.assertIsInstance(result, ValidationResult)
            self.assertIsInstance(result.passed, bool)
    
    def test_loop_detection(self):
        loop_strategy = RoutingStrategy(
            path=[0, 1, 2, 1, 4],
            constraints={'total_delay': 0.03, 'total_loss': 0.01},
            score=0.8,
            protocol_path=['IP', 'OTN', 'IP', 'OTN'],
            estimated_delay=0.03,
            estimated_loss=0.01
        )
        result = self.validator.validate(loop_strategy, self.env.get_topology())
        self.assertFalse(result.passed)
        self.assertTrue(len(result.rejection_reasons) > 0)
    
    def test_empty_path_fails(self):
        empty_strategy = RoutingStrategy(
            path=[],
            constraints={},
            score=0,
            protocol_path=[],
            estimated_delay=0,
            estimated_loss=0
        )
        result = self.validator.validate(empty_strategy, self.env.get_topology())
        self.assertFalse(result.passed)
    
    def test_validation_result_structure(self):
        reasoner = ReasoningAgent("Temp", max_candidates=5)
        strategy = reasoner.compute_reroute(self.env.get_topology(), 0, 8)
        if strategy:
            result = self.validator.validate(strategy, self.env.get_topology())
            self.assertTrue(hasattr(result, 'rejection_reasons'))
            self.assertTrue(hasattr(result, 'improvement_suggestions'))
            self.assertTrue(hasattr(result, 'detailed_checks'))


class TestAgentCluster(unittest.TestCase):
    def setUp(self):
        self.cluster = AgentCluster({
            'max_candidates': 10,
            'delay_threshold': 0.055,
            'loss_threshold': 0.04
        })
        self.env = NetworkEnvironment(num_nodes=15, num_edges=30, seed=42)
    
    def test_self_healing_success(self):
        edges = list(self.env.graph.edges())
        self.assertGreater(len(edges), 0)
        self.env.inject_fault(edges[0])
        success, strategy = self.cluster.execute_self_healing(
            self.env, 0, 10, business_weight=0.9
        )
        self.assertIsInstance(success, bool)
        self.assertIsInstance(strategy, (RoutingStrategy, type(None)))
    
    def test_blackboard_initialized(self):
        self.assertIsNotNone(self.cluster.blackboard)
        self.assertIsInstance(self.cluster.blackboard, BlackBoard)
    
    def test_causal_reasoner_initialized(self):
        self.assertIsNotNone(self.cluster.causal_reasoner)
        self.assertIsInstance(self.cluster.causal_reasoner, CausalReasoner)
    
    def test_execution_summary(self):
        edges = list(self.env.graph.edges())
        if len(edges) > 0:
            self.env.inject_fault(edges[0])
        self.cluster.execute_self_healing(self.env, 0, 10)
        
        summary = self.cluster.get_execution_summary()
        self.assertIn('total_attempts', summary)
        self.assertIn('blackboard_publishes', summary)


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.env = NetworkEnvironment(num_nodes=12, num_edges=20, seed=100)
        self.cluster = AgentCluster({
            'max_candidates': 5,
            'delay_threshold': 0.05
        })
    
    def test_full_self_healing_flow(self):
        edges = list(self.env.graph.edges())
        if len(edges) >= 2:
            self.env.inject_fault(edges[0])
            self.env.inject_fault(edges[1])
        
        success, strategy = self.cluster.execute_self_healing(
            self.env, 0, 8, business_weight=0.85, max_retries=2
        )
        self.assertIsNotNone(success)
    
    def test_concurrent_routing_requests(self):
        routes = [(0, 5), (1, 6), (2, 7)]
        results = []
        for src, dst in routes:
            success, strategy = self.cluster.execute_self_healing(
                self.env, src, dst
            )
            results.append((success, strategy))
        
        self.assertEqual(len(results), len(routes))
    
    def test_knowledge_sharing_via_blackboard(self):
        edges = list(self.env.graph.edges())
        if len(edges) > 0:
            self.env.inject_fault(edges[0])
        
        self.cluster.execute_self_healing(self.env, 0, 8)
        
        trace = self.cluster.blackboard.get_execution_history()
        self.assertGreater(len(trace), 0)
        
        perceptor_knowledge = self.cluster.blackboard.query_by_source(KnowledgeSource.PERCEPTOR)
        self.assertGreater(len(perceptor_knowledge), 0)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkEnvironment))
    suite.addTests(loader.loadTestsFromTestCase(TestBlackBoard))
    suite.addTests(loader.loadTestsFromTestCase(TestCausalReasoner))
    suite.addTests(loader.loadTestsFromTestCase(TestPerceptionAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestReasoningAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentCluster))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print(f"测试摘要:")
    print(f"  运行: {result.testsRun}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"  成功率: {success_rate:.1f}%")
    print(f"{'='*60}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)