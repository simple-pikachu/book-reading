# Chapter 11: Scaling MySQL

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 287–311 页（书中印刷页码）

---

## 1. 什么是扩展（第 287 页）

**要点**：垂直扩展（更强硬件）有上限；水平扩展通过分片、读池等分散负载。

---

## 2. 读密集 vs 写密集（第 289–291 页）

- **读扩展**：复制 + 读池 + 负载均衡。
- **写扩展**：分片（sharding）；MySQL 单源写入是长期规则。

**原文**：

> scale reads with replicas, scale writes with sharding.

---

## 3. 功能分片（第 291 页）

按业务功能将表拆到独立集群（与第 2 章 functional sharding 一致）。

---

## 4. 读池扩展（第 292–297 页）

### 4.1 配置管理（第 294 页）

- 用 **服务发现**（如 Consul）自动维护副本列表，勿手工改配置。
- 每读池至少 3 节点 + 独立备份/报表副本。

### 4.2 健康检查（第 295–296 页）

- 简单：端口存活检查。
- 复杂：HTTP 脚本检查复制延迟、查询延迟。
- 确认 `read_only` / `super_read_only`。
- 全部副本失败健康检查时需 **fallback** 策略。

### 4.3 负载均衡算法（第 297 页）

高负载时推荐 **leastconn**，非 round-robin。

---

## 5. 写扩展：分片（第 299–302 页）

### 5.1 分区键选择

- 选核心实体主键（如 user_id）。
- ER 图分析连接度；易分片模型为多个弱连接子图。
- 避免跨分片查询；分片均匀且足够小。

### 5.2 多分区键

复杂模型可能需按多维度存储部分数据两次。

### 5.3 跨分片查询

应为例外；需并行查询 + 激进缓存。

---

## 6. Vitess（第 303 页）

YouTube 开源分片中间件；管理拓扑、路由、在线 DDL；大规模 MySQL 常用。

---

## 7. ProxySQL（第 306–309 页）

**用途**：

- 连接池、查询路由、查询缓存。
- **按用户/ schema 分片**路由到不同 hostgroup。
- 缓解**连接风暴**（thundering herd）。
- 启用 **集群模式** 同步配置。

---

## 8. 队列（第 298 页）

用外部队列（非 MySQL 作队列）处理异步任务。

---

## 9. 本章小结（第 311 页）

**要点**：先理解工作负载；读用副本+代理，写用分片；提前规划分片而非事故后补救；SLO 驱动架构决策。

**原文**：

> If you consider sharding when you have incidents where capacity issues are a major contributing cause, then you likely have considered it too late.
