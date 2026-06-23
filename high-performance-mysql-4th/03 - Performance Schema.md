# Chapter 3: Performance Schema

> 来源：《High Performance MySQL》第 4 版（Sveta Smirnova 贡献）  
> 页码范围：第 41–73 页（书中印刷页码）

---

## 1. 章节导言（第 41 页）

**要点**：高负载下调优是迭代过程；Performance Schema 是存储诊断数据的「数据库」，配合 sys schema 使用。

**原文**：

> Tuning the performance of databases under high load is an iterative cycle. Every time you make a change to tune the performance of the database, you need to understand if the change had any effect.

> Performance Schema is a database that stores the data required to answer these questions.

---

## 2. Performance Schema 简介（第 41–42 页）

**要点**：两个核心概念——

| 概念 | 含义 |
|------|------|
| **Instrument（检测器）** | 需要采集信息的 MySQL 代码片段，如 `wait/lock/metadata/sql/mdl` |
| **Consumer（消费者）** | 存储检测数据的表（执行次数、无索引次数、耗时等） |

**原文**：

> The first is an instrument. An instrument refers to any portion of the MySQL code that we want to capture information about.

> The second concept is a consumer, which is simply a table that stores the information about what code was instrumented.

> enabling instruments calls additional code, which in turn means instruments consume CPU.

---

## 3. Instrument 元素（第 42–43 页）

**要点**：`setup_instruments` 表列出所有检测器；名称用 `/` 分隔，从左到右由通用到具体。

**示例**：
- `statement/sql/select` — SELECT 语句
- `wait/synch/mutex/innodb/autoinc_mutex` — InnoDB 自增互斥锁

**原文**：

> The leftmost part of the instrument name indicates the type of the instrument. Thus, statement indicates that the instrument is a statement, wait indicates it is a wait, and so on.

---

## 4. Consumer 组织（第 44 页）

**要点**（8.0.25 约 110 张表）：

| 后缀 | 含义 |
|------|------|
| `*_current` | 当前正在发生的事件 |
| `*_history` | 每线程最近 10 条 |
| `*_history_long` | 全局最近 10,000 条 |

**事件类型**：`events_waits`、`events_statements`、`events_stages`、`events_transactions`

**Digest**：将参数化查询聚合，如 `WHERE user_id=?` 统一统计。

**原文**：

> Digests are a way to aggregate queries by removing the variations in them.

---

## 5. 资源消耗（第 45 页）

**要点**：

- 数据存于内存；可限制 consumer 最大大小。
- 自扩容表分配的内存禁用 instrumentation 后**不会释放**（需重启）。
- 检测器越多 CPU 越高；行锁检测器比语句检测器开销大得多。

**原文**：

> This memory is never freed once allocated, even if you disabled specific instrumentation and truncated the table.

---

## 6. 局限性（第 45–46 页）

**要点**：

1. 组件必须支持 instrumentation（如某存储引擎不支持内存检测则无法追踪）。
2. 仅在启用后采集数据（无法追溯启用前的分配）。
3. 禁用后内存难以释放（需重启）。

---

## 7. sys Schema（第 46 页）

**要点**：5.7+ 内置，仅为 performance_schema 上的视图和存储过程，**不存储数据**。

**原文**：

> it only accesses data stored in the performance_schema tables.

---

## 8. 理解线程（第 46–47 页）

**要点**：

- `THREAD_ID` ≠ `PROCESSLIST_ID`
- `threads` 表包含所有线程；需杀连接时先查 `PROCESSLIST_ID`
- Performance Schema 各处使用 `THREAD_ID`

**原文**：

> THREAD_ID is not equal to PROCESSLIST_ID!

---

## 9. 配置（第 48–52 页）

### 9.1 启用/禁用 Performance Schema

- `performance_schema=ON/OFF`：仅启动时可改（配置文件或命令行）。

### 9.2 启用/禁用 Instruments

三种方式：`UPDATE setup_instruments`、sys 存储过程 `ps_setup_enable_instrument`、`performance-schema-instrument` 启动参数（可持久化）。

### 9.3 启用/禁用 Consumers

15 个 consumer；`global_instrumentation` 关闭则全部不采集。

### 9.4 特定对象监控

`setup_objects` 表按 EVENT/FUNCTION/PROCEDURE/TABLE/TRIGGER 配置。

### 9.5 线程监控

`setup_threads`（后台线程）、`setup_actors`（用户连接，HOST/USER/ENABLED/HISTORY）。

### 9.6 内存大小调整

变量模式：`performance_schema_object_[size|instances|classes|length|handles]`。

### 9.7 默认值（第 52–53 页）

- 5.7+ 默认启用，多数 instruments 关闭；8.0 额外默认启用元数据锁和内存检测。
- `mysql`/`information_schema`/`performance_schema` 库不检测。
- `_history` 存 10 条/线程；`_history_long` 存 10,000 条；SQL 文本最大 1024 字节。

---

## 10. 使用 Performance Schema（第 53–72 页）

### 10.1 检查 SQL 语句（第 53–57 页）

**关键优化指标列**（`events_statements_*`）：

| 列 | 重要性 | 含义 |
|----|--------|------|
| `CREATED_TMP_DISK_TABLES` | 高 | 磁盘临时表 |
| `SELECT_FULL_JOIN` | 高 | 全表扫描 JOIN |
| `NO_INDEX_USED` | 高 | 未使用索引 |
| `SELECT_SCAN` | 中 | 第一表全扫描 |

**sys 视图**：`statement_analysis`、`statements_with_full_table_scans`、`statements_with_temp_tables` 等。

### 10.2 预编译语句（第 57–58 页）

- 表：`prepared_statements_instances`
- 统计为累计值；`DROP PREPARE` 后数据消失。

### 10.3 存储例程（第 58–60 页）

- 启用 `statement/sp/%` 可追踪 IF/ELSE 分支、错误处理器执行路径。

### 10.4 语句剖析（第 60–61 页）

- `events_stages_*` + `stage/%` instruments
- 关注：`stage/sql/%tmp%`、`%lock%`、`Sending data`（与 ROWS_SENT 对比）

### 10.5 读 vs 写性能（第 61–62 页）

- 按 `EVENT_NAME` 统计语句类型
- `Handler_*` 状态变量统计读/写行数

### 10.6 元数据锁（第 62–63 页）

- 表：`metadata_locks`；启用 `wait/lock/metadata/sql/mdl`
- MDL 持有至事务结束；多语句事务中持有者可能不在 processlist

### 10.7 内存使用（第 63–65 页）

- `memory_summary_*` 表；sys 视图 `memory_global_total`、`memory_by_thread_by_current_bytes`

### 10.8 变量（第 66–69 页）

- 服务器变量、状态变量、用户变量
- 8.0 不再依赖 `information_schema` 追踪变量
- `variables_info` 记录变量来源（COMMAND_LINE/COMPILED/PERSISTED/DYNAMIC）

### 10.9 最常见错误（第 69–70 页）

- `events_errors_summary_*` 按用户/主机/线程/全局聚合错误

### 10.10 检查 Performance Schema 自身（第 71–72 页）

- `SHOW ENGINE PERFORMANCE_SCHEMA STATUS`
- 默认不检测对 `performance_schema` 库的查询（需改 `setup_actors`）

---

## 11. 本章小结（第 73 页）

**要点**：

- 保持 Performance Schema **启用**，按需动态开启 instruments/consumers。
- 善用 sys schema 作为快捷方式。
- 理解内存管理：不是泄漏，是 consumer 数据驻留内存直至重启。

**原文**：

> you should keep Performance Schema enabled, dynamically enabling the instruments and consumers that will help you address whatever concerns you might have

> You should also leverage the sys schema as a shortcut to addressing the most common questions.
