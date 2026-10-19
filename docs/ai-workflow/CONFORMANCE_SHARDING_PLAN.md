# W12: Workflow 2.16.0 — acceptance-matrix sharding and the managed conformance width (Revision 5)

- **Work item:** `conformance-sharding` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner's item C
  (decided 2026-10-13), row 15 of `docs/ROADMAP.md`. Its starting point is the Codex CI
  plan of 2026-10-13, whose A+B part shipped as workflow#27.
- **Roadmap step:** W12, row 15 of "What's next". This plan makes it the current item.
- **Branch:** `milestone/conformance-sharding`
- **Base commit:** `971ea16` (main after #54: the release source is Workflow 2.15.0;
  this repository's own installation is also 2.15.0, automatic gates, default `2.2`,
  no `GATE_POLICY.json`)
- **Plan revision:** 5, a plan amendment after the first measurement came back
  inconclusive (section 3.4). Every checkpoint section carries its
  `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

The managed `workflow-conformance` job sets every managed repository's pull-request
finish time: 14-20 minutes per run here (runs 39164199663, 39167895389, 39165789747,
39169402360). The acceptance-matrix suite (415 tests, a disposable repository per test)
is the long pole: 1,068 s in the managed parallel job against 609 s serially, because
four processes contend for the runner's CPUs.

This milestone **measures first and builds on the measurement**:

1. Build, as a candidate in the managed template, the scheduling the owner asked for:
   the acceptance suite split into shards of whole test classes, run as processes inside
   the one job, under one global worker limit.
2. Measure on GitHub runners, nothing merged, the managed step's wall time unsharded and
   sharded (widths 3 and 4), comparing variants only on the same CPU type (section 3).
   Record the numbers before anything else builds on them.
3. Ship exactly what the numbers support, as Workflow 2.16.0 (a template change,
   `feat:` for the minor bump), and apply the same scheduling to this repository's own
   release-source conformance where it helps, without weakening a check.

### What the repository already has (do not redo it)

- **PR cancellation is already in the managed template** (since 2.10.0, W5): the
  concurrency group is `workflow-conformance-` plus the ref for a pull request and the
  run identity otherwise, and `cancel-in-progress` is true for a pull request only, so a
  main push is never cancelled. `ConformanceTemplate.test_concurrency_expressions_are_exact`
  and `test_group_semantics` pin it. The request said to add it if missing; it is not
  missing. This milestone keeps it, re-pins it and changes nothing there.
- **Width is `min(4, nproc)`** in the managed template and in this repository's CI
  (`release-source-conformance`). The runner is a public-repository `ubuntu-latest`
  (four vCPUs); the measurement records `nproc` to confirm it.
- The `Workflow CI` consolidation (`checks`, `release-source-conformance`, `aggregate`)
  shipped as workflow#27. Out of scope: workflow#30 part 2, #31, #39, #45, #52, #48, #50,
  Controller work and Manager changes.

### Outcomes the measurement can lead to (decided now, section 3 gives the rule)

| Outcome | When | What ships |
|---|---|---|
| O1 | sharding passes the rule | the sharded template with the measured width and shard count; the same scheduling in this repository's CI; release 2.16.0 |
| O3 | sharding is rejected | the template bytes return to 2.15.0 exactly; the evidence file is the only deliverable; **no release is built** (no manifest change, no 2.16.0, the payload and its `WORKFLOW_RELEASE` stay at 2.15.0), row 15 is marked Done as "measured, no change" |
| none | the measurement is **inconclusive** (section 3.3: not enough same-CPU evidence after the bounded top-up rounds) | no outcome is selected; CP2 is not started (section 5, CP2); the orchestrator raises it to the owner (a re-measure or a re-plan). Incompatible evidence never selects O1 or O3 |

Revision 5 measures no width-2 variant, so the former outcome O2 (a width change without
sharding) can no longer be selected and is removed; the ids O1 and O3 keep their meaning.

**Lifecycle path of each outcome** (the state machine has no "not applicable"
checkpoint, so the path is named here and CP2 states it again, outcome-neutrally):

| Outcome | Path from CP2 to the end of the milestone |
|---|---|
| O1 | CP2, CP3 and CP4 are implemented in order; no amendment. |
| O3 | At the end of CP2 (`COMPLETE`, template restored, evidence recorded) the orchestrator runs `/request-plan-amendment conformance-sharding` from `IMPLEMENTING`. The amended plan drops CP3 and CP4 from the registry, and its requirements mapping no longer lists R4 and R5 (and states that R2 is not delivered because the measurement rejected sharding); the amended plan is reviewed (local, then manual external) and approved with `/approve-review plan`, whose reconciliation removes CP3 and CP4 from the live map and leaves CP2, whose section is unchanged, `COMPLETE`. The milestone then proceeds to `SELF_REVIEWING_IMPLEMENTATION`, technical approval and `/accept-milestone` with CP1 and CP2 as its checkpoints. |

CP2's section is written so that it needs no change under any of these paths; an
amendment under O3 therefore never re-opens it.

Cancellation never counts as "what helped": it is already shipped, so an outcome that
changes nothing but it ships nothing (O3).

## 2. Exact rules (read before the checkpoints)

### 2.1 What a shard is

- The unit is the **acceptance module** `workflow_acceptance_matrix_test.py`. A **shard**
  is a set of whole `unittest.TestCase` classes defined in that module. A class is never
  split. A class with no tests of its own or inherited (the shared bases `MatrixCase`,
  `_PlanReviewBindingCase`, `_PlanApprovalClosureCase`) has zero tests and is not a unit.
- Inherited tests belong to the subclass that inherits them: `loadTestsFromTestCase`
  returns them, so each `*Product` class runs its inherited tests in its own shard. Two
  forms of class-level skip exist and are treated differently. A skip decorator on the
  class (`@unittest.skip`) makes `unittest` record a `skip` under the id of each of the
  class's tests: that is a recorded outcome of those ids and passes the gate. A
  `unittest.SkipTest` raised in `setUpClass` makes `unittest` record one skip under the
  id `setUpClass (module.Class)` and run none of the class's tests: the expected ids are
  then missing and an id outside the list is present, so gate 3 fails. That is a
  declared limit (section 2.4), not a recorded outcome.
- **Subtests** belong to their parent test. A failing subtest makes the parent test id
  fail; a passing subtest is not enumerated (a declared limit, section 2.4).
- **Module hooks:** `plan` uses `loadTestsFromModule`, which honours `load_tests`;
  `run` uses `loadTestsFromTestCase`, which does not, and a `setUpModule` would run once
  per shard. `plan` therefore **refuses** (exit 1, naming the hook) when the module
  defines `load_tests`, `setUpModule` or `tearDownModule`, so a future payload cannot
  silently diverge between the baseline and the shards. The real module defines none
  today.
- **Partition:** the planning process loads the module once, groups
  `loadTestsFromModule` tests by class, and assigns classes to `N` shards by
  longest-processing-time on test count (largest class first to the lightest shard, ties
  by class name). The partition is deterministic. With fewer classes than `N`, there are
  fewer shards. `N` is a constant of the template.
- **Expected ids:** the `test.id()` of every test `loadTestsFromModule` returns in the
  planning process. This list is the coverage baseline.

### 2.2 What is a gate and what is an aid

Gates (any one failing fails the job):

1. **Plan:** the planning step exits 0 and writes a plan. A failed plan is a failed
   job, never a silent fall-back to the unsharded suite.
2. **Per shard:** its process exits 0 **and** it wrote a result file that parses, names
   its shard and its class list, and says it completed.
3. **Coverage:** the multiset of test ids recorded across every shard's result file equals
   the expected ids: every expected id exactly once, no id twice, no id outside the
   list (a `setUpClass` failure, and a `SkipTest` raised in `setUpClass`, are reported by
   `unittest` under an id outside the list and so fail here as well as, for a failure,
   in the shard). A missing, unparsable or incomplete shard
   file is named and fails.
4. **Outcome:** each recorded outcome is `ok`, `skip` or `xfail`. A failure, an error, a
   failed subtest, an unexpected success or an id that started and never finished is a
   failure.
5. **Other suites:** each of the eight other suites passes exactly as today (exit 0 and a
   result file).
6. **One width:** the shards and the eight other suites are one queue under one limit,
   `min(W, nproc)` processes at a time; nothing nested.

Aids (they inform, they never decide): the longest-first order and the test-count
balance of the partition; per-unit seconds; the step summary rows; the grouped logs; the
shard logs in a diagnostic artifact. A badly balanced partition costs time and never
correctness.

A failure message names the **shard** (`acceptance 3/4`), its classes, and the
**original test ids** that failed or are missing, read from the result files, and the
log of the shard is printed unfolded.

### 2.3 What counts as a pass of the whole job

The job passes when gates 1 to 6 hold. The nine suite rows of the step summary remain
(the acceptance row aggregates its shards: `passed (N shards, T tests)` with the longest
shard's seconds); the shard rows follow it.

### 2.4 Declared limits (stated so nobody reads more into the gate than it gives)

- A `unittest.SkipTest` raised in `setUpClass` **fails** the gate (section 2.1): sharding
  does not map it to skips of the class's tests. The real module has no `setUpClass`
  today; a future payload that skips a whole class must use the class decorator.
- Ids are test-method granularity. A test that stops running some of its subtests while
  passing is not detected; sharding cannot make that better or worse.
- The baseline is the module itself. A test deleted from the module disappears from the
  baseline and from the shards alike. The independent count is the release's
  `manager.conformance.suites` (415), which `check-manager-block` compares to a fresh
  count at release time; the consumer's job does not enforce it.
- Test ordering between classes changes (shards run in separate processes). The suite
  passes only if its classes are order-independent, which they already must be (each
  class builds its own disposable repositories); the measurement runs would show a
  dependency as a failure.
- The partition balances by test count, not time. If the evidence shows the largest class
  bounds the wall time, that is recorded and no finer split is attempted (a class is
  never split).
- The 60 s-scale runner variance of GitHub, and its mix of CPU models, are handled by
  comparing timings only between runs of the same CPU model, three repetitions per
  variant, bounded top-up rounds and a margin in the rule, not by a statistical test.

## 3. The measurement, its validity and the decision rule (fixed before the revision 5 measurement)

### 3.1 What is measured

A throwaway-branch workflow that runs the **managed step as the template ships it**,
over this repository's own tree (its installed scripts are the payload consumers get),
once per variant and repetition, each on its own `ubuntu-latest` runner. The sharded
variants' step text is the template's run block with only its two constants replaced
(`width_cap` `W` and shard count `N`; CP1 makes each constant appear on exactly one line
so the replacement is exact and tested). The **control variant** v1 is not the candidate
template: it is the 2.15.0 step text itself (`git show 971ea16:templates/.github/workflows/workflow-conformance.yml`)
with exactly one line changed so that V3 can read its peak (`echo "start $1"` becomes
`echo "start $1 running K"`, `K` the units running including this one). Variants:

| Variant | W | N | Meaning |
|---|---:|---:|---|
| v1 | 4 | 0 | the control: today's 2.15.0 step, unsharded (equal to it but for the `start` line) |
| v3 | 4 | 4 | candidate: sharded, 4 shards, up to 4 processes |
| v4 | 4 | 8 | candidate: sharded, 8 shards, up to 4 processes |
| v5 | 3 | 4 | candidate: sharded, 4 shards, up to 3 processes |

The width-2 variants of revision 4 (v2 unsharded, v6 sharded) are dropped: the first
measurement (section 3.4) showed no gain at width 2. The remaining ids are kept so that
both measurements read alike.

A **round** runs each variant it enables three times (repetitions a, b and c), each job on
its own runner, `max-parallel` 6, `fail-fast` false. The first round enables the four
variants (12 jobs); a top-up round (section 3.3) enables v1 and the candidates still
undecided, with the content otherwise byte-identical. Each job records `nproc`, the CPU
model and the image version, the step's start and end, each unit's seconds (the step
prints `done <unit> exit S in Ns`), the peak number of units running at once (the step
prints `start <unit> running K` as it starts each unit, and the largest `K` is the peak)
and, for the candidates, the coverage line (`expected T, recorded T`).

The orchestrator pushes the prepared content to the throwaway branch
`measure/conformance-sharding`, whose workflow triggers on pushes to `measure/**` only
(so it never runs on `main` or a pull request), reads the results with `gh run view`,
and deletes the branch when the measurement ends. Workers never push. CP1 prepared the
kit; CP2 adapts it to this revision before anything is measured, then records the numbers.

### 3.2 The rule

Definitions, applied to the runs of every round so far:

- A run's **runner type** is its recorded (`nproc`, CPU model string, image version)
  triple. Timings are compared only between runs of the same runner type, never across
  CPU models, `nproc` or images (`D-Same-CPU`).
- A run is **valid** when it passes V1 and V3 (section 3.3) and its step succeeded with,
  for a candidate, full coverage (gate 3). Every valid run counts; no run is chosen or
  dropped by its timing.
- The **cell** `(v, c)` is the set of valid runs of variant `v` on runner type `c`;
  `M(v, c)` is the median of their step walls.
- The **same-CPU pairs** of candidate `s` on `c` number `P(s, c) = min(n(v1, c), n(s, c))`,
  `n` the number of valid runs in the cell.
- `c` **qualifies** for `s` when `P(s, c) >= 2` and both cells `(v1, c)` and `(s, c)`
  pass V4.
- On a qualifying `c`, `s` **shows the gain** when `M(s, c) <= 0.85 * M(v1, c)` (the 15%
  threshold, applied per runner type) **and** the slowest valid run of `s` on `c` is faster
  than the fastest valid run of v1 on `c` (so every same-CPU pair favours `s`, whichever
  way the runs are paired). Otherwise `s` **fails** on `c`.
- After each round every candidate not yet decided gets a **status**: **passes** when at
  least two runner types qualify for it and it shows the gain on every one of them;
  **rejected** when it fails on at least one qualifying runner type, or a run of it failed
  a gate (rule 4); **undecided** otherwise (fewer than two qualifying runner types, each
  showing the gain). A `passes` or `rejected` status is final once reached; only undecided
  candidates are evaluated again, on all their valid runs so far.

The rules:

1. **Sharding is adopted (O1)** when, after the last round, at least one candidate passes.
2. **Width and shard count:** each passing candidate's score `G(s)` is the largest
   `M(s, c) / M(v1, c)` over its qualifying runner types, from the round in which it
   passed (its worst same-CPU ratio). Among the passing candidates, take the smallest `W`
   (then the smallest `N`) whose `G` is within 5% of the best: `G(s) <= 1.05 * min G`.
   An undecided or rejected candidate is never chosen. Fewer processes leave the runner
   less contended and are the safer default.
3. **Sharding is rejected (O3)** when every candidate is rejected. The width stays 4 and
   the template returns to 2.15.0.
4. Candidate runs also must cover every id (gate 3). A candidate with a run that failed a
   gate is rejected and listed. A v1 run whose suites failed makes the measurement
   inconclusive (the control is broken; section 3.3).

The comparison is the step's wall time, because that is what sets the pull-request
finish. Runner-minutes equal wall time in one job and are not separately weighed.

### 3.3 Validity, top-up rounds and the inconclusive result (checked before any outcome is selected)

These checks are evaluated by the measurement kit's validator from the recorded job
facts, before the rule of section 3.2 is read, and they are fixed now:

| Id | Requirement | A run or cell that fails it |
|---|---|---|
| V1 | `nproc` is at least 4. | the run is invalid |
| V2 | Revision 5 replaces revision 4's requirement that more than half of all jobs share one (`nproc`, CPU model, image) triple with the per-runner-type comparison of section 3.2: a run is compared only with runs of its own runner type, and no run is invalid for its runner type. | not applicable |
| V3 | The recorded peak of units running at once equals `min(W, nproc)` of the variant (every variant queues at least that many units: nine, or the shards plus eight), so the intended width was actually exercised. | the run is invalid |
| V4 | The valid runs of a cell (two or more) differ by at most 20% of their median (largest minus smallest). | the cell is noisy: its runner type does not qualify for that variant, and a noisy v1 cell disqualifies the runner type for every candidate; its runs are kept and listed |

**Invalid runs are preserved.** The evidence file lists every invalid run with its run id,
job, the facts that failed and the check, and keeps its timings marked `invalid, not
used`. An invalid run never enters a median.

**Top-up rounds (the replacements).** Hosted runners cannot be asked for a CPU model, so a
runner type with too few same-CPU pairs is filled by running more, never by choosing
runs. When, after a round, any candidate is undecided and no v1 run has failed its suites,
the orchestrator runs a top-up round: a new push to the throwaway branch that enables v1
and every undecided candidate, three repetitions each (the kit takes the list of variants;
the content is otherwise byte-identical). Invalid runs are not replaced one by one; the
top-up rounds cover them. At most **three** top-up rounds are run, so four rounds and at
most 12 runs of each variant in all. The measurement ends after the first round in which
no candidate is undecided, or after the third top-up round.

**The decision is reached** after the last round, in this order:

1. a v1 run failed its suites: **inconclusive**;
2. at least one candidate passes: **O1**, by rules 1 and 2 (an undecided candidate is listed
   and never chosen);
3. every candidate is rejected: **O3**;
4. otherwise (no candidate passes and at least one is still undecided after the third
   top-up round): **inconclusive**.

**Inconclusive is not an outcome.** No outcome (O1 or O3) is selected from it, CP2 is not
started (section 5, CP2), and the orchestrator raises it to the owner (a re-measure or a
re-plan). The only way to an outcome is the rule above.

Rejection and O3 are acceptable outcomes; this plan has no preferred result. Expectation
only, not a decision: four vCPUs and 609 s serial against 1,068 s contended suggest the
acceptance suite is a poor use of a four-way wide queue, so a gain is plausible.

### 3.4 The first measurement (run 39176546521, revision 4's rule)

The orchestrator ran revision 4's measurement as run 39176546521 on
`RodrigoFAbreu/workflow` (throwaway branch `measure/conformance-sharding`; job records kept
outside the repository). All 12 jobs succeeded and every sharded job recorded 415 of 415
test ids. The validator reported **inconclusive**: V2, no (`nproc`, CPU model, image)
triple was held by more than half of the jobs. CPU models: AMD EPYC 7763 on five jobs, AMD
EPYC 9V74 on three, Intel Xeon Platinum 8573C on three, AMD EPYC 9V45 on one; every job
had `nproc` 4 and image 20261012.334.1.

Same-CPU pairs, indicative only (one pair each): on the EPYC 7763, v1 1,197 s against
v3 994 s, v4 1,033 s and v5 985 s; on the Xeon 8573C, v1 1,031 s against v4 832 s and
v5 747 s. At width 2, v2 took 972 and 995 s (EPYC 9V74 only, with no same-CPU control) and
v6 952 s (9V74) and 1,144 s (7763): no gain.

**Disposition.** CP2 records this run in the evidence file as inconclusive under
revision 4's rule. Its runs do **not** count toward revision 5's rule: this rule was fixed
after those numbers were seen, the run had two repetitions per variant, and its pairs are
one run each, so a fresh measurement under the fixed rule decides.

## 4. Decisions

| Id | Decision |
|---|---|
| D-Inline | The scheduler and the shard tool live **inside the template's run block** (a quoted heredoc writing a small stdlib-only Python file next to the shell scheduler). The template is one self-contained file that `workflow-manager` installs; a consumer has no `tools/`. Rejected: a new payload script (a payload change and a downgrade consequence for a template-sized need). |
| D-Same-Text | The release's tests extract the heredoc from the template and run the real text. This repository's CI (CP3) embeds the **same** Python text, pinned equal by a test, so there is one tested implementation. |
| D-One-Job | One job, the required check name `workflow-conformance` unchanged. Separate jobs per shard are rejected for the reasons the CI plan gave (more peak jobs, queue time on a shared free account, checkout overhead). |
| D-Global-Limit | Shards and the eight other suites are one longest-first queue under one limit; acceptance shards come first. |
| D-No-Fallback | A failed planning step fails the job. |
| D-Per-Unit-Copy | Each unit keeps today's isolation: its own complete copy of the checkout, its own `TMPDIR` and `HOME`. A shard is a unit. The copy cost is part of the measured time. |
| D-Evidence-File | The measured numbers are written to `docs/ai-workflow/CONFORMANCE_SHARDING_EVIDENCE.md` (CP2), not into this plan: the numbers do not exist at plan time, and a record of data is not design. This plan states the rule; the file states the numbers and which outcome they select, and the reviewers check one against the other. The file is a reviewed deliverable and is protected at the implementation stage (section 9), so technical approval binds it. Under O3 an amendment does happen (section 1), to drop CP3 and CP4; it is a change of scope, not a data record, and does not touch CP2. |
| D-Commit-Type | A template change releases as a minor, 2.16.0, titled `feat:`; the manifest's version change agrees (`release.py check-title ... --agree`). |
| D-Release-Identity | The package builder refuses a release whose `WORKFLOW_RELEASE` (`payload/scripts/workflow_protocol.py:49`) differs from the manifest version (`tools/release/package.py`, `check_release_constant`; a scratch bump to 2.16.0 alone fails with `WORKFLOW_RELEASE = '2.15.0', but the manifest version is '2.16.0'`). A 2.16.0 release therefore must bump the constant, the assertions that pin it (`payload/scripts/workflow_protocol_test.py`, the `describe` test and `test_the_release_constant_and_the_protocol_version`) and the manifest digests of the payload files it touches. This is release-identity bookkeeping, not a behaviour change: the build guard stays as it is, the installed tree stays untouched, and O3 builds no release and leaves the 2.15.0 payload bytes as they are. |
| D-Same-CPU | Timings are compared only between runs of the same runner type (`nproc`, CPU model, image), never across CPU models (revision 5, the owner's option A of 2026-10-19, after the first measurement mixed four CPU models). Hosted runners cannot be asked for a CPU model, so missing same-CPU evidence is filled by more runs (top-up rounds), never by choosing runs. |
| D-Downgrade | A template change only (plus the release-identity bookkeeping of `D-Release-Identity`, which changes no behaviour): no state key, phase, configuration or commit shape changes. Moving back to 2.15.0 is `workflow-manager update` to 2.15.0 and restores the 2.15.0 template; nothing remains behind and nothing is undetectable. The `manager` block says so, `signals` empty, `min_manager_version` stays `1.13.0` (the Manager reads the same `suites=` line and the same template record shape). |

No row of the repository's open-decision register is finalized here.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The sharded scheduler as a candidate in the managed template, its tests and the measurement kit | - | 4 | 1 |
| CP2 | Measure, record the evidence and apply the decision to the template | CP1 | 2 | 1 |
| CP3 | The same scheduling in this repository's release-source conformance, and the user document | CP2 | 3 | 1 |
| CP4 | Release 2.16.0: manifest, release history, downgrade posture | CP2, CP3 | 2 | 1 |

**Conformance at a checkpoint** (the procedure W4 to W11 used). `manifest.json` carries
2.15.0's digests until CP4, and stock `release.py stage-conformance` verifies the
manifest before it builds the fixture, so a changed template byte is refused. CP1 to CP3
stage a scratch release from the checkpoint's own commit (`package.stage` with the
zlib-ng virtual environment's Python, into an empty directory outside the repository and
outside `/tmp`), rewrite `sha256` and `size` of every `artifacts` and `templates` record
of the **scratch** `manifest.json` from the bytes on disk with a throw-away script kept
outside the repository, then run `package.stage_conformance` and the nine payload suites
in that fixture (`TMPDIR` outside `/tmp`). The `tools/release` tests run in the same
virtual environment. The committed `manifest.json` is never touched before CP4. CP4 runs
the stock `release.py stage-conformance --commit <CP4 commit> --out "$(mktemp -d)/fixture"`
against its committed manifest. The only payload changes in this milestone are the release
identity bookkeeping of CP4 (the `WORKFLOW_RELEASE` constant, the two assertions that
pin it, and the three edits of `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` that
the tested-releases pin requires, `D-Release-Identity`); no behaviour changes, so the nine suites' results are the
2.15.0 results; they are run to prove it. CP1 to CP3 change no payload byte at all.

<!-- CP1 -->
### CP1 — The sharded scheduler as a candidate, its tests and the measurement kit

**Files:** `templates/.github/workflows/workflow-conformance.yml`,
`tools/release/release_test.py`.

The template's run block gains the candidate scheduling of section 2:

- The `suites="..."` line stays exactly one line and unchanged (the Manager and
  `release.py` count suites from it), and the nine suite names stay in it.
- Two constants, each alone on one line: `width_cap=4` and `shards=4`
  (`shards=0` means "do not shard", the value the kit uses for the control variants).
- A quoted heredoc writes `$base/shards.py` (stdlib only), with three subcommands:
  `plan` (load the module in `scripts/`, group tests by class, partition into `N`
  shards, write the plan with the expected ids), `run` (load exactly the classes of one
  shard with `loadTestsFromTestCase`, check the loaded ids equal the plan's ids for that
  shard, run them with a `TextTestResult` subclass that records every test id's outcome
  and failed subtests under their parent id, write the shard's result file, exit 1
  unless everything succeeded) and `check` (the coverage and outcome gates of section
  2.2, naming shards and original ids).
- The shell scheduler queues the shards first and the eight other suites after them,
  starts at most `min(width_cap, nproc)` units at a time, prints `start <unit> running K`
  as it starts each unit (`K` the units running including this one: the peak the
  validity check V3 reads), copies the checkout per unit,
  and then runs `check`, collecting every result before deciding (a unit that did not
  write its result is `missing`, as today). The summary keeps its nine suite rows.
- The concurrency block is byte-identical to 2.15.0.

**Tests** (`release_test.py`, extending `ConformanceTemplate`; the existing pins are
kept and adapted only where the step body now has a heredoc):

- The template carries each constant on exactly one line, and the substitution the kit
  applies (the same textual replacement, written in the test) yields a step that still
  parses as shell and keeps everything else byte for byte.
- The heredoc's Python, extracted from the template, run against a stand-in module with
  inheritance (a base with a test, two subclasses), a class-level skip decorator, a class whose `setUpClass` raises `SkipTest`, a
  `skipTest` in a test, subtests that pass and subtests that fail, a failing test, an erroring
  `setUpClass`, and a class with no tests: exact partition (every class once, ids equal
  the baseline), `check` passes only when every id is recorded once, and records the class-decorator skip as `skip` for each of its ids, and fails, naming
  the shard and the original ids, for each of a failed test, a failed subtest, a
  `setUpClass` error, a `setUpClass` `SkipTest` (a failure, section 2.4), a missing
  shard file, a truncated shard file, a duplicated id, an
  extra id, an id that started and never finished and an unexpected success.
- `plan` refuses, naming the hook, on a stand-in module that defines `load_tests`,
  `setUpModule` or `tearDownModule` (each separately).
- The partition is deterministic and balanced on the stand-in, and on the **real**
  acceptance module (`payload/scripts/workflow_acceptance_matrix_test.py`, loaded
  without running anything): for `N` in 1, 2, 4, 8 the shards partition exactly the tests of
  `loadTestsFromModule` (compared with its `len`, and with `manifest.json`'s
  `manager.conformance.suites["workflow_acceptance_matrix_test.py"]`, never a literal
  415), each class appears once, and a class with inherited tests carries them.
- The step body, run with stand-in suites as the existing tests do: all pass; each of the
  nine suites failing in turn; a failing shard; a shard whose copy fails (the
  `uncopyable` case: every unit reported, none lost); concurrency never exceeds the
  width and never exceeds it when shards and suites are queued together; isolation of
  `TMPDIR`, `HOME` and the per-unit repository copy for a shard as for a suite; the
  failure message names the shard and the original ids; a failed plan fails the job.
- `shards=0` reproduces 2.15.0's behaviour (nine units, no heredoc work, apart from the
  added `start` line): a behavioural test of the committed template against stand-in
  suites. The kit's control variants do not depend on it (section 3.1: they are the
  2.15.0 text); it is the evidence that the candidate with `shards=0` does not regress
  the unsharded path. The `start` line's `K` never exceeds the width in any test above.

**The measurement kit** (prepared by the worker under `$TMPDIR`, not committed, so no
file of it is a repository path): a generator script that reads the committed template
and `git show 971ea16:templates/.github/workflows/workflow-conformance.yml`, emits
`measure-conformance.yml` with the 12 jobs of section 3.1 (the control variants are the
2.15.0 step text, changed only by the `start` line, which prints `running K` so V3 can
read their peak, and, for v2, by the width line's two `4`s becoming `2`; the sharded
variants are the committed template with the two constants set). The kit checks the
control claim by a textual diff of each control step against the 2.15.0 step, which must
show exactly those lines and no other, and fails otherwise; the check is itself exercised
against the **real** 2.15.0 step and the real committed template, where it must pass for
v1 and v2 and must fail when any further line differs, and a `README` with the exact commands for the orchestrator to run (create the
throwaway branch from the CP1 commit in a separate worktree, add the workflow and push,
`gh run list/view` to read the jobs, delete the branch), and a local dry run of one
sharded variant against the repository (all gates pass, `expected 415, recorded 415`)
with the serial run's counts, skip ids and skip reasons for comparison.
The kit also holds the **validator** of section 3.3 (a script reading the jobs' recorded
`nproc`, CPU model, image, peak `K`, and step walls, and printing V1 to V4 per job and
variant and the list of jobs to replace) and its own checks, run before the kit is
handed over: synthetic job records that must be rejected for each of a runner with
`nproc` 2, an `nproc` differing between jobs, a differing CPU model, a differing image, a
peak `K` below `min(W, nproc)`, and repetitions more than 20% apart; a valid synthetic
set that must pass; proof that the validator reports an inconclusive set instead of
an outcome when a (variant, repetition) has no valid run; a V2 set with no strict
majority triple (inconclusive); a control (v1 and, separately, v2) that fails V4 after the
replacement bound (inconclusive, rule 3 never evaluated); a sharded variant that fails V4
after the bound (excluded, listed, and never selected as `s` or as rule 2's choice, with
the best of the others selected instead); every sharded variant lost to V4
(inconclusive) against every sharded variant lost to gate failures alone (sharding
rejected); and a V4 failure whose replacement list names both repetitions of the
variant, whichever is faster. The README names the
replacement push (jobs to enable, a V4 failure naming both repetitions) and the
two-replacement limit. The worker stops
after CP1 and reports the kit's location; the orchestrator runs the measurement.

**Verification:** the nine payload suites in the scratch fixture; the `tools/release`
tests; a local run of the sharded step on this repository's tree equals the serial
acceptance run (415 tests, the same skipped ids and reasons).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Measure, record the evidence and apply the decision

**Files:** `docs/ai-workflow/CONFORMANCE_SHARDING_EVIDENCE.md`,
`templates/.github/workflows/workflow-conformance.yml`,
`tools/release/release_test.py`.

CP1's kit description is the revision 4 kit; revision 5's sections 3.1 to 3.3 replace it,
and CP2 brings the kit to them before anything is measured.

**No checkpoint start that cannot finish.** CP2 runs as two dispatches, and the CP2 start
is recorded only when the measurement has selected an outcome:

1. **Preparation** (no checkpoint start or claim is recorded, and no repository path
   changes: the kit lives outside the repository, at its CP1 location
   `~/scratch-conformance-sharding/kit`). The worker updates `generate.py` and
   `validate.py` (and `collect.py`, `selfcheck.py` and the `README.md` where the new
   record shape and commands need it) to revision 5's sections 3.1 to 3.3, runs the
   kit's self-checks, and **stops before measuring**, reporting that the kit is ready, the
   self-check results, and that nothing was measured or recorded. The self-checks cover,
   with synthetic job records:
   - `generate.py` emits v1, v3, v4 and v5 only, repetitions a, b and c (12 jobs), and a
     top-up workflow enabling exactly the variants it is given, otherwise byte-identical;
     the v1 control differs from the real 2.15.0 step by exactly the `start` line, and the
     check fails when any further line differs;
   - runs of different runner types are never compared (v1 on one CPU model only and a
     candidate on another only leave the candidate undecided); a differing `nproc` or
     image is a different runner type;
   - qualification at one same-CPU pair (does not qualify) and at two (qualifies); V1
     (`nproc` 2) and V3 (a peak below `min(W, nproc)`) invalidate the run; a V4-noisy
     candidate cell disqualifies its runner type for that candidate, a noisy v1 cell for
     every candidate;
   - the 15% threshold per runner type at exactly 0.85 (gain) and just above it (fails);
     the slowest-candidate-against-fastest-control condition failing alone;
   - the gain on two runner types passes; on one only, undecided; a failure on one
     qualifying runner type rejects even with gains on two others; a status, once
     reached, is not re-evaluated;
   - the top-up list names v1 and only the undecided candidates; no fourth top-up round is
     ever requested;
   - rule 2 picks the smallest `W`, then `N`, within 5% of the best `G`, and never an
     undecided or rejected candidate;
   - the decision order of section 3.3: a failed v1 run gives inconclusive; one passing
     and one undecided candidate after the bound give O1 from the passing one; every
     candidate rejected (including by gate failures alone) gives O3; no candidate passing
     with one undecided after the bound gives inconclusive.
2. **Measurement** (the orchestrator): the first round and any top-up rounds, from the
   kit, until `validate.py` prints `status: decided` or `status: inconclusive`.
3. **Recording**, only after `status: decided`: the orchestrator starts CP2 and the worker
   records the evidence and applies the outcome, as below. After `status: inconclusive`
   CP2 is never started: no `IN_PROGRESS` entry or claim exists to release, and the
   orchestrator raises the result to the owner. A worker that finds CP2 already
   `IN_PROGRESS` without a decided result does not continue: it reports the state as the
   case of workflow#55 and stops.

The recording:

- The evidence file records: the first measurement as section 3.4 states it
  (inconclusive under revision 4's rule, its runs not counted); then, for revision 5's
  measurement, the run ids and branch commit of every round, `nproc`, CPU model and image
  of each job, the peak units running, each job's step wall and each unit's seconds, the
  coverage lines, any failed run, the validity result V1, V3 and V4 per run and cell with
  every invalid run preserved and marked, the per-runner-type table (cells, medians,
  same-CPU pairs, qualification, ratios, gain or failure), each candidate's status after
  each round, the top-up rounds run, the application of the section 3.2 rule step by
  step, and the selected outcome (O1 or O3) with its constants.
  Nothing in the file is estimated; a number not measured is written as not measured.
- The template is then set by the outcome: O1 keeps the sharded scheduler with the
  chosen `width_cap` and `shards`; O3 restores the 2.15.0 template bytes (the file equals
  `git show 971ea16:templates/.github/workflows/workflow-conformance.yml`) and stops:
  CP3 and CP4 are then not implemented: the worker reports the outcome and stops, and
  the orchestrator takes the O3 path of section 1 (`/request-plan-amendment` dropping
  CP3 and CP4), so the milestone is closed with the evidence as its deliverable.
  Under O1 the next checkpoint is CP3; no amendment is needed.
- `release_test.py`: the constants' pins match the outcome (for O1 the width and the
  shard count); for O3 the sharding tests of CP1 are removed with the sharding (the
  2.15.0 tests apply again).

**Verification:** the same as CP1; the validator's output is attached to the evidence and
its V1, V3 and V4 results are reproducible from the recorded job facts; the evidence's
selected outcome is reproducible from its own per-runner-type table by the rule (a reviewer
recomputes the medians over the valid runs).
<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Release-source conformance and the user document

**Files:** `.github/workflows/workflow-ci.yml`, `tools/release/release_test.py`,
`docs/RELEASING.md`.

Applies to O1 (under O3 it is dropped by amendment, section 1).

The managed-step measurement is a **proxy** for this job: `release-source-conformance`
runs the same suites on the same `ubuntu-latest` runner class and is not itself measured.
It takes the scheduling and the constants the evidence selected.

- `release-source-conformance` gets the same scheduling over the staged fixture instead
  of the checkout: the same shards, the same single limit, the same coverage gate, the
  heredoc text byte-identical to the template's (D-Same-Text), the same constants. It
  keeps `release.py stage-conformance --commit HEAD`, the 60-minute timeout, the
  diagnostic `source-conformance-logs` upload (it now also holds the shard logs and
  result files), and `aggregate` is untouched. Never the installed `scripts/`.
- `release_test.py` extends `WorkflowCI` the way CP1 extended `ConformanceTemplate`: the
  actual step body with stand-in suites, a failing shard, the equality of the embedded
  Python text with the template's, and the unchanged triggers, permissions, concurrency
  (a pull request's superseded run is cancelled, a main run is not) and job names.
- `docs/RELEASING.md` describes the sharded step, the diagnostics and where a shard
  failure shows. No required check, ruleset or job name changes.

**Verification:** `tools/release` tests, `tools/docs/check_docs.py` and its tests, the
nine payload suites, and a local run of the CI step body against a staged fixture
(coverage `expected 415, recorded 415`).
<!-- /CP3 -->

<!-- CP4 -->
### CP4 — Release 2.16.0

**Files:** `manifest.json`, `docs/release-history.md`, `docs/common-problems.md`,
`payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`.

Applies to O1 (under O3 it is dropped by amendment, section 1).

- The release identity (`D-Release-Identity`): `WORKFLOW_RELEASE` in
  `payload/scripts/workflow_protocol.py` becomes `"2.16.0"`; the two assertions at
  `payload/scripts/workflow_protocol_test.py` (the `describe` test and
  `test_the_release_constant_and_the_protocol_version`) become `"2.16.0"`;
  `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` changes in exactly three places,
  following the 2.13.0 and 2.14.0 releases: the tested-releases list (the test at
  `payload/scripts/workflow_protocol_test.py:3865` asserts `**Workflow {WORKFLOW_RELEASE}**`
  appears in it) gains **Workflow 2.16.0** under protocol `1.5`; the unpinned
  `"workflow_release"` example becomes `2.16.0`; and the protocol `1.5` history entry
  notes that 2.16.0 keeps it. Any other 2.15.0 mention is history and stays. Nothing
  else in the payload changes; the protocol version stays `1.5`. The package build guard is not touched.
- `manifest.json` 2.16.0 (`workflow_version`) with the `sha256` and `size` of the template
  record and of each payload record changed above refreshed and its derivation text
  extended with W12, every other record unchanged, `counts` unchanged.
  The `manager` block: `min_manager_version` `1.13.0`; a `posture` and an `undetectable`
  text that say, truthfully, that the template (plus the release constant) is the only change, that no state, phase,
  configuration or commit shape changes, and that moving back is
  `workflow-manager update` to 2.15.0; `signals` empty; `new_work_only` empty;
  `gate_default_change` empty; `conformance.suites` computed by
  `release.py manager-block --release-dir <scratch directory> --write` from a staging of
  CP4's own content, in one commit, in the order 2.15.0 used (every other edit and
  digest first, stage, write the counts, one commit). No hand-written count.
  `check-manager-block --commit HEAD` then agrees.
- `docs/release-history.md`: a 2.16.0 row with the outcome, the measured numbers, the
  release-identity note (the payload changes only its release constant), the downgrade posture and what stays open (#30 part 2, #31, #39, #45, #52, #48, #50).
- `docs/common-problems.md`: how to read a sharded conformance failure (the shard name,
  the original ids and the unfolded shard log) and what "missing shard" means.
- Documents whose header names 2.15.0 are re-checked and bumped as
  `tools/docs/check_docs.py` requires. `docs/ROADMAP.md` is marked Current now and Done
  at acceptance, not in this checkpoint.
- Consumers pick the template up with `workflow-manager update`; this repository's own
  installed `workflow-conformance.yml` changes only through that command after the
  release.

**Verification:** the nine suites pass in a stock `release.py stage-conformance` fixture
(including `workflow_protocol_test.py` at 2.16.0); `release.py build` of the commit
succeeds, which is the guard that failed before this bookkeeping existed;
`check-manager-block` is clean; the
`update-fixture` step passes from the 2.15.0 bootstrap through the 1.13.0 update;
`check-title ... --agree` agrees with `feat:`; `tools/docs/check_docs.py` is clean;
`workflow-manager verify .` is clean; the tools tests pass in the zlib-ng virtual
environment.
<!-- /CP4 -->

## 6. Tests and verification summary

Each checkpoint's tests are listed in its section. Every checkpoint runs the nine
payload suites from a staged fixture of its own commit (CP1 to CP3 through the
scratch-manifest procedure of section 5) and the `tools/release` tests; CP4 adds the
release steps above. The measurement itself (CP2) is the only step that needs GitHub.

## 7. Risks

- **The measurement is noisy** (shared runners). Three repetitions per variant, timings
  compared only on the same CPU type, a 15% margin per CPU type, the gain required on two
  CPU types and a 5% tie band; a decision inside the noise is "no change".
- **The runners are not comparable, or smaller than assumed.** A two-CPU runner turns
  `min(W, nproc)` into 2 for every variant, and hosted pools mix CPU models (four in the
  first measurement, section 3.4). Section 3.3 checks `nproc`, the peak width actually
  reached and the spread within each same-CPU cell; section 3.2 never compares runs of
  different runner types; invalid runs are kept and covered by at most three top-up rounds.
- **The measurement may still end inconclusive.** Each candidate needs two CPU types with
  two same-CPU pairs each. The first measurement's spread (five, three, three and one jobs
  of 12 over four CPU models) suggests two types are reachable within the top-up rounds,
  but a rare or noisy pool can leave a candidate undecided. An inconclusive result is
  safe: no outcome is selected, CP2 is never started, and the orchestrator raises it to
  the owner.
- **Sharding changes test order between classes.** Mitigation: classes already build
  their own disposable repositories; a dependency would fail the measurement runs and
  the local equivalence run before anything ships.
- **A shard may be starved or fail to start.** The per-unit result file is mandatory; a
  missing file is a named failure, as a missing suite file is today.
- **Per-unit checkout copies multiply with `N`.** Counted in the measured time; `N` is
  chosen by the rule, not by assumption.
- **The heredoc grows the template.** It stays one self-contained, tested file; the
  alternative (a payload script) is a larger blast radius (D-Inline).
- **A required-check-time gain is limited by the slowest unit.** If a single class
  dominates, sharding gains little and the rule rejects it.

## 8. Requirements

| Id | Requirement | Checkpoints |
|---|---|---|
| R1 | A measured decision on GitHub runners (sharded at widths 3 and 4 against unsharded, compared only on the same CPU type) taken only from evidence that passed the runner-validity and same-CPU comparability checks, recorded in the evidence file before any later checkpoint builds on it; no gain is an accepted outcome and ships only what helped | CP1, CP2 |
| R2 | If adopted, acceptance sharding by whole classes inside the one managed job under one global limit, the required check name unchanged, every test id exactly once (inherited tests, skips and subtests included), failures naming the shard and the original ids, and any failed, missing or incomplete shard failing the job | CP1, CP2 |
| R3 | The managed template's width set from the measurement, and PR cancellation of superseded runs (main pushes never cancelled) kept and pinned | CP1, CP2 |
| R4 | The same scheduling in this repository's own release-source conformance where it helps, without weakening any check | CP3 |
| R5 | Release 2.16.0 bookkeeping: the release constant and its pinning assertions so the package builds, release history, downgrade posture (a template change only, apart from the release constant), the `manager` block (`min_manager_version` 1.13.0) | CP4 |

## 9. Artifact classification

`docs/ai-workflow/registry/conformance-sharding-artifacts.json` is declared as the
previous release-source items declared theirs. At the plan stage the plan
(`docs/ai-workflow/CONFORMANCE_SHARDING_PLAN.md`), the registry and the mapping are
protected; `templates/`, `tools/`, `payload/`, `fixtures/`, `.github/`, `manifest.json`,
`docs/RELEASING.md`, `docs/release-history.md`, `docs/common-problems.md`,
`docs/ROADMAP.md` and `docs/ai-workflow/` (which includes the evidence file) are
excluded. At the implementation stage the protected set is: `templates/`, `tools/`,
`payload/`, `fixtures/`, `.claude/commands/` and `scripts/` (prefixes); `manifest.json`,
`docs/RELEASING.md`, `docs/release-history.md`, `docs/common-problems.md`,
`docs/gates.md`, `docs/glossary.md` and the declaration itself (exact paths); and, as
reviewed deliverables of this item, the exact paths
`docs/ai-workflow/CONFORMANCE_SHARDING_EVIDENCE.md` (R1's deliverable and the record a
reviewer recomputes the medians from) and `.github/workflows/workflow-ci.yml` (R4's
deliverable, with the D-Same-Text equality). Exact protected paths are checked before
the excluded prefixes `docs/ai-workflow/` and `.github/`, so these two are protected
while the rest of those prefixes stays excluded, along with the plan, `docs/ROADMAP.md`
and the machinery's own bookkeeping. Every path section 5 names is classified at both
stages, including this plan file; the declaration check runs at publication and refuses
otherwise.

## 10. Revision history

| Rev | Change |
|---|---|
| 1 | First plan for row 15. |
| 2 | Review round 1 (`LPR-R1-I01` to `-I03`, `-O01` to `-O06`): the lifecycle path of each outcome is named (section 1; O2 always aligns the CI width as a declared proxy, so there is no O2-without-CI); the evidence file and `workflow-ci.yml` are protected at the implementation stage (section 9); the `setUpClass` `SkipTest` rule is stated, declared and pinned (sections 2.1, 2.4, CP1); rule 2 requires the chosen variant to satisfy rule 1; `plan` refuses module hooks; real-module pins compare with the module and the manifest. No finding rejected. |
| 3 | External review round 1 (`EPR-R1-I01`, `-I02`): CP4 now carries the release-identity bookkeeping the package build requires (`WORKFLOW_RELEASE`, its two assertions, the manifest `workflow_version` and digests; `D-Release-Identity`), and the "template only" claims are qualified; section 3.3 adds runner-validity and comparability checks V1 to V4 evaluated before the decision rule, preserved invalid runs, bounded replacements, an inconclusive result that selects no outcome, the step's `start <unit> running K` line for V3, and the kit validator with its own checks (CP1, CP2). No finding rejected. |
| 4 | Local review round 3 (`LPR-R3-I01`, `-I02`, `-O01` to `-O03`): the control variants are defined as the 2.15.0 step text with only the `start` line (and v2's width line) changed, so the kit's textual diff can pass and is exercised against the real files (3.1, CP1); every V1 to V4 failure has a stated consequence, V4 replacing both repetitions as a pair, a control failing V4 or all sharded variants lost to V4 being inconclusive, a sharded variant failing V4 being excluded (3.3, CP1 self-checks); V2's majority is across all jobs; CP4 names the three `ORCHESTRATION_PROTOCOL.md` edits and section 5 is corrected; section 7 names the likelihood of an inconclusive result. No finding rejected. |
| 5 | Plan amendment after the first measurement (run 39176546521) came back inconclusive under V2 (four CPU models, no majority triple); the owner chose option A on 2026-10-19. Dispositions: (1) timings are compared only within one (`nproc`, CPU model, image) runner type and V2 is replaced by the per-runner-type rule (3.2, 3.3, `D-Same-CPU`); V1, V3, V4 (now per same-CPU cell) and the coverage gate are kept; (2) three repetitions per variant (3.1); (3) v2 and v6 are dropped, with them the outcome O2 (section 1, CP3, CP4, R1); v1 is the control and v3, v4, v5 are kept as candidates, each showed a same-CPU gain in the first run; (4) the decision under mixed CPU models is fixed: two same-CPU pairs per qualifying CPU type, the gain (15% per type, every pair favouring the candidate) on at least two types and on every qualifying type, at most three top-up rounds that re-run v1 and the undecided candidates, and the stated inconclusive cases (3.2, 3.3); (5) run 39176546521 is recorded as inconclusive under revision 4's rule and does not count (3.4); (6) CP2 prepares the kit without a checkpoint start, stops before measuring, and is started only after a decided result, so an inconclusive result leaves no `IN_PROGRESS` residue (workflow#55). CP1 (`COMPLETE`) is unchanged; its kit description is superseded by CP2's preparation. |
