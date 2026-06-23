# Chapter 10: Backup and Recovery

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 257–286 页（书中印刷页码）

---

## 1. 为何要备份（第 258 页）

**要点**：备份是为**恢复**；需定义 RPO（可接受数据丢失量）和 RTO（可接受恢复时间）。

---

## 2. 恢复需求（第 259 页）

在设计备份方案前先明确业务可容忍的丢失与停机时间。

---

## 3. 设计备份方案（第 260–267 页）

| 维度 | 选项 |
|------|------|
| **在线 vs 离线** | 优先在线（InnoDB 热备） |
| **逻辑 vs 物理** | 逻辑可移植；物理（raw）更快恢复 |
| **备份内容** | 数据 + binlog（时间点恢复） |
| **增量/差异** | 减少全备频率 |

**原文**：

> Everyone knows that they need backups, but not everyone realizes that they need recoverable backups.

---

## 4. 复制与备份（第 268 页）

- 从副本备份可减少源库压力。
- **副本不是备份**；需 `super_read_only` 保证一致性。
- **延迟复制**可提供误操作恢复窗口。

---

## 5. 管理与备份 Binary Log（第 269 页）

- 频繁备份 binlog；`binlog_expire_logs_seconds` 控制保留。
- 勿手工删除 binlog 文件。

---

## 6. 备份工具（第 269–270 页）

| 工具 | 说明 |
|------|------|
| **Percona XtraBackup** | 开源物理热备，推荐 |
| **MySQL Enterprise Backup** | Oracle 商业方案 |
| **mydumper** | 多线程逻辑备份，优于 mysqldump |
| **mysqldump** | 单线程，大数据集慢 |

---

## 7. 备份数据（第 270–278 页）

### 逻辑备份

`mysqldump` / `mydumper`；可压缩管道导入。

### 文件系统快照

LVM snapshot；需预留 copy-on-write 空间。

### XtraBackup

拷贝 `.ibd` + tail redo log → **prepare** 使数据一致。

---

## 8. 从备份恢复（第 281–285 页）

**通用步骤**：停服/限流 → 准备环境 → 恢复文件或导入 SQL → 回放 binlog → 验证 → 开放服务。

- 逻辑恢复：分块提交，避免单事务过大。
- 物理恢复：检查文件权限属主；观察 error log。
- 恢复期间可用 `--skip-networking` 隔离。

---

## 9. 本章小结（第 286 页）

**要点**：

- **定期测试恢复**；mysqldump 几小时备份可能需数周恢复。
- 首选 **XtraBackup（物理）+ mydumper（逻辑）**。
- 通过 DROP TABLE / 机房丢失测试验证备份有效性。

**原文**：

> Don't fall into the trap of thinking that a replica is a backup.

> The worst time to find out how long your recovery will take is when you actually need it.
