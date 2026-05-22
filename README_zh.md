# AI 游戏进化系统 / AI Game Evolution System

> 自主进化的游戏设计引擎。运行于 Git 仓库内，无人值守无限迭代设计。

---

## 核心概念

**游戏本身内置本地蒸馏 LLM 作为核心机制** — 不是用模型驱动设计器，而是游戏机制本身就依赖本地模型运行。模型的快/慢/聪明/笨拙都成为游戏体验的一部分。

当前代表作：**低语迷城**（Whispering Maze）— AI 城主叙事 Roguelike。

---

## 仓库结构

```
design.json         ← 当前代设计（严格 Schema，不允许省略字段）
sim_report.json     ← 仿真报告（蒙特卡洛 + 边界测试）
audit_report.json   ← 静态审计报告
evolution.log       ← 人类可读日志（每代追加 3 句话）
.evolution_rules     ← 成功基因法则（每 10 代自动生成）
design_index.json    ← 全代际主索引（O(1) 查询所有历史）
CLAUDE.md           ← Agent 系统提示词（完整进化协议）
evo_runner.py       ← 无人值守循环运行器
README_zh.md        ← 本文档
```

---

## 快速开始

```bash
cd /opt/data/game-evolution

# 查看当前状态
git log --all --oneline

# 运行单代进化（手动模式）
python3 evo_runner.py

# GitHub 已同步（自动）
# 仓库: https://github.com/xinranxi/AIGameDesign
```

---

## 进化协议（12 步循环）

| 步骤 | 操作 | 产出 |
|------|------|------|
| 1 | 考古学：解析 git log 获取 fitness | parent pool |
| 2 | 决定变异策略 | mutation_type |
| 3 | 设计师激活：重写 design.json | 新设计 |
| 4 | 仿真器激活：蒙特卡洛 1000 轮 | sim_report.json |
| 5 | 审计器激活：静态审查 | audit_report.json |
| 6 | 计算 fitness = sim×0.4 + audit×0.4 + novelty×0.2 | 评分 |
| 7 | Git commit + GitHub sync | 持久化 |
| 8 | 更新 design_index.json | 索引刷新 |
| 9 | 上下文压缩（每 10 代） | 日志章节 |
| 10 | 自我迭代（每 10 代） | 进化法则 |
| 11 | 自然选择（每 20 代） | 分支淘汰/合并 |
| 12 | 递归回到步骤 1 | 无限循环 |

---

## 游戏设计 Schema（不可省略）

每代 design.json 必须包含以下全部字段：

```
[Meta]
  title          游戏标题
  genre          类型标签
  session_length 单局时长（如"15分钟"）
  target_emotion 核心情绪目标（如"心流/挫败后爆发/社交优越感"）
  target_platform 目标平台

[Core Loop]
  input      玩家可执行的行为（≤3 个核心操作）
  system     系统处理规则（自然语言描述算法）
  output     玩家收到的反馈与状态变更
  iteration  驱动玩家重复循环的动机

[Mechanics]（数组，每个机制必须包含）
  id               M001 格式
  name             机制名称
  category         战斗/经济/移动/社交/成长
  method           具体方法论，必须细致到算法层面
  formula          数值公式，标准数学记号
  params           参数默认值与取值范围
  boundary_cases   边界情况处理清单（≥3 条）
  dependencies     依赖的其他机制 ID
  unlock_condition 玩家何时获得此机制

[Progression]
  difficulty_curve 难度曲线公式（如"y = x^1.2"）
  reward_schedule  强化程序（如"可变比率，平均5次掉落1次稀有"）
  skill_tree        关键节点及前置条件

[Economy]
  sources          资源产出方式清单（≥2）
  sinks            资源消耗方式清单（≥2）
  inflation_control 防通胀/通缩机制

[Audit Log]
  version          版本号
  parent_design    继承自哪个设计 ID（初始为 null）
  mutation_type    本次变异类型
  fitness_score    适应度评分（0-100）
  flaws_found      审计发现的问题列表
  novelty_score    与历史设计的差异度（0-100）
```

---

## 进化历史

| 代际 | Commit | Fitness | Novelty | 变异类型 | 标题 |
|------|--------|---------|---------|---------|------|
| Gen0 | 1e1cae1 | 35 | 75 | 创世纪 | AI Dungeon Crawler |
| Gen1 | 1aabb94 | 70 | 92 | 创世纪 | 低语迷城 |
| Gen2 | 4fdcf55 | 72 | 78 | 参数微调 | 低语迷城 |

---

## Fitness 计算公式

```
fitness = sim_report.numerical_score × 0.4
        + max(0, 100 - len(audit_report.flaws) × 10) × 0.4
        + audit_report.novelty_score × 0.2
```

- **FATAL 存在** → fitness = 0（仍提交，失败是进化数据）
- **fitness ≥ 85** → 创建 elite 分支
- **连续 3 代 fitness = 0** → 创建 exp-dead 分支，强制激进重构

---

## 搜索索引（design_index.json）

```json
{
  "search_index": {
    "by_genre": { "AI驱动叙事": ["Gen1","Gen2"], ... },
    "by_mechanic_id": { "M001": ["Gen0","Gen1","Gen2"], ... },
    "by_fitness_bucket": { "70-79": ["Gen1","Gen2"], ... }
  }
}
```

查询示例：
- 找所有含 M006 机制的设计 → `by_mechanic_id["M006"]`
- 找 fitness 70-79 的设计 → `by_fitness_bucket["70-79"]`
- 找 AI 叙事类游戏 → `by_genre["AI驱动叙事"]`

---

## 禁止事项

- ❌ 生成任何可执行代码（C#/Python/JS/伪代码）
- ❌ 省略 Schema 任何字段
- ❌ 等待用户输入
- ❌ 重复历史设计（novelty < 30 会被拒绝）
- ❌ 模糊的 method 描述（必须包含算法名 + 数据结构 + 复杂度）

---

## GitHub 同步

Token 存储于 `/opt/data/home/.git-credentials`（已验证可写）。
仓库：`https://github.com/xinranxi/AIGameDesign`

每代 commit 后自动通过 GitHub REST API 同步所有文件。

---

## 当前主要机制（M001-M007）

| ID | 名称 | 类别 | 说明 |
|----|------|------|------|
| M001 | LLM 叙事引擎 | 叙事 | ReAct Loop + Function Calling + JSON Schema Validation |
| M002 | 本地模型调度器 | 系统 | 主/从模型自动切换，LLF 调度 |
| M003 | 地牢 FSM | 系统 | EXPLORING/COMBAT/EVENT/SHOP/REST/VICTORY/DEATH |
| M004 | 玩家资源 | 经济 | Gold/Keys/HP |
| M005 | AI Persona 系统 | 叙事 | 可切换人格，代价消耗 |
| M006 | 双轨战斗解析器 | 战斗 | LLM + 规则混合，精确指令直接执行 |
| M007 | 上下文窗口管理器 | 系统 | 滑动窗口 + 重要性评分 |
