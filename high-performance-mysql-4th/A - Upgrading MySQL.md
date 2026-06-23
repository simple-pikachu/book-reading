# Appendix A: Upgrading MySQL

> 来源：《High Performance MySQL》第 4 版  
> 页码范围：第 343–348 页（书中印刷页码）

---

## 1. 导言：稳定性与功能的权衡（第 343 页）

**要点**：

- 升级是在**稳定性**与**新特性**之间的 trade-off（Stewart Smith 的「dot-20 规则」：软件往往要到 x.y.20 才够成熟——非铁律，但说明新版本与稳定性的张力）。
- MySQL 用户基数大，他人已替你踩坑；版本过新可能引入回归，过旧则错过修复与优化。

**原文**：

> Upgrading is a trade-off between stability and features. You should consider this when choosing to upgrade.

> If you upgrade to too new of a version, you may unknowingly introduce a bug or regression into your environment. If you stay too far behind, you may be experiencing nonobvious bugs or won't be able to take advantage of a feature that has been optimized for performance.

---

## 2. 为何要升级？（第 343–344 页）

| 原因 | 说明 |
|------|------|
| **安全漏洞** | 虽越来越少见，仍可能发生；安全团队可能要求升级 |
| **已知 Bug** | 生产异常时查当前版本及之后 release notes，可能已是已修复 bug |
| **新特性** | Oracle 常在**小版本**（如 8.0.21→8.0.22）加入影响负载的特性；升级前必读 release notes |
| **EOL** | 应保持在 Oracle 支持期内，至少仍有安全修复 |

**原文**：

> MySQL doesn't always adhere to a strict major/minor/point release strategy with respect to how features are added. Many people may expect that a point release would only contain bug fixes, and a minor version change would include minor features. Oracle often releases new features in minor point releases that may have an impact on your workload.

---

## 3. 升级生命周期（第 344 页）

**典型步骤**：

1. 阅读 **release notes**（含小版本）
2. 阅读官方 **upgrade notes**
3. **测试**新版本
4. **升级**生产服务器

**风险**：

- 须有回滚计划（查询变慢、崩溃 bug 等）
- **大/小版本降级**（如 8.0→5.7）：只能恢复升级前备份
- **MySQL 8.0 起**：点版本也不可降级（如 8.0.25 不能回到 8.0.24），须导出再导入

**原文**：

> For all major and minor version changes, the only way to downgrade is to restore a backup from before you upgraded. This makes upgrading especially risky, so be sure you have a plan.

> It's important to note that since MySQL 8.0, you cannot downgrade point release versions either.

---

## 4. 测试升级（第 345–347 页）

**要点**：降级风险高，应尽可能组合多种测试方法。

### 4.1 开发环境测试

- 适合发现**语法**等明显问题
- 开发库数据量小，无法反映生产规模下的性能回归（10 行 vs 1000 万行）

### 4.2 生产镜像（Production Mirror）

- 复制生产数据，停复制，升级副本
- 用 `tcpdump` + `pt-query-digest` 将 SQL 流量同时打到生产与升级副本
- 应用仍只写生产；副本提供性能指标与语法错误信号（Etsy Code As Craft 博文思路）

### 4.3 只读副本

- 在可读副本上先升级，观察**读流量**；有问题则 depool
- **无法**测试写路径与写性能

### 4.4 工具：pt-upgrade

- 对两目标执行相同查询集，对比行数、数据、错误
- 输入可为 slow log、general log、binlog
- 流程：收集关键查询 → 两台相同环境 → 仅一台升级 → 运行 `pt-upgrade`

**原文**：

> Given the risk we cited before about downgrading, you should employ as many of these methods as are feasible prior to upgrading.

---

## 5. 大规模升级（第 346–347 页）

**原地升级简述**：停 MySQL → 替换二进制 → 启动 → 运行 `mysql_upgrade`（8.0 前）。

**Ansible  playbook 骨架**（数百台服务器宜自动化）：

| 步骤 | 动作 |
|------|------|
| 1. Verify target | 防误升生产；查是否可写（`read_only` 副本较安全）；确认未已升级 |
| 2. Set downtime | 抑制监控告警 |
| 3. Preconditions | 关闭依赖服务（CM、监控等）避免 MySQL 离线时报错 |
| 4. Remove old packages | 彻底卸载旧包，避免 5.7/8.0 冲突 |
| 5. Install new packages | 安装新版本 |
| 6. Start mysqld | 启动服务 |
| 7. mysql_upgrade | **仅 <8.0**；若 `super_read_only=ON` 须临时关闭 |
| 8. Restart mysqld | 干净重启确认配置与升级文件 |
| 9. Verify | `SELECT 1` |
| 10. Restore services | 恢复 CM/监控 |
| 11. Clear downtime | 结束维护，观察失败节点 |

**原文**：

> MySQL 8.0 moved the mysql_upgrade process into the startup of the server itself. There is no need to run this as an additional step.

> With this process, you're able to point your runbook at any server and only upgrade the nonupgraded nodes that are not taking traffic.

---

## 6. 附录小结（第 348 页）

**要点**：

- 升级动机：修复在遇 bug、利用新特性（如 8.0 **Instant ADD COLUMN** 省去全表重建）
- 大版本升级须充分测试：延迟偏差、新错误
- 有信心后**缓慢 rollout**，备好回滚
- 大机群**重度自动化**，降低误操作与登录错误主机风险

**原文**：

> MySQL 8.0 introduced a feature for InnoDB where columns can be added instantly—no need to rebuild the entire table. This type of feature enhancement can be a huge time saver for companies that perform a high volume of ALTER TABLE .. ADD COLUMN statements.

> Lastly, if you have a large fleet of servers to manage, consider investing heavily in automating the process as best as possible.

---

## 升级决策与测试矩阵

```
为何升级？ ──► 读 release notes + upgrade notes
                    │
                    ▼
测试（尽量多项并用）：
  · 开发环境（语法）
  · 生产镜像 + 流量复制（读写指标）
  · 只读副本（读路径）
  · pt-upgrade（查询对比）
                    │
                    ▼
生产：Ansible 等自动化 │ 仅非写节点 │ 不可降级须备备份
```
