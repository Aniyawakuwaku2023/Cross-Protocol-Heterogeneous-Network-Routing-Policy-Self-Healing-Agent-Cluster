from typing import Tuple, Optional, List
from environment.network_sim import NetworkEnvironment
from agents.cluster import (
    PerceptionAgent, ReasoningAgent, ValidationAgent, 
    AgentCluster, RoutingStrategy, RiskPattern, ValidationResult
)


def run_perceptor_demo():
    """感知 Agent 演示"""
    print("\n" + "="*70)
    print("Demo 1: 感知 Agent - 多模态风险检测")
    print("="*70)
    
    env = NetworkEnvironment(num_nodes=15, num_edges=30, seed=42)
    perceptor = PerceptionAgent(
        name="Perceptor-Demo",
        threshold_delay=0.025,
        threshold_loss=0.012,
        threshold_util=0.80
    )
    
    env.inject_fault()
    env.inject_congestion(5, congestion_level=0.92)
    
    risks = perceptor.monitor(env.get_topology())
    
    print(f"\n[Result] 检测到 {len(risks)} 个风险模式:")
    for risk in risks:
        print(f"  [{risk.severity.name}] {risk.risk_type} @ {risk.location}")
        print(f"          指标: {risk.metrics}")
        print(f"          置信度: {risk.confidence:.2%}")


def run_reasoner_demo():
    """推理 Agent 演示"""
    print("\n" + "="*70)
    print("Demo 2: 推理 Agent - 长链路径搜索")
    print("="*70)
    
    env = NetworkEnvironment(num_nodes=20, num_edges=40, seed=42)
    reasoner = ReasoningAgent(name="Reasoner-Demo", max_candidates=15)
    
    edges = list(env.graph.edges())
    if len(edges) > 3:
        env.inject_fault(edges[3])
    if len(edges) > 8:
        env.inject_fault(edges[8])
    
    src, dst = 0, 15
    print(f"\n[Task] 寻找最优路径 {src} -> {dst}")
    print(f"[Constraint] 业务权重: 0.9 (高优先级)")
    
    strategy = reasoner.compute_reroute(
        env.get_topology(), src, dst, 
        business_weight=0.9,
        max_hops=10
    )
    
    if strategy:
        print(f"\n[Result] 找到最优路径:")
        print(f"  路径: {' -> '.join(map(str, strategy.path))}")
        print(f"  协议: {' -> '.join(strategy.protocol_path)}")
        print(f"  评分: {strategy.score:.4f}")
        print(f"  预计时延: {strategy.estimated_delay:.4f}s")
        print(f"  预计丢包: {strategy.estimated_loss:.4f}")
        print(f"  约束详情: {strategy.constraints}")
    else:
        print("[Result] 未找到有效路径")


def run_validator_demo():
    """验证 Agent 演示 - 可解释验证"""
    print("\n" + "="*70)
    print("Demo 3: 验证 Agent - 可解释闭环验证")
    print("="*70)
    
    env = NetworkEnvironment(num_nodes=12, num_edges=25, seed=42)
    validator = ValidationAgent(
        name="Validator-Demo",
        delay_threshold=0.05,
        loss_threshold=0.04
    )
    
    reasoner = ReasoningAgent("Temp-Reasoner")
    strategy = reasoner.compute_reroute(env.get_topology(), 0, 11)
    
    print(f"\n[Test 1] 有效路径验证:")
    if strategy:
        result = validator.validate(strategy, env.get_topology())
        print(f"  结果: {'PASS' if result.passed else 'FAIL'}")
        print(f"  评分: {result.score:.2f}")
    
    print(f"\n[Test 2] 环路检测 (带环路的路径):")
    loop_strategy = RoutingStrategy(
        path=[0, 1, 2, 1, 4],
        constraints={'total_delay': 0.03, 'total_loss': 0.01},
        score=0.8,
        protocol_path=['IP', 'OTN', 'IP'],
        estimated_delay=0.03,
        estimated_loss=0.01
    )
    result = validator.validate(loop_strategy, env.get_topology())
    print(f"  结果: {'PASS' if result.passed else 'FAIL'}")
    if result.rejection_reasons:
        print(f"  拒绝原因: {result.rejection_reasons}")


def run_causal_reasoning_demo():
    """因果推理演示"""
    print("\n" + "="*70)
    print("Demo 4: 因果推理引擎 - 故障传播分析")
    print("="*70)
    
    from agents.cluster import BlackBoard, CausalReasoner, KnowledgeSource
    
    env = NetworkEnvironment(num_nodes=15, num_edges=30, seed=42)
    blackboard = BlackBoard()
    causal_reasoner = CausalReasoner(blackboard)
    perceptor = PerceptionAgent("Perceptor-01")
    perceptor.attach_blackboard(blackboard)
    
    edges = list(env.graph.edges())
    fault_edge = env.inject_fault(edges[0])
    print(f"\n[Event] 链路 {fault_edge} 发生故障")
    
    risks = perceptor.monitor(env.get_topology())
    if risks:
        fault = risks[0]
    else:
        fault = RiskPattern(
            risk_type='LINK_FAILURE',
            location=fault_edge,
            severity=RiskLevel.CRITICAL,
            confidence=1.0,
            metrics={}
        )
    
    causal_links = causal_reasoner.analyze_fault_propagation(fault, env.get_topology())
    print(f"\n[Causal Analysis] 发现 {len(causal_links)} 条因果链:")
    for link in causal_links[:5]:
        print(f"  {link.source[0]} -> {link.target[0]}: {link.relationship} (强度: {link.strength:.2f})")
    
    secondary = causal_reasoner.predict_secondary_failures(fault, env.get_topology())
    print(f"\n[Prediction] 预测 {len(secondary)} 个潜在二次故障:")
    for edge in secondary[:3]:
        print(f"  链路 {edge} 可能因负载过高而故障")
    
    test_path = [0, 2, 5, 10, 12]
    reasoning_chain = causal_reasoner.build_reasoning_chain(fault, secondary, test_path)
    print(f"\n[Reasoning Chain] 推理链解释:")
    for step in reasoning_chain:
        print(f"  - {step}")


def run_blackboard_demo():
    """黑板系统演示"""
    print("\n" + "="*70)
    print("Demo 5: 黑板共享系统 - Agent 间知识共享")
    print("="*70)
    
    from agents.cluster import BlackBoard, KnowledgeSource
    
    blackboard = BlackBoard()
    
    blackboard.publish(
        KnowledgeSource.PERCEPTOR,
        'risk_detection',
        {'type': 'LINK_FAILURE', 'location': (3, 7)}
    )
    
    blackboard.publish(
        KnowledgeSource.REASONER,
        'routing_strategy',
        {'path': [0, 2, 5, 10], 'score': 0.85}
    )
    
    print(f"\n[BlackBoard] 知识库内容:")
    for knowledge_type, entries in blackboard.knowledge_base.items():
        print(f"  {knowledge_type}: {len(entries)} 条")
    
    latest_strategy = blackboard.query('routing_strategy', latest=True)
    print(f"\n[Query] 最新路由策略: {latest_strategy}")
    
    print(f"\n[Execution Trace] 共 {blackboard.publish_count} 次发布")


def run_cluster_demo():
    """Agent 集群自愈演示"""
    print("\n" + "="*70)
    print("Demo 6: Agent 集群 - 端到端自愈流程")
    print("="*70)
    
    env = NetworkEnvironment(num_nodes=25, num_edges=50, seed=42)
    cluster = AgentCluster({
        'max_candidates': 12,
        'delay_threshold': 0.055,
        'loss_threshold': 0.04
    })
    
    print("\n[Phase 1] 初始状态 - 注入多个故障")
    edges = list(env.graph.edges())
    env.inject_fault(edges[0])
    if len(edges) > 5:
        env.inject_fault(edges[5])
    env.inject_congestion(8, 0.95)
    
    routes = [(0, 15), (3, 20), (7, 18)]
    
    for src, dst in routes:
        success, strategy = cluster.execute_self_healing(
            env, src, dst, business_weight=0.85
        )
        if success:
            print(f"[Cluster] [OK] 路由 {src}->{dst} 成功建立")
        else:
            print(f"[Cluster] [FAIL] 路由 {src}->{dst} 失败")
    
    summary = cluster.get_execution_summary()
    print(f"\n[Summary] 执行摘要:")
    print(f"  自愈尝试次数: {summary['total_attempts']}")
    print(f"  感知 Agent 执行: {summary['perceptor_executions']} 次")
    print(f"  推理 Agent 执行: {summary['reasoner_executions']} 次")
    print(f"  验证 Agent 执行: {summary['validator_executions']} 次")
    print(f"  黑板发布次数: {summary['blackboard_publishes']}")


def run_batch_routing_demo():
    """批量路由计算演示"""
    print("\n" + "="*70)
    print("Demo 7: 批量路由 - 多业务并发计算")
    print("="*70)
    
    env = NetworkEnvironment(num_nodes=30, num_edges=60, seed=42)
    reasoner = ReasoningAgent(name="Batch-Reasoner", max_candidates=20)
    
    requests = [
        (0, 20, 0.95),
        (5, 25, 0.80),
        (10, 28, 0.70),
        (2, 18, 0.90),
        (15, 29, 0.75)
    ]
    
    print(f"\n[Task] 批量计算 {len(requests)} 条路由...")
    results = reasoner.compute_reroute_batch(env.get_topology(), requests)
    
    print(f"\n[Result] 成功计算 {len(results)}/{len(requests)} 条路由:")
    for (src, dst), strategy in results.items():
        print(f"  {src}->{dst}: {'->'.join(map(str, strategy.path[:5]))}... "
              f"(评分: {strategy.score:.3f})")


def run_self_healing_demo():
    """完整自愈流程演示（兼容原有接口）"""
    print("\n" + "="*70)
    print("Self-Healing Demo - 完整自愈流程")
    print("="*70)
    
    env = NetworkEnvironment(num_nodes=20, num_edges=40, seed=42)
    perceptor = PerceptionAgent("Perceptor-01")
    reasoner = ReasoningAgent("Reasoner-01")
    validator = ValidationAgent("Validator-01")
    
    failed_edge = env.inject_fault()
    
    faults = perceptor.monitor(env.get_topology())
    if faults:
        print(f"\n[Agent] 检测到 {len(faults)} 个链路故障")
    
    src, dst = 0, 10
    strategy = reasoner.compute_reroute(env.get_topology(), src, dst)
    
    if strategy:
        print(f"\n[Agent] 为 {src}->{dst} 推理新路径: {'->'.join(map(str, strategy.path))}")
        
        result = validator.validate(strategy, env.get_topology())
        if result.passed:
            print("[System] 自愈成功。新路由已部署。")
            env.apply_routing_policy(strategy.path)
        else:
            print("[System] 自愈验证失败。正在重试...")
    else:
        print("[System] 未找到可行路径")


def run_stress_test():
    """压力测试：模拟多次故障和恢复"""
    print("\n" + "="*70)
    print("Stress Test - 多轮故障与恢复")
    print("="*70)
    
    import random
    random.seed(123)
    
    env = NetworkEnvironment(num_nodes=30, num_edges=70, seed=123)
    cluster = AgentCluster({'max_candidates': 15})
    
    success_count = 0
    total_attempts = 5
    
    for round_num in range(total_attempts):
        print(f"\n--- 第 {round_num + 1}/{total_attempts} 轮 ---")
        
        num_faults = random.randint(1, 3)
        for _ in range(num_faults):
            try:
                env.inject_fault()
            except RuntimeError:
                break
        
        src, dst = random.randint(0, 25), random.randint(0, 25)
        while src == dst:
            src, dst = random.randint(0, 25), random.randint(0, 25)
        
        success, strategy = cluster.execute_self_healing(
            env, src, dst, business_weight=random.uniform(0.6, 1.0)
        )
        
        if success:
            success_count += 1
            print(f"[Stress Test] 第 {round_num + 1} 轮: 成功")
        else:
            print(f"[Stress Test] 第 {round_num + 1} 轮: 失败")
    
    print(f"\n[Stress Test Summary]")
    print(f"  成功率: {success_count}/{total_attempts} ({success_count/total_attempts*100:.1f}%)")
    print(f"  总自愈尝试: {cluster.self_healing_attempts}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = "full"
    
    demos = {
        'perceptor': run_perceptor_demo,
        'reasoner': run_reasoner_demo,
        'validator': run_validator_demo,
        'causal': run_causal_reasoning_demo,
        'blackboard': run_blackboard_demo,
        'cluster': run_cluster_demo,
        'batch': run_batch_routing_demo,
        'healing': run_self_healing_demo,
        'stress': run_stress_test,
        'full': None
    }
    
    if mode == 'full':
        print("\n" + "="*70)
        print("跨协议异构网络路由策略自愈 Agent 集群系统")
        print("核心特性: 黑板共享 | 因果推理 | 可解释验证")
        print("="*70)
        run_perceptor_demo()
        run_reasoner_demo()
        run_validator_demo()
        run_causal_reasoning_demo()
        run_blackboard_demo()
        run_cluster_demo()
        run_batch_routing_demo()
        run_stress_test()
    elif mode in demos:
        demos[mode]()
    else:
        print(f"可用模式: {', '.join(demos.keys())}")
        print("用法: python main.py [mode]")
        print("默认(无参数): 运行所有演示")