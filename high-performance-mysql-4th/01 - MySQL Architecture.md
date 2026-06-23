# Chapter 1: MySQL Architecture

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 1–18 页（书中印刷页码）

---

## 1. 章节导言（第 1 页）

**要点**：MySQL 架构灵活，适用于从小型个人网站到大型企业应用；理解其设计才能「顺势而为」。

**原文**：

> MySQL's architectural characteristics make it useful for a wide range of purposes. Although it is not perfect, it is flexible enough to work well in both small and large environments. These range from a personal website up to large-scale enterprise applications. To get the most from MySQL, you need to understand its design so that you can work with it, not against it.

> This chapter provides a high-level overview of the MySQL server architecture, the major differences between the storage engines, and why those differences are important.

---

## 2. MySQL 逻辑架构（第 1 页）

**要点**：三层结构——客户端层、服务器核心层、存储引擎层。

| 层级 | 职责 |
|------|------|
| **顶层（Clients）** | 连接处理、认证、安全等通用网络服务 |
| **第二层（Server Core）** | 查询解析、分析、优化、内置函数；跨引擎功能（存储过程、触发器、视图） |
| **第三层（Storage Engines）** | 数据的存储与检索；通过 Storage Engine API 与服务器通信 |

**原文**：

> The topmost layer, clients, contains the services that aren't unique to MySQL. They're services most network-based client/server tools or servers need: connection handling, authentication, security, and so forth.

> The second layer is where things get interesting. Much of MySQL's brains are here, including the code for query parsing, analysis, optimization, and all the built-in functions (e.g., dates, times, math, and encryption). Any functionality provided across storage engines lives at this level: stored procedures, triggers, and views, for example.

> The third layer contains the storage engines. They are responsible for storing and retrieving all data stored "in" MySQL.

> The server communicates with them through the storage engine API. This API hides differences between storage engines and makes them largely transparent at the query layer.

**脚注要点**（第 1 页）：

- InnoDB 会自行解析外键定义，因为 MySQL 服务器本身尚未实现外键。
- MySQL 5.5+ 支持线程池插件 API，但常见做法是在接入层做线程池（见第 5 章）。

---

## 3. 连接管理与安全（第 2 页）

**要点**：

- 默认每个客户端连接对应一个线程，查询在该线程中执行。
- 服务器维护线程缓存，避免频繁创建/销毁线程。
- 认证基于用户名、来源主机、密码；也支持 TLS + X.509 证书。
- 连接后，服务器会校验每条查询的权限。

**原文**：

> By default, each client connection gets its own thread within the server process. The connection's queries execute within that single thread, which in turn resides on one core or CPU.

> The server maintains a cache of ready-to-use threads, so they don't need to be created and destroyed for each new connection.

> When clients (applications) connect to the MySQL server, the server needs to authenticate them. Authentication is based on username, originating host, and password. X.509 certificates can also be used across a Transport Layer Security (TLS) connection.

> Once a client has connected, the server verifies whether the client has privileges for each query it issues (e.g., whether the client is allowed to issue a SELECT statement that accesses the Country table in the world database).

---

## 4. 优化与执行（第 2–3 页）

**要点**：

- 解析查询生成 parse tree，再经多种优化（重写、表读取顺序、索引选择等）。
- 可用 `EXPLAIN` 查看优化决策。
- 优化器不关心存储引擎类型，但会询问引擎能力与统计信息。
- **查询缓存**：MySQL 5.7.20 起已弃用，8.0 完全移除；推荐用 memcached/Redis 做结果集缓存。

**原文**：

> MySQL parses queries to create an internal structure (the parse tree) and then applies a variety of optimizations. These can include rewriting the query, determining the order in which it will read tables, choosing which indexes to use, and so on.

> The optimizer does not really care what storage engine a particular table uses, but the storage engine does affect how the server optimizes the query.

> In older versions, MySQL made use of an internal query cache to see if it could serve the results from there. However, as concurrency increased, the query cache became a notorious bottleneck. As of MySQL 5.7.20, the query cache was officially deprecated as a MySQL feature, and in the 8.0 release, the query cache is fully removed.

> a popular design pattern is to cache data in memcached or Redis.

---

## 5. 并发控制（第 3 页）

**要点**：MySQL 在**服务器层**和**存储引擎层**两个层面处理并发；用电子表格协作类比说明读写冲突问题。

**原文**：

> Any time more than one query needs to change data at the same time, the problem of concurrency control arises. For our purposes in this chapter, MySQL has to do this at two levels: the server level and the storage-engine level.

> We need an approach for allowing concurrent access to a high-volume spreadsheet.

---

## 6. 读/写锁（第 3–4 页）

**要点**：

- **读锁（共享锁）**：多客户端可同时读，互不阻塞。
- **写锁（排他锁）**：独占资源，阻塞其他读锁和写锁。
- 锁管理开销应足够小，客户端才不易察觉。

**原文**：

> Read locks on a resource are shared, or mutually nonblocking: many clients can read from a resource at the same time and not interfere with one another.

> Write locks, on the other hand, are exclusive—that is, they block both read locks and other write locks—because the only safe policy is to have a single client writing to the resource at a given time and to prevent all reads when a client is writing.

---

## 7. 锁粒度（第 4–5 页）

**要点**：

- 锁粒度越小，并发越高，但锁管理开销也越大。
- MySQL 允许多存储引擎各自实现锁策略。

### 7.1 表锁（Table Locks）

- 开销最低，锁定整张表。
- 写锁阻塞所有读写；无写时读者可获读锁。
- `READ LOCAL` 允许部分并发写；写队列优先级高于读队列。

### 7.2 行锁（Row Locks）

- 并发最高，开销最大。
- 在**存储引擎**层实现，服务器基本不感知。

**原文**：

> A locking strategy is a compromise between lock overhead and data safety, and that compromise affects performance.

> MySQL, on the other hand, does offer choices. Its storage engines can implement their own locking policies and lock granularities.

> Row locks are implemented in the storage engine, not the server.

**脚注**（第 5 页）：还有元数据锁（DDL/表名变更）、8.0 的应用级锁函数；日常数据变更的内部锁主要由 InnoDB 处理。

---

## 8. 事务（第 5–7 页）

**要点**：

- 事务 = 一组 SQL，**原子执行**（全部成功或全部回滚）。
- 用 `START TRANSACTION` 开始，`COMMIT` / `ROLLBACK` 结束。
- 仅靠事务不够，还需满足 **ACID**。

### ACID 四要素

| 属性 | 含义 |
|------|------|
| **Atomicity（原子性）** | 全部提交或全部不提交 |
| **Consistency（一致性）** | 数据库始终从一个一致状态到另一个一致状态 |
| **Isolation（隔离性）** | 事务完成前，结果通常对其他事务不可见 |
| **Durability（持久性）** | 提交后变更永久保存（有多级实现） |

**原文**：

> A transaction is a group of SQL statements that are treated atomically, as a single unit of work. If the database engine can apply the entire group of statements to a database, it does so, but if any of them can't be done because of a crash or other reason, none of them is applied. It's all or nothing.

> ACID stands for atomicity, consistency, isolation, and durability.

> ACID transactions and the guarantees provided through them in the InnoDB engine specifically are one of the strongest and most mature features in MySQL.

**示例 SQL**（第 6 页）：

```sql
START TRANSACTION;
SELECT balance FROM checking WHERE customer_id = 10233276;
UPDATE checking SET balance = balance - 200.00 WHERE customer_id = 10233276;
UPDATE savings SET balance = balance + 200.00 WHERE customer_id = 10233276;
COMMIT;
```

---

## 9. 隔离级别（第 7–8 页）

**要点**：ANSI SQL 定义四个隔离级别；MySQL 各存储引擎实现略有差异。

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 锁定读 |
|----------|------|------------|------|--------|
| READ UNCOMMITTED | ✓ | ✓ | ✓ | 否 |
| READ COMMITTED | ✗ | ✓ | ✓ | 否 |
| REPEATABLE READ | ✗ | ✗ | ✓* | 否 |
| SERIALIZABLE | ✗ | ✗ | ✗ | 是 |

\* InnoDB/XtraDB 用 MVCC 解决幻读问题。

**MySQL 默认**：`REPEATABLE READ`

**原文**：

> REPEATABLE READ is MySQL's default transaction isolation level.

> SERIALIZABLE places a lock on every row it reads.

---

## 10. 死锁（第 8–9 页）

**要点**：

- 两个或多个事务互相持有并请求对方已锁定的资源，形成循环依赖。
- InnoDB 检测循环依赖并立即返回错误；或按锁等待超时放弃。
- InnoDB 回滚持有**最少排他行锁**的事务。
- 应用应设计为重试机制。

**原文**：

> A deadlock is when two or more transactions are mutually holding and requesting locks on the same resources, creating a cycle of dependencies.

> the InnoDB storage engine, will notice circular dependencies and return an error instantly.

> the way InnoDB currently handles deadlocks is to roll back the transaction that has the fewest exclusive row locks (an approximate metric for which will be the easiest to roll back).

---

## 11. 事务日志（第 9–10 页）

**要点**：

- 采用 **Write-Ahead Logging（预写日志）**：先改内存，再写事务日志（顺序 I/O），稍后异步刷盘。
- 崩溃后可通过日志恢复未刷盘的数据变更。

**原文**：

> Instead of updating the tables on disk each time a change occurs, the storage engine can change its in-memory copy of the data.

> the storage engine can then write a record of the change to the transaction log, which is on disk and therefore durable.

> known as write-ahead logging

---

## 12. MySQL 中的事务（第 10–12 页）

### 12.1 AUTOCOMMIT（第 10–11 页）

- 默认单条 DML 自动提交。
- `SET AUTOCOMMIT=0` 后需显式 `COMMIT`/`ROLLBACK`。
- 部分 DDL（如 `ALTER TABLE`）、`LOCK TABLES` 会隐式提交事务。

### 12.2 隔离级别设置

```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

建议在服务器级别设置默认值，仅在必要时改会话级别。

### 12.3 混合存储引擎（第 11 页）

- **禁止**在同一事务中混用事务表与非事务表（如 InnoDB + MyISAM）。
- 回滚时非事务表无法撤销，导致数据不一致。

**原文**：

> MySQL doesn't manage transactions at the server level. Instead, the underlying storage engines implement transactions themselves.

> It is best practice to not mix storage engines in your application.

### 12.4 隐式锁与显式锁（第 11–12 页）

- InnoDB 使用**两阶段锁协议**：事务期间随时加锁，提交/回滚时一次性释放。
- 显式锁（标准 SQL 未定义，慎用）：
  - `SELECT ... FOR SHARE`（8.0，替代 `LOCK IN SHARE MODE`）
  - `SELECT ... FOR UPDATE`
- **不建议**使用 `LOCK TABLES`（InnoDB 已支持行级锁）。

**原文**：

> InnoDB uses a two-phase locking protocol. It can acquire locks at any time during a transaction, but it does not release them until a COMMIT or ROLLBACK.

---

## 13. 多版本并发控制 MVCC（第 12–14 页）

**要点**：

- 行级锁 + MVCC，许多读操作无需加锁。
- 通过**快照**让事务看到一致视图；不同事务可能同时看到同一表的不同数据。
- InnoDB 为每个事务分配 Transaction ID；修改时写 undo log，通过 rollback pointer 串联版本链。
- 读时比较记录的 trx_id 与 read view，不可见则沿 undo log 回溯。
- undo 写入也会 redo log（崩溃恢复需要）。
- **兼容隔离级别**：`READ COMMITTED`、`REPEATABLE READ`；不兼容 `READ UNCOMMITTED`、`SERIALIZABLE`。

**原文**：

> multiversion concurrency control (MVCC)

> MVCC works by using snapshots of the data as it existed at some point in time.

> most read queries never acquire locks.

> MVCC works only with the REPEATABLE READ and READ COMMITTED isolation levels.

---

## 14. 复制 Replication（第 14–15 页）

**要点**：

- MySQL 设计为**单节点写入**；通过复制将变更分发到其他节点。
- 源节点为每个副本维护复制客户端线程，有写操作时推送数据。
- 生产环境建议至少 **3 个副本**，分布在不同 region 做灾备。
- 8.0 重要特性：GTID、多源复制、并行复制、半同步复制（详见第 9 章）。

**原文**：

> MySQL is designed for accepting writes on one node at any given time.

> For any data you run in production, you should use replication and have at least three more replicas, ideally distributed in different locations (in cloud-hosted environments, known as regions) for disaster-recovery planning.

---

## 15. 数据文件结构（第 15–16 页）

**要点**（MySQL 8.0）：

- 表元数据并入 `.ibd` 文件的数据字典。
- 引入 **dictionary object cache**（LRU 内存缓存）：分区定义、表定义、存储程序、字符集等。
- `.ibd` 和 `.frm` 被每表 `.sdi`（serialized dictionary information）替代。

**原文**：

> In version 8.0, MySQL redesigned table metadata into a data dictionary that is included with a table's .ibd file.

> The .ibd and .frm files are replaced with serialized dictionary information (.sdi) per table.

---

## 16. InnoDB 存储引擎（第 16–17 页）

**要点**：

- **默认且推荐**的通用事务存储引擎。
- 数据存放在 **tablespace**（一系列数据文件）中。
- MVCC + 四隔离级别；默认 `REPEATABLE READ` + **next-key locking** 防幻读。
- **聚簇索引**（Clustered Index）：主键查找极快；二级索引含主键列，主键过大则二级索引也大。
- 内部优化：预测性预读、自适应哈希索引、插入缓冲（详见第 4 章）。
- 支持热备份：MySQL Enterprise Backup、Percona XtraBackup（第 10 章）。
- 5.6 起支持 **Online DDL**，5.7/8.0 持续扩展。

**原文**：

> InnoDB is the default transactional storage engine for MySQL and the most important and broadly useful engine overall.

> It is best practice to use the InnoDB storage engine as the default engine for any application.

> InnoDB has a next-key locking strategy that prevents phantom reads in this isolation level: rather than locking only the rows you've touched in a query, InnoDB locks gaps in the index structure as well, preventing phantoms from being inserted.

> secondary indexes contain the primary key columns, so if your primary key is large, other indexes will also be large.

---

## 17. JSON 文档支持（第 17 页）

**要点**：

- 5.7 引入 JSON 类型：自动校验 + 优化存储（优于 BLOB 存 JSON）。
- 8.0.7 支持 JSON 数组的**多值索引**（multivalued indexes）。

**原文**：

> the JSON type arrived with automatic validation of JSON documents as well as optimized storage that allows for quick read access, a significant improvement to the trade-offs of old-style binary large object (BLOB) storage engineers used to resort to for JSON documents.

> MySQL 8.0.7 adds the ability to define multivalued indexes on JSON arrays.

---

## 18. 数据字典变更（第 17 页）

**要点**：

- 8.0 移除基于文件的表元数据，改用 InnoDB 表存储的数据字典。
- 备份流程需改为查询新数据字典获取表定义（不再依赖 `.frm`）。

**原文**：

> Another major change in MySQL 8.0 is removing file-based table metadata storage and moving to a data dictionary using InnoDB table storage.

---

## 19. 原子 DDL（第 17 页）

**要点**：

- MySQL 8.0 的 DDL 要么**全部成功**，要么**全部回滚**。
- 通过 DDL 专用的 undo/redo log 实现。

**原文**：

> Finally, MySQL 8.0 introduced atomic data definition changes. This means that data definition statements now can either wholly finish successfully or be wholly rolled back.

---

## 20. 本章小结（第 18 页）

**要点**：

- MySQL 分层架构：服务器层查询执行 + 存储引擎层；Storage Engine API 是核心。
- 近年 Oracle 将开发重心放在 InnoDB：原子 DDL、在线 DDL、崩溃恢复、安全运维等。
- **后续章节以 InnoDB 为主**，极少涉及其他引擎。

**原文**：

> MySQL has a layered architecture, with server-wide services and query execution on top and storage engines underneath. Although there are many different plug-in APIs, the storage engine API is the most important.

> If you understand that MySQL executes queries by handing rows back and forth across the storage engine API, you've grasped the fundamentals of the server's architecture.

> InnoDB is the default storage engine and the one that should cover nearly every use case. As such, the following chapters focus heavily on the InnoDB storage engine when talking about features, performance, and limitations, and only rarely will we touch on any other storage engine from here on out.

---

## 架构总览

```
┌─────────────────────────────────────┐
│  第一层：Clients                     │
│  连接处理 / 认证 / 安全              │
├─────────────────────────────────────┤
│  第二层：Server Core                 │
│  查询解析 / 优化 / 内置函数           │
│  存储过程 / 触发器 / 视图             │
├─────────────────────────────────────┤
│  第三层：Storage Engines             │
│  InnoDB（默认推荐）/ 其他引擎...      │
└─────────────────────────────────────┘
         ↑ Storage Engine API ↑
```
