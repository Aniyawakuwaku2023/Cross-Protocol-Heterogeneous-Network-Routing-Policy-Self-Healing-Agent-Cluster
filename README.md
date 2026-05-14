# Cross-Protocol-Heterogeneous-Network-Routing-Policy-Self-Healing-Agent-Cluster
构建了跨协议异构网络路由自愈多 Agent 集群，解决复杂网络故障收敛慢与缺乏解释性的痛点。核心逻辑：采用黑板架构实现多 Agent 协作。感知 Agent 多模态监控异常；推理 Agent 结合因果引擎分析故障传播链，执行 K-最短路径长链推理，综合时延、丢包等五维权重生成最优路由；验证 Agent 进行闭环沙箱校验并输出具象化改进建议。具体成果：面对突发故障，集群彻底摆脱人工干预，平均仅需 3 步即可全自动完成‘感知-推理-验证’自愈闭环，策略生成具备极高可解释性。
