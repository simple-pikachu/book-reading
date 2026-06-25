# Chapter 8: Query Performance Optimization

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 191–226 页（书中印刷页码）

---

## 1. 章节导言（第 191 页）

**要点**：

- Schema 优化与索引是高性能的必要条件，但**不够**——还需设计好查询。
- 查询优化、索引优化、Schema 优化**相辅相成**，应反复参照第 6、7、8 三章。
- 本章目标：理解 MySQL **如何真正执行查询**，从而判断高效/低效，扬长避短。

**原文**：

> If your queries are bad, even the best-designed schema and indexes will not perform well.

> Our goal is to help you understand deeply how MySQL really executes queries, so you can reason about what is efficient or inefficient, exploit MySQL's strengths, and avoid its weaknesses.

---

## 2. 查询慢的原因（第 191 页）

**要点**：

- 一切围绕**响应时间（response time）**。
- 查询由子任务组成；优化子任务 = **消除**、**减少次数**或**加快速度**。
- 查询生命周期：客户端 → 服务器（解析、规划、执行）→ 客户端；执行阶段涉及大量存储引擎调用及分组/排序等后处理。
- 时间消耗在：网络、CPU、统计、规划、锁（mutex 等待）、**存储引擎取行**（内存/CPU/I/O）。
- 优化目标：避免操作被**无谓执行**、**执行过多次**或**执行过慢**。

---

## 3. 优化数据访问（第 192–197 页）

大多数慢查询的根本原因是处理了**过多数据**。分析步骤：

1. 应用是否取回了**比需要更多**的数据（行或列）？
2. MySQL 是否**检查了比需要更多**的行？

### 3.1 是否请求了不需要的数据（第 192–193 页）

| 典型错误 | 说明 |
|----------|------|
| **取行过多** | MySQL **不会**按需返回前 N 行后停止，而是生成**完整结果集**；客户端库再取全部数据并丢弃多余部分 → 加 `LIMIT` |
| **多表 JOIN 用 SELECT \*** | 返回所有表的全部列；应只选需要的列，如 `SELECT sakila.actor.* FROM sakila.actor ...` |
| **SELECT \*** | 阻碍覆盖索引、增加 I/O/内存/CPU；表结构变更时也有风险（开发便利 vs 性能需权衡） |
| **重复取数** | 如每条评论都查一次用户头像 URL → 首次缓存后复用 |

### 3.2 MySQL 是否检查了过多数据（第 194–197 页）

**三个简单成本指标**（均记录在慢查询日志中）：

| 指标 | 说明 |
|------|------|
| 响应时间 | = **服务时间** + **排队时间**；负载变化下不稳定；可用 QUBE 估算上限 |
| 检查行数（rows examined） | 反映查找效率；非完美指标（行长短、内存 vs 磁盘不同） |
| 返回行数（rows sent） | 理想情况与检查行数接近；JOIN 时通常 1:1 ~ 10:1，有时差几个数量级 |

**响应时间细分**：

- **服务时间**：服务器实际处理查询的时间。
- **排队时间**：等待 I/O、行锁等（通常最难单独测量）。
- 常见等待：I/O 等待、锁等待；高并发、硬件、存储引擎锁均影响响应时间。

**访问类型（EXPLAIN `type` 列）**：从全表扫描到常量查找，越靠后越快（读更少数据）。

- 全表扫描 `ALL` → 索引扫描 → 范围扫描 → 唯一索引查找 → 常量 `const`
- 无好访问类型时，通常靠**加合适索引**解决。

**WHERE 三种应用方式**（从优到劣）：

1. **存储引擎层**：索引查找时直接过滤（最优）。
2. **覆盖索引**：`Using index`，服务器层过滤，无需读表行。
3. **读表后过滤**：`Using where`，服务器层读完整行再丢弃。

**Sakila 示例**：`film_actor WHERE film_id = 1`

- 有索引：`type: ref`，约 10 行。
- 无索引：`type: ALL`，约 5462 行 + `Using where`。

**注意**：`GROUP BY` + `COUNT()` 即使有 `Using index` 也可能需扫描全表（无 WHERE 无法消行）；MySQL 只报告访问总行数，不报告实际用于构建结果集的行数。

**高级修复手段**：

- 覆盖索引
- 改 Schema（如汇总表，见第 6 章）
- 重写复杂查询

**原文**：

> Is MySQL Examining Too Much Data?

---

## 4. 重构查询的方式（第 198–200 页）

目标：用替代方式得到想要的结果，**不一定**从 MySQL 拿回相同结果集；可改应用代码配合。

### 4.1 复杂查询 vs 多个简单查询（第 198–199 页）

- 传统观念：尽量少查询、在库内多做工作（网络与解析/优化开销大）。
- **MySQL 不同**：连接/断开高效，简单查询极快；现代网络延迟也降低。
- 商品硬件上简单查询可达 **10 万+ QPS**；单连接千兆网下 **2000+ QPS**。
- 但连接响应仍慢于内存中每秒百万级行遍历 → **能少查仍应少查**。
- 有时**分解**为几个简单查询反而更高效；也常见反例：10 次单行查询本可 1 次 10 行查询，甚至每列单独查。

### 4.2 拆分查询（Chopping Up）（第 199 页）

保持语义，分块执行、每次影响更少行。

**示例：批量清理历史数据**

```sql
-- 不推荐：一次性大 DELETE
DELETE FROM messages WHERE created < DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- 推荐：循环 LIMIT 10000，可用 pt-archiver
DELETE FROM messages WHERE created < DATE_SUB(NOW(), INTERVAL 3 MONTH) LIMIT 10000;
```

- 每次 1 万行：足够高效，影响可控；事务型引擎宜更小事务。
- 可在批次间 **sleep** 分散负载、缩短持锁时间；复制环境下可减轻 lag。

### 4.3 JOIN 分解（Join Decomposition）（第 200 页）

用多个单表查询 + **应用层 JOIN**，替代多表 JOIN。

**适用场景**：

| 优势 | 说明 |
|------|------|
| 缓存更高效 | 已缓存的 tag/post 可跳过对应查询 |
| 降低锁竞争 | 单表查询有时更少争用 |
| 分库分表 | 表可放不同服务器 |
| 查询本身更高效 | 大表用 `IN()` 列表，MySQL 可排序 ID 优化取行 |
| 减少重复行访问 | 应用层 JOIN 每行只取一次；SQL JOIN 可能重复访问 |

**何时考虑**：大量缓存复用、跨服务器分布、大表 `IN()` 替代 JOIN、同一表多次 JOIN。

---

## 5. 查询执行基础（第 201–218 页）

### 5.1 执行路径概览（第 201 页）

1. 客户端发送 SQL
2. 服务器解析、预处理、优化 → **执行计划**
3. 执行引擎通过存储引擎 API 执行
4. 服务器返回结果给客户端

### 5.2 查询状态（第 204 页）

**要点**：

- **半双工**：同一时刻只能发送或接收，无法中断消息；无流控。
- 客户端查询以**单个数据包**发送 → `max_allowed_packet` 重要。
- 服务器响应通常**多包**；客户端必须接收**完整结果集**，不能只取几行后让服务器停止 → **`LIMIT` 至关重要**。
- 服务器是**推送**行（"drinking from the fire hose"），客户端无法中途叫停。
- 默认：客户端库**缓冲整个结果集**于内存；未取完前服务器保持 **Sending data** 状态且不释放锁等资源。
- **非缓冲模式**（如 PHP `mysql_unbuffered_query`、Perl `mysql_use_result`）：省内存、可更早处理，但服务器资源持锁更久；可用 `SQL_BUFFER_RESULT` 折中。

### 5.3 优化过程（第 205–216 页）

`SHOW FULL PROCESSLIST` 查看 `Command` 列：

| 状态 | 含义 |
|------|------|
| Sleep | 等待新查询 |
| Query | 执行查询或向客户端发送结果 |
| Locked | 等待**服务器级表锁**（InnoDB 行锁不显示为此状态） |
| Analyzing and statistics | 检查存储引擎统计、优化查询 |
| Copying to tmp table [on disk] | GROUP BY / filesort / UNION 等写临时表 |
| Sorting result | 排序结果集 |

繁忙服务器上 `statistics` 等短暂状态若持续很久，通常表示异常。

### 5.4 执行引擎（第 217 页）

**子步骤**：解析 → 预处理 → 优化。

**解析器与预处理器**：

- 解析器：分词、构建解析树、语法校验。
- 预处理器：表/列存在性、别名消歧、**权限检查**。

**基于成本的优化器（CBO）**：

- 预测各执行计划成本，选最低成本。
- 成本单位原为随机 4KB 页读，现更复杂（含 WHERE 比较估算等）。
- 查看估算：`SHOW STATUS LIKE 'Last_query_cost'`（假设每次读都触发磁盘 I/O，不含缓存）。

**优化器可能选错计划的原因**：

- 统计信息不准（InnoDB 因 MVCC 行数统计不精确）
- 成本模型 ≠ 真实成本（顺序 I/O、页已在内存等）
- MySQL 最小化**成本**而非你的**延迟**目标
- 不考虑并发其他查询
- 有时遵循规则而非成本（如 FULLTEXT `MATCH()`）
- 不考虑存储函数/UDF 成本
- 搜索空间过大可能错过最优计划

**静态 vs 动态优化**：

| 类型 | 特点 | 场景 |
|------|------|------|
| **静态** | 仅看解析树；与参数值无关；"编译期" | 预处理语句可做一次 |
| **动态** | 依赖上下文、参数、行数；"运行期" | 每次执行需重评估；执行中可能再优化 |

**MySQL 已知优化类型**（勿抢先"帮"优化器，除非确知有益）：

- 重排 JOIN 顺序
- OUTER JOIN → INNER JOIN 转换
- 代数等价变换、常量折叠（如 `(5=5 AND a>5)` → `a>5`）
- `COUNT()`/`MIN()`/`MAX()` 优化（B-tree 首尾行 → `Select tables optimized away`）
- 常量表达式求值、主键/唯一索引常量查找
- 覆盖索引
- 子查询改写
- 提前终止（`LIMIT`、不可能条件 `Impossible WHERE`、DISTINCT/not-exists）
- 相等传播（`USING`/`ON` 自动传播 WHERE，**无需**手写两表条件）
- `IN()` 列表排序 + 二分查找 **O(log n)**，优于等效 OR 链 **O(n)**

**表与索引统计**：优化器在**服务器层**，统计由**存储引擎**提供（页数、基数、行/键长度、键分布等）。

### 5.5 MySQL 的 JOIN 执行策略（第 212 页）

- MySQL 中 **JOIN 含义很广**：任何查询（含子查询、单表 SELECT）都是 JOIN。
- `UNION`：各分支查询 + 写入临时表再读出。
- 传统：**嵌套循环 JOIN**（找一行 → 嵌套找下一表匹配行 → 回溯）。
- **MySQL 8.0.20+**：块嵌套循环废弃，改用 **Hash Join**（一侧数据集可放内存时更快）。

### 5.6 执行计划与 JOIN 优化器（第 212–215 页）

- 执行计划是**指令树**，非字节码；`EXPLAIN FORMAT=TREE` / `EXPLAIN EXTENDED` + `SHOW WARNINGS` 可查看。
- 多表 JOIN 概念上可画**平衡树**，MySQL 实际总是 **左深树**（从驱动表逐层嵌套）。
- **JOIN 优化器**：选最低成本表顺序；`EXPLAIN` 中**第一行 = 驱动表**。
- **Sakila 三表 JOIN 示例**：优化器选 `actor`(200 行) 驱动优于 `film`(1000 行) 驱动 → 更少索引探测与回溯；可用 `STRAIGHT_JOIN` 强制顺序（罕见需要）。
- n 表 JOIN 有 **n!** 种顺序；10 表约 362 万 → 超 `optimizer_search_depth` 时用贪心搜索。
- `LEFT JOIN`、相关子查询等依赖关系可缩小搜索空间。

### 5.7 排序优化（第 216 页）

无法用索引排序时 → **filesort**（内存或磁盘）。

| 算法 | 行为 | 特点 |
|------|------|------|
| **两遍（旧）** | 先排序行指针+ORDER BY 列，再回表读行 | 两次读表，随机 I/O 多 |
| **单遍（新）** | 读查询所需全部列，排序后输出 | 大 I/O 数据集更高效；占 sort buffer 更大 |

**注意**：filesort 为每元组分配**最大可能**记录空间（含 VARCHAR 全长；utf8mb4 每字符 4 字节）→ 临时空间可能远超表大小。

**JOIN + ORDER BY**：

- ORDER BY 仅引用**驱动表**列 → 可先 filesort 再 JOIN（`Using filesort`）。
- 否则先 JOIN 写临时表再 filesort（`Using temporary; Using filesort`）；`LIMIT` 在 filesort **之后**应用。

### 5.8 查询执行引擎（第 217 页）

- 按计划调用存储引擎 **handler API**；每表一个 handler 实例（优化阶段即创建以取元数据）。
- 约十几种基本操作（索引首行/下一行等）即可执行大多数查询。
- 表锁由**服务器**管理；引擎行锁（如 InnoDB）不替代服务器锁。
- 日期函数、视图、触发器等跨引擎功能在服务器层实现。

### 5.9 返回结果给客户端（第 218 页）

- 无结果集的语句也返回受影响行数等信息。
- **增量发送**：生成一行即发一行，省内存、客户端更早收到数据。
- 每行单独协议包（TCP 层可合并）；可用 `SQL_BUFFER_RESULT` 改变行为。

---

## 6. 优化器限制（第 219–220 页）

| 限制 | 说明 |
|------|------|
| **UNION** | 无法将外层 `WHERE`/`LIMIT`/`ORDER BY` 下推到各分支；`LIMIT 20` 可能先物化全部行再取 20 → 应在**每个 SELECT 内**重复 `LIMIT`/`ORDER BY`，最外层再加总 `ORDER BY` |
| **相等传播** | 大 `IN()` 列表经传播复制到多表 → 优化/执行变慢；无内置规避 |
| **并行执行** | 单查询无法多 CPU 并行 |
| **同表 SELECT + UPDATE** | 不允许更新时子查询读同一表（ERROR 1093）→ 用**派生表**物化为临时表再 JOIN 更新 |

**同表更新绕过示例**：

```sql
UPDATE tbl
INNER JOIN (
  SELECT type, COUNT(*) AS c FROM tbl GROUP BY type
) AS der USING(type)
SET tbl.c = der.c;
```

---

## 7. 特定查询类型优化（第 221–225 页）

> 本节建议可能随版本变化；未来 MySQL 或可自行完成部分优化。

### 7.1 COUNT()（第 221–222 页）

**两种语义**：

| 形式 | 含义 |
|------|------|
| `COUNT(column)` / `COUNT(expr)` | 统计**非 NULL 值**次数 |
| `COUNT(*)` | 统计**行数**；不展开 `*`，统计行时**始终用 COUNT(\*)** |

**多色统计（单次查询）**：

```sql
-- 推荐
SELECT SUM(IF(color = 'blue', 1, 0)) AS blue,
       SUM(IF(color = 'red', 1, 0)) AS red
FROM items;

-- 等价写法
SELECT COUNT(color = 'blue' OR NULL) AS blue,
       COUNT(color = 'red' OR NULL) AS red
FROM items;
```

**近似计数**：`EXPLAIN` 的 `rows` 估算；或放宽 WHERE 条件换速度（缓存场景）。

**深度优化**：覆盖索引 → 外部缓存（memcached）→ **"快、准、简：三选二"**。

### 7.2 JOIN（第 223 页）

- `ON`/`USING` 列加索引；按**实际 JOIN 顺序**加索引——通常只需在**第二个表**上加（除非其他查询也需要）。
- `GROUP BY`/`ORDER BY` 尽量只引用**单表**列，以便用索引。
- 升级 MySQL 时注意 JOIN 语法、运算符优先级变化（可能变交叉连接或语法错误）。

### 7.3 GROUP BY ROLLUP（第 223 页）

- `WITH ROLLUP` 超聚合可能未充分优化；`EXPLAIN` 看 filesort / 临时表。
- 可尝试 hint、应用层聚合、子查询/FROM 子句、临时表 + `UNION`，或将 ROLLUP 逻辑移到应用。

### 7.4 LIMIT / OFFSET（第 223–224 页）

- 分页几乎总配 `ORDER BY`；需支持排序的索引。
- **`OFFSET` 是痛点**：`LIMIT 10000, 20` 生成 10020 行丢弃 10000 行。

**优化手段**：

1. **限制最大页数**
2. **延迟 JOIN（deferred join）**：先在覆盖索引上 `LIMIT`，再 JOIN 回表取列

```sql
SELECT film.film_id, film.description
FROM sakila.film
INNER JOIN (
  SELECT film_id FROM sakila.film ORDER BY title LIMIT 50, 5
) AS lim USING(film_id);
```

3. **位置查询**：预计算 `position` 列 → `WHERE position BETWEEN 50 AND 54`
4. **键集分页（cursor）**：记住上一页最后主键，不用 OFFSET

```sql
-- 第一页
SELECT * FROM sakila.rental ORDER BY rental_id DESC LIMIT 20;
-- 后续页（假设上一页最小 rental_id = 16030）
SELECT * FROM sakila.rental
WHERE rental_id < 16030
ORDER BY rental_id DESC LIMIT 20;
```

5. 预计算汇总表、冗余窄表（主键 + ORDER BY 列）

**原文**：

> This technique is very efficient no matter how far you paginate into the table.

### 7.5 SQL_CALC_FOUND_ROWS（第 225 页）

- 并非"预测"总行数，而是生成**完整结果集再丢弃** → 极昂贵。
- 替代方案：
  - **"下一页"链接**：`LIMIT 21` 取 20 条，有第 21 条则显示下一页
  - 缓存前 1000 行供翻页
  - `EXPLAIN` 估算行数
  - 单独 `COUNT(*)`（覆盖索引时往往更快）

### 7.6 UNION（第 225 页）

- MySQL **总是**建临时表存放 UNION 结果再读出（即使可直返客户端）。
- 优化有限 → 手动下推 `WHERE`/`LIMIT`/`ORDER BY` 到各 `SELECT`。
- **始终用 `UNION ALL`**（除非需去重）；无 `ALL` 则临时表上 DISTINCT 全行判重，很贵。
- `UNION ALL` **不能**避免临时表。

---

## 8. 本章小结（第 226 页）
**要点**：

- 查询优化是 Schema、索引、查询设计拼图的最后一块；需理解执行过程才能推理耗时所在。
- 新维度：MySQL 如何根据一表/索引中的数据访问另一表/索引。

**三管齐下**：

1. **少做事**（stop doing things）
2. **做更少次**（do them fewer times）
3. **做得更快**（do them more quickly）

**原文**：

> Optimization always requires a three-pronged approach: stop doing things, do them fewer times, and do them more quickly.
