# Chapter 2: InnoDB 存储引擎

> 来源：《MySQL技术内幕：InnoDB存储引擎（第2版）》姜承尧  
> 页码范围：约第 17–61 页（书中印刷页码）  
> 对照版本：MySQL 8.0.34

说明：本地 PDF 为扫描件；原文摘自第2版公开书摘整理，与印刷页可能有少量标点差异。

---

## 1. 概述与早期性能叙事（约第 17–19 页）

**要点**：

- InnoDB 面向高并发 OLTP；书中用早期互联网站点案例说明其承载能力。
- 读本章时重点抓**内存结构、刷新、Checkpoint、关键特性**；不要死磕书中 InnoDB 1.2 的 Master Thread 逐步流程（8.0 后台任务已高度拆分）。

**原文**：

> 在著名的社交新闻网站 Slashdot.org 以及 Mytrix 等应用中，InnoDB 存储引擎得到了广泛使用。据称，在 Mytrix 的应用中，InnoDB 存储引擎可以支持每秒 800 次左右的并发访问请求，并且数据库的大小已经超过了 1TB。这充分显示了 InnoDB 存储引擎在 OLTP 应用中的强大处理能力。

**8.0.34 新写法**：

```sql
SELECT VERSION();
SHOW VARIABLES LIKE 'innodb_version';
SHOW ENGINE INNODB STATUS\G
SHOW STATUS LIKE 'Innodb_%';
-- 现代容量与 QPS 取决于硬件、缓冲池、redo、业务模型；案例仅作文史背景
```

---

## 2. 后台线程（约第 20–24 页）

**要点**：

- 后台线程负责刷新脏页、合并缓冲、回收 undo、写 redo 等，保证缓冲池与磁盘最终一致。
- 书中按 Master Thread、IO Thread、Purge Thread 等分类讲述；8.0 中 Page Cleaner、purge 等已多线程化，Master Thread「每秒/每十秒循环」细节仅作历史。

**原文**：

> InnoDB 存储引擎是多线程的模型，因此后台有多个不同的后台线程，负责处理不同的任务。后台线程的主要作用是负责刷新内存池中的数据，保证缓冲池中缓存的数据是最新的；此外还将已修改的数据文件刷新到磁盘文件，保证在数据库发生异常的情况下 InnoDB 能恢复到正常运行状态。

**8.0.34 新写法**：

```sql
SHOW VARIABLES LIKE 'innodb_page_cleaners';
SHOW VARIABLES LIKE 'innodb_purge_threads';
SHOW VARIABLES LIKE 'innodb_read_io_threads';
SHOW VARIABLES LIKE 'innodb_write_io_threads';
SHOW VARIABLES LIKE 'innodb_io_capacity';
SHOW VARIABLES LIKE 'innodb_io_capacity_max';
-- 不要背书中 1.2 Master Thread 伪代码当现行调度真相
```

```ini
[mysqld]
innodb_page_cleaners=4
innodb_purge_threads=4
innodb_read_io_threads=4
innodb_write_io_threads=4
```

---

## 3. IO Thread 与异步 IO（约第 24–26 页）

**要点**：

- InnoDB 大量使用 AIO（Asynchronous IO）处理读写请求，提升 I/O 吞吐。
- `SHOW ENGINE INNODB STATUS` 的 `FILE I/O` 段可观察 pending I/O、read/write threads。

**原文**：

> InnoDB 存储引擎中使用了大量的 AIO（Async IO）来处理写磁盘操作，这样可以极大地提高数据库的性能。在 InnoDB 1.0.x 开始，read ahead 等方式都通过 AIO 来进行。用户可以通过命令 `SHOW ENGINE INNODB STATUS` 来观察 IO Thread 的状态，在输出的 `FILE I/O` 部分可以看到相关信息。

**8.0.34 新写法**：

```sql
SHOW ENGINE INNODB STATUS\G
SHOW VARIABLES LIKE 'innodb_use_native_aio';   -- Linux 上通常 ON
SHOW VARIABLES LIKE 'innodb_read_io_threads';
SHOW VARIABLES LIKE 'innodb_write_io_threads';
```

```bash
# 也可配合 performance_schema / sys 看等待
mysql -e "SELECT * FROM sys.io_global_by_wait_by_bytes LIMIT 10;"
```

---

## 4. 内存：缓冲池与页类型（约第 26–32 页）

**要点**：

- 缓冲池缓存的页类型包括：索引页、数据页、undo 页、插入缓冲（insert buffer）、自适应哈希索引、锁信息、数据字典等。
- 可通过多个 buffer pool instance 降低热点互斥（`innodb_buffer_pool_instances`）。

**原文**：

> InnoDB 存储引擎的缓冲池中缓存的数据页类型有：索引页、数据页、undo 页、插入缓冲（insert buffer）、自适应哈希索引（adaptive hash index）、InnoDB 存储引擎的锁信息（lock info）、数据字典信息（data dictionary）等。不能简单地认为缓冲池只是缓存索引页和数据页，它们只是占缓冲池很大的一部分而已。

> 通过参数 `innodb_buffer_pool_instances` 可以将缓冲池划分为多个实例，每个页平等地分配到不同缓冲池实例中，其好处是减少了资源在缓冲池内部的竞争，增加数据库的并发处理能力。该参数默认值为 1。

**8.0.34 新写法**：

```sql
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
SHOW VARIABLES LIKE 'innodb_buffer_pool_instances';
SHOW VARIABLES LIKE 'innodb_buffer_pool_chunk_size';
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_%';

-- 官方名 Change Buffer（覆盖 insert/delete/purge 等）
SHOW VARIABLES LIKE 'innodb_change_buffering';
SHOW VARIABLES LIKE 'innodb_change_buffer_max_size';
```

```ini
[mysqld]
# 专用库主机可开自动调优（内存较大时）
innodb_dedicated_server=ON
# 或手动：
# innodb_buffer_pool_size=8G
# innodb_buffer_pool_instances=8
```

字典元数据在 8.0 由**事务型数据字典**管理，不再依赖 `.frm`；勿再把「frm + 引擎内部字典」当现行模型。

---

## 5. LRU：midpoint insertion strategy（约第 32–36 页）

**要点**：

- InnoDB 不把新读入页直接插到 LRU 头部，而插入 midpoint（old 区入口）。
- 防止全表扫描等一次性页挤掉热点页。

**原文**：

> InnoDB 存储引擎从磁盘读取的页放入缓冲池中时，并不是直接放入到 LRU 列表的首部，而是放在 LRU 列表的 midpoint 位置。这个 midpoint 位置可以通过参数 `innodb_old_blocks_pct` 控制，默认是 37，即新读取的页插入到 LRU 列表长度约 37% 的位置处。在 InnoDB 存储引擎中，将 midpoint 之后的列表称为 old 列表，之前的称为 new 列表。可以简单理解为 new 列表中的页都是较为活跃的热点数据。

> 为什么不直接将读取到的页放入到 LRU 列表的首部呢？如果直接放入首部，那么一些仅仅进行一次的选择性（或全表）扫描操作可能会把缓冲池中的热点数据页刷出，从而影响缓冲池的效率。为了解决这个问题，InnoDB 存储引擎引入了 midpoint insertion strategy：新读入的页先进入 old 区域；只有在 old 区域停留超过一定时间（由 `innodb_old_blocks_time` 控制，单位为毫秒）后再次被访问，才会被移入 new 区域成为热点页。

**8.0.34 新写法**：

```sql
SHOW VARIABLES LIKE 'innodb_old_blocks_pct';    -- 默认约 37
SHOW VARIABLES LIKE 'innodb_old_blocks_time';   -- 默认 1000（ms）
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_data';
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_old';
SHOW STATUS LIKE 'Innodb_buffer_pool_read%';
```

```sql
-- 观测命中率（书中要求不应长期低于 95%）
SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests';
SHOW STATUS LIKE 'Innodb_buffer_pool_reads';
-- hit ≈ 1 - Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests
```

---

## 6. 缓冲池命中率与 STATUS 时间窗口（约第 36–38 页）

**要点**：

- Buffer pool hit rate 一般不应长期小于 **95%**。
- `SHOW ENGINE INNODB STATUS` 中许多指标是**过去某段时间窗口**的统计，不是严格瞬时快照。

**原文**：

> 一般来说，Buffer pool hit rate 的值不应该小于 95%。若小于 95%，则应观察是否由于全表扫描导致 LRU 列表被污染，或缓冲池本身设置过小。

> 需要注意的是，`SHOW ENGINE INNODB STATUS` 显示的许多内容并不是当前的状态，而是过去某个时间范围内 InnoDB 存储引擎的状态信息。因此在分析时，应结合多次采样与其他监控手段，而不是把单次输出当作瞬时绝对值。

**8.0.34 新写法**：

```sql
SHOW ENGINE INNODB STATUS\G
-- 关注 BUFFER POOL AND MEMORY 段中的 Hit rate / 命中相关行

SELECT
  VARIABLE_VALUE AS reads
FROM performance_schema.global_status
WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads';

SELECT *
FROM sys.metrics
WHERE Variable_name LIKE 'innodb_buffer_pool%'
LIMIT 30;
```

---

## 7. Checkpoint 与 LSN（约第 38–42 页）

**要点**：

- Checkpoint 目的可概括为：缩短恢复时间、缓冲池不够时刷脏页、redo 空间紧张时推进检查点。
- LSN（Log Sequence Number）单调递增，用于标记 redo 位置与页的版本关系。

**原文**：

> Checkpoint 技术的目的是解决以下几个问题：一是缩短数据库的恢复时间；二是缓冲池不够用时，将脏页刷新到磁盘；三是 redo 日志不可用时，刷新脏页。InnoDB 通过 LSN（Log Sequence Number）来标记版本。LSN 是 8 字节的数字，每个页有 LSN，redo log 中也有 LSN，Checkpoint 也有 LSN。可以通过 `SHOW ENGINE INNODB STATUS` 观察。

**8.0.34 新写法**：

```sql
SHOW ENGINE INNODB STATUS\G
-- LOG 段：Log sequence number / Log flushed up to / Last checkpoint at

SHOW VARIABLES LIKE 'innodb_redo_log_capacity';   -- ≥8.0.30 主配置
SHOW VARIABLES LIKE 'innodb_log_file_size';        -- 弃用兼容，勿再当主调参
SHOW VARIABLES LIKE 'innodb_max_dirty_pages_pct';
SHOW VARIABLES LIKE 'innodb_adaptive_flushing';
```

```ini
[mysqld]
innodb_redo_log_capacity=2G
innodb_max_dirty_pages_pct=90
innodb_adaptive_flushing=ON
```

---

## 8. 关键特性：Insert / Change Buffer（约第 42–50 页）

**要点**：

- 书中「Insert Buffer」针对**非唯一辅助索引**的插入优化：先缓存在缓冲中，再异步合并到辅助索引页，减少随机 IO。
- 后续升级为 **Change Buffer**，可覆盖 Insert / Delete marking / Purge。
- `innodb_change_buffer_max_size`：占缓冲池百分比，**默认 25，最大 50**。
- Insert Buffer 在实现上是共享表空间中的一棵 B+ 树；使用独立表空间（`.ibd`）恢复时需注意与系统表空间中 change buffer 的一致性。

**原文**：

> InnoDB 存储引擎的关键特性包括：插入缓冲（Insert Buffer）、两次写（Double Write）、自适应哈希索引（Adaptive Hash Index）、异步 IO（Async IO）、刷新邻接页（Flush Neighbor Page）等。

> Insert Buffer 的设计针对非唯一的辅助索引。对于非唯一辅助索引的插入或更新操作，不是每次都直接插入到索引页中，而是先判断索引页是否在缓冲池中：若在，则直接插入；若不在，则先放入 Insert Buffer 中，再以一定频率合并（merge）回辅助索引叶页，从而将对同一索引页的多次离散 IO 转为批量顺序 IO。

> 从 InnoDB 1.0.x 开始，Insert Buffer 升级为 Change Buffer，可对 Insert、Delete、Purge 等操作进行缓冲。参数 `innodb_change_buffer_max_size` 控制 Change Buffer 最大使用缓冲池的百分比，默认值为 25，最大可设为 50。

> Insert Buffer 的数据结构是一棵 B+ 树，位于共享表空间中。因此，若表使用独立表空间（`.ibd`），在恢复或迁移单表文件时需要特别注意：仅拷贝 `.ibd` 可能无法完整还原仍滞留在共享表空间 Change Buffer 中的变更。

**8.0.34 新写法**：

```sql
SHOW VARIABLES LIKE 'innodb_change_buffering';
-- all / none / inserts / deletes / changes / purges 等（以本机帮助为准）
SET GLOBAL innodb_change_buffering = 'all';

SHOW VARIABLES LIKE 'innodb_change_buffer_max_size';  -- 默认 25
-- SET GLOBAL innodb_change_buffer_max_size = 30;  -- ≤50

SHOW STATUS LIKE 'Innodb_ibuf_%';
SHOW ENGINE INNODB STATUS\G
-- 关注 INSERT BUFFER AND ADAPTIVE HASH INDEX 段
```

```ini
[mysqld]
innodb_change_buffering=all
innodb_change_buffer_max_size=25
innodb_file_per_table=ON
```

---

## 9. Doublewrite 与 partial page write（约第 50–53 页）

**要点**：

- 页大小通常 16KB，操作系统可能按更小单位写盘；宕机可能导致**部分页写（partial page write）**。
- Doublewrite：先写到 doublewrite buffer（共享表空间连续区域），再写到真正表空间页；崩溃后可用副本恢复损坏页。

**原文**：

> 当发生 partial page write（部分写）时，可能只有 4KB 或 8KB 写入成功，导致页数据损坏。InnoDB 存储引擎的 doublewrite（两次写）特性用于解决该问题：脏页先写到共享表空间中的 doublewrite 区域，完成后再写到数据文件的实际位置。若写数据文件过程中崩溃，恢复时可用 doublewrite 中的副本进行页的还原。

**8.0.34 新写法**：

```sql
SHOW VARIABLES LIKE 'innodb_doublewrite';
SHOW STATUS LIKE 'Innodb_dblwr_%';
-- 生产 OLTP 通常保持开启；仅在可接受风险的基准测试中才考虑关闭
```

---

## 10. AHI、Native AIO、关闭与恢复（约第 53–61 页）

**要点**：

- Adaptive Hash Index：对热点索引页自动建哈希，加速等值查找。
- Native AIO：在支持的平台上使用操作系统原生异步 IO。
- `innodb_fast_shutdown`：控制关闭时是否完整 purge/合并；`innodb_force_recovery`：损坏时强制启动级别（慎用）。

**原文**：

> 自适应哈希索引（Adaptive Hash Index，AHI）由 InnoDB 存储引擎自行监控索引页的查询，若发现某些页几乎以哈希方式被访问，则自动建立哈希索引以加速查找。用户只能选择开启或关闭，不能人工干预其内部行为。

> Native AIO：在 Linux 等平台上，InnoDB 可使用原生异步 IO 接口，减少 IO 调度线程开销。参数 `innodb_use_native_aio` 用于控制。

> 参数 `innodb_fast_shutdown` 影响关闭行为：值为 1（默认）时表示快速关闭，不进行完整的 purge 与 change buffer 合并等；值为 0 表示完整清理后关闭；值为 2 表示将日志刷新到磁盘后中止，类似崩溃，重启需做恢复。

> 参数 `innodb_force_recovery` 可在表空间损坏等场景下强制启动 InnoDB，取值 0–6。大于 0 时通常应视为只读抢救模式，尽快逻辑导出数据，而不是继续业务写入。

**8.0.34 新写法**：

```sql
SHOW VARIABLES LIKE 'innodb_adaptive_hash_index';
SHOW VARIABLES LIKE 'innodb_use_native_aio';
SHOW VARIABLES LIKE 'innodb_fast_shutdown';
SHOW VARIABLES LIKE 'innodb_force_recovery';  -- 正常运行必须为 0
```

```ini
[mysqld]
innodb_adaptive_hash_index=ON
innodb_use_native_aio=ON
innodb_fast_shutdown=1
# 仅抢救时临时设置，例如：
# innodb_force_recovery=1
```

```sql
-- 多缓冲池 + 专用服务器（8.0 常用组合）
SHOW VARIABLES LIKE 'innodb_buffer_pool_instances';
SHOW VARIABLES LIKE 'innodb_dedicated_server';
SHOW VARIABLES LIKE 'innodb_page_cleaners';
```

---

## 11. 本章 8.0.34 对照摘要

| 书中说法 | 8.0.34 |
|----------|--------|
| Insert Buffer | **Change Buffer** + `innodb_change_buffering` |
| 死磕 Master Thread 1.2 流程 | 看 page cleaner / purge / IO threads |
| 单缓冲池叙事 | 多 `innodb_buffer_pool_instances`；可选 `innodb_dedicated_server` |
| 字典靠 frm | **事务型数据字典**，无 frm |
| 命中率 / Checkpoint / Doublewrite / AHI | 原理仍成立，用 STATUS + 现代参数观测 |
