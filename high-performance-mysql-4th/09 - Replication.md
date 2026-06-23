# Chapter 9: Replication

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 227–255 页（书中印刷页码）

---

## 1. 复制概述（第 227 页）

**要点**：将源节点写入分发到一个或多个副本；用于读扩展、高可用、灾备——**不能替代备份**。

---

## 2. 复制如何工作（第 229 页）

源节点写 binary log → 副本 I/O 线程拉取 → 写入 relay log → SQL 线程重放。

---

## 3. 复制底层（第 230 页）

线程模型、日志格式、位点/GTID。

---

## 4. 选择复制格式（第 230 页）

| 格式 | 特点 |
|------|------|
| **STATEMENT** | 日志小；不确定函数、临时表问题 |
| **ROW** | 日志大；数据一致性好，**推荐** |
| **MIXED** | 自动选择 |

---

## 5. GTID（第 231 页）

全局事务标识符，简化 failover 与拓扑管理，避免位点对不齐。

---

## 6. 崩溃安全的复制（第 232 页）

`sync_binlog` 与 `innodb_flush_log_at_trx_commit` 配合，减少崩溃后位点不一致。

---

## 7. 延迟复制（第 233 页）

副本故意落后 N 秒/分钟，用于误操作恢复窗口。

---

## 8. 多线程复制（第 234 页）

`replica_parallel_workers` 并行应用 relay log，降低延迟。

---

## 9. 半同步复制（第 237 页）

至少一个副本确认收到日志后才提交，牺牲延迟换一致性。

---

## 10. 复制过滤（第 237 页）

`replicate_do_db` 等易误用导致数据不一致，慎用。

---

## 11. 复制故障转移（第 239–240 页）

- **计划提升**：维护窗口切换源。
- **非计划提升**：源故障时提升副本；需考虑数据丢失与 GTID。
- **权衡**：写可用性 vs 一致性。

---

## 12. 复制拓扑（第 241–244 页）

| 拓扑 | 说明 |
|------|------|
| **Active/Passive** | 单写，一热一备 |
| **Active/Read Pool** | 单写多读副本 |
| **链式/环形** | 一般不推荐 |

**原文**：

> The most practical replication topology is to use one source, taking all your writes, and one or more replicas.

---

## 13. 管理与监控（第 247–248 页）

`SHOW REPLICA STATUS`；`Seconds_Behind_Source` 衡量延迟（有局限）；`pt-table-checksum` 校验一致性。

---

## 14. 常见问题（第 251–254 页）

| 问题 | 处理 |
|------|------|
| 源 binlog 损坏 | 重建副本 |
| **重复 server_id** | 每实例唯一 ID |
| 未定义 server_id | 配置文件中显式设置 |
| 临时表 + statement 复制 | 改用 row 或跳过 |
| 过滤规则误配 | 审计 `SQL_LOG_BIN` 与过滤规则 |
| 延迟过大 | 并行复制、分片、临时降低耐久性（慎用） |
| 超大包 | `max_allowed_packet` |
| 磁盘满 | 监控与清理 |

---

## 15. 复制限制（第 254 页）

单源写入瓶颈、延迟、一致性与工具复杂度。

---

## 16. 本章小结（第 255 页）

**要点**：至少三副本跨 region；`super_read_only` 保护副本；出错按官方文档重建副本。

**原文**：

> Replication is not a backup.
