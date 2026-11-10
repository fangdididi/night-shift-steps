---
name: night-shift-steps
description: Rewrite an operating procedure, runbook, setup guide or safety instruction in a controlled-language style so a tired, stressed, non-native or first-time reader can follow it without misreading. Use it when someone asks to make steps clearer, write a runbook or SOP, prepare instructions for someone else to carry out, translate-proof a procedure, or "write it like a maintenance manual".
---

# Night-shift steps

## What this is

Most procedures are written by the person who already knows the job. They read fine at a desk. They fail at 3 a.m., in a noisy room, on a phone, in a second language, or when the reader is scared of breaking something. The failures are predictable: two actions hidden in one step, a warning that sits *after* the step it guards, a condition that arrives at the end of the sentence, a passive sentence that hides who must act, and words like "properly" that ask the reader to guess.

This skill turns such text into steps that a person can follow literally. It borrows the discipline of controlled languages used in aircraft and industrial maintenance (short sentences, one action per sentence, active voice, one word for one thing), the safety-message order used on equipment labels (signal word, hazard, consequence, avoidance), and the habit of writing an expected result after each risky step so the reader knows when to stop.

It is not a "make it sound human" pass. The goal is a procedure that cannot be misread, even if it sounds a little plain.

## When to use it

- Runbooks, incident playbooks, on-call checklists, deploy and rollback steps.
- Setup or repair guides for hardware, home devices, lab equipment, or office IT.
- Standard operating procedures (SOPs) and handover notes for another person or another shift.
- Instructions that will be machine-translated or read by non-native speakers.
- Any text where one misread step can lose data, money, or cause injury.

Do not use it for essays, marketing copy, or conceptual explanations. Those need a different voice.

## The rules (default level)

| # | Rule | Limit or test |
|---|---|---|
| R1 | One action per step | No ", then", "and then", ";" or two verbs joined by "and" inside a step |
| R2 | Short instruction sentences | 20 words in English, about 35 characters in Chinese |
| R3 | Short descriptive sentences | 25 words in English, about 45 characters in Chinese |
| R4 | Imperative, active voice | Start with the verb. Name the actor if it is not the reader |
| R5 | Condition first | "If the light is red, stop." never "Stop if the light is red." |
| R6 | One word, one meaning | Lock terms in a glossary. Never swap synonyms for variety |
| R7 | Exact values | Numbers with units, labels exactly as shown on screen or device |
| R8 | Safety message before the step | Signal word, hazard, consequence, what to do |
| R9 | Expected result after risky steps | "Result: ..." and what to do if the result is different |
| R10 | No guessing words | Remove "properly", "as needed", "make sure", "should", "just" |

**Strict level** (for safety-critical or regulated text): apply every rule without exceptions, allow no hedges at all, and put a Result line after every step. **Light level** (for an internal note that is already decent): apply R1, R5, R8 and R9 only.

### Signal words

Use the lowest word that is still true. Do not inflate.

- **DANGER**: will cause death or serious injury if ignored.
- **WARNING**: can cause death, serious injury, or loss of important data or money.
- **CAUTION**: can cause minor injury or damage that you can fix.
- **NOTICE**: no injury risk; property, data or time risk only.

Every safety message has three parts: what the hazard is, what happens if the reader ignores it, and what to do. "Be careful" is not a safety message.

## How to work

1. **Fill the procedure card.** Before you edit, write down: the goal state ("Disk 2 rebuilding"), who will follow it (role, language, conditions such as gloves, noise, phone screen, night), what they have (access, tools, time), the hazards, and the stop conditions. Ask the user for anything you cannot infer. A missing stop condition is the most common gap.
2. **List the facts you must keep.** Every number, unit, label, command, order constraint, warning and condition. The rewrite must contain all of them and add none. If you think a value is wrong, flag it; do not fix it silently.
3. **Split into actions.** One verb that the reader does = one step. Navigation counts ("Go to Storage" and "Select Disk 2" are two steps). Move background into a short "Before you start" paragraph.
4. **Rewrite each step.** Verb first, condition first, exact labels in bold or `code`, units always. Replace every passive that hides an actor: "The key is generated" becomes "The tool generates the key" or, better, the step the reader takes to generate it.
5. **Place the safety messages.** For each step that deletes, overwrites, powers off, restarts, disconnects, heats, cuts or pressurizes, put the message directly above the step. Pick the signal word from the ladder above.
6. **Add results and exits.** After each risky or state-changing step, write what the reader sees when it worked. If the result can differ, give one line: "If you see X, stop and go to Recovery A." Write the recovery sections.
7. **Lock the glossary.** Pick one term per thing (for example "tray", not "caddy" or "sled"). Save it as `glossary.json` if the procedure will be maintained.
8. **Lint.** Run `python scripts/stepcheck.py lint procedure.md --glossary glossary.json`. Fix every UNSAFE and REWORK finding, or explain why one is a false positive.
9. **Do a literal walk-through.** Read only the numbered steps, as someone who does exactly what each sentence says and nothing more. Where would they stop, guess, or do something harmful? Fix those places.
10. **Return** the rewritten procedure, then a short change list (rule numbers), the list of facts you could not verify, and open questions.

## The helper script

`scripts/stepcheck.py` is a standard-library Python linter for Markdown procedures, English or Chinese.

| Code | Severity | Meaning |
|---|---|---|
| HAZARD-NO-WARNING | hard | A risky step has no safety message above it |
| LATE-WARNING | hard | The safety message sits after the step it guards |
| WEAK-WARNING | fix | The message does not say what happens |
| LONG | fix | Instruction sentence over the limit |
| STACKED | fix | More than one action in a step |
| HIDDEN-ACTOR | fix | Passive voice or 被 hides who acts |
| HEDGE / VAGUE | fix | Guessing words |
| CONDITION-LAST | fix | The condition comes after the action |
| DRIFT | fix | A banned synonym from the glossary |
| NO-RESULT, LONG-DESC | note | Advice only |

Verdict: **READY** (exit 0), **REWORK** (exit 1), **UNSAFE** (exit 2). The script uses word lists and patterns, so it misses things and sometimes flags a correct sentence. It never replaces step 9.

## Example

Before:

> 3. Power off the NAS if it is still running.
> 4. Pull out the tray for Disk 2 and put the new disk in it.
> CAUTION: The old disk can be hot.

After:

> WARNING: Power off the NAS before you remove a disk. A disk removed while it runs can corrupt the second disk.
> 5. Push the power button for 2 seconds to power off the NAS.
> Result: All the lights on the front go off after about 1 minute.
> CAUTION: The old disk can be hot after use. Hold it by the tray, or you can burn your fingers.
> 6. Pull out the tray for Disk 2.
> 7. Put the new disk in the tray.

Changes: R1 (split step 4), R5 (condition removed by making power-off its own step), R8 (warning moved up and given a consequence), R9 (result added). Full files are in `examples/`.

## Tips

- If the source text is wrong, the clearest rewrite is still wrong. Flag doubtful values in the change list.
- Keep commands, paths and on-screen labels byte-for-byte. Clear prose around a mistyped command is worse than the original.
- A step that needs a long explanation is usually two steps plus a note before them.
- Number steps continuously. Do not restart numbering inside one procedure; use separate sections for recovery.
- Read the Chinese and English versions side by side when you produce both: each step should map one-to-one.
- Never claim the output complies with any official controlled-language standard. Say "written in a controlled style".
