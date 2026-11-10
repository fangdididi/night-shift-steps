# night-shift-steps（夜班步骤）

[English](README.md) | **简体中文**

一个智能体技能：把操作流程、运维手册、安装指南和安全说明改写成疲惫、紧张、母语不同或第一次操作的人也能照字面执行、一步都不会读错的步骤。

## 为什么需要它

流程通常是由已经会做的人写的。换一个不熟悉的人，在夜里、在压力下、在小屏幕上、用第二语言去读，就容易出错。同样的毛病反复出现：

- 一个步骤里藏着两个动作；
- 警告放在它要保护的步骤**后面**；
- 条件放在句子末尾；
- 被动句让人不知道该谁来做；
- "正确地""视情况"这类词逼人去猜；
- 做完一步之后，没法判断有没有做对。

**night-shift-steps** 采用受控语言的写作纪律（短句、一步一个动作、主动语态、一样东西只用一个词），把安全信息放在正确的位置、按正确的顺序写，并在每个有风险的步骤后加上预期结果和出口。

## 功能

- 十条清晰规则（R1–R10），分轻量、默认、严格三档强度。
- 信号词阶梯（危险 / 警告 / 小心 / 注意）和"三段式"安全信息写法。
- 十步工作流：流程卡、事实清单、拆分、改写、放置安全信息、结果与恢复、锁定术语、检查、照字面走查、交付。
- `scripts/stepcheck.py`：无依赖的 Markdown 流程检查器，支持中英文，给出 READY / REWORK / UNSAFE 结论和可用于 CI 的退出码。
- 支持术语表，防止同义词漂移（"托架""硬盘架""支架"混用）。
- 中英文的改写前后完整示例。

## 安装

**Claude Code**

```bash
git clone https://github.com/fangdididi/night-shift-steps ~/.claude/skills/night-shift-steps
```

**Codex / 其他读取 `SKILL.md` 的智能体**

把仓库克隆到智能体的技能目录（例如 `~/.codex/skills/night-shift-steps`），或者在提示词里让智能体读取 `SKILL.md`。中文用户可以让智能体读取 `SKILL.zh-CN.md`。

**Cursor**

克隆到项目的 `.cursor/skills/night-shift-steps`，或把 `SKILL.md` 的内容放进项目规则。

辅助脚本只需要 Python 3.8 或更高版本，不需要其他依赖。

## 使用方法

可以这样对智能体说：

- "把这份发布回滚手册改写一下，让值班的人凌晨三点也能照着做。"
- "把这些笔记整理成我爸能照着换路由器的步骤。"
- "把这份实验室 SOP 改成严格模式：一步一个动作，每步后面写结果。"
- "检查这份流程有没有警告放错位置、一步多动作的问题，先别改写。"

自己运行检查器：

```bash
python scripts/stepcheck.py lint my-runbook.md --glossary glossary.json
python scripts/stepcheck.py lint my-runbook.md --json   # 输出 JSON
python scripts/stepcheck.py demo                        # 看它如何标出一份糟糕的流程
python -m unittest discover -s tests                    # 运行测试
```

### 检查器能识别的格式

```markdown
警告：拔硬盘之前必须先关机。开着机拔硬盘会导致另一块硬盘的数据损坏。
5. 按住电源键 2 秒，关闭 NAS。
结果：大约 1 分钟后，前面板的灯全部熄灭。
```

编号行是步骤。以 `危险：`、`警告：`、`小心：`、`注意：`（或 `DANGER:`、`WARNING:`、`CAUTION:`、`NOTICE:`）开头的行是安全信息。以 `结果：`（或 `Result:`）开头的行是预期结果。代码块会被跳过。

## 示例

检查 `examples/before.md` 的输出：

```text
  L5    step 1   fix   STACKED            more than one action: one action per step (', then', verb and verb)
  L6    step 2   fix   HEDGE              remove or make exact: should
  L7    step 3   fix   CONDITION-LAST     put the condition first, then the action
  L7    step 3   hard  HAZARD-NO-WARNING  add a safety message above this step (power off)
  L10   step 5   fix   VAGUE              say the exact action or value: make sure, properly
VERDICT: UNSAFE
```

`examples/after.md` 和 `examples/after.zh-CN.md` 的检查结果都是 `VERDICT: READY`。

## 文件结构

```text
night-shift-steps/
├── SKILL.md              # 技能说明（英文）
├── SKILL.zh-CN.md        # 技能说明（中文）
├── README.md
├── README.zh-CN.md
├── LICENSE
├── scripts/
│   └── stepcheck.py      # 流程检查器
├── examples/
│   ├── before.md
│   ├── after.md
│   ├── after.zh-CN.md
│   └── glossary.json
└── tests/
    └── test_stepcheck.py
```

## 局限

检查器依靠词表和模式匹配，会漏掉一些问题，也会误报一些正确的句子。工作流里的"照字面走查"才是真正的检查。本技能以受控风格写作，不证明符合任何官方标准。

## 许可证

[MIT](LICENSE)
