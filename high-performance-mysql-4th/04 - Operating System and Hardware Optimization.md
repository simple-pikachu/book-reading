# Chapter 4: Operating System and Hardware Optimization

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 75–97 页（书中印刷页码）

---

## 1. 章节导言（第 75 页）

**要点**：MySQL 性能受操作系统和硬件限制；I/O 密集型负载可优化应用，但更常应升级 I/O、增加内存或重配磁盘。

**原文**：

> Your MySQL server can perform only as well as its weakest link, and the operating system and hardware on which it runs are often limiting factors.

---

## 2. 什么限制 MySQL 性能（第 75 页）

**要点**：

| 瓶颈 | 频率 |
|------|------|
| **CPU 耗尽** | 最常见（并行查询过多或少数查询占用 CPU 过久） |
| **I/O 饱和** | 较少（SSD 普及后） |
| **内存耗尽** | 通常因给 MySQL 分配过多内存 |

**原文**：

> the most frequent bottleneck we see is CPU exhaustion.

> I/O saturation can still happen but much less frequently than CPU exhaustion. This is largely because of the transition to using solid-state drives (SSDs).

---

## 3. 如何为 MySQL 选择 CPU（第 76 页）

**要点**：

- **低延迟**：需要快速 CPU（每查询单核）。
- **高吞吐**：多 CPU 并行服务多查询。
- 未满载时，多余 CPU 可用于 InnoDB purge、网络等后台任务。

**原文**：

> Low latency (fast response time): To achieve this, you need fast CPUs because each query will use only a single CPU.

> High throughput: If you can run many queries at the same time, you might benefit from multiple CPUs to service the queries.

---

## 4. 平衡内存与磁盘（第 76–77 页）

### 4.1 缓存、读与写

- 足够内存可完全避免读磁盘（缓存命中后）。
- 写无法像读一样消除，只能延迟和合并（Write-Ahead Logging、I/O merging）。

### 4.2 工作集（Working Set）

**要点**：只需工作集在内存中即可，不必整个库都放进内存。

**原文**：

> you don't need the whole database to fit in memory for optimal performance—just the working set.

---

## 5. 固态存储（第 77–79 页）

**要点**：

- SSD 已是 OLTP 标准；HDD 仅见于超大数仓或遗留系统。
- 优势：随机 I/O、高并发；闪存写需擦除大块，有写放大和垃圾回收。
- 设备越满，GC 越忙，性能可能下降。

**原文**：

> Flash memory gives you very good random I/O performance at high concurrency.

> as the device fills up, the garbage collector has to work harder to keep some blocks clean, so the write amplification factor increases.

---

## 6. RAID 性能优化（第 79–85 页）

| 级别 | 特点 | 适用 |
|------|------|------|
| RAID 0 | 快、无冗余 | 仅开发环境 |
| RAID 1 | 读快、镜像 | 日志、双盘服务器 |
| RAID 5 | 经济、SSD 下可行 | 注意单盘故障重建性能 |
| RAID 6 | 双校验，容忍两盘故障 | 写比 RAID 5 慢 |
| RAID 10 | 镜像+条带，读写均好 | **数据存储首选** |
| RAID 50 | RAID 5 条带化 | 超大数据集 |

**RAID 缓存**：

- 读缓存通常浪费（OS/DB 已有更大缓存）。
- **写缓存**重要，但必须有 BBU 或闪存后备，否则断电可能损坏数据。
- RAID 0/1/10：100% 内存用于写缓存；RAID 5 需预留内部操作内存。

**原文**：

> RAID 10 is a very good choice for data storage.

> you shouldn't enable it unless your controller has a battery backup unit (BBU) or other nonvolatile storage.

---

## 7. RAID 故障、恢复与监控（第 81–82 页）

**要点**：

- RAID 不替代备份；需监控阵列降级/失败状态。
- 注意潜伏性介质损坏（latent corruption）；定期一致性检查。
- 热备盘（hot spare）在多盘环境下几乎必备。
- 监控 BBU 和学习周期；闪存后备缓存可避免学习周期停机。

---

## 8. 网络配置（第 86 页）

**要点**：

- 最大问题通常是**延迟**和**丢包**（1% 丢包即可严重降性能）。
- **DNS** 是常见瓶颈；生产环境建议 `skip_name_resolve`（用户 host 列只能用 IP）。
- 高并发时调整本地端口范围、`tcp_max_syn_backlog`。

**原文**：

> enabling skip_name_resolve is a good idea for production servers.

> Broken or slow DNS resolution is a problem for lots of applications, but it's particularly severe for MySQL.

---

## 9. 选择文件系统（第 87–88 页）

**要点**：

- 推荐日志文件系统：ext4、XFS、ZFS。
- ext3/4 日志模式：`data=writeback`（InnoDB 通常安全）、`data=ordered`、`data=journal`。
- 挂载选项：`noatime,nodiratime` 可提升 5%–10%。
- **推荐 XFS**；ext3 有严重限制（每 inode 单互斥锁、fsync 刷全盘脏块）。

**原文**：

> We usually recommend using the XFS filesystem.

---

## 10. 选择磁盘队列调度器（第 89 页）

**要点**：Linux 默认 `cfq` 对服务器很差；改用 `noop`（硬件 RAID/SAN）或 `deadline`（直连磁盘）。

**原文**：

> The main thing is to use anything but cfq, which can cause severe performance problems.

---

## 11. 内存与交换（第 90–91 页）

**要点**：

- 用 tcmalloc/jemalloc 替代 glibc 可提升性能、减少碎片。
- **避免 swap**：`swappiness=0`；考虑 `innodb_flush_method=O_DIRECT`。
- OOM killer 可能杀 MySQL 或 SSH；调整 `oom_score_adj`。
- `memlock` 可锁内存但危险（内存不足时崩溃）。

**原文**：

> We recommend you run your databases without using swap space at all.

> Servers should be set to 0: $ echo 0 > /proc/sys/vm/swappiness

---

## 12. 操作系统状态（第 92–94 页）

### vmstat 关键列

- `r`：等待 CPU 的进程数
- `si/so`：swap 进出（应接近 0，不超过 10 blocks/s）
- `wa`：I/O 等待 CPU 时间

### iostat 关键列

- `await`：队列等待时间
- `%util`：非标准利用率定义，单盘参考价值有限

**并发公式**：`concurrency = (r/s + w/s) * (svctm/1000)`

---

## 13. 其他有用工具（第 95 页）

dstat、collectl、mpstat、blktrace、**pt-diskstats**（Percona Toolkit）、**perf**。

---

## 14. 本章小结（第 96–97 页）

**要点**：

- 四大资源：CPU、内存、磁盘、网络。
- SSD 应为 OLTP 标准；HDD 仅用于极低成本或 PB 级数仓。
- Linux 建议：XFS、`swappiness=0`、合适的磁盘调度器。
- 问题可能「出现在一处、根因在另一处」——先问是否需要更多 I/O 还是更多内存（工作集大小）。

**原文**：

> The four fundamental resources MySQL needs are CPU, memory, disk, and network resources.

> Solid-state devices are great for improving server performance overall and should generally be the standard for databases now, especially OLTP workloads.
