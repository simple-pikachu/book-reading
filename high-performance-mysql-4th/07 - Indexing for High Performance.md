# Chapter 7: Indexing for High Performance

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 155–189 页（书中印刷页码）

---

## 1. 章节导言（第 155 页）

**要点**：索引是提升查询性能最有力的手段之一；最优索引常需配合改写查询（与第 8 章紧密相关）。

**原文**：

> Index optimization is perhaps the most powerful way to improve query performance. Indexes can improve performance by many orders of magnitude.

---

## 2. 索引基础（第 156–160 页）

**要点**：

- 索引在**存储引擎层**实现，非标准化。
- **最左前缀**：多列索引仅对左前缀高效；`(last_name, first_name, dob)` 不能跳过中间列。
- ORM 不能替代索引设计知识。

**B-tree 适用查询**：全值匹配、左前缀、列前缀、范围、精确+范围组合、覆盖索引、ORDER BY。

**限制**：不能以非左列开头；不能跳过列；范围条件后的列无法用于索引访问优化。

**原文**：

> MySQL can only search efficiently on the leftmost prefix of the index.

---

## 3. 索引类型（第 156–161 页）

| 类型 | 说明 |
|------|------|
| **B-tree** | 默认；InnoDB 用 B+ 树 |
| **自适应哈希索引** | InnoDB 自动为热点页建内存哈希，不可配置 |
| **FULLTEXT** | 关键词搜索，用于 MATCH AGAINST |

---

## 4. 索引的收益（第 161 页）

减少扫描行数、避免排序、将随机 I/O 变为顺序 I/O 等。

---

## 5. 高性能索引策略（第 162–177 页）

### 5.1 前缀索引（第 162–164 页）

缩短索引长度；需评估选择性（distinct 比例）。

### 5.2 多列索引（第 165–166 页）

`(a,b)` ≠ 两个单列索引；按**选择性**与查询模式排列列顺序。

### 5.3 聚簇索引（第 170–177 页）

- InnoDB 表数据即主键 B+ 树叶子节点。
- 主键应**短且递增**（避免 UUID 随机插入导致页分裂）。
- 二级索引叶子含主键列。

### 5.4 覆盖索引（第 178 页）

索引包含查询所需全部列，无需回表。

### 5.5 索引扫描排序（第 180 页）

ORDER BY 可利用索引顺序，避免 filesort。

---

## 6. 冗余与重复索引（第 182 页）

如 `(a)` 与 `(a,b)` 中 `(a)` 可能冗余；用工具检测。

---

## 7. 未使用索引（第 185 页）

Performance Schema / sys 可发现从未使用的索引。

---

## 8. 索引与表维护（第 186–188 页）

- **损坏**：`CHECK TABLE`；InnoDB 损坏极罕见，多为硬件或人为操作 `.ibd`。
- **统计信息**：`ANALYZE TABLE`；InnoDB 采样页面；`innodb_stats_on_metadata=OFF` 避免大库上 SHOW 触发重采样。
- **碎片**：`OPTIMIZE TABLE` 或 `ALTER TABLE ... ENGINE=InnoDB`。

---

## 9. 本章小结（第 189 页）

**三条原则**：

1. **单行随机访问慢**——尽量一次读含多行的块。
2. **按序范围访问快**——顺序 I/O + 无需额外排序。
3. **索引下推等**——在存储引擎层过滤（MySQL 5.6+ ICP）。

**原文**：

> Single-row access is slow, especially on spindle-based storage.

> Accessing ranges of rows in order is fast.
