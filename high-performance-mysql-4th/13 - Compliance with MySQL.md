# Chapter 13: Compliance with MySQL

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 325–341 页（书中印刷页码）

---

## 1. 章节导言（第 325 页）

**要点**：

- 数据库团队职责涵盖性能、可用性、成本、灾备及**合规**。
- 需协助业务保护数据、通过监管认证；合规要求应融入数据架构、自动化运维、访问管理与「基础设施即代码」。
- 本章**非法律建议**；具体控制项应咨询公司法务。

**原文**：

> Your job is not limited to managing this data while the business is running. You also need to help the business protect the data and certify for regulatory certifications that are either legally required or critical for business.

> This chapter does not seek to give you legal advice. We are looking to help you manage compliance needs when you are running a large number of databases and how to design for compliance early on.

---

## 2. 什么是合规？（第 326–328 页）

**要点**：

- **GRC**（Governance, Risk Management, Compliance）：评估风险、遵守处理/传输个人或健康数据相关法律。
- 早期创业公司合规需求少；业务增长后会面临多种法规，部分适用于全业务数据，部分仅特定范围。
- **Controls（控制项）**：公司内部定义并执行的流程与规则，降低不良风险结果概率。

### 2.1 常见法规与认证

| 名称 | 要点（对 DBA） |
|------|----------------|
| **SOC 2** | 安全、可用性、处理完整性、机密性、隐私；需变更管理、备份恢复、实例访问管理 |
| **SOX（萨班斯）** | 上市公司必须；收入相关库仅授权人员访问，变更须记录与有据；**404 控制**要求财务数据有审计轨迹 |
| **PCI DSS** | 处理信用卡数据的金融机构；持卡人数据访问控制，架构上数据分离 |
| **HIPAA** | 美国 ePHI；访问控制、加密、访问活动日志 |
| **FedRAMP** | 美国联邦云供应商认证；配置管理、访问控制、安全评估、审计 |
| **GDPR** | 欧盟个人数据；同意、访问限制、「被遗忘权」 |
| **Schrems II（2020）** | 否定 Privacy Shield；欧盟个人数据不宜进入美国资产或由美国人员访问；对架构影响大于初版 GDPR |

**原文**：

> Controls are processes and rules that a company internally defines and practices to reduce the chances of an unwanted risk outcome.

> Schrems II signaled widespread impact on all US companies that operate and collect data on EU persons.

---

## 3. 为合规控制而设计（第 328 页）

**要点**：

- 合规是**持续过程**，难以临时「贴上去」；角色分离、变更追踪等应在公司度过「找产品市场契合」阶段后尽早倡导。
- 成长到一定规模后，你需向各类审计师**提供合规证据**；理解各控制项目标可简化审计。

**原文**：

> Building for compliance is an ongoing process that cannot be easily "added on" when needed.

---

## 4. 密钥管理（第 329–331 页）

### 4.1 何谓「密钥」

- 应用/运维数据库密码
- API token
- SSH 私钥
- 证书密钥

### 4.2 实践原则

**要点**：

- 密钥须**安全存储并与配置分离**；云环境优先用云厂商密钥管理方案。
- 至少满足 **NIST** 级加密（HIPAA、FedRAMP 等要求）。
- 自托管密钥管理复杂度高；须明确密钥服务不可用时的 trade-off，并与法务、安全对齐缓存策略。
- **不要跨服务共享数据库凭证**；泄露时爆炸半径可控。
- **不要把生产库密码提交到代码仓库**；PR 合并前扫描密钥（GitHub 等可自动化）。

### 4.3 选型考量

| 维度 | 说明 |
|------|------|
| **空间限制** | 云方案可能对密钥长度有限制；SSH 密钥、SSL 私钥较长时可能需换方案或双系统 |
| **密钥轮换** | 三大云均支持自动轮换与版本；无自动轮换须规划计划/紧急轮换且不中断服务（视为一次部署） |
| **区域可用** | 运行时拉取密钥；多区域部署须考虑复制与故障模式 |

**原文**：

> Do not share database credentials across services. This is the type of decision that pays off in orders of magnitude if you have a database accidentally leak.

> Do not check production database credentials in code repositories.

---

## 5. 角色与数据分离（第 332 页）

### 5.1 合规驱动的分片

**要点**：不同合规域（如营销通信 vs 医疗新产品 PHI）应使用**独立集群**，便于对 HIPAA 等控制单独落地，不拖累现有数据集。

### 5.2 独立数据库用户

**要点**：多应用、多代码库时**尽早**为各服务分配独立凭证；泄露时爆炸半径已知且可隔离。

**原文**：

> It is very important to start well-controlled data access controls early in your organization by not sharing the same database access credentials across multiple code bases.

---

## 6. 变更追踪（第 333–337 页）

**要点**：审计不应每年成为「大 scramble」；通过结构化日志与流程，让证据**内置**于日常运维。

```
Schema 变更 ──┐
用户管理   ──┼──► 结构化日志平台 ──► 审计证据
数据访问   ──┘
```

### 6.1 数据访问日志

**推荐**：Percona Audit Log 插件或 MySQL Enterprise Audit——在数据变更「最后一跳」记录，覆盖多路径写入。

**不推荐用触发器**：

| 原因 |
|------|
| 写性能开销，高峰雪上加霜 |
| 业务逻辑进库，难测试/发布 |
| 仅能跟踪写，无法扩展读审计 |

**Percona Audit Log 要点**：

```sql
INSTALL PLUGIN audit_log SONAME 'audit_log.so';
SHOW PLUGINS;
```

- 可配置跟踪的语句动词；可安装但不监控（灵活但需监控插件确实在跑）
- 检查示例：
  - `mysql -e "show plugins" | grep -w audit_log | grep -iw active`
  - `mysqladmin variables | grep -w audit_log_policy | grep -iw queries`
- 输出：本地文件（可能撑满磁盘）或 **rsyslog** 转发至集中日志平台
- 须文档化暂存与管道；缓冲变慢会导致**查询变慢**；应做混沌测试

### 6.2 Schema 变更版本控制

**要点**（见第 6 章工具）：

- 版本控制记录**谁提出、谁审批、如何上线**
- **每集群独立仓库**；金融库与实验库审批圈不同
- 限制可提交/批准 schema 变更的人员，符合最小权限

### 6.3 数据库用户管理

**配置管理**：用户与权限纳入 CM 仓库，PR + 同行评审 = 审计证据。

**凭证轮换**（无 MySQL 8.0.14+ 双密码时）：

1. 先创建新用户名/密码
2. 验证 `SHOW GRANTS` 权限一致（宜自动化）
3. 应用部署替换配置
4. 滚动重启服务
5. 删除旧用户

**MySQL 8.0.14+**：双密码 + 密码过期策略简化轮换。

**清理闲置用户**：定期对比实例用户与应用配置；建议**六个月未连接则删除**。可用 Performance Schema：

```sql
UPDATE performance_schema.setup_instruments
SET ENABLED='YES' WHERE NAME='memory/sql/user_conn';
-- 查询 performance_schema.users
```

或结合审计日志判断近期是否连接。

---

## 7. 备份与恢复流程（第 338–340 页）

**要点**（第 10 章详述备份类型）：

SOC 2 等常要求**创建并测试**备份（本来也应测试）。

| 要求 | 说明 |
|------|------|
| 自动化备份 | 不可全靠手工 |
| 失败告警 | 备份失败须通知 |
| 自动化恢复测试 | 并追踪失败与修复 |
| 集中日志 | 实例可替换，日志应在中央存储 |

**实现思路**：

- 将备份/恢复测试作为**监控检查**（需支持长时间任务）；或与监控团队协调
- 或留「面包屑」文件（带时间戳），监控快速检查文件存在
- 记录备份/恢复耗时指标，对照 MTTR/RPO 目标；实例过大时数据支撑拆分或调整 SLA
- **备份存储权限**：许多泄露来自备份桶权限过宽，而非攻破在线系统

**原文**：

> Many security breaches happen not through breaching the live infrastructure, but through backups leaking from a storage bucket somewhere.

---

## 8. 本章小结（第 341 页）

**要点**：

- 合规影响法务、财务、IT 与发布流程；本章聚焦 DBA 职责。
- **提前规划**：应用用户分离、轮换策略、加密存储密码、可信日志管道、受控 schema 变更。
- 目标不是一次覆盖全部控制项，而是让**在 scope 内的证据**尽可能自动化、易汇总。

**原文**：

> Broadly, the best way to get ahead of control-related nightmares is to plan early. Separate your application users, plan a credential rotation strategy, and ensure that your passwords are always stored encrypted—never as plain text.

> Ultimately, these controls are meant to protect the business and your customers' privacy.

---

## 合规建设检查清单

| 领域 | 早期动作 |
|------|----------|
| 密钥 | 云 KMS、禁止密码入库、不共享 DB 用户 |
| 架构 | 敏感数据独立集群/用户；ProxySQL 分用户路由可兼顾合规 |
| 审计 | Audit 插件 + rsyslog/集中日志；勿用触发器 |
| 变更 | Schema CM + 每集群仓库；用户权限 CM |
| 备份 | 自动备份/测试/告警/集中日志；收紧备份桶 ACL |
