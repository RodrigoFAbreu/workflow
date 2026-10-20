# W14: Workflow 2.18.0 — harness-neutral command bodies (Revision 5)

- **Work item:** `harness-neutral-commands` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner placed it as row 17 of
  `docs/ROADMAP.md` (workflow#59, raised by the Workflow Controller lane on 2026-10-19).
- **Roadmap step:** W14, row 17 of "What's next" (marked Current by this plan).
- **Branch:** `milestone/harness-neutral-commands`
- **Base commit:** `ad6f863` (main after #63: the release source is Workflow 2.17.0;
  this repository's own installation is also 2.17.0, automatic gates, default `2.2`, no
  `GATE_POLICY.json`)
- **Plan revision:** 5. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.18.0, a minor release (`feat:`), so that the Workflow Controller's harness
adapter (its step A5: other harnesses, Codex first, as workers) can read the one shared
`.claude/commands/<name>.md` set, map its frontmatter to that harness's settings,
substitute the arguments and send the body as the prompt, with no per-harness copy.

Why `feat:` and not `fix:`/`docs:`: the release adds a **documented command-file
contract** (a new shipped document, a test that pins it and a rule that every command
taking arguments names `$ARGUMENTS`) that a separate product depends on. That is a new
capability, not a correction. No script, state field, ledger, phase, commit shape or
protocol field changes; the downgrade posture (section 3, D-Release) says what an older
release reads.

Four deliverables, as the request lists them:

1. **Neutral naming.** The shipped command bodies stop calling the model "Claude"; they
   say "the agent", defined once.
2. **The user-only guard restated, never weakened.** The literal-confirmation check
   (mechanism 2) is the control each user-only command carries under every harness; the
   `disable-model-invocation: true` flag is an additional layer where the harness enforces
   it. The Claude Code `SlashCommand`/`Skill` history moves out of the bodies.
3. **The frontmatter contract**, in one shipped place, with a test that every key in use is
   in it.
4. **`$ARGUMENTS`** confirmed and documented as the argument placeholder, and present in
   every command that takes arguments.

Plus the release bookkeeping: re-recorded golden hashes, `WORKFLOW_RELEASE` and its two
pinned assertions, manifest digests and measured suite counts, release history, the
downgrade posture, the `manager` block.

### The premise needs two corrections (read this first)

The request counts "18 of the 22 commands" saying "Claude must never…". Reading the files:

- **Only seven command files name the model "Claude" in prose**: `approve-review.md`,
  `adopt-gate-policy.md`, `request-plan-amendment.md`, `resume-implementation.md`
  (guard sentences and, for four user-only commands, the `description:`),
  `review-plan.md`, `review-implementation.md` and `review-functional.md` ("any capable
  Claude model"). Every other occurrence, in sixteen files, is the **`Claude-Session:`
  trailer name** (a Git trailer key that the commit-message rules and `workflow_state.py`
  name literally). It is an identifier, not the model, and it **stays**. (Sixteen
  trailer files plus `review-plan.md` and `review-functional.md` make the request's 18.)
- **Two commands that take arguments never name `$ARGUMENTS`**: `apply-pr-review.md` (hint
  `<work-item-id>`, "the work item id is required") and `prepare-review.md` (hint
  `<base-sha> <stage> [work-item-id]`) rely on Claude Code appending the arguments to a
  body with no placeholder. Another adapter that substitutes only the token would send
  them no argument at all. This is the real `$ARGUMENTS` gap (D-Args).

### Hard requirements (invariants)

- **No guard weakens.** Every confirmation check, every refusal and every numbered step of
  every command stays. A sentence is reworded only to replace the model's name, to restate
  which control holds where (D-Guard) or to move Claude Code history (D-Guard). The tests
  that pin the guards pass, with only the pinned model name updated where a pin quotes it.
- **A rename, not a rewrite.** The CP2 hunk table (section 5) lists every body hunk; the
  review reads it against `git diff`.
- **No behaviour change.** No script, schema, state, ledger, phase, trailer or protocol
  value changes. `Claude-Session:` and `Co-Authored-By:` remain exactly as they are.
- **The files stay in `.claude/commands/`**; no per-harness copy; no Controller or Manager
  change.

### Non-goals

Moving the command files; per-harness copies; any Controller or Manager change; any
behaviour change of a command; the managed `CLAUDE.md` block text (`templates/CLAUDE.md`
is Claude Code's own file and the Manager's to install); the historical design records
(`WORKFLOW_V2_PLAN.md`, `WORKFLOW_V2_AUDIT.md` and the earlier plans, which describe what
was true when written); and #60, #56, #30 part 2, #31, #39, #45, #50, #52, #55.

### What is a gate and what is an aid

- **Gates (a failure stops work):** the neutrality tests (D-Term), the user-only body
  tests (D-Guard), the frontmatter-key coverage test (D-Contract), the `$ARGUMENTS` test
  (D-Args), the golden hashes, every existing suite, the release tests and the
  documentation check.
- **Aids (never a stop):** the CP2 hunk table and the word-level diff the reviewer may run
  against the base commit to confirm "rename, not rewrite". It is a reading aid; the
  gates above are what fail.

## 2. What exists today (facts this plan relies on)

- Frontmatter keys in use across the 22 command files (counted): `description` (22),
  `state_writer` (22), `argument-hint` (21), `review-subject` (21), and
  `disable-model-invocation` (6, always `true`). Nothing else.
- `state_writer` is a conformance declaration: `workflow_state.discover_state_writers`
  fails closed on a missing or contradictory one for every file under `.claude/commands/`
  and `scripts/`. `review-subject` (`bundle`, `verdict` or `none`) is required of the
  14 commands in `workflow_state.REVIEW_SUBJECT_ROSTER`; seven more declare it too, and
  one (`recover-implementation-provenance.md`) does not.
  `disable-model-invocation: true` is compared with the protocol's `user_only` action
  flag by `workflow_protocol_test.py` (`test_user_only_matches_the_command_files_flag`).
- `$ARGUMENTS` appears in 18 command files. `apply-pr-review.md` and `prepare-review.md`
  take arguments without it; `adopt-gate-policy.md` (`argument-hint: ""`) and
  `bootstrap-workflow-v2.md` (no hint, a hard-coded work item) take none.
- The six user-only commands each describe two mechanisms: (1) the flag, (2) the literal
  confirmation text the user's own current-turn message must supply. `approve-review.md`
  lines 41 to 66 call (1) "the primary, harness-enforced control" and carry a "Verified
  coverage of mechanism (1)" paragraph about Claude Code's `SlashCommand` and `Skill`
  tools and changelog; the other five refer to it.
- Pins that quote the model's name: `workflow_integration_test.py` (two, "any capable
  Claude model", lines about 463 and 659), `workflow_state_test.py` (one, "Claude must
  never invoke this command on the user's behalf", about 19835) and
  `workflow_protocol_test.py` (one, "Claude must stop and wait for a human/external input
  at exactly six points", about 3939). The golden hashes are
  `_GOLDEN_COMMAND_FILE_SHA256` in `workflow_integration_test.py`.
- Prose "Claude" also occurs in `MILESTONE_WORKFLOW.md` (14 lines), `REVIEW_PROTOCOL.md`
  (4 prose lines, plus the `Claude-Session:` trailer name) and the operator reference
  (3 lines): the documents every command points to.

## 3. Design decisions

### D-Term: "the agent", defined once, and what counts as harness-specific

The term is **the agent**: whatever carries out the steps of a command body, a model under
whichever harness. It is never the user. "The user" stays "the user".

The rename rules (the exact rules the neutrality test pins):

- "Claude" naming the model becomes "the agent" (sentence-initial "The agent"); "any
  capable Claude model" becomes "any capable model"; "Claude's skill list" becomes "the
  agent's command list".
- **What stays, because it is an identifier and not the model:** the `Claude-Session:`
  trailer key; the `.claude/` directory in a path; a model-id example such as
  `anthropic/claude-opus-5-5` (lower case, a value format, not the model's name).
- **What counts as harness-specific** and leaves the bodies: the name of a harness product
  ("Claude Code"), a harness tool name (`SlashCommand`, `Skill` as a tool) and the history
  of how one harness enforces a flag. They live in one place: the Claude Code note of
  `COMMAND_FILES.md` (D-Contract).
- The definition is written **once**, in `COMMAND_FILES.md` ("Terms"). Bodies are sent to a
  worker one at a time, so they use the word in its plain sense and do not each repeat a
  definition; the contract document is what an adapter author reads.

The gate test forbids, in every command body (frontmatter included) and in the in-scope
documents other than `COMMAND_FILES.md`, the pattern `Claude` not followed by `-Session`,
and the words `SlashCommand` and `Claude Code`. Lower-case `claude` is not matched.

### D-Scope: which documents are in scope (kept small)

In scope, because every command points to them and a worker reads them as part of the
prompt: `MILESTONE_WORKFLOW.md` (its "Claude stops/must stop here" lines, 14),
`REVIEW_PROTOCOL.md` (4 prose lines) and the operator reference (3 lines, plus its
"User-only commands" bullet restated like the bodies). All three are shipped under
`payload/docs/ai-workflow/`. Out of scope: everything named in the non-goals, and
`README.md`'s "open Claude Code" (it is the user's own start instruction for Claude Code).
A one-sentence rename per line; no paragraph is rewritten.

### D-Guard: restating the user-only control

For each of the six user-only commands the paragraph that today reads "(1) the flag,
primary, harness-enforced; (2) the literal confirmation" becomes, in substance:

> The control this command carries itself, under every harness, is the
> literal-confirmation check (mechanism 2, below). `disable-model-invocation: true` is an
> additional layer where the harness enforces it; it does not replace the check. The agent
> must never invoke this command on the user's behalf, including as a step of another
> command's execution, whatever the flag says.

Every command keeps its exact mechanism (2) paragraph (the confirmation text, the exact
id and stage word, "never fabricate, infer or carry over", "ask for it and stop"), its
validator name, and its refusals. The lead sentence "This command is user-only by
construction" stays in every body (`payload/scripts/workflow_gate_policy_test.py` pins it
for `accept-milestone.md`, so that test needs no edit); the restatement follows it. The
pinned phrase **"the control this command carries
itself, under every harness"** appears in all six, so the test can require it. The numbering
(1), (2) is kept where a command uses it.

**What moves:** `approve-review.md`'s "Verified coverage of mechanism (1)" paragraph (the
`SlashCommand` and `Skill` tool history, the changelog, the inconclusive same-session test
and the open fresh-session test) goes, with its facts kept and its tense kept ("until that
result is recorded"), to the **Claude Code note** in `COMMAND_FILES.md`. The body keeps one
sentence: how the flag is enforced differs by harness, and the harness notes in
`COMMAND_FILES.md` record what is known per harness. (The bodies' pointer wording is "the
harness notes in `COMMAND_FILES.md`": it names no harness product, so D-Term's gate and
this hunk agree; the section in the document itself keeps its title, "The Claude Code
note", because the document is outside the gate.) `accept-milestone.md`'s pointer "see
`approve-review.md` for this installation's verified/unverified coverage" is re-pointed to
the same wording.

This can only strengthen the statement of the control: the check that was already
"actually load-bearing" (the removed paragraph's own words) is now stated first and as the
one that always holds.

### D-Contract: the frontmatter contract, in one shipped place

**Where (open decision OD-1, recommended):** a new shipped document
`payload/docs/ai-workflow/COMMAND_FILES.md`, installed as `docs/ai-workflow/COMMAND_FILES.md`.
An adapter author reads a short stable document, not a 1,300-line operator reference; the
operator reference gets a pointer and its three renames. The cost is one manifest record.

The document has these sections, in this order: Purpose and who reads it; Terms (the agent,
the user, the harness, the adapter); The file format (frontmatter between two `---` lines
of single-line `key: value` pairs, then the body); **The keys** (table); **`$ARGUMENTS`**;
**The user-only commands**; **The Claude Code note**; **Neutrality rules** (D-Term).

**The keys**: one table row per key, with its class, who reads it and what an adapter does.
Three classes:

| Key | Class | What an adapter does |
|---|---|---|
| `disable-model-invocation` | **Honour** | `true` (six commands): never launch the command for a model on the model's own initiative or as a step of another command; launch it only on the user's own request. An adapter that cannot tell refuses the command. The command's own confirmation check stays on regardless. |
| `state_writer` | **Honour** | A command file declares `true` or `false` only (`"publisher"` is a script-side value and never appears in a command file). `true`: the command changes `WORKFLOW_STATE.json`, always through `workflow_state.state_transaction`. Launch it in the checkout whose state it changes, with permission to run the Workflow scripts and Git there; never give the worker another way to write the state file. `false`: it never writes that file. The Workflow's conformance check requires the key on every command. |
| `review-subject` | **Carry** | `bundle`, `verdict` or `none`: what the command reviews or consumes. Read by the Workflow's own conformance check (which commands call `assert_bundle_not_rejected`). An adapter passes the file through unchanged and needs no action. |
| `description` | **Hint** | One line, shown when listing commands. No semantics. |
| `argument-hint` | **Hint** | The argument shape, for display and prompts. The grammar the body enforces is in the body. |

Rules for adapters (also in the document): an unknown key is ignored and never fails the
launch; the Workflow adds a key only with a row here (the test); a key's class never
changes silently.

**Tests (gates):** every frontmatter key in `payload/.claude/commands/*.md` has a row, and
every row's key is in use (so the document cannot go stale in either direction); each row's
class is one of the three words.

### D-Args: `$ARGUMENTS`

Confirmed: `$ARGUMENTS` is the Workflow's argument placeholder. The contract, stated in the
document:

- **Where:** the literal token `$ARGUMENTS`, in the body only (never in the frontmatter).
- **What an adapter substitutes:** the argument string exactly as the user typed it after
  the command name, verbatim and unparsed, at **every** occurrence of the token. The body
  does the parsing (a work-item id, `plan|implementation`, a base commit).
- **Empty:** no argument given is substituted as the empty string. The body's own argument
  grammar decides what that means. A body that requires an argument (a stage, a base
  commit, an id named "from `$ARGUMENTS` only") refuses without it, and a body whose
  argument is optional applies its own stated default: for most, the active work item;
  `milestone-plan.md` identifies the milestone from the active-milestone, roadmap and
  backlog documents; `prepare-review.md` uses the flat review path with no work item and
  never resolves one from `active_work_item_id`. The contract document states this general
  rule only and does not promise "the active work item" as a universal default; it does
  not claim that every body spells out its empty case (several state only what an omitted
  id means), and CP2 adds no such sentence.
- **Rule for bodies (gate):** every command whose `argument-hint` is non-empty names
  `$ARGUMENTS` in its body, so no adapter has to append arguments after the body as Claude
  Code does for a body with no placeholder. A command with no hint takes no arguments.

CP2 adds the missing sentence to the two bodies that lack it (`apply-pr-review.md`,
`prepare-review.md`): "The argument string is `$ARGUMENTS`: …" followed by the command's
own existing statement of the arguments and of the required id. Their behaviour is the same
under Claude Code (it substitutes the token rather than appending the string).

### D-Release: 2.18.0

A minor, `feat:`. Command text and documentation only; no script, state or protocol change;
`WORKFLOW_RELEASE` becomes 2.18.0 and the protocol stays at its current version.

**Downgrade posture** (for the `manager` block and the release history): an older release
reads everything this release writes, because nothing it reads changes. Moving back from
2.18.0 to 2.17.0 restores the older wording of the command bodies and the three documents
and removes `COMMAND_FILES.md`; the six user-only guards still enforce the same confirmation
check on both sides (2.17.0's `accept-milestone.md` and `retire-legacy-work-item.md` lack
the "must never invoke" sentence 2.18.0 adds, so the wording is not identical), and
nothing in the state file, ledgers or commit shapes differs. **Adapters:** a
non-Claude-Code adapter following `COMMAND_FILES.md` needs 2.18.0 or later (2.17.0's
`apply-pr-review.md` and `prepare-review.md` lack `$ARGUMENTS`, so an adapter that
substitutes only the token sends them no arguments, and `COMMAND_FILES.md` does not exist
there); moving back to 2.17.0 is safe for Claude Code only. `min_manager_version` stays 1.13.0, `new_work_only` stays
empty and `gate_default_change` stays empty, unless CP3 finds the Manager's contract
requires otherwise.

## 4. Open decisions (for the plan reviewer and the user)

| Id | Decision | Recommendation |
|---|---|---|
| OD-1 | Where the contract lives: a new shipped `COMMAND_FILES.md`, or a section of the operator reference | New document (D-Contract): short, stable name for the Controller to cite; one manifest record. |
| OD-2 | The term: "the agent" or "the model" | "The agent": it also covers a harness that wraps a model in tools, and it reads well in "the agent must never invoke". |
| OD-3 | Whether to add `$ARGUMENTS` to `apply-pr-review.md` and `prepare-review.md` | Yes (D-Args): one sentence each, and a gate so no adapter must append. The alternative, documenting an append rule, makes every adapter reproduce Claude Code's fallback. |
| OD-4 | Whether `state_writer` is an "Honour" key | Yes, as worded in D-Contract: it states what the launch environment must allow. `review-subject` is "Carry". |
| OD-5 | Whether the documents in scope include `MILESTONE_WORKFLOW.md` and `REVIEW_PROTOCOL.md` (about 17 one-line renames) | Yes; the worker is told to read them, and the gate test makes the neutrality claim checkable. |

None of these finalizes an "Open decision" row of `docs/TECHNICAL_DECISIONS.md` (the file
does not exist in this repository's release source).

## 5. Checkpoints

Three checkpoints. CP1 and CP2 depend only on each other in one direction (CP2 points to
CP1's document); CP3 is the release. Each checkpoint runs the nine payload suites from a
staged fixture of its own commit (`release.py stage-conformance` run on a scratch release, prepared as
the next paragraph says, for CP1 and CP2), the `tools/release` tests in the zlib-ng
virtual environment, and the `tools/docs` tests.

**Scratch staging for CP1 and CP2 (EPR-001).** `release.py stage-conformance` calls
`verify_release` first (`tools/release/package.py:508`), which refuses a file the manifest does not
list (`package.py:281`, "untracked file in release"); CP1 creates `COMMAND_FILES.md`, whose
record is the committed manifest's CP3 deliverable. So the scratch preparation, done in a
copy of the release source outside the repository and never in the repository's manifest or
installation, does three things: it copies the checkpoint's tree; it adds the
`distribution` record for `COMMAND_FILES.md` (the rule and rationale CP3 will commit) and
updates `counts`; and it refreshes the `sha256` and `size` of every touched record. It
stages from that adjusted scratch release. Manifest verification is not weakened: the
scratch manifest is verified in full, and CP3 re-does the same edits in the committed
`manifest.json`, which then stages unmodified.

**Release tests for CP1 and CP2 (EPR-002).** `tools/release/release_test.py` does not read
the working tree: `test_round_trip` stages the repository's own `HEAD` (`REPO_ROOT` is
`HERE.parent.parent`, `release_test.py:31`; `package.stage(REPO_ROOT, "HEAD", ...)`,
`release_test.py:393`) and builds it, which runs the same full manifest verification
(`package.py:420`). So the staged-fixture preparation above does not reach it, and a
`HEAD` holding `COMMAND_FILES.md` without its record fails with "untracked file in
release". The unchanged suite therefore runs in a disposable Git copy, never in the
repository:

1. `git clone <repository> <scratch>/repo` (a clone keeps the full history and every
   `v*` tag the reproduction tests stage by `refs/tags/`); check out the checkpoint's commit;
2. in the clone, apply the same manifest preparation as above (the `COMMAND_FILES.md`
   record, `counts`, refreshed `sha256` and `size` of every touched record) and
   `git commit` it, so the clone's `HEAD` is the checkpoint's tree plus that manifest;
3. run `python -m unittest tools/release/release_test.py` (the file under test is the
   clone's own copy, so its `REPO_ROOT` is the clone) in the zlib-ng virtual environment.

No assertion is skipped or loosened and `release_test.py` is not edited for this; the
repository's `manifest.json` stays as it is until CP3, whose own `tools/release` run is
against the repository's committed `HEAD` directly.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The command-file contract and the neutral documents | - | 3 | 1 |
| CP2 | Neutral command bodies, the restated guards, `$ARGUMENTS` and the golden hashes | CP1 | 4 | 1 |
| CP3 | Release 2.18.0 | CP1, CP2 | 2 | 1 |

<!-- CP1 -->
### CP1 — The command-file contract and the neutral documents

**Files:** `payload/docs/ai-workflow/COMMAND_FILES.md`,
`payload/docs/ai-workflow/MILESTONE_WORKFLOW.md`,
`payload/docs/ai-workflow/REVIEW_PROTOCOL.md`,
`payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`, `docs/README.md`,
`payload/scripts/workflow_integration_test.py`, `payload/scripts/workflow_protocol_test.py`.

- **`COMMAND_FILES.md`** as D-Contract, D-Args, D-Term and D-Guard specify. The Claude Code
  note carries `approve-review.md`'s facts: the bundled frontmatter reference documents the
  flag as blocking the `SlashCommand` tool without naming the `Skill` path; the changelog
  confirms skill-aware handling; a same-session test was inconclusive because the skill
  table is fixed at session start; a decisive test needs a flagged command invoked through
  `Skill` from a fresh session; until recorded, the confirmation check is the control that
  holds. The document has the standard page header of the shipped documents.
- **`MILESTONE_WORKFLOW.md`, `REVIEW_PROTOCOL.md`, the operator reference:** the D-Scope
  renames, one line each. The operator reference's "User-only commands" bullet states the
  restated control (the check holds under every harness; the flag is an additional layer)
  and a new pointer line names `COMMAND_FILES.md`. `REVIEW_PROTOCOL.md`'s
  `Claude-Session:` trailer line is untouched.
- **`docs/README.md`:** one row, "run the commands from another harness" →
  `COMMAND_FILES.md`.
- **Tests** (new class in `workflow_integration_test.py`, reading the staged fixture):
  1. every key used in the command files has a row in the document's key table and every
     row's key is in use; each class is `Honour`, `Carry` or `Hint`;
  2. the document defines the term ("the agent") and names the placeholder `$ARGUMENTS`,
     what an adapter substitutes and the empty case as D-Args now words it (the body's grammar decides; no universal "active work item" default);
  3. the document lists the six user-only commands and each of them carries the flag (the
     document's list equals the set the frontmatter flags);
  4. the neutrality pattern (D-Term) matches nothing in `MILESTONE_WORKFLOW.md`,
     `REVIEW_PROTOCOL.md` and the operator reference.
  `workflow_protocol_test.py`'s pin of the six-point sentence is updated to the renamed
  sentence ("The agent must stop and wait …"); nothing else in it changes.

**Verification:** the nine suites pass in a fixture staged from the adjusted scratch release
of section 5 (it includes `COMMAND_FILES.md`) of this checkpoint (the
neutrality test of the command bodies is CP2's, so CP1 does not run it); the documentation
check is clean; the `tools/release` tests pass, unchanged, in the zlib-ng environment from
the disposable Git copy of section 5 whose `HEAD` carries the manifest preparation (EPR-002).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Neutral command bodies, the restated guards, `$ARGUMENTS` and the golden hashes

**Files:** `payload/.claude/commands/approve-review.md`,
`payload/.claude/commands/accept-milestone.md`,
`payload/.claude/commands/adopt-gate-policy.md`,
`payload/.claude/commands/request-plan-amendment.md`,
`payload/.claude/commands/resume-implementation.md`,
`payload/.claude/commands/retire-legacy-work-item.md`,
`payload/.claude/commands/review-plan.md`,
`payload/.claude/commands/review-implementation.md`,
`payload/.claude/commands/review-functional.md`,
`payload/.claude/commands/apply-pr-review.md`,
`payload/.claude/commands/prepare-review.md`,
`payload/scripts/workflow_integration_test.py`, `payload/scripts/workflow_state_test.py`.

The hunk table (the whole of the change to the bodies; anything else is out of the plan):

| File | Hunks |
|---|---|
| `approve-review.md` | `description` ("never invoked by the agent autonomously"); the user-only paragraph restated (D-Guard); the "Verified coverage" paragraph replaced by its one-sentence pointer; mechanism (2) paragraph unchanged |
| `adopt-gate-policy.md` | `description`; the user-only paragraph restated; "User-only guard" paragraph unchanged (this body numbers neither mechanism) |
| `request-plan-amendment.md` | `description`; the user-only paragraph restated (the `USER_OVERRIDE` sentences stay); mechanism (2) and the `reason` requirement unchanged |
| `resume-implementation.md` | `description`; "(1) … (2) …" restated; "The agent must never invoke this command on the user's behalf, including as a step of another command's execution" |
| `accept-milestone.md` | "(1) … primary, harness-enforced — see `approve-review.md` …" restated and re-pointed to `COMMAND_FILES.md`; the "agent must never invoke" sentence is **added** (the body has none today) |
| `retire-legacy-work-item.md` | "(1) … (2) …" restated; the "agent must never invoke" sentence is **added** (the body has none today); no model name to change |
| `review-plan.md`, `review-implementation.md` (2), `review-functional.md` | "any capable Claude model" → "any capable model" |
| `apply-pr-review.md`, `prepare-review.md` | one `$ARGUMENTS` sentence each (D-Args) |

- **Golden hashes:** `_GOLDEN_COMMAND_FILE_SHA256` in `workflow_integration_test.py`
  covers six of CP2's eleven files today (`approve-review.md`, `accept-milestone.md`,
  `review-plan.md`, `review-implementation.md`, `review-functional.md`,
  `apply-pr-review.md`). CP2 **re-records those six rows** by computing each file's
  SHA-256 (the procedure the earlier releases used) and **adds five new rows** for the
  files that have none -- `adopt-gate-policy.md`, `request-plan-amendment.md`,
  `resume-implementation.md`, `retire-legacy-work-item.md` and `prepare-review.md` -- so
  that all eleven changed bodies, in particular all six user-only ones, are gated against
  an unplanned edit. A dated comment line names this milestone; the pin is not loosened.
- **Pinned model-name text updated, same meaning:** the two "any capable Claude model"
  pins in `workflow_integration_test.py` and the "Claude must never invoke this command on
  the user's behalf" pin in `workflow_state_test.py`.
- **New tests** (`workflow_integration_test.py`):
  1. **neutrality (gate):** the D-Term pattern matches nothing in any command file,
     frontmatter included, and the sixteen files that name `Claude-Session:` still do;
  2. **`$ARGUMENTS` (gate):** every command whose `argument-hint` is non-empty contains the
     token in its body, and no frontmatter contains it; the hint is parsed as a YAML-style
     scalar (quoted or bare), `""` (as in `adopt-gate-policy.md`) counting as empty;
  3. **each user-only body still carries its literal-confirmation step (gate):** a table of
     the six commands, each with the needles of its own check taken from the 2.17.0 text
     (the validator name, the exact id and stage word, "refuse to write anything unless",
     the never-fabricate sentence, "ask for it and stop" or its command's equivalent), matched
     after whitespace normalisation (`" ".join(text.split())`, as `workflow_state_test.py`
     already does) because the bodies wrap lines, the pinned phrase "the control this command carries itself, under every harness", the
     sentence "The agent must never invoke", and the flag in the frontmatter; the six
     named commands equal the commands whose frontmatter carries the flag;
  4. the body of `approve-review.md` no longer contains the history (`SlashCommand`,
     "changelog") and `COMMAND_FILES.md` does.

**Verification:** the nine suites pass in a fixture staged from the adjusted scratch release
of section 5 (record for `COMMAND_FILES.md` added, counts and digests refreshed); the existing guard tests (`TestResumeImplementationCommandFile`,
the retire and adopt command-file tests, the accept-milestone pins) pass unchanged except
for the pinned name; `git diff ad6f863 -- payload/.claude/commands` read against the hunk
table; the word-level diff shows only listed hunks; the `tools/release` tests pass,
unchanged, from the disposable Git copy of section 5 (EPR-002).
<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Release 2.18.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`,
`docs/RELEASING.md`, `tools/release/release_test.py`.

- `manifest.json` 2.18.0: a `distribution` record for `COMMAND_FILES.md` (rule, rationale),
  `counts` updated, and every touched record's `sha256` and `size` refreshed (the eleven
  command files, the three documents, `workflow_integration_test.py`,
  `workflow_state_test.py`, `workflow_protocol_test.py`, `workflow_protocol.py`,
  `ORCHESTRATION_PROTOCOL.md`). The `manager` block: `min_manager_version` 1.13.0, the
  posture text of D-Release, `new_work_only` and `gate_default_change` empty, and
  `conformance.suites` computed by `release.py manager-block --release-dir <scratch>
  --write` from a staging of CP3's own content (no hand-written count).
- `WORKFLOW_RELEASE` in `workflow_protocol.py` becomes 2.18.0, with its two pinned
  assertions in `workflow_protocol_test.py` and the matching `ORCHESTRATION_PROTOCOL.md`
  edits (the tested-releases note and the envelope example); the protocol version stays.
- `docs/release-history.md`: the 2.18.0 row (what it adds, the downgrade posture, what stays
  open: #30 part 2, #31, #39, #45, #50, #52). `docs/RELEASING.md`: only a count it states
  that this release moves, if any. `tools/release/release_test.py`: the new record and
  counts, the posture text.
- `docs/ROADMAP.md` is marked Current now (done with the plan) and Done at acceptance, not
  in this checkpoint.

**Verification:** the nine suites pass in a stock `release.py stage-conformance` fixture;
`release.py build` of the commit succeeds; `check-manager-block` is clean; the update
fixture passes; `tools/docs/check_docs.py` is clean; `workflow-manager verify .` is clean;
the tools tests pass in the zlib-ng virtual environment.
<!-- /CP3 -->

## 6. Tests and verification summary

Each checkpoint's tests are listed in its section. The new tests are in the integration
suite, so only its measured count moves; CP3 records the measured counts of all nine
suites. Nothing is tested only by reading prose, except the "rename, not rewrite" claim,
which the hunk table and the word-level diff support and the gates (neutrality, guard
steps, golden hashes) bound.

## 7. Risks

- **A guard silently weakened by a rewording.** Mitigation: the hunk table limits the
  change; the new user-only test pins each command's own confirmation needles from the
  2.17.0 text; the existing guard tests stay; the golden hashes make any unplanned edit
  fail.
- **Over-renaming an identifier.** `Claude-Session:` is a trailer name the commit rules
  and `workflow_state.py` use; the neutrality pattern excludes it by construction, and
  the neutrality test also asserts that the sixteen files that name it still do.
- **Contract drift.** A new key added without a row, or a stale row: the key-coverage test
  fails in both directions.
- **An adapter that appends arguments anyway.** Harmless: the token is substituted and an
  appended copy is only redundant.
- **This repository runs 2.17.0.** The new wording is exercised only in tests and
  fixtures here.

## 8. Requirements

| Id | Requirement | Checkpoints |
|---|---|---|
| R1 | The shipped command bodies and the in-scope documents name the model "the agent", defined once, with a gate test and the identifiers that stay listed | CP1, CP2 |
| R2 | Each user-only command states the literal-confirmation check as the control it carries under every harness and the flag as an additional layer; the Claude Code history moves to the contract document; no guard weakens, and a test pins each body's confirmation step | CP1, CP2 |
| R3 | One shipped document lists every frontmatter key with its class and what an adapter does, with a test that keys in use and documented keys agree | CP1 |
| R4 | `$ARGUMENTS` is documented (where, substitution, empty case) and present in every command that takes arguments, with a gate test | CP1, CP2 |
| R5 | Golden hashes re-recorded; release 2.18.0 bookkeeping (release constant and assertions, manifest digests, sizes and measured counts, release history, downgrade posture, `manager` block) | CP2, CP3 |

## 9. Artifact classification

`docs/ai-workflow/registry/harness-neutral-commands-artifacts.json` is declared as the
previous release-source items declared theirs (the generated template does not classify
`payload/`, `manifest.json` or the user documents). At the plan stage the plan
(`docs/ai-workflow/HARNESS_NEUTRAL_COMMANDS_PLAN.md`), the registry and the mapping are
protected; `payload/` (including the shipped `COMMAND_FILES.md`), `fixtures/`,
`templates/`, `tools/`, `manifest.json`, the user documents (`docs/README.md`,
`docs/release-history.md`, `docs/RELEASING.md`), `docs/ROADMAP.md`, `docs/milestones/` and
`.github/` are excluded. At the implementation stage `payload/`, `fixtures/`, `templates/`,
`tools/`, `manifest.json`, those user documents and the declaration itself are protected;
the plan, `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md`, `docs/milestones/` and
`docs/ai-workflow/` are excluded. Every path section 5 names is classified at both stages,
including this plan file; the declaration check runs at publication and refuses otherwise.

## 10. Revision history

| Rev | Change |
|---|---|
| 1 | First plan for row 17. |
| 2 | Local review round 1 (REVISE). IMP-1: D-Args' empty-case rule restated as what is true (empty string; the body's grammar decides), no new body sentence. IMP-2: CP2 re-records six golden rows and adds five for the files that had none. OPT-1 to OPT-4 accepted (lead sentence kept; "adds" and the unnumbered case in the hunk table; whitespace normalisation and `""` parsing; `state_writer` is `true`/`false` in command files). |
| 3 | Local review round 2 (REVISE). IMP-3: D-Args' empty-case sentence no longer claims an optional id falls back to the active work item (`milestone-plan.md` and `prepare-review.md` do not); it states the general rule and names those two defaults, and CP1 test 2 pins that wording. OPT-5: the bodies' pointer wording is "the harness notes in `COMMAND_FILES.md`", so D-Term's gate and the D-Guard hunk agree. OPT-6: the D-Release downgrade posture drops "identical in substance", names the two 2.17.0 gaps and says a non-Claude-Code adapter needs 2.18.0 or later and moving back is safe for Claude Code only. |
| 4 | Manual external review round 1 (REVISE). EPR-001: section 5 now specifies the scratch staging for CP1 and CP2 (adds `COMMAND_FILES.md`'s distribution record and adjusts counts, hashes and sizes in a scratch release, then stages from it; the committed manifest stays CP3's deliverable), and both checkpoints' verification lines point to it. |
| 5 | Manual external review round 2 (REVISE). EPR-002: section 5 now specifies how the unchanged `tools/release` suite runs for CP1 and CP2: `release_test.py` stages the repository's `HEAD` (`release_test.py:393`), so it runs in a disposable Git clone (history and tags kept) whose `HEAD` commits the same manifest preparation; no assertion is skipped, `release_test.py` is unedited, and the repository's manifest stays CP3's deliverable. Both checkpoints' verification lines name it. |
