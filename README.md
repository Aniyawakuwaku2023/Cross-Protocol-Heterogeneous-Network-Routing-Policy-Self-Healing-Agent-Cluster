# 跨协议异构网络路由策略自愈 Agent 集群系统

[English](README_EN.md) | 简体中文

## 项目简介

这是一个基于多 Agent 协作的智能网络自愈系统，实现了跨协议异构网络环境下的故障感知、长链推理路由与闭环验证。系统包含感知、推理、验证三个核心 Agent，通过黑板共享系统实现协作，适用于 OTN/IP/Optical/MPLS/SDN 等多种协议共存的复杂网络环境。

## 核心特性

- **多 Agent 协作架构**：感知 Agent、推理 Agent、验证 Agent 分工协作，通过黑板共享系统实现知识传递
- **因果推理引擎**：分析故障传播链，预测二次故障风险，构建可解释的推理链
- **长链路径搜索**：K-最短路径算法，综合评估时延、丢包、带宽、跳数、协议约束
- **可解释验证**：验证 Agent 输出结构化的拒绝原因与改进建议，而非简单的通过/失败
- **跨协议支持**：支持 OTN、IP、Optical、MPLS、SDN 等多种传输协议及其兼容性约束
- **多模态感知**：实时监控链路时延、丢包率、带宽利用率、抖动等指标

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        网络环境模拟器                             │
│                  (NetworkEnvironment)                            │
│         支持多协议异构拓扑 / 故障注入 / 遥测数据                  │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      黑板共享系统 (BlackBoard)                    │
│         知识发布/订阅 / 执行轨迹追踪 / Agent 间上下文共享         │
└─────────────────────────────────────────────────────────────────┘
            │                   │                    │
            ▼                   ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   感知 Agent    │  │   推理 Agent    │  │   验证 Agent    │
│ (Perception)    │  │  (Reasoning)    │  │  (Validation)   │
│                 │  │                 │  │                 │
│ • 多模态监控    │  │ • K-最短路径    │  │ • 环路检测      │
│ • 风险识别      │  │ • 多约束评分    │  │ • 性能验证      │
│ • 协议检测      │  │ • 路径避让      │  │ • 协议兼容性    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
            │                   │                    │
            └───────────────────┴────────────────────┘
                                │
                    ┌───────────────────────┐
                    │    因果推理引擎       │
                    │  (CausalReasoner)     │
                    │                       │
                    │ • 故障传播分析        │
                    │ • 二次故障预测        │
                    │ • 推理链构建          │
                    └───────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.8+
- NetworkX 3.0+

### 安装依赖

```bash
pip install networkx
```

### 运行演示

```bash
# 运行完整演示
python main.py

# 运行特定模块
python main.py perceptor   # 感知 Agent 演示
python main.py reasoner    # 推理 Agent 演示
python main.py validator   # 验证 Agent 演示
python main.py causal      # 因果推理演示
python main.py blackboard  # 黑板系统演示
python main.py cluster     # 集群自愈演示
python main.py stress      # 压力测试
```

### 运行测试

```bash
python test_cluster.py
```

## 项目结构

```
PythonProject/
├── environment/
│   └── network_sim.py    # 网络环境模拟器
│       ├── NetworkEnvironment     # 跨协议异构网络环境
│       ├── LinkMetrics           # 链路多模态指标
│       └── ProtocolConstraint    # 协议约束规则
├── agents/
│   └── cluster.py         # Agent 集群核心模块
│       ├── BlackBoard             # 黑板共享系统
│       ├── CausalReasoner         # 因果推理引擎
│       ├── PerceptionAgent        # 感知 Agent
│       ├── ReasoningAgent         # 推理 Agent
│       ├── ValidationAgent        # 验证 Agent
│       └── AgentCluster           # 集群管理器
├── main.py               # 主程序入口
├── test_cluster.py       # 单元测试
└── README.md             # 项目文档
```

## 核心模块详解

### 1. 感知 Agent (PerceptionAgent)

负责实时监控网络状态，识别潜在风险：

```python
perceptor = PerceptionAgent(
    name="Perceptor-01",
    threshold_delay=0.035,
    threshold_loss=0.015,
    threshold_util=0.85
)
risks = perceptor.monitor(env.get_topology())
```

### 2. 推理 Agent (ReasoningAgent)

基于长链推理生成最优路由策略：

```python
reasoner = ReasoningAgent(name="Reasoner-01", max_candidates=10)
strategy = reasoner.compute_reroute(
    graph=env.get_topology(),
    source=0,
    target=10,
    business_weight=0.9
)
```

### 3. 验证 Agent (ValidationAgent)

闭环验证策略安全性，输出可解释的验证结果：

```python
validator = ValidationAgent(
    name="Validator-01",
    delay_threshold=0.06,
    loss_threshold=0.05
)
result = validator.validate(strategy, env.get_topology())
# result.passed                    # 是否通过
# result.rejection_reasons         # 拒绝原因
# result.improvement_suggestions   # 改进建议
# result.detailed_checks          # 详细检查结果
```

### 4. Agent 集群 (AgentCluster)

一键执行完整自愈流程：

```python
cluster = AgentCluster({
    'max_candidates': 10,
    'delay_threshold': 0.055,
    'loss_threshold': 0.04
})
success, strategy = cluster.execute_self_healing(
    env=network_env,
    src=0,
    dst=15,
    business_weight=0.85
)
```

## 运行效果示例

```
======================================================================
[Cluster] 自愈流程 #1
[Cluster] 路由请求: 0 -> 15, 业务权重: 0.85
======================================================================
[Cluster] 感知到 3 个风险
  [CRITICAL] LINK_FAILURE @ (5, 10)
  [WARNING] DEGRADATION @ (8, 12)
[Cluster] 因果分析: 发现 12 条关联影响
[Cluster] 推理引擎提议: 0->2->7->12->15
[Cluster] 策略评分: 0.731
[Cluster] 协议序列: Optical->IP->OTN

[Validator-01] [PASS] 验证通过
   推理链:
     - 观察到 LINK_FAILURE @ (5, 10)
     - 预测可能的二次故障: 2 条高风险链路
     - 选择路径 0->2->7->12->15
     - 路径中 4/4 条链路不受故障影响
```

## 技术亮点

### 多约束综合评分

推理 Agent 采用加权评分机制，综合考虑多个约束条件：

| 约束维度 | 权重 | 说明 |
|---------|------|------|
| 时延 | 35% | 端到端总时延 |
| 丢包率 | 25% | 端到端总丢包率 |
| 带宽利用率 | 20% | 路径最大链路利用率 |
| 跳数 | 10% | 路径长度 |
| 协议转换 | 10% | 协议切换次数 |

### 因果推理链

系统不仅能找到故障后的替代路径，还能解释"为什么选择这条路径"：

1. **故障传播分析**：分析故障如何影响相邻节点和链路
2. **二次故障预测**：预测负载重分配可能引发的级联故障
3. **推理链构建**：输出结构化的决策解释

### 协议兼容性约束

系统内置了真实的协议约束规则：

| 协议 | 可连接的协议 | 说明 |
|------|-------------|------|
| OTN | OTN, IP, MPLS, SDN | 光传送网 |
| IP | 全部 | IP 协议 |
| Optical | Optical, OTN | 光层 |
| MPLS | OTN, IP, MPLS, SDN | 多协议标签交换 |
| SDN | OTN, IP, MPLS, SDN | 软件定义网络 |

## 扩展建议

1. **接入真实网络控制器**：将 NetworkEnvironment 替换为真实 SDN 控制器接口
2. **引入机器学习**：基于历史数据训练路径预测模型
3. **增加并发控制**：支持多路由请求的并发处理
4. **完善协议栈模拟**：增加协议转换开销和设备状态模拟

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题或建议，欢迎提交 Issue。
