#!/usr/bin/env python3
"""stepcheck.py - lint a written procedure so a tired first-time reader can follow it.

Usage:
  python scripts/stepcheck.py lint FILE [--glossary FILE.json] [--json]
  python scripts/stepcheck.py demo

Procedure format (Markdown):
  1. Numbered lines are steps ("1." or "1)").
  WARNING:/CAUTION:/DANGER:/NOTICE: lines (or 危险/警告/小心/注意/提示) are safety messages.
  Result:/You see:/结果： lines are expected results of the step above.
  Everything else is description. Fenced code blocks are skipped.

Verdict and exit code: READY (0), REWORK (1), UNSAFE (2).
Standard library only.
"""
import json
import re
import sys

STEP_RE = re.compile(r"^\s*(\d+)[.)]\s+(.*)$")
SAFETY_RE = re.compile(r"^\s*(?:\*\*)?(DANGER|WARNING|CAUTION|NOTICE|危险|警告|小心|注意|提示)(?:\*\*)?\s*[:：]\s*(.*)$", re.I)
RESULT_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?(Result|You see|Expected|结果|你会看到|预期)(?:\*\*)?\s*[:：]\s*(.*)$", re.I)
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

LIMITS = {"en": {"step": 20, "desc": 25}, "zh": {"step": 35, "desc": 45}}

IMPERATIVES = set("""add apply attach back block call change check clean clear click close compare confirm connect copy create cut delete
disable disconnect download drain drop edit empty enable enter erase export fill find fit flush format go hold install isolate
keep kill label lift list load lock log loosen lower measure mount move note open paste pause plug press pull push put raise
read reboot record reload remove rename repeat replace reset restart restore run save scan select send set start stop switch
tag tap tighten turn type unlock unmount unplug update upload verify wait wipe write""".split())

HAZARD_EN = ["delete", "drop table", "drop database", "erase", "format", "wipe", "overwrite", "truncate", "rm -rf",
             "force push", "--force", "kill", "power off", "shut down", "disconnect", "unplug", "restart", "reboot",
             "drain", "high voltage", "hot", "pressure", "blade", "factory reset", "revoke", "destroy"]
HAZARD_ZH = ["删除", "清空", "格式化", "覆盖", "强制", "断电", "关机", "重启", "拔掉", "断开", "高压", "高温", "恢复出厂", "销毁", "吊销"]

HEDGE_EN = ["should", "might", "may want to", "probably", "try to", "if needed", "as needed", "as appropriate",
            "as necessary", "if necessary", "somewhat", "basically", "just", "simply", "quickly", "etc"]
HEDGE_ZH = ["可能", "适当", "酌情", "尽量", "视情况", "大概", "差不多", "简单地", "随便", "等等"]
VAGUE_EN = ["ensure", "make sure", "handle", "manage", "deal with", "take care of", "properly", "correctly",
            "appropriate", "relevant", "as usual", "the usual way"]
VAGUE_ZH = ["确保", "处理一下", "搞定", "弄好", "正确地", "相关的", "照常", "按老办法"]
CHAIN_EN = [(r",\s*then\b", "', then'"), (r"\band then\b", "'and then'"), (r";", "semicolon"),
            (r"\bafter that\b", "'after that'"), (r"\balso\b", "'also'")]
CHAIN_ZH = ["然后", "接着", "再把", "并且", "同时", "；", "之后再"]
CONSEQ_EN = ["can", "will", "could", "causes", "cause", "result in", "lose", "lost", "damage", "injur", "or you", "drops", "stops", "breaks", "ends", "deletes", "corrupt"]
CONSEQ_ZH = ["会", "导致", "造成", "丢失", "损坏", "受伤", "否则"]
PASSIVE_RE = re.compile(r"\b(is|are|was|were|be|been|being|gets|got)\s+(?:\w+ly\s+)?(\w+(?:ed|en)|set|put|cut|run|shut)\b", re.I)
ADJ_OK = {"open", "even", "given", "often", "seven", "eleven", "golden", "hidden"}

SEVERITY = {"HAZARD-NO-WARNING": "hard", "LATE-WARNING": "hard", "WEAK-WARNING": "fix", "LONG": "fix",
            "STACKED": "fix", "HIDDEN-ACTOR": "fix", "HEDGE": "fix", "VAGUE": "fix", "CONDITION-LAST": "fix",
            "DRIFT": "fix", "NO-RESULT": "note", "LONG-DESC": "note"}


def lang_of(text):
    cjk = len(CJK_RE.findall(text))
    return "zh" if cjk >= max(4, len(text) * 0.2) else "en"


def strip_inline(text):
    text = re.sub(r"`[^`]*`", "CODE", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return text.replace("**", "").replace("__", "")


def length_of(text, lang):
    t = strip_inline(text)
    if lang == "zh":
        return len(CJK_RE.findall(t)) + len(re.findall(r"[A-Za-z0-9]+", t))
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'/-]*", t))


def sentences(text, lang):
    t = strip_inline(text)
    parts = re.split(r"(?<=[.!?])\s+|(?<=[。！？])", t)
    return [p.strip() for p in parts if p.strip()]


def has_word(text, phrase):
    return re.search(r"(?<![\w-])" + re.escape(phrase) + r"(?![\w])", text, re.I) is not None


def parse(text):
    items, in_code = [], False
    for no, raw in enumerate(text.splitlines(), 1):
        if raw.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = STEP_RE.match(raw)
        if m:
            items.append({"kind": "step", "n": int(m.group(1)), "text": m.group(2).strip(), "line": no})
            continue
        m = SAFETY_RE.match(raw)
        if m:
            items.append({"kind": "safety", "word": m.group(1).upper(), "text": m.group(2).strip(), "line": no})
            continue
        m = RESULT_RE.match(raw)
        if m:
            items.append({"kind": "result", "text": m.group(2).strip(), "line": no})
            continue
        if items and items[-1]["kind"] == "step" and raw.startswith((" ", "\t")):
            items[-1]["text"] += " " + raw.strip()
            continue
        items.append({"kind": "desc", "text": raw.strip(), "line": no})
    return items


def hazards_in(text, lang):
    low = text.lower()
    words = HAZARD_ZH if lang == "zh" else HAZARD_EN
    found = []
    for w in words:
        if lang == "zh":
            if w in text:
                found.append(w)
        elif w.startswith("-") or " " in w:
            if w in low:
                found.append(w)
        elif has_word(low, w) or re.search(r"\b" + re.escape(w) + r"(s|ed|ing)?\b", low):
            found.append(w)
    return found


def check_step(item, lang, glossary):
    issues = []
    text = item["text"]
    lim = LIMITS[lang]["step"]
    for s in sentences(text, lang):
        n = length_of(s, lang)
        if n > lim:
            issues.append(("LONG", f"{n} {'chars' if lang == 'zh' else 'words'} (limit {lim}): split it"))
    plain = strip_inline(text)
    low = plain.lower()
    if lang == "zh":
        chains = [c for c in CHAIN_ZH if c in plain]
    else:
        chains = [label for rx, label in CHAIN_EN if re.search(rx, low)]
        sents = sentences(text, lang)
        starts = [s.split()[0].lower().strip(",:") for s in sents if s.split()]
        if sum(1 for w in starts if w in IMPERATIVES) >= 2:
            chains.append("two imperative sentences")
        if re.search(r"\b(" + "|".join(IMPERATIVES) + r")\b[^,.]*\band\s+(" + "|".join(IMPERATIVES) + r")\b", low):
            chains.append("verb and verb")
    if chains:
        issues.append(("STACKED", "more than one action: one action per step (" + ", ".join(chains[:3]) + ")"))
    if lang == "zh":
        if "被" in plain:
            issues.append(("HIDDEN-ACTOR", "uses 被: name who does it"))
    else:
        for m in PASSIVE_RE.finditer(plain):
            if m.group(2).lower() not in ADJ_OK:
                issues.append(("HIDDEN-ACTOR", f"'{m.group(0)}': say who does it"))
                break
    hedges = [h for h in (HEDGE_ZH if lang == "zh" else HEDGE_EN) if (h in plain if lang == "zh" else has_word(low, h))]
    if hedges:
        issues.append(("HEDGE", "remove or make exact: " + ", ".join(hedges[:4])))
    vague = [v for v in (VAGUE_ZH if lang == "zh" else VAGUE_EN) if (v in plain if lang == "zh" else has_word(low, v))]
    if vague:
        issues.append(("VAGUE", "say the exact action or value: " + ", ".join(vague[:4])))
    if lang == "zh":
        i = plain.find("如果")
        if i > 0 and not plain.startswith(("如果", "若")):
            issues.append(("CONDITION-LAST", "put 如果… first, then the action"))
    else:
        if re.search(r"\S\s+(if|unless|when|only if)\s", low) and not re.match(r"^(if|unless|when|only if)\b", low):
            issues.append(("CONDITION-LAST", "put the condition first, then the action"))
    for preferred, banned in glossary.items():
        for b in banned:
            if (b in plain) if lang == "zh" else has_word(low, b.lower()):
                issues.append(("DRIFT", f"'{b}' -> use '{preferred}' (glossary)"))
    return issues


def check_safety(item, lang):
    low = item["text"].lower()
    words = CONSEQ_ZH if lang == "zh" else CONSEQ_EN
    if not any((w in item["text"]) if lang == "zh" else (w in low) for w in words):
        return [("WEAK-WARNING", "state what happens if the reader ignores it")]
    return []


def lint(text, glossary=None):
    glossary = glossary or {}
    lang = lang_of(text)
    items = parse(text)
    findings = []
    steps = [i for i in items if i["kind"] == "step"]
    for idx, it in enumerate(items):
        if it["kind"] == "step":
            for code, msg in check_step(it, lang, glossary):
                findings.append({"line": it["line"], "step": it["n"], "code": code, "msg": msg})
            haz = hazards_in(strip_inline(it["text"]) + " " + " ".join(re.findall(r"`([^`]*)`", it["text"])), lang)
            if haz:
                before = idx > 0 and items[idx - 1]["kind"] == "safety"
                after = idx + 1 < len(items) and items[idx + 1]["kind"] == "safety"
                if not before and after:
                    findings.append({"line": it["line"], "step": it["n"], "code": "LATE-WARNING",
                                     "msg": "move the safety message above this step (" + ", ".join(haz[:3]) + ")"})
                elif not before:
                    findings.append({"line": it["line"], "step": it["n"], "code": "HAZARD-NO-WARNING",
                                     "msg": "add a safety message above this step (" + ", ".join(haz[:3]) + ")"})
                if not (idx + 1 < len(items) and items[idx + 1]["kind"] == "result") and not after:
                    findings.append({"line": it["line"], "step": it["n"], "code": "NO-RESULT",
                                     "msg": "risky step: add what the reader sees when it worked"})
        elif it["kind"] == "safety":
            for code, msg in check_safety(it, lang):
                findings.append({"line": it["line"], "step": None, "code": code, "msg": msg})
        elif it["kind"] == "desc":
            lim = LIMITS[lang]["desc"]
            for s in sentences(it["text"], lang):
                n = length_of(s, lang)
                if n > lim:
                    findings.append({"line": it["line"], "step": None, "code": "LONG-DESC",
                                     "msg": f"{n} {'chars' if lang == 'zh' else 'words'} (limit {lim})"})
    for f in findings:
        f["severity"] = SEVERITY[f["code"]]
    if any(f["severity"] == "hard" for f in findings):
        verdict = "UNSAFE"
    elif any(f["severity"] == "fix" for f in findings):
        verdict = "REWORK"
    else:
        verdict = "READY"
    if not steps:
        verdict = "REWORK"
        findings.append({"line": 0, "step": None, "code": "NO-STEPS", "severity": "fix",
                         "msg": "no numbered steps found: write the actions as a numbered list"})
    return {"lang": lang, "steps": len(steps), "verdict": verdict, "findings": findings}


def render(report):
    out = [f"language: {report['lang']}   steps: {report['steps']}"]
    for f in sorted(report["findings"], key=lambda x: (x["line"], x["code"])):
        where = f"step {f['step']}" if f["step"] is not None else "text"
        out.append(f"  L{f['line']:<4} {where:<8} {f['severity']:<5} {f['code']:<18} {f['msg']}")
    out.append(f"VERDICT: {report['verdict']}")
    return "\n".join(out)


DEMO = """# Rotate the database password

Before you begin, you need admin access to the vault and a 15 minute maintenance window that has been approved by the on-call lead.

1. Open the vault console and find the entry called prod-db, then copy the old password somewhere safe.
2. The new password is generated by the rotate command.
3. Restart the API pods if the old connections hang.
WARNING: Restarting drops live sessions.
4. Make sure everything works properly.
"""

EXIT = {"READY": 0, "REWORK": 1, "UNSAFE": 2}


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    as_json = "--json" in argv
    if argv[1] == "demo":
        rep = lint(DEMO)
        print(DEMO)
        print(json.dumps(rep, ensure_ascii=False, indent=1) if as_json else render(rep))
        return EXIT[rep["verdict"]]
    if argv[1] == "lint" and len(argv) >= 3:
        glossary = {}
        if "--glossary" in argv:
            with open(argv[argv.index("--glossary") + 1], encoding="utf-8") as fh:
                glossary = json.load(fh).get("terms", {})
        with open(argv[2], encoding="utf-8") as fh:
            rep = lint(fh.read(), glossary)
        print(json.dumps(rep, ensure_ascii=False, indent=1) if as_json else render(rep))
        return EXIT[rep["verdict"]]
    print(__doc__)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv))
