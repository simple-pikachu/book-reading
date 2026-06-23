# Chapter 6: Schema Design and Management

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 125–154 页（书中印刷页码）

---

## 1. 章节导言（第 125 页）

**要点**：Schema 设计影响索引策略（见第 7 章）与查询性能（见第 8 章）；好的设计从选对数据类型开始。

**原文**：

> This chapter covers schema design and management. Good schema design is the foundation for everything else we discuss in this book on indexing and on query performance optimization.

---

## 2. 选择最优数据类型（第 125 页）

**要点**：

- **更小通常更好**：占用更少磁盘、内存和 CPU 缓存，处理更快。
- **简单更好**：整型比字符串做比较/排序更快；用 MySQL 内建类型（`DATE`、`TIME`、`DATETIME`）而非字符串存时间。
- **尽量避免 NULL**：除非业务明确需要「未知」，否则用 `NOT NULL` 并设默认值；`NULL` 使索引、值比较和 `COUNT()` 更复杂。

**原文**：

> Smaller is usually better. Smaller data types are usually faster, because they use less space on the disk, in memory, and in the CPU cache.

> Simple is usually better. Fewer CPU cycles are typically required to process operations on simpler data types.

> Try to avoid NULL if possible. It's harder for MySQL to optimize queries that refer to nullable columns, because they make indexes, index statistics, and value comparisons more complicated.

---

## 3. 整数类型（第 125–126 页）

**要点**：

| 类型 | 存储（字节） |
|------|-------------|
| TINYINT | 1 |
| SMALLINT | 2 |
| MEDIUMINT | 3 |
| INT | 4 |
| BIGINT | 8 |

- 有符号范围：\(-2^{N-1}\) 到 \(2^{N-1}-1\)；`UNSIGNED` 将范围翻倍为 0 到 \(2^N-1\)。
- `INT(11)` 中的 11 **不限制**合法值范围，仅影响部分客户端显示宽度。
- 需要精确小数时用 `DECIMAL`；`FLOAT`/`DOUBLE` 不精确；存货币等可用 `BIGINT` 存「分」。

**原文**：

> There are five integer types: TINYINT, SMALLINT, MEDIUMINT, INT, or BIGINT. These require 8, 16, 24, 32, and 64 bits of storage space, respectively.

> INT(1) and INT(20) are the same except for the display width.

> The FLOAT and DOUBLE types are approximate. If you need to store exact fractional numbers, use DECIMAL instead.

---

## 4. 实数类型（第 126 页）

**要点**：

- `FLOAT` 4 字节，`DOUBLE` 8 字节；`DECIMAL` 可存相同精度范围但存储空间更大。
- 对精度敏感场景优先 `DECIMAL` 或整数缩放（如 BIGINT 存分）。

**原文**：

> A FLOAT column uses 4 bytes of storage. DOUBLE consumes 8 bytes and has greater precision and range.

---

## 5. 字符串类型（第 126–128 页）

### 5.1 VARCHAR 与 CHAR

**要点**：

- `VARCHAR` 变长，需 1–2 字节长度前缀 + 数据；`CHAR` 定长，不足补空格（`PAD SPACE`），检索时通常去掉尾部空格。
- 短且长度固定（如 MD5 哈希、Y/N 标志）用 `CHAR` 更省空间；`CHAR(1)` 存 Y/N 比 `VARCHAR(1)` 少一字节。
- 慷慨定义长度是坏习惯：`VARCHAR(5)` 与 `VARCHAR(200)` 存 `"hello"` 空间相同，但排序时 200 会分配更大临时缓冲区。

**原文**：

> VARCHAR stores variable-length character strings and is the most common string data type.

> CHAR is fixed-length, so it's useful if you want to store very short strings. If all the values are nearly the same length, CHAR is a good choice.

> Storing the value "hello" in a VARCHAR(5) and a VARCHAR(200) uses exactly the same amount of space on disk. But if you sort the values, the VARCHAR(200) will use much more memory.

### 5.2 BINARY 与 VARBINARY

**要点**：与 CHAR/VARCHAR 类似，但按字节而非字符处理，不做字符集排序；适合存二进制数据且避免 `\0` 填充问题。

### 5.3 BLOB 与 TEXT

**要点**：

- 家族：`TINYTEXT`/`TEXT`/`MEDIUMTEXT`/`LONGTEXT` 与对应 `BLOB` 类型。
- InnoDB 常将大值存行外；行内保留 1–4 字节指针。
- 排序默认只比较前 `max_sort_length` 字节；可对前缀建索引。
- **不要把图片存数据库**——应存文件系统或对象存储，库中只存路径。

**原文**：

> BLOB and TEXT are string data types designed to store large amounts of data as either binary or character strings, respectively.

> When MySQL sorts BLOB or TEXT columns, it sorts only the first max_sort_length bytes of such columns.

> Don't store images in a database. Store the images on a filesystem or in an object store, and store the path in the database.

### 5.4 ENUM

**要点**：

- 内部存整数（1, 2, 3…），磁盘紧凑；与 `CHAR`/`VARCHAR` 互转时可能锁表且慢。
- 按定义顺序排序，非字母序；自定义顺序用 `FIELD()`。
- 示例：`webservicecalls` 表将 `service`/`method` 改为 `ENUM` 后，与 `VARCHAR` 版 JOIN 性能对比显示 `ENUM` 在某些场景更慢（类型转换开销）。

**原文**：

> Using ENUM is sometimes a good idea. The string values are stored internally as integers, which are very compact.

> ENUM columns sort according to the order in which the ENUM members were listed in the column specification, not in alphabetical order.

---

## 6. 日期与时间类型（第 128–130 页）

**要点**：

| 类型 | 说明 |
|------|------|
| **DATETIME** | 1000–9999 年，8 字节，与时区无关 |
| **TIMESTAMP** | 4 字节，范围 1970–2038，自动时区转换；`DEFAULT CURRENT_TIMESTAMP` / `ON UPDATE` |
| **YEAR** | 1 字节 |

- `TIMESTAMP` 在 8.0 前行为怪异；修改列后务必 `SHOW CREATE TABLE` 确认。
- **2038 问题**：`TIMESTAMP` 上限约 2038-01-19；长期未来日期用 `DATETIME`。
- 需要亚秒精度时评估是否用 `INT` 存 Unix 时间戳（微秒）——简单但失去日期函数便利。

**原文**：

> DATETIME can hold a large range of values, from the year 1000 to the year 9999, with a precision of one second. It uses 8 bytes of storage space.

> TIMESTAMP uses only half as much storage as DATETIME, but it has a much smaller range.

> TIMESTAMP also suffers from the year 2038 problem.

---

## 7. 位压缩数据类型（第 130–131 页）

### 7.1 BIT

**要点**：可存最多 64 位；InnoDB 将 `BIT` 列存为足够大的 `CHAR`/`BINARY`（如 `BIT(1)` 实际占 1 字节）。MySQL 8 前行为怪异，推荐用 `TINYINT` 代替。

### 7.2 SET

**要点**：最多 64 个预定义字符串，内部打包为位图；可用 `FIND_IN_SET()` 查询，但不如在 `TINYINT` 上用位运算清晰、可移植。

**原文**：

> A SET column can have a maximum of 64 distinct members. MySQL stores the members internally as integers.

> We recommend using integer types with bit operations instead.

---

## 8. JSON 数据类型（第 131–133 页）

**要点**：

- 8.0 原生 `JSON` 类型；与规范化关系表相比，同数据集 JSON 表 `Data_length` 更大（括号等元数据开销）。
- 查询：`json_data->'$.designation'`；索引需 **生成列** + 普通索引：
  ```sql
  ALTER TABLE asteroids_json
    ADD COLUMN designation VARCHAR(30)
      GENERATED ALWAYS AS (json_data->>"$.designation"),
    ADD INDEX (designation);
  ```
- 有索引时 SQL 版通常更快（索引精确定位单行 vs JSON 全表扫描）。

**原文**：

> Our SQL version uses three 16 KB pages, and our JSON version uses five 16 KB pages to store the additional characters for defining JSON.

> To index a field inside JSON, we need to use a generated column and then index that column.

---

## 9. 选择标识符（第 133–135 页）

**要点**：

- 主键列尽量短；InnoDB 二级索引叶子含主键值——宽主键放大所有索引。
- 避免用 `ENUM`/`SET` 做主键。
- 避免用 `VARCHAR` 存 MD5/SHA1/UUID 字符串；用 `UNHEX()` 存 `BINARY(16)` 可省一半空间。
- **警惕自动生成 Schema**：ORM 常生成低效设计。

**原文**：

> In general, an identifier column should be as short as possible, because you're likely to use them for joins.

> Beware of Autogenerated Schemas. ORMs can generate schemas that work, but they often aren't designed well.

---

## 10. 特殊数据的 Schema 技巧（第 135 页）

**要点**：IP 地址不要 `VARCHAR(15)`，用 `INT UNSIGNED` + `INET_ATON()`/`INET_NTOA()`（或 8.0+ `INET6_ATON`/`INET6_NTOA` 支持 IPv6），从约 16 字节降至 4 字节。

**原文**：

> The space used shrinks from ~16 bytes for a VARCHAR(15) down to 4 bytes for an integer.

---

## 11. MySQL Schema 设计陷阱（第 135–138 页）

### 11.1 列太多

**要点**：单表数千列会导致查询变慢、内存暴涨；宽行使缓存容纳更少行。

### 11.2 JOIN 太多

**要点**：MySQL 对单查询 JOIN 数量有限制（`max_join_size` 等）；过多 JOIN 通常意味着 schema 需反规范化或拆分。

### 11.3 滥用 ENUM

**要点**：用 `ENUM` 存国家代码并列出全部 300+ 值——改成员需 `ALTER TABLE`，极不灵活。

### 11.4 伪装的 ENUM（SET 误用）

**要点**：`is_default SET('Y','N')` 只允许一个值时，语义等同 ENUM，却更复杂。

### 11.5 非空偏执（Not Invented Here）

**要点**：不要为了回避 `NULL` 而用魔法值（如 `0000-00-00`）；`sql_mode` 严格模式下非法。审慎使用 `NULL` 表示缺失。

**原文**：

> The All-Powerful ENUM. Using ENUM for a "country" column with hundreds of values is a recipe for pain.

> ENUM in Disguise. A SET that only allows one value is really an ENUM.

> NULL is not the enemy. We suggest considering NULL when the absence of a value is a valid state.

---

## 12. Schema 管理（第 138–153 页）

### 12.1 作为数据平台的一部分

**要点**：

- 与 partner 团队（应用开发）协作，把 schema 变更纳入 CI/CD。
- **版本控制**：schema 变更应与代码 deploy 同等对待。
- 商业工具：Liquibase 等；开源：Skeema（diff + 生成 DDL，不自行执行生产变更）。

**原文**：

> Set up your partner teams for success. Integrate schema management with continuous integration.

> Source control for schema changes should be as standard as the process your engineering team uses for code deploys.

### 12.2 生产环境执行 Schema 变更

**要点**：

| 方式 | 说明 |
|------|------|
| **Native DDL** | 8.0 支持 `INPLACE`/`INSTANT` 算法；仍可能锁表或限流 |
| **pt-online-schema-change** | Percona 工具；触发器同步增量；切换时短暂锁表 |
| **gh-ost** | GitHub 工具；无触发器，伪装为 replica 消费 binlog；对触发器敏感环境更友好 |

**选型**：

- **pt-osc**：需要强一致、可接受触发器、表已有触发器时可能冲突。
- **gh-ost**：更好应对高负载、避免触发器；但存在短暂不一致窗口。

**原文**：

> Native DDL statements. See the documentation for which changes are allowed using either INPLACE or INSTANT algorithms.

> pt-online-schema-change uses triggers to capture changes to the table while the schema change is in progress.

> gh-ost connects as a replica to one of your cluster replicas and consumes row-based replication events to build the new table without triggers.

### 12.3 Schema 变更 CI/CD 流水线

**要点**：预提交钩子 + Skeema diff → 测试环境验证 → 生产用 gh-ost/pt-osc 执行；配置 gh-ost 节流参数保护集群。

---

## 13. 小结（第 153–154 页）

**要点**：

- 选对数据类型是性能基础：`NULL`、`ENUM`/`SET`、`BIT` 各有陷阱。
- Schema 演进需工具化、自动化，使变更安全可扩展。
- 下一章将深入索引设计原则。

**原文**：

> Choosing optimal data types and managing schema changes is a crucial part of making this evolution safe and scalable.

> The indexing principles in the next chapter build on the schema design choices you make here.
