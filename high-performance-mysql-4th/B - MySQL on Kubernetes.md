# Appendix B: MySQL on Kubernetes

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 349–351 页（书中印刷页码）

---

## 1. 导言（第 349 页）

**要点**：

- Kubernetes 在过去五年几乎无处不在；组织自有 K8s 时迟早会被问：**MySQL 是否也该上 K8s？**
- 表面合理：K8s 集群运维复杂，希望复用专长，不止跑无状态负载。
- 需区分**好理由**与**差理由**；本章澄清围绕「数据库上容器」的 FUD。

**原文**：

> If your organization runs its own Kubernetes clusters, you will at some point get asked whether running MySQL on them too is a good idea. And on the surface it seems like a reasonable path to take.

> But there are good reasons to explore running MySQL on Kubernetes and not so good reasons to do so. Let's demystify some of the FUD around running MySQL on Kubernetes here.

---

## 2. 用 Kubernetes 供给资源（第 349–350 页）

**背景**：

- K8s 兴起前，许多公司自建或拼装开源的 VM/裸金属供给栈。
- K8s 成为较完整的计算+存储生态；「一套栈统治一切」很有吸引力。
- 有状态负载（如 MySQL）长期被排除——常见说法是「数据库不能跑在容器里」。

### 2.1 仔细界定目标

**要点**：

- 先问：**「我们具体想拿回什么价值？」**
- K8s 对无状态负载强在弹性与计算效率；对有状态负载可缩小目标为：**仅用 K8s 供给与配置数据库主机**。
- 须 upfront 明确：数据库 workload 与无状态 workload **分开管理**、运维技能不同、容器失败处理方式不同。

**原文**：

> The important thing to keep in mind is "What specific value do we want to get back here?" Kubernetes is powerful for stateless loads because it brings elasticity and efficiency of compute resources.

> This means you need to be clear up front that the database workloads that will be provisioned with Kubernetes will be managed separately from stateless workloads, will require different operator skill sets, and will handle container failure differently.

### 2.2 选择控制平面

**要点**：

- 生态中有多种 MySQL Operator；最佳选择取决于 K8s 管理 MySQL 的**范围**。
- 需要「全能」Operator（供给、故障转移、连接管理）还是**仅作供给层**、上线后用其他方式管理？
- 尽早决定控制平面期望，驱动后续可运维细节。

---

## 3. 细节事项（第 350 页）

与 K8s 工程团队（最好有专职团队）对齐前，需共识：

| 议题 | 问题 |
|------|------|
| 数据规模 | 单实例**最大数据集**多大？ |
| 存储模型 | 卷挂载到容器、恢复与数据分离？还是数据在容器内？ |
| 吞吐与资源 | 最大查询吞吐？如何限流/分配资源？ |
| 节点隔离 | 数据库节点是否与无状态弹性 workload **混部**？ |
| 控制平面 | 是否 K8s 原生？用何 Operator？ |
| 备份恢复 | 如何备份？恢复流程？ |
| 变更与升级 | MySQL 配置与版本如何安全滚动？ |
| 集群升级 | K8s 集群自身升级如何不影响数据库？ |

**原文**：

> Remember that this is now a new operating model for running a relational database, and on this less-paved road, everything gets more complex as it gets bigger.

---

## 4. 作者建议（第 350–351 页）

**要点**：

- 投资学习**已在 K8s 生态验证**的控制平面，如 **Vitess**。
- **先爬再走**：MySQL 不应是组织在 K8s 上跑 workload 的**第一只小白鼠**；先用无状态 workload 验证可行性与踩坑。
-  adoption 从**小数据集**（磁盘仅数 GB）、**非关键数据**开始，让 DBA、K8s 团队、特性团队熟悉有状态运维模型。
- 有状态 workload on K8s 仍在成熟中，相对直接跑 VM **仍处早期**；慢而谨慎的 adoption 长期回报更高。
- **自问失败模式**：若一切崩盘，如何重建？会丢数据吗？须有答案。

**原文**：

> Our advice with running MySQL on Kubernetes is to invest in learning a control plane that is already vetted and proven in the Kubernetes ecosystem, like Vitess. But also crawl before you try to run.

> MySQL should not be the first guinea pig for running workloads on Kubernetes in your organization.

> Especially consider what the failure modes look like with MySQL on Kubernetes and ask yourself: if everything goes wrong, how will I put this back together again? Will I lose data?

---

## 5. 附录小结（第 351 页）

**要点**：

- K8s 增长快、云原生生态丰富，投资吸引力大。
- 决策须从**团队与公司风险/收益** lens 审视。
- 理解有状态服务在组织 K8s 旅程中的位置；复用 K8s 投资合理，但须与**数据层稳定性**平衡。

**原文**：

> Kubernetes is one of the fastest growing infrastructure platforms in tech right now and for good reason.

> But you should consider decisions like running MySQL on Kubernetes through the lens of risk and reward to your team and your company.

> It is understandable to want to leverage existing investment in Kubernetes for all workloads, but that needs to be well balanced against your data store layer's stability needs.

---

## K8s + MySQL 采纳路径

```
明确目标（仅供给？还是全生命周期 Operator？）
        │
        ▼
选控制平面（如 Vitess）+ 与 K8s 团队对齐 SLO/备份/隔离
        │
        ▼
先无状态验证 ──► 小库、非关键数据试点
        │
        ▼
评估失败模式与数据丢失风险 ──► 再扩大规模
```
