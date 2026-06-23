# Chapter 5: Optimizing Server Settings

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 99–124 页（书中印刷页码）

---

## 1. 章节导言（第 99 页）

**要点**：

- 配置应基于**工作负载、数据和应用需求**，而非仅硬件规格。
- 正确设置少数基本项后，进一步调优收益通常很小；更应关注 schema、索引和查询设计。
- 不要盲目信任论坛/Stack Overflow 的「最优配置」；变更前读手册并测试。

**原文**：

> You should configure the server for the workload, data, and application requirements, not just the hardware.

> Changing them without understanding the impact can lead to crashes, constant stalls, or slow performance.

---

## 2. MySQL 配置如何工作（第 100–103 页）

**要点**：

- 配置来源：命令行参数 + 配置文件（Unix 常见 `/etc/my.cnf` 或 `/etc/mysql/my.cnf`）。
- 用 `mysqld --verbose --help` 确认实际读取的配置文件路径。
- **作用域**：global、session、per-object；动态变量用 `SET GLOBAL` 修改，重启后丢失（除非写入配置文件）。
- **8.0 `SET PERSIST`**：同时生效于运行时并持久化到磁盘。

**原文**：

> MySQL 8.0 introduced a new feature called persisted system variables... The new syntax SET PERSIST now allows you to set the value once for runtime and MySQL will write this setting out to disk.

---

## 3. 规划变量变更（第 104 页）

**要点**：先优化查询和 schema；用版本控制跟踪配置变更；监控 SLO 而非仅跑 benchmark。

---

## 4. 不该做的事（第 105–106 页）

**要点**：

| 不要做 | 原因 |
|--------|------|
| 迭代 benchmark「调优」 | 投入大、收益小 |
| **按比率调优**（如 buffer pool 命中率） | 命中率与性能无因果关系 |
| 使用「调优脚本」 | 可能固化错误实践 |
| 相信崩溃时的内存公式 | 过时且不可靠 |

**原文**：

> You should not "tune by ratio." ... the cache hit ratio has nothing to do with whether the cache is too large or too small.

> Don't believe the popular memory consumption formula—yes, the very one that MySQL itself prints out when it crashes.

---

## 5. 创建配置文件（第 106–108 页）

**要点**：

- 提供最小示例配置（`innodb_buffer_pool_size`、`innodb_log_file_size`、`max_connections` 等需按环境填写）。
- **8.0 `innodb_dedicated_server`**：按可用内存自动配置 buffer pool、log 等四项，云环境扩容时尤其有用。
- `open_files_limit` 尽量设大，避免 error 24。
- 用 `mysqladmin extended-status -ri60` 观察状态变量变化。

---

## 6. 配置内存使用（第 109–111 页）

### 6.1 每连接内存

峰值连接数 × 每查询内存；注意 prepared statements、数据字典等意外消耗。

### 6.2 为 OS 预留内存

`innodb_dedicated_server` 通常用 50%–75% RAM，至少留 25% 给连接、OS 等。

### 6.3 InnoDB Buffer Pool

- 最重要的性能变量；缓存行数据、索引、自适应哈希、change buffer、锁等。
- 不必远大于实际数据量；过大导致关闭/预热慢。
- `innodb_buffer_pool_dump_at_shutdown` + `innodb_buffer_pool_load_at_startup` 加速冷启动。

### 6.4 Thread Cache

- `thread_cache_size`：保持 `Threads_created` 每秒 < 10（理想 < 1）。
- 按 `Threads_connected` 波动设置（如 100–120 连接 → cache 20）。

---

## 7. 配置 I/O 行为（第 112–118 页）

### 7.1 InnoDB 事务日志

- 将随机写转为顺序 log I/O；大小由 `innodb_log_file_size` × `innodb_log_files_in_group` 控制。

### 7.2 Log Buffer

- 默认 1 MB；`innodb_log_buffer_size` 建议 1–8 MB。

### 7.3 `innodb_flush_log_at_trx_commit`

| 值 | 行为 |
|----|------|
| 0 | 每秒刷盘，提交时不刷 |
| **1** | 每次提交刷到持久存储（**默认，最安全**） |
| 2 | 每次提交写 log，每秒刷盘 |

### 7.4 `innodb_flush_method`

- 有 BBU 的 RAID 推荐 **O_DIRECT**。

### 7.5 表空间

- `innodb_file_per_table=1` 推荐；注意 DROP TABLE 在旧版本/ext3 上可能很慢（8.0.23+ 已改善）。
- 长事务 + REPEATABLE READ → undo log 膨胀；监控 `History list length`；可用 `innodb_max_purge_lag` 限流。

### 7.6 其他 I/O

- **`sync_binlog=1`** 强烈推荐，勿改。
- 好 RAID + BBU 写缓存 + SSD 是生产标配。

---

## 8. 配置并发（第 119 页）

**要点**：

- 5.7+ 通常无需限制并发；瓶颈时首选**分片**。
- 旧版本可调 `innodb_thread_concurrency`（0=无限制）。
- `innodb_commit_concurrency` 限制同时提交线程数。

---

## 9. 安全设置（第 120–122 页）

| 选项 | 说明 |
|------|------|
| `max_connect_errors` | 默认 100 太小，可增大或配合 `skip_name_resolve` |
| `max_connections` | 覆盖正常负载 + 管理余量（500 可作起点） |
| `skip_name_resolve` | **强烈推荐**，禁用 DNS 认证查找 |
| `sql_mode` | 谨慎变更，升级前检查默认值变化 |
| `sysdate_is_now` | 使 SYSDATE() 确定性，利于复制/恢复 |
| `read_only` / `super_read_only` | **副本强烈推荐** |

---

## 10. 高级 InnoDB 设置（第 122–123 页）

| 选项 | 说明 |
|------|------|
| `innodb_buffer_pool_instances` | 多核高并发下减少全局互斥锁争用 |
| `innodb_io_capacity` | 告知 InnoDB 可用 I/O 能力（SSD 可设很高） |
| `innodb_read/write_io_threads` | 默认各 4，I/O 繁忙时可增加 |
| `innodb_strict_mode` | 非法 CREATE TABLE 选项报错而非警告 |
| `innodb_old_blocks_time` | 设 ~1000ms 防止 ad hoc 查询驱逐热页 |

---

## 11. 本章小结（第 124 页）

**要点**：

1. 从示例配置出发，设基本项 + 安全项即可。
2. 专用服务器首选 **`innodb_dedicated_server`**（处理约 90% 性能配置）。
3. 否则最重要两项：**`innodb_buffer_pool_size`**、**`innodb_log_file_size`**。
4. 不要「调优」、不要用比率/公式/调优脚本。

**原文**：

> innodb_dedicated_server, which handles 90% of your performance configuration.

> Congratulations—you just solved the vast majority of real-world configuration problems we've seen!
