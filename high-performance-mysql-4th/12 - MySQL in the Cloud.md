# Chapter 12: MySQL in the Cloud

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 313–324 页（书中印刷页码）

---

## 1. 章节导言（第 313 页）

**要点**：

- 云迁移往往不由 DBA 决定；你能控制的是如何构建数据库环境。
- 两条路径：**托管 MySQL**（省心、贵、控制少）与 **在 VM 上自建**（灵活、可观测、运维负担大）。
- 本章不覆盖云产品 bug；应关注动态信息源（newsletter、bug board）。

**原文**：

> In all likelihood, you won't have much control over whether you move to a cloud provider or even which one your organization ultimately adopts. What you can control is how you build your database environment. There are two directions you can take: managed MySQL or building on VMs.

> Managed MySQL tends to be more hands-off, but it's usually more expensive and gives you less control. Building on a VM means you get a lot more flexibility in how you build and how to observe your platform, but it requires more time and operational overhead.

---

## 2. 托管 MySQL 概览（第 313–314 页）

**要点**：

| 优势 | 劣势 |
|------|------|
| 几行配置/terraform 即可上线，含副本与定时备份 | 无 OS/文件系统访问，进程内操作受限 |
| 降低 MySQL 认知负担，适合快速起步 | 出问题只能提工单等待 |
| 各公有云均有托管方案 | 无法搭建高级拓扑，备份/恢复方式受限 |

**原文**：

> The key appeal of managed solutions is that they provide an accessible database setup without needing to get deep into MySQL specifics. With a few clicks or a terraform apply, you can have a database online with a replica and scheduled backups, and you're all ready to go.

> On the other hand, with managed MySQL you lack a lot of visibility and control. You do not have access to the operating system or the filesystem, and you are restricted in how much you can do within the process itself.

> It is worth noting that many of these cloud offerings give you a MySQL-compatible data store. This is a data store that has a SQL interface but with internal workings that may be entirely different from the Oracle MySQL that this book focuses on.

---

## 3. Amazon Aurora for MySQL（第 314–316 页）

### 3.1 核心特性

**要点**：

- **计算与存储分离**，可独立、灵活扩展。
- 托管快照备份、快速 schema 变更、审计日志、单区域内复制等运维任务。
- 集群内复制基于**专有块存储**，非社区版 MySQL 复制；可写 binlog 供跨集群复制或 CDC。
- **Aurora fast DDL**（写作时）为 AWS「lab mode」；若仍如此，见第 6 章外部在线 schema 变更工具。

**原文**：

> Aurora MySQL is a MySQL-compatible hosted database. Aurora's most appealing selling point is that it separates compute from storage, which allows them to scale separately and more flexibly.

> It is important to note that replication within an Aurora cluster is entirely proprietary to Amazon and is not the replication we know and use in Oracle MySQL. Since all Aurora instances in a cluster share the same storage layer to access data, replication within a cluster is done using block storage.

### 3.2 兼容性注意

**要点**：

- 「MySQL compatible」须确认**具体主版本**；托管 Aurora 方案**均非 MySQL 8.0 兼容**，部分旧方案仅兼容 5.6。
- 从自建 MySQL 迁移前须在应用中充分测试。

**原文**：

> When Amazon says "MySQL compatible," you have to confirm which major version of MySQL is intended in that phrase. None of the hosted solutions in Aurora is MySQL 8.0 compatible, for example, and some of the older ones are only compatible with MySQL 5.6.

### 3.3 关键产品形态

| 形态 | 说明 |
|------|------|
| **标准 Aurora** | 长期运行的计算实例 + 六副本内部复制的存储 |
| **Aurora Serverless** | 无长期计算，用 serverless 平台承载计算层，适合非持续负载 |
| **Aurora Global Database** | 多地理区域数据可用，无需手动 binlog 复制；有 trade-off，需查文档 |
| **Aurora Multi-Master** | 单区域内多节点同时写，高写可用；限制多（如 5.6 内核、节点数上限、不能与 Global Database 混用） |

**要点**：

- 关键任务库建议配合 **RDS Proxy**，缓解应用侧连接风暴。
- 各 Aurora 选项**总有 trade-off**（例如无法同时实现多写高可用与跨区域亚秒级复制）。

**原文**：

> If you are looking to put any mission-critical databases on Aurora, we strongly recommend you also consider using Amazon's RDS Proxy to manage how your application will communicate with Aurora.

> The important takeaway is that, although Aurora has a number of options, there are always trade-offs. For example, you cannot achieve both multiwriter high availability and cross-regional subsecond replication.

---

## 4. GCP Cloud SQL（第 317 页）

**要点**：

**限制**（虽运行社区版，但为支持多租户与管理而禁用部分能力）：

- `SUPER` 权限禁用
- 加载插件禁用（Cloud SQL 自有审计日志方案）
- 部分客户端禁用（如 `mysqldump`、`mysqlimport`）
- 无法 SSH 登录实例

**托管能力**：

- 原生高可用与自动故障转移
- 静态数据加密
- 灵活升级方式（维护窗口仍有停机，需与 SLO 平衡）

**原文**：

> Cloud SQL is GCP's managed MySQL offering. A core difference between this offering and AWS's is that it runs the community server but with certain features disabled specifically to allow for the multitenancy and managed aspect of the product.

---

## 5. 云上虚拟机运行 MySQL（第 318 页）

**要点**：

- 与裸金属类似：**完全控制**运维各方面。
- 可单区域主库 + 多区域副本、延时副本；可定制备份策略；性能问题可深入 OS/文件系统排查。
- 云厂商选择往往不由你决定；需了解所选托管方案能力，或论证改用 VM。

**原文**：

> Running MySQL on a VM is just like running it on bare metal. You get complete and total control over all operational aspects.

> You can run your primary MySQL in a single region but set up replicas in other regions for disaster-recovery purposes—or run a time-delayed replica.

---

## 6. 云机器类型（第 318–320 页）

### 6.1 优势

**要点**：云 VM 可按 vCPU、内存、网络、磁盘灵活选型并**随负载 resize**（如节假日临时扩容），这是上云的重要动机。

### 6.2 CPU 选型

**要点**：

- 第 4 章 CPU 指导仍适用；云上是 **vCPU**，可能与同物理机其他租户共享，延迟与利用率波动更大。
- 从物理机迁移估算公式：**vCPU 数 = (核心数 × 峰值 CPU 使用率 95%) × 2**  
  例：40 核、峰值 30% → 约 24 vCPU；无对应机型可向上取整或选自定义机型（可能更贵）。
- **目标利用率**：典型约 50%，峰值 65%–70%；持续 ≥70% 通常伴随查询延迟上升。
- 关注 CPU 芯片代际：高流量 Web 应用宜选较新代；批处理可用略旧代节省成本。

**原文**：

> with cloud providers, you're getting virtual CPUs, not physical CPUs. This means that the CPU is not exclusively yours. It may be shared with other tenants on the same physical host.

> We recommend a target of 50% typical utilization, with peaks up to 65%–70%. If you sustain 70% CPU or greater, you will likely see latency increase, and you should consider adding more CPUs.

### 6.3 内存与网络

**要点**：

- 内存：按工作集选型，**宁多勿少**（见第 1、4 章）。
- 网络：核对机器类型的带宽上限；大批量读可能在小机型上耗尽带宽。
- **跨可用区/区域出站流量通常计费**；副本仍建议放不同 zone 以冗余。

---

## 7. 磁盘类型选择（第 320–321 页）

**要点**：

- 磁盘选型一旦投入使用，迁移成本高（通常需挂第二块盘拷贝数据）。
- 读密集：更多内存优于更快磁盘；工作集大于 buffer pool 必然读盘。
- 写密集：必然写盘，易出现磁盘瓶颈。

### 7.1 本地盘 vs 网络盘

| 类型 | 特点 |
|------|------|
| **本地附加盘** | 高性能、稳定吞吐；**易丢数据**（ ephemeral）；主机故障或关机换宿主可能丢盘；通常无 RAID；建议软件 RAID（见第 4 章） |
| **网络附加盘** | 冗余可靠优先于极致性能；可能有短暂停顿；快照/备份工具便利；配合 ACID 设置（`innodb_flush_log_at_trx_commit=1`、`sync_binlog=1`）可安全快照；大容量副本恢复快 |

- 本地盘需自行解决备份（LVM、XtraBackup 等，见第 10 章）。
- 云厂商**不提供**类似硬件 RAID 卡的写缓存（BBU/闪存后备）。

**原文**：

> Locally attached disks have the benefit of offering incredibly high performance and consistent throughput but are also vulnerable to data loss.

> By contrast, network-attached disks go the other way, offering redundancy and reliability over performance.

### 7.2 SSD vs HDD

**要点**：数据卷一律 SSD；预算紧时启动盘可用 HDD，但 SSD 启动快 2–3 倍，故障重启场景更重要。

### 7.3 IOPS 与吞吐

**要点**：

- 迁移 workload 宜有历史磁盘指标；可用 Percona Toolkit 的 `pt-diskstats` 采集一天峰值。
- 新库：了解读写比；否则取性能与成本折中，并预期后续调整。

---

## 8. 自建 VM 运维贴士（第 322–324 页）

### 8.1 应对宿主机重启

**要点**：

- 无魔法规避；选项：故障转移到副本（第 9 章）或等待源库恢复。
- 非计划提升很复杂；建议让服务器自然上线、复制自动重连。

**建议**：

- SSD 启动盘，重启常 <5 分钟
- 主机 down 告警抑制最多 5 分钟
- 源库重启后可脚本动态关闭 `read_only`（配合 `crond @reboot`）；需能查询系统是否应接受写
- 自动通知相关团队（邮件/聊天）

**原文**：

> Our advice is to just allow the server to come back online and replication to reattach itself naturally.

### 8.2 分离 OS 与 MySQL 数据

**要点**：

- 快照仅含数据；网络盘可卸挂接到其他机器；可换 OS 无需重拷数据
- PID 文件、socket、部分日志建议放 OS 盘（日志也可放数据盘）

### 8.3 备份 binlog 到对象存储

**要点**：

- 设生命周期自动清理；防误删策略
- **权限**：库机可写不可读删；读删由受限账号/机器控制

### 8.4 磁盘自动扩容

**要点**：

- 网络盘按**预置容量**计费；可目标 90% 使用率 + API 自动扩容
- 注意：检测频率须高于「剩余空间被写满」所需时间；防止无限扩容（如意外 64 TB）；扩容 API 可能导致短暂停顿，须在负载下测试

**原文**：

> With network-attached disks, you pay for the amount of space provisioned, not used.

---

## 9. 本章小结（第 324 页）

**要点**：

- 公有云上数据库方案众多；DBA 常被问及托管选型及 trade-off。
- **没有免费午餐**；最有用的是结合业务阶段与运营方式框定取舍。

**原文**：

> The most important thing to keep in mind when giving your input in these discussions is that there is no free lunch. Every one of your options comes with a set of trade-offs.

> The most useful thing you can do is to frame these trade-offs in the context of how your business operates and what maturity stage it is in to help guide your organization toward the best fit.

---

## 云数据库路径总览

```
┌─────────────────────────────────────────────────────────┐
│  托管 MySQL（Aurora / Cloud SQL / 同类）                 │
│  快、省心 │ 贵、黑盒、拓扑与备份受限                      │
├─────────────────────────────────────────────────────────┤
│  云 VM 自建 MySQL                                        │
│  全控制、灵活拓扑与备份 │ 机器/磁盘/重启/备份自管         │
└─────────────────────────────────────────────────────────┘
```
