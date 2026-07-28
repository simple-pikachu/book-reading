# Chapter 1: MySQL 体系结构和存储引擎

> 来源：《MySQL技术内幕：InnoDB存储引擎（第2版）》姜承尧  
> 页码范围：约第 1–15 页（书中印刷页码）  
> 对照版本：MySQL 8.0.34

说明：本地 PDF 为扫描件；原文摘自第2版公开书摘整理，与印刷页可能有少量标点差异。

---

## 1. 数据库与实例（约第 1–2 页）

**要点**：

- **数据库**是二级存储器上按数据模型组织的数据集合（文件集合）。
- **数据库实例**是进程/程序，夹在用户与操作系统之间；一切定义、查询、维护、运行控制都经实例完成。
- 日常说的「启动/关闭 MySQL」实质是启动/关闭实例；应用只能通过实例访问数据库。

**原文**：

> 从概念上来说，数据库是文件的集合，是依照某种数据模型组织起来并存放于二级存储器中的数据集合；数据库实例是程序，是位于用户与操作系统之间的一层数据管理软件，用户对数据库数据的任何操作，包括数据库定义、数据查询、数据维护、数据库运行控制等都是在数据库实例下进行的，应用程序只有通过数据库实例才能和数据库打交道。

**8.0.34 新写法**：

```sql
SELECT VERSION();                    -- 期望 8.0.34
SHOW VARIABLES LIKE 'datadir';       -- 数据库文件所在目录
SHOW VARIABLES LIKE 'basedir';
SHOW VARIABLES LIKE 'pid_file';
SHOW VARIABLES LIKE 'port';
SHOW PROCESSLIST;                    -- 当前实例内会话/线程
```

```bash
# 启停的是「实例」，不是「某个库文件」
mysqld --version
mysqladmin -uroot -p shutdown
```

---

## 2. MySQL 体系结构概览（约第 2–4 页）

**要点**：

- 逻辑上仍可按「连接层 → SQL 层（解析/优化/执行）→ 存储引擎层」理解。
- 连接协议可选 TCP/IP、命名管道（Windows）、UNIX 域套接字（同机）等。
- 优化器、权限、视图、存储过程等在服务器层；真正存取数据由引擎负责。

**原文**：

> 在 Linux 和 Unix 系统上，本地连接还可以使用 UNIX 域套接字（UNIX Domain Socket）。UNIX 域套接字其实并不是一个网络协议，所以只能在 MySQL 客户端和数据库实例在同一台服务器上的情况下使用。用户可以在 MySQL 配置文件中指定套接字文件路径，在 Linux 系统下默认路径通常为 `/tmp/mysql.sock`。用户也可以在连接时通过 `--socket` 选项指定。

**8.0.34 新写法**：

```ini
# my.cnf / my.ini 示例
[mysqld]
port=3306
socket=/var/run/mysqld/mysqld.sock
bind-address=127.0.0.1

[client]
socket=/var/run/mysqld/mysqld.sock
```

```bash
# 同机优先走 socket（无 TCP 开销）
mysql -uroot -p -S /var/run/mysqld/mysqld.sock
# 或显式 TCP
mysql -uroot -p -h 127.0.0.1 -P 3306 --protocol=TCP
```

```sql
SHOW VARIABLES LIKE 'socket';
SHOW VARIABLES LIKE 'skip_networking';
```

---

## 3. 存储引擎是基于表的（约第 5–6 页）

**要点**：

- MySQL 的可插拔存储引擎是其核心特色之一。
- **引擎粒度是表，不是库**：同一 schema 内不同表可用不同引擎（生产上仍强烈建议统一 InnoDB）。

**原文**：

> 需要特别注意的是，存储引擎是基于表的，而不是数据库。

**8.0.34 新写法**：

```sql
SHOW ENGINES\G
SHOW VARIABLES LIKE 'default_storage_engine';
-- 8.0.34 默认即为 InnoDB
SET PERSIST default_storage_engine = 'InnoDB';

CREATE TABLE t_innodb (id INT PRIMARY KEY) ENGINE=InnoDB;
CREATE TABLE t_mem    (id INT PRIMARY KEY) ENGINE=MEMORY;  -- 仅临时/缓存场景

SELECT TABLE_SCHEMA, TABLE_NAME, ENGINE
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'test';
```

不要再把 MyISAM、Maria、ARCHIVE、FEDERATED 与 InnoDB 并列为「生产 OLTP 主选」；对照 `SHOW ENGINES` 看 Support 列，`InnoDB` 为 DEFAULT。

---

## 4. InnoDB 存储引擎（约第 6–9 页）

**要点**：

- 面向 OLTP：事务、行锁、外键、默认非锁定读（一致性读不阻塞写）。
- 自 MySQL 5.5.8 起即为默认引擎；8.0.34 仍默认 InnoDB，且系统表也是 InnoDB。
- 关键机制：MVCC、next-key locking、Insert Buffer（现称 Change Buffer）、doublewrite、Adaptive Hash Index、read ahead。
- 表数据按**聚集主键**组织；无显式主键时 InnoDB 生成 **6 字节 ROWID**。

**原文**：

> InnoDB 存储引擎支持事务，其设计目标主要面向在线事务处理（OLTP）的应用。其特点是行锁设计、支持外键，并支持类似于 Oracle 的非锁定读，即默认读取操作不会产生锁。从 MySQL 数据库 5.5.8 版本开始，InnoDB 存储引擎是默认的存储引擎。

> InnoDB 存储引擎通过多版本并发控制（MVCC）来获得高并发性，并且实现了 SQL 标准的 4 种隔离级别，默认为 REPEATABLE READ。同时，使用一种被称为 next-key locking 的策略来避免幻读（phantom）现象的产生。除此以外，InnoDB 存储引擎还提供了插入缓冲（insert buffer）、二次写（double write）、自适应哈希索引（adaptive hash index）、预读（read ahead）等高性能、高可靠的功能。

> InnoDB 存储引擎的表是基于聚簇索引建立的，因此表中的每一行数据都按主键顺序存放。若表未定义主键，InnoDB 会为每行生成一个 6 字节的 ROWID 作为主键。

**8.0.34 新写法**：

```sql
SHOW VARIABLES LIKE 'default_storage_engine';   -- InnoDB
SHOW VARIABLES LIKE 'transaction_isolation';   -- 勿再用 tx_isolation
SHOW VARIABLES LIKE 'innodb_adaptive_hash_index';
SHOW VARIABLES LIKE 'innodb_doublewrite';
SHOW VARIABLES LIKE 'innodb_change_buffering';   -- 原 Insert Buffer 升级名

-- 显式主键（推荐），避免隐式 6 字节 ROWID
CREATE TABLE orders (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (id),
  KEY idx_user (user_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

SHOW CREATE TABLE orders\G
```

系统库已是 InnoDB，勿再假设「权限表 = MyISAM、崩溃半更新」：

```sql
SELECT TABLE_NAME, ENGINE
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'mysql'
ORDER BY TABLE_NAME;
```

---

## 5. MyISAM 存储引擎（约第 9–11 页）

**要点**：

- 不支持事务；锁粒度主要为**表锁**；曾以全文索引见长（InnoDB 亦已支持全文）。
- 缓存策略：主要缓存**索引**，数据依赖 OS 缓存。
- 文件：`.MYD`（数据）、`.MYI`（索引）；书中时代还有 `.frm`（8.0 已无，见第 3 章笔记）。

**原文**：

> MyISAM 存储引擎不支持事务、不支持行级锁，只支持表锁。MyISAM 存储引擎的缓冲池只缓存索引文件，并不缓存数据文件，数据文件的缓存交由操作系统本身来完成。MyISAM 表由 MYD 与 MYI 文件组成，分别存放数据和索引。此外，MyISAM 支持全文索引（FULLTEXT）。

**8.0.34 新写法**：

```sql
-- 仍可创建，但不作为 OLTP/默认引擎
CREATE TABLE t_myisam (id INT, title VARCHAR(200), FULLTEXT(title)) ENGINE=MyISAM;

SHOW ENGINES WHERE Engine = 'MyISAM';
-- 分区：8.0 仅 InnoDB（及 NDB）原生分区；MyISAM 分区表需升级前改造
```

生产选型：**默认且几乎唯一切实选项是 InnoDB**；MyISAM 仅边缘/只读归档等特例，不要与 InnoDB「并列主选」。

---

## 6. NDB 存储引擎（约第 11–12 页）

**要点**：

- NDB（NDBCLUSTER）面向集群；数据可分布在多节点内存中。
- JOIN 等复杂关联往往在 **MySQL 数据库层（SQL 节点）** 完成，而非全部下推到数据节点。

**原文**：

> NDB 存储引擎是一个集群存储引擎，其特点是数据全部放在内存中（从 MySQL 5.1 开始可以将非索引数据放在磁盘上），因此主键查找（primary key lookups）的速度极快。但需要注意的是，NDB 存储引擎的 JOIN 操作是在数据库层完成的，而不是在存储引擎层完成的，这意味着复杂的 JOIN 操作需要巨大的网络开销，因此查询速度很慢。

**8.0.34 新写法**：

```sql
SHOW ENGINES WHERE Engine LIKE '%NDB%';
-- 多数单机/主从/InnoDB Cluster 场景无需启用 NDB
-- 需要水平扩展优先评估 InnoDB Cluster / Group Replication / 分片中间件
```

---

## 7. 事务：数据库与文件系统的分水岭（约第 12–13 页）

**要点**：

- 事务（ACID）是数据库相对传统文件系统的核心能力差异。
- 支持事务的引擎（以 InnoDB 为代表）才能可靠承载 OLTP 一致性需求。

**原文**：

> 相信在任何一本关于数据库原理的书中，可能都会提到数据库与传统文件系统的最大区别在于数据库是支持事务的。

**8.0.34 新写法**：

```sql
START TRANSACTION;
UPDATE account SET bal = bal - 100 WHERE id = 1;
UPDATE account SET bal = bal + 100 WHERE id = 2;
COMMIT;
-- 或 ROLLBACK;

SHOW VARIABLES LIKE 'autocommit';
SET SESSION transaction_isolation = 'REPEATABLE-READ';
```

---

## 8. 账户、认证与字符集（约第 13–15 页，对照 8.0.34）

**要点**（书中多为 5.x 口吻，本节以 8.0.34 为准）：

- `mysql.user` **无 `password` 列**，密码在 `authentication_string`。
- 默认认证插件为 **`caching_sha2_password`**；**8.0.34 起弃用 `mysql_native_password`**。
- 用 **`CREATE USER` / `ALTER USER`**，禁止 `GRANT` 顺手建用户、禁止 `PASSWORD()`。
- 支持角色（ROLE）；服务器默认字符集为 **`utf8mb4`**。

**原文**：

> （书中账户章节仍按「用户名 + 主机 + 密码」与权限表叙述；连接与权限校验发生在实例层。以下按 8.0.34 改写操作，不沿用书中 `PASSWORD()` / `GRANT` 建用户写法。）

**8.0.34 新写法**：

```sql
SHOW VARIABLES LIKE 'default_authentication_plugin';
-- caching_sha2_password

SELECT user, host, plugin, authentication_string
FROM mysql.user
WHERE user = 'appuser';

-- 正确建用户（不要 GRANT 创建用户）
CREATE USER 'appuser'@'%'
  IDENTIFIED WITH caching_sha2_password BY 'StrongPass!2026';

CREATE ROLE 'app_read', 'app_write';
GRANT SELECT ON appdb.* TO 'app_read';
GRANT SELECT, INSERT, UPDATE, DELETE ON appdb.* TO 'app_write';
GRANT 'app_read', 'app_write' TO 'appuser'@'%';
SET DEFAULT ROLE ALL TO 'appuser'@'%';

ALTER USER 'appuser'@'%' IDENTIFIED BY 'AnotherStrongPass!';
-- 避免：IDENTIFIED WITH mysql_native_password（8.0.34 已弃用）

SHOW VARIABLES LIKE 'character_set_server';   -- utf8mb4
SHOW VARIABLES LIKE 'collation_server';       -- utf8mb4_0900_ai_ci（常见）

CREATE DATABASE appdb
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;
```

---

## 9. 本章核对清单（8.0.34）

| 检查项 | 期望 |
|--------|------|
| `default_storage_engine` | `InnoDB` |
| `mysql` 系统表 ENGINE | `InnoDB` |
| 建用户 | `CREATE USER` + 角色 |
| 认证插件 | `caching_sha2_password` |
| 字符集 | `utf8mb4` |
| 引擎选型 | 不以 MyISAM/Maria 作 OLTP 并列主选 |

```sql
SHOW ENGINES;
SHOW VARIABLES LIKE 'default_storage_engine';
SHOW VARIABLES LIKE 'default_authentication_plugin';
SHOW VARIABLES LIKE 'character_set_server';
```
