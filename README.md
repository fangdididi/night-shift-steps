# night-shift-steps

**English** | [简体中文](README.zh-CN.md)

An agent skill that rewrites procedures, runbooks, setup guides and safety instructions so a tired, stressed, non-native or first-time reader can follow them literally, without misreading a single step.

## Why

Procedures are usually written by someone who already knows the job. They break when the reader does not: at night, under pressure, on a small screen, in a second language. The same mistakes show up again and again:

- two actions hidden in one step,
- a warning placed *after* the step it protects,
- a condition that arrives at the end of the sentence,
- passive sentences that hide who must act,
- words like "properly" or "as needed" that force a guess,
- no way to tell whether a step worked.

**night-shift-steps** applies a controlled-language discipline (short sentences, one action per step, active voice, one word per thing), puts safety messages in the right place and order, and adds an expected result and an exit after every risky step.

## Features

- Ten clear rules (R1–R10) with three strength levels: light, default and strict.
- A signal-word ladder (DANGER / WARNING / CAUTION / NOTICE) and a three-part safety message pattern.
- A ten-step workflow: procedure card, fact list, split, rewrite, safety placement, results and recovery, glossary lock, lint, literal walk-through, delivery.
- `scripts/stepcheck.py`: a dependency-free linter for Markdown procedures in English and Chinese, with READY / REWORK / UNSAFE verdicts and exit codes for CI.
- Glossary support to stop synonym drift ("tray" vs "caddy" vs "sled").
- Worked before/after examples in English and Chinese.

## Installation

**Claude Code**

```bash
git clone https://github.com/fangdididi/night-shift-steps ~/.claude/skills/night-shift-steps
```

**Codex / other agents that read `SKILL.md`**

Clone the repo into your agent's skills folder (for example `~/.codex/skills/night-shift-steps`), or point the agent at `SKILL.md` in your prompt.

**Cursor**

Clone into `.cursor/skills/night-shift-steps` in your project, or copy `SKILL.md` into your project rules.

The helper script needs Python 3.8 or newer and nothing else.

## Usage

Ask your agent, for example:

- "Rewrite this deploy rollback runbook so the on-call person can follow it at 3 a.m."
- "Turn these notes into steps my dad can follow to replace the router."
- "Make this lab SOP strict: one action per step and results after every step."
- "Review this procedure for late warnings and stacked steps. Don't rewrite yet."

Run the linter yourself:

```bash
python scripts/stepcheck.py lint my-runbook.md --glossary glossary.json
python scripts/stepcheck.py lint my-runbook.md --json   # machine-readable
python scripts/stepcheck.py demo                        # see it flag a bad procedure
python -m unittest discover -s tests                    # run the tests
```

### Procedure format the linter reads

```markdown
WARNING: Power off the NAS before you remove a disk. A disk removed while it runs can corrupt the second disk.
5. Push the power button for 2 seconds to power off the NAS.
Result: All the lights on the front go off after about 1 minute.
```

Numbered lines are steps. `DANGER:`, `WARNING:`, `CAUTION:`, `NOTICE:` (or `危险：`, `警告：`, `小心：`, `注意：`) lines are safety messages. `Result:` (or `结果：`) lines are expected results. Code blocks are skipped.

## Example

Linting `examples/before.md`:

```text
  L5    step 1   fix   STACKED            more than one action: one action per step (', then', verb and verb)
  L6    step 2   fix   HEDGE              remove or make exact: should
  L7    step 3   fix   CONDITION-LAST     put the condition first, then the action
  L7    step 3   hard  HAZARD-NO-WARNING  add a safety message above this step (power off)
  L10   step 5   fix   VAGUE              say the exact action or value: make sure, properly
VERDICT: UNSAFE
```

`examples/after.md` and `examples/after.zh-CN.md` pass with `VERDICT: READY`.

## File structure

```text
night-shift-steps/
├── SKILL.md              # skill instructions (English)
├── SKILL.zh-CN.md        # skill instructions (Chinese)
├── README.md
├── README.zh-CN.md
├── LICENSE
├── scripts/
│   └── stepcheck.py      # procedure linter
├── examples/
│   ├── before.md
│   ├── after.md
│   ├── after.zh-CN.md
│   └── glossary.json
└── tests/
    └── test_stepcheck.py
```

## Limits

The linter uses word lists and patterns. It will miss some problems and flag some correct sentences. The literal walk-through in the workflow is the real check. The skill writes in a controlled style; it does not certify compliance with any official standard.

## License

[MIT](LICENSE)
