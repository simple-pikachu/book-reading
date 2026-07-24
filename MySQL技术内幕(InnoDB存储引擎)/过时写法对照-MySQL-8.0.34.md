# 《MySQL技术内幕：InnoDB存储引擎（第2版）》过时写法对照

> 书籍：姜承尧，机械工业出版社，2013-05（ISBN 9787111422068）  
> 书中基线：**MySQL 5.6 / InnoDB 1.2.x 时代**  
> 对照目标：**MySQL 8.0.34**  
> 用途：边读原书边对照，区分「仍有效的原理」与「已过时的写法/参数/工具」

---

## 0. 怎么用这份对照

| 读法 | 说明 |
|------|------|
| 原理可留 | B+ 树、MVCC、redo/undo、锁算法、Checkpoint、Doublewrite 等**机制叙事**大多仍成立 |
| 写法要换 | 参数名、文件布局、INFORMATION_SCHEMA 表名、备份工具、认证插件、默认字符集等要按 8.0.34 改 |
| 证据来源 | 官方 [What Is New in MySQL 8.0](https://dev.mysql.com/doc/refman/8.0/en/mysql-nutshell.html)、[8.0.34 Release Notes](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-34.html)；本书 PDF 为扫描件，无法逐页 OCR 引原文，条目按**目录主题 + 5.6 时代通行写法**归纳 |

**阅读建议**：先读原书某一节建立模型，再翻本文件同章节「过时点」，最后用本机 `SELECT VERSION();`（期望 `8.0.34`）验证参数/表是否仍存在。

---

## 1. 总览：仍该学 vs 必须改口

### 1.1 书里现在仍值得认真读的

- InnoDB 内存结构（Buffer Pool、LRU/Flush List）、Checkpoint、Doublewrite
- 聚集索引 / 辅助索引、Cardinality、覆盖索引、ICP / MRR 思路
- 行锁三种算法（Record / Gap / Next-Key）、一致性非锁定读、死锁示例
- redo / undo / purge / group commit 的事务实现骨架
- 「别在循环里提交」「警惕长事务」等工程习惯（第 7 章）

### 1.2 一页纸速查：最高频过时写法

| 书中常见说法（5.6 味） | MySQL 8.0.34 现状 | 严重度 |
|------------------------|-------------------|--------|
| 调 Query Cache / `SQL_CACHE` | **已彻底移除** | 致命 |
| `.frm` / `.par` / `.isl` 即元数据 | **事务型 Data Dictionary**；文件式元数据已移除 | 致命 |
| `innodb_file_format` / Antelope·Barracuda / `innodb_large_prefix` | **变量已移除**；默认 `ROW_FORMAT=DYNAMIC` | 高 |
| `INSERT Buffer` 专指插入 | 现称 **Change Buffer**（可缓冲 insert/delete/purge） | 中 |
| `tx_isolation` | 用 **`transaction_isolation`** | 高 |
| `INFORMATION_SCHEMA.INNODB_SYS_*` | 改为 **`INNODB_*`**（去掉 `SYS_`） | 高 |
| `INNODB_LOCKS` / `INNODB_LOCK_WAITS` | 用 **Performance Schema `data_locks` / `data_lock_waits`** | 高 |
| `GRANT` 顺手建用户 / `PASSWORD()` | **禁止**；用 `CREATE USER` / `ALTER USER` | 高 |
| 默认字符集 `latin1` / 三字节 `utf8` | 默认 **`utf8mb4`**；旧 `utf8` 实为 `utf8mb3`（弃用路径） | 高 |
| MyISAM 分区表 / 通用分区 handler | **仅 InnoDB（及 NDB）原生分区** | 高 |
| `ibbackup` 热备叙事 | 用 **MySQL Enterprise Backup / Percona XtraBackup / Clone Plugin** 等 | 中 |
| `innodb_log_file_size` + `innodb_log_files_in_group` | **≥8.0.30 弃用**，优先 **`innodb_redo_log_capacity`** | 高（对 8.0.34） |
| `mysql_native_password` | **8.0.34 起弃用**，默认倾向 `caching_sha2_password` | 高（对 8.0.34） |
| 手跑 `mysql_upgrade` | **≥8.0.16 由 server 启动自动升级**（`--upgrade`） | 中 |

---

## 2. 分章对照

### 第 1 章 MySQL 体系结构与存储引擎（约 p.1–15）

| # | 书中写法 / 关注点 | 8.0.34 对照 | 读时怎么记 |
|---|-------------------|-------------|------------|
| 1.1 | 把 MyISAM、Archive、Federated、**Maria 引擎**等与 InnoDB「并列选型」 | 生产 OLTP **默认且几乎唯一切实选项是 InnoDB**；Maria 引擎从未成为主流替代叙事；MyISAM 仅边缘场景 | 引擎对比表当历史，选型结论改写为「InnoDB first」 |
| 1.2 | 系统库/权限表可视为 MyISAM 表 | **`mysql` 系统表已是 InnoDB**；账户语句具事务性（要么全成要么全滚） | 别再假设「权限表崩溃半更新」的旧故事 |
| 1.3 | 连接方式章节仍可用 | Windows 命名管道权限在 8.0 更收紧；认证插件默认已变 | 连上之后先看 `SHOW VARIABLES LIKE 'default_authentication_plugin';` |

**对照 SQL（8.0.34）**

```sql
SELECT VERSION();
SHOW ENGINES;
SHOW VARIABLES LIKE 'default_storage_engine';
SHOW VARIABLES LIKE 'default_authentication_plugin';
```

---

### 第 2 章 InnoDB 存储引擎（约 p.17–61）

| # | 书中写法 | 8.0.34 对照 | 说明 |
|---|----------|-------------|------|
| 2.1 | 按 InnoDB **1.0.x / 1.2.x** 讲 Master Thread 阶段 | 后台任务已高度拆分（purge、page cleaner、io threads 等）；Master Thread 细节**不能当现行调度真相** | 学「曾经为何卡在 Master Thread」即可，别背 1.2 流程当现状 |
| 2.2 | **插入缓冲（Insert Buffer）** | **Change Buffer**：还可缓冲 delete marking / purge；参数 `innodb_change_buffering` | 书中插图可留，术语与参数名要换 |
| 2.3 | 自适应哈希、Doublewrite、邻接页刷新 | 机制仍在；调参与监控入口有演进（如 metrics、dedicated server） | 原理有效，配置章节以后面官方手册为准 |
| 2.4 | 版本表停留在 5.6 插件式 InnoDB | 8.0 InnoDB 与 server **深度一体化**（数据字典、原子 DDL） | 「独立插件式 InnoDB」心智模型要升级 |

**对照 SQL**

```sql
SHOW VARIABLES LIKE 'innodb_change_buffering';
SHOW VARIABLES LIKE 'innodb_adaptive_hash_index';
SHOW VARIABLES LIKE 'innodb_doublewrite';
SHOW STATUS LIKE 'Innodb_buffer_pool%';
```

---

### 第 3 章 文件（约 p.62–90）

| # | 书中写法 | 8.0.34 对照 | 严重度 |
|---|----------|-------------|--------|
| 3.1 | **表结构定义文件 `.frm`** | **已移除**；元数据在 Data Dictionary（`mysql.ibd` 等） | 致命 |
| 3.2 | 分区 `.par`、触发器 `.TRN/.TRG`、远程表空间 `.isl` | **文件式元数据移除**；外置表空间靠 `innodb_directories` 等 | 高 |
| 3.3 | redo：数据目录下 `ib_logfile0/1`，靠 `innodb_log_file_size` × `innodb_log_files_in_group` | **≥8.0.30**：容量用 **`innodb_redo_log_capacity`**；文件落在 `#innodb_redo/`（通常 32 个文件） | 高 |
| 3.4 | undo 常与系统表空间混谈 | 独立 undo tablespace；`CREATE/ALTER/DROP UNDO TABLESPACE`；`innodb_undo_tablespaces` 已不可随意当调参主角 | 高 |
| 3.5 | `sync_frm` 一类参数 | **已移除** | 高 |
| 3.6 | 二进制日志章节大体可用 | 默认/推荐更偏 **ROW**；配合 GTID、组复制时心智不同 | 中 |

**对照 SQL**

```sql
SHOW VARIABLES LIKE 'innodb_redo_log_capacity';
SHOW VARIABLES LIKE 'innodb_log_file_size';          -- 弃用兼容，勿再作为主配置
SHOW VARIABLES LIKE 'innodb_log_files_in_group';     -- 同上
SHOW VARIABLES LIKE 'innodb_undo_directory';
SHOW VARIABLES LIKE 'datadir';
-- 数据目录中不应再依赖 .frm 作为真相源
```

**配置写法对照**

```ini
# 书中/5.6 味（过时）
innodb_log_file_size=512M
innodb_log_files_in_group=2
innodb_file_format=Barracuda
innodb_large_prefix=1

# 8.0.34 推荐口径
innodb_redo_log_capacity=2G   # 按负载调整；可运行时 SET GLOBAL
# 勿再写 innodb_file_format / innodb_large_prefix
```

---

### 第 4 章 表（约 p.91–182）

| # | 书中写法 | 8.0.34 对照 |
|---|----------|-------------|
| 4.1 | **Named File Formats**（Antelope / Barracuda） | 概念与相关变量**作废**；不必再为「开 Barracuda」折腾 |
| 4.2 | Compact / Redundant 为主叙事；Compressed/Dynamic 当「新格式」 | **默认 DYNAMIC**；COMPRESSED 临时表在 8.0 **不再支持** |
| 4.3 | 字符集默认常按 latin1 / utf8（mb3）举例 | **默认 utf8mb4**；新库请直接 `utf8mb4` + 合适 collation（如 `utf8mb4_0900_ai_ci`） |
| 4.4 | 分区可挂在 MyISAM 等引擎 | **仅 InnoDB 原生分区可用**；升级前必须改引擎或去掉分区 |
| 4.5 | DDL = 改 `.frm` + 引擎元数据，崩溃语义复杂 | **Atomic DDL**：字典更新、引擎操作、binlog **同一原子事务** |
| 4.6 | Online DDL 能力按 5.6 列表 | 8.0 大幅扩展；**`ALGORITHM=INSTANT`**（加列/改名/删列等，版本细节以 8.0.29+ 为准） |

**对照 SQL**

```sql
SHOW VARIABLES LIKE 'character_set_server';
SHOW VARIABLES LIKE 'collation_server';
SHOW VARIABLES LIKE 'innodb_default_row_format';

CREATE TABLE t_demo (
  id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  name VARCHAR(64) NOT NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci
  ROW_FORMAT=DYNAMIC;

-- Instant DDL 示例（支持时几乎只改元数据）
ALTER TABLE t_demo ADD COLUMN note VARCHAR(32), ALGORITHM=INSTANT;
```

---

### 第 5 章 索引与算法（约 p.183–248）

| # | 书中写法 | 8.0.34 对照 |
|---|----------|-------------|
| 5.1 | B+ 树插入/删除/分裂 | **原理仍核心**；8.0 索引页结构变更时的锁粒度改进（SX 意向锁等）让并发读更好，但书中算法故事仍可学 |
| 5.2 | Cardinality / 采样统计 | 统计持久化与 `information_schema_stats_expiry` 等行为不同；直方图（5.7+）书中未覆盖 |
| 5.3 | `EXPLAIN` 可写 `EXPLAIN PARTITIONS` / `EXTENDED` | 关键字**已移除**（效果默认开启）；用 `EXPLAIN ANALYZE`（8.0.18+）看真实执行 |
| 5.4 | 全文检索按早期 InnoDB FTS | 功能仍在，但分词器/中文场景常外接 ES 等；别把书中示例当唯一方案 |
| 5.5 | Optimizer Hint 语法偏早期 | 8.0 有更完整的 **Optimizer Hints**（`/*+ ... */`） |

**对照 SQL**

```sql
EXPLAIN FORMAT=TREE SELECT * FROM t_demo WHERE id = 1;
EXPLAIN ANALYZE SELECT * FROM t_demo WHERE name = 'x';
-- 错误示范（8.0 已无）：EXPLAIN PARTITIONS SELECT ...
```

---

### 第 6 章 锁（约 p.249–284）

| # | 书中写法 | 8.0.34 对照 |
|---|----------|-------------|
| 6.1 | 行锁三算法、间隙锁、Next-Key | **仍是必读** |
| 6.2 | 查锁用 `INFORMATION_SCHEMA.INNODB_LOCKS` / `INNODB_LOCK_WAITS` | **已移除** → `performance_schema.data_locks` / `data_lock_waits`（及 `sys.innodb_lock_waits`） |
| 6.3 | `SHOW ENGINE INNODB STATUS` 仍可用 | 继续用，但日常优先 P_S / sys |
| 6.4 | 自增锁模式讨论偏早期 | 关注 `innodb_autoinc_lock_mode`；并行插入与复制语义要按 8.0 文档复核 |
| 6.5 | 「锁升级」按通用数据库教科书讲 | InnoDB **没有** Oracle 式行锁升级到表锁；书中若对比其他库，别误套到 InnoDB |

**对照 SQL**

```sql
SELECT * FROM performance_schema.data_locks LIMIT 20;
SELECT * FROM performance_schema.data_lock_waits LIMIT 20;
SELECT * FROM sys.innodb_lock_waits\G
```

---

### 第 7 章 事务（约 p.285–349）

| # | 书中写法 | 8.0.34 对照 |
|---|----------|-------------|
| 7.1 | `tx_isolation` / `tx_read_only` | 用 **`transaction_isolation` / `transaction_read_only`** |
| 7.2 | `innodb_support_xa` 可关 | **已移除**；InnoDB XA 两阶段提交**始终开启** |
| 7.3 | 分布式事务 / 内部 XA | 机制仍在；高可用更常见路径是 **Group Replication / InnoDB Cluster**（书中未覆盖） |
| 7.4 | 隐式提交 SQL 列表 | 大方向仍对，但具体语句集合以 8.0 手册为准 |
| 7.5 | 坏习惯：循环提交、滥用自动提交 | **仍然正确**，继续当工程红线 |

**对照 SQL**

```sql
SELECT @@transaction_isolation, @@transaction_read_only;
-- 过时：SELECT @@tx_isolation;
SET SESSION transaction_isolation = 'READ-COMMITTED';
```

---

### 第 8 章 备份与恢复（约 p.350–382）

| # | 书中写法 | 8.0.34 对照 |
|---|----------|-------------|
| 8.1 | **ibbackup** 作为热备主角 | 商业线是 **MySQL Enterprise Backup**；开源常用 **Percona XtraBackup**；8.0 还有 **Clone Plugin** |
| 8.2 | mysqldump / `SELECT ... INTO OUTFILE` / `LOAD DATA` | 仍可用；大实例更常见物理备份 + binlog；注意 `secure_file_priv` |
| 8.3 | 复制 = 传统异步主从 | 另有半同步、GTID、**Group Replication**、只读副本拓扑；「快照+复制」思路可留，组件要换代 |
| 8.4 | 二进制日志恢复步骤 | 原理仍对；配合 GTID 时用 `mysqlbinlog` / `GTID_PURGED` 等 8.0 流程 |

---

### 第 9 章 性能调优（约 p.383–410）

| # | 书中写法 | 8.0.34 对照 |
|---|----------|-------------|
| 9.1 | RAID / 机械盘为主的硬件叙事 | NVMe、云盘、本地 SSD 为主；RAID Write Back 仍有参考价值但非唯一真相 |
| 9.2 | 内存 / Buffer Pool 重要性 | **仍成立**；可用 `innodb_dedicated_server` 自动推一批参数（慎用于非独占机） |
| 9.3 | sysbench / mysql-tpcc | 工具链仍在，版本与参数已变；另有 `mysqlslap`、BenchWare、应用压测 |
| 9.4 | 缺 Performance Schema / sys schema 体系化监控 | 8.0 **默认开启 P_S**；优先 `sys`、`performance_schema`，而不是只看 `SHOW STATUS` |

---

### 第 10 章 源码编译与调试（约 p.411–424）

| # | 书中写法 | 8.0.34 对照 |
|---|----------|-------------|
| 10.1 | MySQL **5.1** 调试路径、旧 cmake/选项 | 完全过时；请跟 **8.0 源码树 + 现行 CMake 选项** |
| 10.2 | InnoDB 作为较独立模块浏览 | 8.0 与 server/数据字典耦合更深，目录与模块边界已变 |
| 10.3 | 获取「InnoDB 引擎源码」的旧社区路径 | 以 [mysql-server](https://github.com/mysql/mysql-server) 对应 tag（如 `mysql-8.0.34`）为准 |

---

## 3. SQL / 运维「过时写法」速查卡

### 3.1 账户与安全

```sql
-- 过时（书中/老资料常见）
GRANT ALL ON db.* TO 'u'@'%' IDENTIFIED BY 'pwd';
SET PASSWORD = PASSWORD('pwd');

-- 8.0.34
CREATE USER 'u'@'%' IDENTIFIED BY 'pwd';   -- 默认 caching_sha2_password
ALTER USER 'u'@'%' IDENTIFIED BY 'new';
GRANT ALL ON db.* TO 'u'@'%';
-- 8.0.34：mysql_native_password 已弃用，勿再主动选用（除非兼容遗留客户端）
```

### 3.2 查询缓存

```sql
-- 过时：整段删除即可
SET GLOBAL query_cache_type = ON;
SELECT SQL_CACHE * FROM t;

-- 8.0.34：无 Query Cache。缓存放到应用层 / ProxySQL / Redis 等
```

### 3.3 GROUP BY 排序依赖

```sql
-- 过时：依赖 GROUP BY 隐式排序，或 GROUP BY col ASC/DESC
SELECT a, b FROM t GROUP BY a;

-- 8.0.34：需要顺序就显式 ORDER BY；ONLY_FULL_GROUP_BY 默认开启
SELECT a, ANY_VALUE(b) AS b FROM t GROUP BY a ORDER BY a;
```

### 3.4 元数据与锁观察

```sql
-- 过时
SELECT * FROM information_schema.INNODB_SYS_TABLES;
SELECT * FROM information_schema.INNODB_LOCKS;

-- 8.0.34
SELECT * FROM information_schema.INNODB_TABLES LIMIT 5;
SELECT * FROM performance_schema.data_locks LIMIT 5;
```

---

## 4. 建议阅读顺序（对照版）

1. **第 5–7 章（索引 / 锁 / 事务）**：原理密度最高，过时点相对少，先建立正确模型。  
2. **第 2–4 章**：用本文件替换 Insert Buffer、文件格式、`.frm`、行格式默认值。  
3. **第 3、8 章**：用 `innodb_redo_log_capacity`、原子 DDL、现代备份/复制替换文件与运维叙事。  
4. **第 1、9、10 章**：当历史与启发，选型/硬件/源码路径以 8.0.34 文档为准。

---

## 5. 本机快速验收清单（8.0.34）

在目标实例执行，确认「书中写法」是否已失效：

```sql
SELECT VERSION();  -- 期望含 8.0.34

-- 应为空或不存在相关变量
SHOW VARIABLES LIKE 'query_cache%';
SHOW VARIABLES LIKE 'innodb_file_format%';
SHOW VARIABLES LIKE 'innodb_large_prefix';
SHOW VARIABLES LIKE 'tx_isolation';

-- 应存在 / 可用
SHOW VARIABLES LIKE 'innodb_redo_log_capacity';
SHOW VARIABLES LIKE 'transaction_isolation';
SHOW VARIABLES LIKE 'character_set_server';
SELECT COUNT(*) FROM performance_schema.data_locks;
SELECT COUNT(*) FROM information_schema.INNODB_TABLES;
```

若 `query_cache%`、`innodb_file_format%`、`tx_isolation` 仍能按书中方式工作，说明连的不是 8.0.34 或看了兼容层假象——以 `VERSION()` 为准。

---

## 6. 参考链接

- 书籍信息：[豆瓣 · MySQL技术内幕：InnoDB存储引擎（第2版）](https://book.douban.com/subject/24708143/)
- [MySQL 8.0 What Is New](https://dev.mysql.com/doc/refman/8.0/en/mysql-nutshell.html)
- [Removal of File-based Metadata](https://dev.mysql.com/doc/refman/8.0/en/data-dictionary-file-removal.html)
- [InnoDB Change Buffer](https://dev.mysql.com/doc/refman/8.0/en/innodb-change-buffer.html)
- [InnoDB Redo Log / innodb_redo_log_capacity](https://dev.mysql.com/doc/refman/8.0/en/innodb-redo-log.html)
- [Changes in MySQL 8.0.34](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-34.html)
