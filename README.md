# 🎮 AI Game Evolution System / AI 游戏进化系统

<!-- language: en -->
> **Autonomous game design evolution engine.** Runs in a Git repository, self-running infinite iteration. Game's core mechanism = local distilled LLM — not using a model to drive a design tool, the game itself embeds the model as gameplay.
<!-- language: zh -->
> **自主进化的游戏设计引擎。** 运行于 Git 仓库内，无人值守无限迭代。游戏核心机制 = 本地蒸馏 LLM — 不是用模型驱动设计器，而是游戏本身就内置模型作为玩法。
<!-- language: en -->
---

## 🔗 Quick Links

| Resource | Description |
|----------|-------------|
| [design.json](./design.json) | Current generation design (Schema-compliant) |
| [sim_report.json](./sim_report.json) | Monte Carlo simulation results |
| [audit_report.json](./audit_report.json) | Static audit report |
| [evolution.log](./evolution.log) | Human-readable evolution log |
| [.evolution_rules](./.evolution_rules) | Success gene rules |
| [design_index.json](./design_index.json) | Master index (O(1) lookup) |
| [CLAUDE.md](./CLAUDE.md) | Agent system prompt (evolution protocol) |
| [evo_runner.py](./evo_runner.py) | Unattended loop runner |

---

## 📊 Evolution Status / 进化状态

| Gen | Commit | Fitness | Novelty | Mutation | Title |
|-----|--------|---------|---------|----------|-------|
| Gen0 | `1e1cae1` | 35 | 75 | 创世纪 | AI Dungeon Crawler |
| Gen1 | `1aabb94` | 70 | 92 | 创世纪 | 低语迷城 |
| Gen2 | `4fdcf55` | 72 | 78 | 参数微调 | 低语迷城 |

**GitHub**: https://github.com/xinranxi/AIGameDesign | **Local**: `/opt/data/game-evolution/`

---

## 🎯 Core Mechanics / 核心机制

| ID | Name | Category | Description |
|----|------|----------|-------------|
| M001 | LLM Narrative Engine | Social | ReAct Loop + Function Calling + JSON Schema Validation. Model's latency IS the suspense. |
| M002 | Local Model Scheduler | Growth | Primary/secondary auto-switch. LLF scheduling decides skill priority. |
| M003 | Dungeon FSM | Movement | EXPLORING → COMBAT → EVENT → SHOP → REST → VICTORY/DEATH |
| M004 | Player Resources | Economy | Gold/Keys/HP with boundary validation |
| M005 | AI Persona System | Social | Switchable personalities (wizard/bard/dwarf/shadow), Gold cost |
| M006 | Dual-Rail Combat Parser | Combat | LLM + rule hybrid. Exact commands execute directly; ambiguous → LLM裁决 |
| M007 | Context Window Manager | Growth | Sliding window + importance scoring. Flag-setting entries never GC'd. |

---

## 🔄 12-Step Evolution Protocol / 进化协议

```
Step 1: Archaeology → parse git log for fitness scores
Step 2: Mutation strategy (falling=激进重构, stable=参数微调, plateau=杂交, first=创世纪)
Step 3: Designer rewrites design.json (inherit ≥50% mechanics)
Step 4: Simulator runs Monte Carlo 1000 rounds → sim_report.json
Step 5: Auditor runs static audit → audit_report.json
Step 6: fitness = sim×0.4 + (100-flaws×10)×0.4 + novelty×0.2
Step 7: Git commit + GitHub sync (REST API PUT)
Step 8: Update design_index.json (rebuild search index)
Step 9: Context compression every 10 gens (log chapter break)
Step 10: Self-iteration every 10 gens (extract → .evolution_rules)
Step 11: Natural selection every 20 gens (branch cull/merge)
Step 12: Recurse to Step 1 → infinite loop
```

---

## 📐 Game Design Schema / 游戏设计Schema

Every `design.json` MUST contain ALL fields — no omissions allowed.

```
[Meta]
  title, genre, session_length, target_emotion, target_platform

[Core Loop]
  input (≤3 ops) | system (algorithmic) | output | iteration

[Mechanics] (array, each with)
  id(M###), name, category, method (algorithm-level), formula (std math),
  params, boundary_cases (≥3), dependencies, unlock_condition

[Progression]
  difficulty_curve | reward_schedule | skill_tree

[Economy]
  sources (≥2) | sinks (≥2) | inflation_control

[Audit Log]
  version, parent_design, mutation_type, fitness_score, flaws_found, novelty_score
```

---

## 🚫 Prohibited / 禁止事项

- ❌ Generate executable code (C#/Python/JS)
- ❌ Omit any Schema field
- ❌ Wait for user input
- ❌ Repeat designs (novelty < 30 rejected)
- ❌ Vague method descriptions (must include: algorithm + data structure + complexity)

---

## 🔢 Fitness Formula / Fitness 计算

```
fitness = sim_report.numerical_score × 0.4
        + max(0, 100 - len(audit_report.flaws) × 10) × 0.4
        + audit_report.novelty_score × 0.2
```

- FATAL exists → fitness = 0 (still committed — failure is evolutionary data)
- fitness ≥ 85 → create elite branch
- 3 consecutive fitness = 0 → exp-dead branch + force radical restructure

---

## 🔍 Search Index / 搜索索引

```json
{
  "by_genre":       { "AI驱动叙事": ["Gen1","Gen2"], "Roguelike": ["Gen0","Gen1","Gen2"] },
  "by_mechanic_id": { "M001": ["Gen0","Gen1","Gen2"], "M006": ["Gen2"] },
  "by_fitness_bucket": { "70-79": ["Gen1","Gen2"], "30-39": ["Gen0"] }
}
```

Query: `by_mechanic_id["M006"]` → `["Gen2"]` | `by_fitness_bucket["70-79"]` → `["Gen1","Gen2"]`

---

## 📌 Current Flagship: 低语迷城 (Whispering Maze)

- **Genre**: AI-Narrative Roguelike, Text Adventure
- **Core**: Local distilled LLM as Dungeon Master — model's hallucinations become content, inference latency creates suspense
- **Loop**: Player free-text → LLM generates narrative + JSON delta → state update → boundary detection → repeat
- **Key insight**: Different models = completely different games. A "dumb" model produces hilariously confused NPC logic. A "smart" model creates deep narrative. Both are valid gameplay.
