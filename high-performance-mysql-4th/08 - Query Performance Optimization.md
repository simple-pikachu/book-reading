# Chapter 8: Query Performance Optimization

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 191–226 页（书中印刷页码）

---

## 1. 章节导言（第 191 页）

**要点**：查询慢通常因访问数据方式不当；优化需结合 schema、索引与执行计划。

---

## 2. 查询慢的原因（第 191 页）

数据访问低效、检查行数过多、额外排序/临时表等。

---

## 3. 优化数据访问（第 192–197 页）

### 3.1 是否请求了不需要的数据

- `SELECT *`、重复查询、缓存可缓存的结果。

### 3.2 MySQL 是否检查了过多数据

指标：`rows_examined` vs `rows_sent`；可用 `EXPLAIN` 的 `rows` 列估算。

**原文**：

> Is MySQL Examining Too Much Data?

---

## 4. 重构查询的方式（第 198–200 页）

- 复杂单查询 vs 多个简单查询（依场景）。
- **查询分解**、**JOIN 分解**（先查 ID 再关联）。

---

## 5. 查询执行基础（第 201–218 页）

### 5.1 客户端/服务器协议（第 202 页）

文本协议、连接状态。

### 5.2 查询状态（第 204 页）

`SHOW PROCESSLIST` / Performance Schema。

### 5.3 优化过程（第 205–216 页）

解析 → 预处理 → 优化器生成执行计划 → 执行引擎。

- 成本模型基于统计信息；`EXPLAIN` 查看计划。
- 子查询、JOIN 顺序、索引选择。

### 5.4 执行引擎（第 217 页）

调用存储引擎 API 逐行或批量取数。

### 5.5 返回结果（第 218 页）

服务端缓存 vs 客户端拉取。

---

## 6. 优化器限制（第 219–220 页）

| 限制 | 说明 |
|------|------|
| UNION | 无法用索引优化各分支 |
| 相等传播 | 某些情况优化器保守 |
| 并行执行 | 有限支持 |
| 同表 SELECT+UPDATE | 需特殊处理 |

---

## 7. 特定查询类型优化（第 221–225 页）

### COUNT()

- `COUNT(*)` 统计行；`COUNT(column)` 统计非 NULL 值。
- 多色统计用 `SUM(color='blue')` 或条件聚合，非 OR 表达式。

### JOIN

- 确保连接列类型一致、有索引；小表驱动大表（依优化器）。

### GROUP BY ROLLUP

- 层次汇总；注意额外开销。

### LIMIT / OFFSET

- **大 OFFSET 极慢**；用「上次最大 ID」键集分页替代。

**原文**：

> This technique is very efficient no matter how far you paginate into the table.

### SQL_CALC_FOUND_ROWS

- 昂贵；改用 LIMIT n+1 判断是否有下一页，或单独 `COUNT(*)`（覆盖索引时更快）。

### UNION

- 始终用 **UNION ALL**（除非需去重）；手动下推 WHERE/LIMIT 到各 SELECT。

---

## 8. 本章小结（第 226 页）

**三管齐下**：少做事、做更少次、做得更快。

**原文**：

> Optimization always requires a three-pronged approach: stop doing things, do them fewer times, and do them more quickly.
