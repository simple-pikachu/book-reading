# Chapter 2: Monitoring in a Reliability Engineering World

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 19–39 页（书中印刷页码）

---

## 1. 章节导言（第 19 页）

**要点**：SRE 原则帮助回答「客户体验是否可接受」「是否应投入可靠性工作」「如何平衡新功能与琐事」；监控应关注**结果（outcomes）**而非**产出（outputs）**。

**原文**：

> Site reliability engineering has changed how teams think about operational work. This is because it consists of a set of principles that allow us to more easily answer questions like: Are we providing an acceptable customer experience? Should we focus on reliability and resilience work? How do we balance new features against toil?

> "Our measure should focus on outcomes, not outputs."

---

## 2. 可靠性工程对 DBA 团队的影响（第 20 页）

**要点**：

- 传统监控侧重单服务器深度剖析（反应式）。
- DBA 角色演变为 SRE / DBRE；服务级别帮助定义「客户何时不满」并平衡时间分配。

**原文**：

> For many years, monitoring database performance relied on deep dives into single-server performance. That still has a lot of value but tends to be more about reactive measurements, like profiling a server that is performing poorly.

> The role of a DBA became more complex and turned into more of a site reliability engineer (SRE) or database reliability engineer (DBRE).

---

## 3. 定义服务级别目标（第 20–21 页）

**要点**：组织内对齐目标前需明确四个问题——测什么、可接受值、降级状态、失败状态。

### 核心术语

| 术语 | 含义 |
|------|------|
| **SLI**（Service Level Indicator） | 「如何衡量客户是否满意？」 |
| **SLO**（Service Level Objective） | 「SLI 的最低可接受范围是多少？」 |
| **SLA**（Service Level Agreement） | 写入合同的 SLO，违约有财务等后果（可选） |

**原文**：

> An SLI answers the question, "How do I measure whether my customers are happy?"

> An SLO answers the question, "What is the minimum I can allow my SLI to be to ensure that my customers are happy?"

> An SLA is an SLO that has been included in an agreement with one or more customers of the business (paying customers, not internal stakeholders), with financial or other penalties if that SLA is not met.

---

## 4. 让客户满意需要什么（第 22 页）

**要点**：

- **不要**将 SLO 设为 100%；定义「让客户满意的最低标准」。
- 可用性每多一个「9」成本急剧上升（见 Table 2-1）。
- 不同功能可有不同 SLI/SLO。

**原文**：

> You must fight that urge, though. Remember that the goal of picking indicators and objectives is to evaluate at any time, with an objective metric, whether your team can innovate with new features or if stability is at risk.

> Reaching three nines of availability is no small feat. Three nines over a whole year amount to just over eight hours, translating to only 10 minutes in a given week.

---

## 5. 测量什么（第 23 页）

**要点**：MySQL 场景下 SLI/SLO 围绕三大主题——**可用性（availability）**、**延迟（latency）**、**无关键错误（lack of critical errors）**。

**原文**：

> In the context of MySQL, it needs to be a representation that defines three major themes: availability, latency, and lack of critical errors.

> "I expect 99.5% of my database requests to be served in less than two milliseconds with no errors" is both a sufficient SLI with a clear SLO and not simple.

---

## 6. 监控方案（第 24 页）

**要点**：

| 类型 | 工具/方案 |
|------|-----------|
| **商业** | SolarWinds Database Performance Management |
| **开源** | Percona Monitoring and Management (PMM) |
| **日志分析** | slow log + Performance Schema → pt-query-digest |
| **深度剖析** | Performance Schema（第 3 章详述，非 SLO 评估首选） |

**原文**：

> Query analysis and monitoring query latency in the context of SLIs and SLOs need to focus on customer experience.

> This is not a tool to determine solely if you are meeting your service reliability promises, as it is far deep in the internals of MySQL.

### 关于「生产环境测试」

**要点**：生产环境测试有价值——快速反馈、促进协作、精准调试。

**原文**：

> Production is where you discover how that change interacts with the rest of the system, at scale, with real customer traffic.

---

## 7. 监控可用性（第 25–26 页）

**要点**：

- 可用性 = 能响应客户请求且无错误（HTTP 200/202 等）。
- 需讨论：灾难时哪些功能不可协商、何为「灾难性」失败、降级形态、MTTR。
- **首选**：从客户端或远程端点验证（被动读应用日志 / 主动 synthetic 测试如 `SELECT 1`）。
- **领先指标**：`Threads_running` 快速增长；接近 `max_connections`。

**原文**：

> Availability is being able to respond to customer requests without an error.

> The preferred method to verify availability is from a client or remote endpoint.

> When threads running are growing at a fast rate and not showing any signs of decline, that indicates queries are not finishing fast enough.

---

## 8. 监控查询延迟（第 27 页）

**要点**：

- 除数据库内部延迟外，还需客户端上报查询完成时间。
- 工具：Datadog、SolarWinds、PMM；追踪：Honeycomb、Lightstep。
- 需与应用团队密切协作。

**原文**：

> besides tracking query latency from the database server directly, you would also be well served by tooling the clients to report on time to query completion, so you can get as close to the customer experience as possible.

---

## 9. 监控错误（第 27–28 页）

**要点**：

- 偶发错误 + 重试可接受；**错误率加速**才是危险信号。
- 客户端错误预警：`Lock wait timeout`（行锁争用）、`Aborted connections`（接入层问题）。
- 服务端：`Connection_errors_xxx` 计数器突增。
- 单次即严重：`read-only mode`、`too many connections`、`cannot create new thread`。

**原文**：

> The rate of errors happening, though, across the fleet of services handling database queries in your infrastructure can be a crucial indicator of brewing trouble.

> getting errors that the MySQL instance is running in read-only mode is a sign of issues even if these errors do not happen very often.

---

## 10. 主动监控（第 29–35 页）

**要点**：SLO 监控关注客户是否满意；**主动监控（steady state monitoring）**提供领先指标，在客户感知失败前预警。

### 10.1 磁盘增长（第 29 页）

- 理想：监控磁盘使用率**增长率**。
- 次优：多阈值（工作时间警告 + 非工作时间严重告警）。
- 最低：单一阈值，需预留足够 lead time。

### 10.2 连接增长（第 30 页）

- 风险 1：`threads_connected` 高但 `threads_running` 低 → 空闲连接过多。
- 风险 2：两者均高 → 数据库过载。
- 用 `threads_connected/max_connections` 百分比监控。
- **连接风暴**：应用感知延迟后开更多连接，加剧负载。

### 10.3 复制延迟（第 31 页）

- 读副本时延迟导致数据不一致感。
- 长期趋势预示写容量瓶颈。
- 告警需可执行；不读副本时勿过度告警。

### 10.4 I/O 利用率（第 32 页）

- 监控 `iostat` 的 IOwait、`IOutil`（持续接近 100% 可能表示全表扫描）。

### 10.5 自增键空间（第 33 页）

- 默认 signed integer 自增主键可能耗尽；长期监控剩余空间。
- PMM：`-collect.auto_increment.columns`；或查 `information_schema`。

### 10.6 备份创建/恢复时间（第 34–35 页）

- 灾难恢复计划需定期验证并调整目标。
- 监控备份恢复耗时趋势（至少一年保留）。

### 10.7 功能分片 vs 水平分片（第 34 页）

| 类型 | 含义 |
|------|------|
| **Functional sharding** | 按业务功能将特定表拆到独立集群 |
| **Horizontal sharding** | 数据集过大，拆到多集群 + 查找机制 |

**原文**：

> Functional sharding means splitting specific tables that serve a specific business function into a dedicated cluster.

> Horizontal sharding is when you have a data set that has grown past the size you can reliably serve out of a single cluster.

---

## 11. 长期性能测量（第 36–38 页）

### 11.1 了解业务节奏（第 36 页）

**要点**：峰值流量可能是平均值的数个数量级；需了解业务周期（电商双11、HR 开放注册、情人节鲜花等）。

### 11.2 有效追踪指标（第 37 页）

**要点**：长期规划关注容量、改进时机、成本；并非所有 on-call 指标都适合长期趋势。

### 11.3 监控工具选型（第 37–38 页）

| 原则 | 说明 |
|------|------|
| **拒绝平均值** | 长期存储用平均值会抹平峰值，产生虚假安全感 |
| **百分位数** | 95th percentile 更易与 SLO 对齐 |
| **长保留期 + 性能** | 能流畅展示长时间跨度数据 |

### 11.4 用 SLO 指导整体架构（第 38 页）

**要点**：SLI/SLO 不仅反映当前表现，还可指示何时投资分片/扩展（详见第 11 章）。

**原文**：

> the same SLIs and SLOs that tell you how the system is performing now can also guide you to knowing when it is time to invest in scaling MySQL.

---

## 12. 本章小结（第 39 页）

**要点**：

- SLI/SLO 应随业务成长持续改进，非一成不变。
- 始终聚焦客户体验；兼顾 reactive 与 proactive 监控。
- 三大关键领域：**延迟、可用性、错误**。
- 主动监控：连接增长、磁盘空间、磁盘 I/O 与延迟。

**原文**：

> They are not meant to be set in stone after the first time you define some SLIs and SLOs.

> We recommend setting goals up front on three key areas: latency, availability, and errors.

> make sure you're also doing proactive monitoring in the areas of connection growth, disk space, and disk I/O and latency.
