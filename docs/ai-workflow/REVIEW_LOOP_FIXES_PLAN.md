# W9: Workflow 2.13.0 — review-loop fixes: a changes file per review stage, an atomic ready file, the governing-version sweep before review, and the Manager metadata block (Revision 6)

- **Work item:** `review-loop-fixes` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner placed it as
  row 10 of `docs/ROADMAP.md` (workflow PR #36) and confirmed on 2026-10-16
  that it comes before item C (acceptance-matrix sharding).
- **Roadmap step:** W9, row 10 of "What's next". This plan makes it the
  current item.
- **Branch:** `milestone/review-loop-fixes`
- **Base commit:** `d911915` (main after #36: the release source is Workflow
  2.12.0; this repository's own installation is also 2.12.0 with automatic
  gates, default 2.2 and no `GATE_POLICY.json`)
- **Plan revision:** 6. Every checkpoint section carries its
  `<!-- CPn -->`/`<!-- /CPn -->` pair. Section 10 has the revision history.

## 1. Goal

Ship Workflow 2.13.0, a minor release (`feat:`: it adds a refusal and a
manifest field), that removes three defects found running 2.12.0 and lets the
Workflow Manager read a release without a Manager release.

1. **workflow#35 — a changes file per review stage.** `CHANGES_SINCE_REVIEW.md`
   compares against the previous bundle generation and carries the findings of
   the file `REVIEW_FEEDBACK.md` only when that file names the previous round.
   An external reviewer's round 2 therefore sees the last *local* round's diff
   and findings. After this release the file holds one section per review
   stage; the manual external stage's section compares against the content that
   stage last reviewed and quotes that stage's own last verdict. The local
   stage's section is today's behaviour. Plan and implementation stages both.
2. **workflow#32 — the flaky real-process test.** A frozen test reads a ready
   file the holder process is still writing. The holder writes it atomically.
3. **workflow#30, part 1 — the governing-version sweep before review.** When a
   plan revision is published, bound or turned into a plan-review bundle, the
   installed conformance sweep (`sweep_governing_version_enumeration`) runs on
   the plan, as 2.11.0 does for checkpoint anchors, so a plan the sweep would
   reject is refused before any review, not at pull-request time when an
   approved plan can no longer be corrected.
4. **The manifest `manager` block, schema 1.** The release carries the data the
   Manager now reads from the release itself (the producer side of
   `workflow-manager/docs/release-metadata.md`).

### Hard requirements (invariants)

- **INV-1** Nothing new is persisted in `WORKFLOW_STATE.json` or
  `WORKFLOW_CONFIG.json`; approvals, gates and who may approve are unchanged.
- **INV-2** `CHANGES_SINCE_REVIEW.md` and the new baseline records stay outside
  `bundle_id` and `review_content_id`; every `APPROVE` still binds, and is by
  rule, a full review of the whole bundle.
- **INV-3** A failure to build a section, the file or a baseline never fails a
  generation or a verdict ingest: the reader falls toward a full review.
- **INV-4** A local round is unchanged: same basis (the previous bundle
  generation), same findings, same condition.
- **INV-5** The only new refusal is the sweep's, on a new plan revision;
  published and bound plans keep working until their next revision.
- **INV-6** This repository's own installation (`.claude/`, `scripts/`, the
  managed `docs/ai-workflow/` documents, `.workflow-manager/`) is never edited.

### Non-goals

- workflow#30 part 2 (a correction route for an approved plan), workflow#31
  and workflow#34 (later rows), and any Controller work.
- A new persisted per-stage verdict record in state (OD-1 chooses a file).
- Changing who may approve, the gate policy, or the Orchestration Protocol
  (D-Protocol).
- `sweep_applying_review_feedback_version_claims` (a sibling pull-request-time
  corpus sweep, `workflow_state_test.py`): it is not moved earlier; this plan
  stays clean under it as it is, and only the governing-version enumeration
  sweep is run early (D-Sweep).

## 2. What exists today (facts this plan relies on)

- **The changes file** is built by `workflow_fingerprint.write_changes_since_review`
  (`payload/scripts/workflow_fingerprint.py`), called from
  `payload/scripts/prepare-ai-review.sh` after the manifest. Plan stage: the
  outgoing `current/` and `.pin` against the staging pin, used only when the
  outgoing `review_content_id` is in the item's consumed list; a wrapper-only
  regeneration of unchanged content carries the live file forward when it names
  the unchanged id. Implementation stages: the previous round's
  `reviewed_implementation_head` (found through that round's generation-record
  commit) against the working tree, over the protected paths. The previous
  findings are `<feedback_dir>/REVIEW_FEEDBACK.md` when its header names the
  previous round's id, else "not available". The file sits next to `current/`
  and is bundled into `review-bundle.tar.gz`, from which the manual reviewer
  works.
- **There is one `REVIEW_FEEDBACK.md`** per work item, overwritten by the local
  reviewer and by the manual ingest alike, so after any round it holds the last
  verdict of either stage. The ledger `plan_review_stages` (and its
  implementation twin) records an entry only for an `APPROVE`; a `REVISE` is a
  phase change plus the consumed-content record, with no per-stage verdict
  record. Nothing in the Workflow keeps what the manual stage last reviewed.
- **Every manual verdict is stored in one place**:
  `workflow_state.ingest_manual_review_verdict` (called by the two
  `/record-manual-*-review` commands and by the protocol's
  `record-external-result`) writes `REVIEW_FEEDBACK.md` through
  `_store_manual_verdict` and publishes state through `state_transaction`.
  Verdict states are `APPROVE`, `REVISE` and `BLOCK`; `BLOCK` writes no state.
- **The 2.11.0 early anchor check** is `workflow_state.assert_plan_checkpoint_anchors`
  (read-only, an exemption for a bound regeneration, the same four error
  classes, one next step `PLAN_ANCHOR_NEXT_STEP`). It is called at four command
  steps (`/milestone-plan`'s publication point and bind, `/apply-plan-review`'s
  publication point and bind) and by `prepare-ai-review.sh` on the pinned
  bytes before the bundle is built.
- **The installed conformance sweep** is `workflow_state.sweep_governing_version_enumeration`
  over the top-level `.md` files of `.claude/commands/` and `docs/ai-workflow/`.
  A plan under `docs/ai-workflow/` is in its corpus; the sweep fails the
  required `workflow-conformance` check at pull-request time, after plan
  approval, when the plan can no longer be corrected.
- **The flaky test** `TestSameWorktreeConcurrencyRealProcesses.test_second_process_reclaims_first_process_destructive_guard_windows_open_simultaneously`
  (`payload/scripts/workflow_state_test.py`) polls `ready.exists()` and then
  `json.loads(ready.read_text())`; the holder subprocess creates the file with
  `Path.write_text`, which truncates first, so the reader can see an empty or
  half-written file.
- **The Manager** (workflow-manager 1.13.0) reads an optional `manager` block
  from `manifest.json` (contract: `workflow-manager/docs/release-metadata.md`,
  read only). Without it a post-2.12.0 release is reported as incomplete.
  `tools/release/` has `package.py` (stage, verify, build, `stage_conformance`)
  and `release.py` (title, pending, immutable, build, `stage-conformance`);
  `manifest.json` is authored by hand, with digests refreshed by a throw-away
  script. CI is `.github/workflows/workflow-ci.yml` (not Manager-managed).

## 3. Design decisions

### D-Keyed: one changes file, one section per review stage (OD-1, OD-2)

The two reviewers read the same generation: the local review, then, on an
`APPROVE`, the manual one, against the same bundle. The file therefore cannot
be generated for "the next reviewer"; it holds a section for each stage.

**The file.** `CHANGES_SINCE_REVIEW.md` keeps its path, its bundling, and its
preamble lines `work_item_id:`, `stage:`, `review_content_id:` (this
generation's id, the line every reader checks) and `revision:`. The previous-round
lines move into the sections. Then one section per stage, with these exact
headings, in this order: for the plan stage `## LOCAL_MODEL_PLAN_REVIEW` then
`## MANUAL_EXTERNAL_PLAN_REVIEW`; for the implementation stage
`## LOCAL_MODEL_IMPLEMENTATION_REVIEW` then
`## MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`. A section with a basis holds
`previous_review_content_id:`, `previous_revision:` (and, at the implementation
stage, `previous_reviewed_implementation_head:`), then `### Previous findings`
and `### Changes` (a fenced diff, or `(no change to the protected content)`).
A section without a basis holds exactly one line, `not available (<reason>):
review the whole bundle.`, with `<reason>` one of `no previous review of this
stage is recorded` or `the previous round cannot be identified`. The reviewer
reads the section named for its role; a role whose section is not available
reviews the whole bundle. The file is written when at least one section has a
basis and deleted otherwise (today's rule, per section).

**The local section** is today's content under INV-4: its basis, its consumed
check, its findings (`REVIEW_FEEDBACK.md` when its header names the previous
round, else not available), and the wrapper-only carry-forward of the whole live
file when its preamble names the unchanged id.

**The manual section** compares against the *stage baseline* (D-Baseline): the
content and the verdict of the manual stage's last recorded round. Its basis
holds when a valid baseline exists for that role and work item and its
`review_content_id` differs from this generation's. Its findings are the
baseline's stored verdict text, never `REVIEW_FEEDBACK.md`. At the plan stage
the diff is the baseline's pin against the staging pin; at the implementation
stage it is the baseline's reviewed head against the working tree over the
protected set (the union of the old and the new classification, as today).

**Review rule (unchanged):** a round may review only the changes and declare
`Review scope: changes` on a `REVISE` or `BLOCK`; every `APPROVE` is a full
review. The only change is "the section named for your role".

**Trust boundary.** `CHANGES_SINCE_REVIEW.md` is a reviewer aid, never a gate.
It stays outside `bundle_id` and `review_content_id` (INV-2), and since 2.12.0
every `APPROVE` is a full review of the whole bundle: an `APPROVE` declaring
`Review scope: changes` is refused at ingest
(`payload/scripts/workflow_fingerprint.py:3807`). A wrong or stale manual
baseline can therefore cost review efficiency (a `REVISE` round that reviews
the wrong changes) but can never let unreviewed content be approved.

### D-Baseline: what the manual stage last reviewed (OD-1)

A baseline is a gitignored record under `.ai-review/<work_item_id>/review-baselines/<ROLE>/`
(next to `current/`, never inside it), `<ROLE>` being
`MANUAL_EXTERNAL_PLAN_REVIEW` or `MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`. It is
written by `workflow_fingerprint.record_stage_baseline`, called by
`ingest_manual_review_verdict` *inside the same `state_transaction` mutator*, under
the state lock, once every refusal has passed and just before the new state is
returned, for a verdict whose status is `REVISE` or `APPROVE` (a `BLOCK` changes
nothing and records nothing), and replaced wholesale by the next such verdict.
It holds:

- `BASELINE.json`: a JSON object with exactly the keys `schema_version` (1),
  `state_revision` (the `state_revision` the verdict's own publication writes),
  `work_item_id`, `role`, `verdict` (`REVISE` or `APPROVE`),
  `review_content_id` (64 hex), `bundle_id` (the verdict's `Reviewed bundle ID:`
  or `null`), `revision` (`plan_revision`, or `implementation_revision`),
  `reviewed_implementation_head` (40 hex at the implementation stage, `null` at
  the plan stage), `classification` and `recorded_at`. `classification` is the
  protected/excluded path and prefix sets in force when the verdict was recorded,
  as objects of path to reason: at the plan stage `protected_paths`,
  `excluded_paths`, `excluded_prefixes`; at the implementation stage
  `protected_paths`, `protected_prefixes`, `excluded_paths`, `excluded_prefixes`
  (the sets the ingest's own `approval_review_content_id` loaded for that
  verdict);
- `VERDICT.md`: the verdict text exactly as stored in `REVIEW_FEEDBACK.md`;
- at the plan stage `pin/`: a copy of the item's `.pin` tree (the protected
  plan content the verdict was about; the ingest has just required the bundle to
  be bound and verified for exactly that `review_content_id`).

The reader (`read_stage_baseline`) returns `None` for anything not exactly this
or not consistent with itself and with the repository: a missing file, a symlink,
a wrong key set or type, a `work_item_id` or `role` that is not the one asked
for, an id that is not 64 hex, a missing `pin/` (plan stage) or an unreadable
`VERDICT.md`; a `VERDICT.md` whose header (`Work item:`, `Reviewer role:`,
`Status:`, `Reviewed review_content_id:`) disagrees with the record's
`work_item_id`, `role`, `verdict` and `review_content_id`; and a content that is
not the recorded id. **Recomputation inputs** (pinned to the record, never to
today's item or working tree, so a baseline survives a plan-revision bump and a
later change to `<id>-artifacts.json`): at the plan stage
`compute_review_content_id_plan_stage_from_pin` over the copied `pin/`, with the
record's `revision` as `plan_revision`, the record's `classification` sets, and
the item's `base_commit`, type and id (fixed for the item); at the
implementation stage `compute_review_content_id_implementation_stage_at_commit`
over `base_commit..<recorded reviewed_implementation_head>` (the commit must be
reachable), with the record's `classification` sets. These are the same
functions `approval_review_content_id` calls, fed the values it used when the
verdict was recorded, so they reproduce the recorded id in supported operation.
A change to the declaration after the record therefore does not drop the manual
section. The recorded classification serves only that recomputation: the
implementation diff selects its paths, as D-Keyed says and as
`_implementation_stage_changes` does today
(`payload/scripts/workflow_fingerprint.py:3280`), from the union of the recorded
and the current protected classifications, so the edits to a path an amendment
newly protects are included. A recorded id
the item's state does not know (neither in its consumed list nor in its stage
ledger) is also `None`. Every `None` is the explicit full-review fallback of the
manual section (INV-3); no approval rule and no id changes.

**Publication order and freshness.** Inside the mutator, under the state lock
that serialises every ingest, the writer (1) removes the role's existing record,
then (2) stages a sibling directory and renames it into place with the
`state_revision` the transaction is about to publish. Hence a later accepted
verdict never leaves an earlier record behind: if the write fails (one warning,
INV-3) the role has no record and the next manual round is a full review; if the
transaction itself then fails, the handler removes the new record. Writers
cannot complete out of order (one lock), and the writer refuses to replace a
record whose `state_revision` is higher than its own. A reader sees the old
record, the new one, or none.
No state key is added (INV-1): 2.12.0 neither reads nor deletes the directory.

**What is guaranteed, and its limits.** In supported operation the baseline is
the latest accepted manual verdict for its stage: the writer runs under the
state lock after the manual ingest and replaces the record atomically; the
reader recomputes the content id and checks the record's internal consistency;
any failure renders the explicit full-review fallback. Outside that guarantee,
stated as limits rather than detected: (a) a deliberately edited or restored
gitignored baseline file (these local files are under the operator's control,
like `REVIEW_FEEDBACK.md` itself); (b) a downgrade below 2.13.0 followed by a
manual review and a re-upgrade, for which D-Downgrade tells the operator to
delete `.ai-review/<id>/review-baselines/`. Under either limit the cost is the
one the trust boundary (D-Keyed) bounds: efficiency, never approval.

**Consequence (OD-3):** the first manual round after the first update to
2.13.0, or after a re-upgrade once `review-baselines/` has been deleted as
D-Downgrade says, has no baseline, so its manual section is not available and
that round is a full review. A manual round after one recorded by 2.13.0 gets
its changes. A directory kept across a downgrade is limit (b).

### D-Sweep: the governing-version sweep, early (OD-4)

`workflow_state.assert_plan_governing_version_sweep(repo_root, work_item_id, *,
state=None, pin_dir=None, allow_bound_regeneration=False)` is read-only and
mirrors `assert_plan_checkpoint_anchors` in every structural way: it returns at
once for a work item whose governing version is not two-stage, and, with
`allow_bound_regeneration`, for a bound regeneration at a ready phase; it reads
the plan document the item declares from `pin_dir` when given, else from the
working tree.

**One rule.** It runs `sweep_governing_version_enumeration` on that one
document, under its repository-relative path, when the path is a top-level `.md`
file of `docs/ai-workflow/` (exactly the corpus the installed sweep reads);
a plan elsewhere is not in the installed corpus and is not judged. A finding
raises `workflow_state.PlanGoverningVersionSweepError` whose message names the
work item, the plan revision, each finding as `<path>:<line> (<form>): <snippet>`
and ends with `workflow_state.PLAN_SWEEP_NEXT_STEP`: reword each flagged passage
so it names no list of governing versions (say a feedback-only item or a
two-stage item), then run the command again.

**Where, and in which order.** Right after the anchor check, at the same four
command steps and in `prepare-ai-review.sh` on the pinned bytes (one Python
block, both checks, `_PLAN_EARLY_CHECK_ERRORS` being the anchor classes plus the
sweep's), so a refusal exits 1 through `cleanup` with nothing promoted, nothing
marked `REJECTED`, no state written. Anchors first: a plan without anchors is
refused for that cause, as today.

**Scope.** Existing approved or bound plans keep working until their next
revision (the same exemption as anchors). The check never edits a plan.

### D-Atomic: the ready file (workflow#32)

The holder subprocess of the real-process test writes its ready file through
`publish_atomically(path, text)`: write to `<path>.tmp`, flush and fsync,
`os.replace` onto `path`. The reader stays as it is, because a file that appears
is now complete. The helper lives in its own constant of the test module so a
test can exercise it deterministically (it asserts that the destination never
exists before the replace and that the temporary file is complete at that
moment). The other worker sources write the fixed text `ready` and are never
parsed, so they are unchanged.

### D-Manager: who authors, who computes, who checks (OD-5)

The block lives in `manifest.json` (a published manifest asset is the commit's
manifest, so the committed file must already be complete). Authoring it there,
rather than in the contract's suggested `release/MANAGER_METADATA.json` copied
into the manifest by the build, is a deliberate departure: the committed
manifest is what CI checks and what is published, so one file has one author
step; the Manager's `release-metadata.md` is to be updated to match.

| Field | Source |
| --- | --- |
| `schema_version`, `min_manager_version`, `downgrade_boundary`, `new_work_only`, `gate_default_change`, `conformance.portability_exceptions` | **Authored** in the release source's `manifest.json`, in this milestone's pull request |
| `conformance.suites` | **Computed** by `tools/release/manager_block.py`: the staged conformance fixture's nine suite files (named by the managed `workflow-conformance.yml` template, the one list), loaded as `unittest` loads a suite, counting test cases; `release.py manager-block (--commit REF | --release-dir DIR) [--write]` prints the measurement and, with `--write`, replaces the block's `suites` in the working-tree `manifest.json`. `--release-dir DIR` measures a directory staged from the working tree with its digests already refreshed, through the same `stage_conformance`; `--commit REF` goes through `verify_release`, so it needs a commit whose manifest digests already match its payload bytes |

For 2.13.0: `min_manager_version` `1.13.0`; `downgrade_boundary.posture` the
empty string (the release writes nothing a move back to 2.12.0 loses; D-Downgrade),
`undetectable` `null`, `signals` `[]`; `new_work_only` one entry (the first
manual round after the update is a full review, D-Baseline); `gate_default_change`
the empty string; `portability_exceptions` `[]` (as 2.12.0).

**CI** gains one step, `release.py check-manager-block --commit HEAD
--manager-releases <saved list>`, which refuses when: (a) the block is not valid
under the contract (schema 1, key types, the closed detector vocabulary,
kebab-case signal names, version strings, `suites` a mapping of file names to
non-negative integers, `portability_exceptions` a list of objects with `suite`,
`test`, `reason`); (b) `suites` differs from the measurement; (c)
`min_manager_version` is newer than the newest published Manager release in the
committed publication evidence `tools/release/manager-releases.json` (the saved
output of `gh release list -R RodrigoFAbreu/workflow-manager --json
tagName,isDraft,isPrerelease,publishedAt`, complete records, plus the date it
was taken), where only a tag matching exactly `vX.Y.Z` that is neither a draft
nor a prerelease counts (`workflow-manager-v1.0.0` and any other tag are
ignored); a record missing `isDraft` or `isPrerelease` makes the evidence
invalid, never counted; (e) a manifest
whose version is 2.12.0 or older has a block, or a manifest newer than 2.12.0
has none. Check (d) (a non-empty posture when a release adds a persisted key, phase or
status) is not built: it is a judgment no tool can make mechanically here (OD-5).
Check (f), the pre-publish update fixture, is built (a CI step, below).

**Offline evidence.** Validation reads only the committed snapshot, so it needs no
network. The snapshot is refreshed by `release.py record-manager-releases`
(runs the `gh` listing, refuses incomplete records, writes the file); the owner
step that publishes Manager 1.13.0 is followed by that refresh in this pull
request. A separate CI step, `release.py compare-manager-releases`, lists live and
reports three distinct outcomes: `consistent`, `snapshot behind` (a published
release the snapshot lacks: a warning, not a failure) and `unavailable` (the API
cannot be reached: a notice, exit 0). Only an unsatisfied minimum against the
snapshot, or invalid evidence, fails the required check.

**Check (f), the update fixture** (CI step `update-fixture`, per the contract):
bootstrap a scratch repository from the previous published release (v2.12.0, its
release assets), run `workflow-manager update` in it with the released minimum
Manager (`manager-pin.json` is advanced to the block's `min_manager_version`;
check (g): the pin version equals `min_manager_version`) against the candidate
staged release, then run the nine candidate frozen suites in the updated
repository and `workflow-manager verify .`. This replaces, not adds to, the
existing candidate-direct bootstrap's role for the upgrade claim; that step stays
for the fresh-install path.

### D-Downgrade: what 2.12.0 loses (OD-6)

2.13.0 writes no new key or value to `WORKFLOW_STATE.json` or
`WORKFLOW_CONFIG.json`, no new commit shape, no new phase. It adds one
gitignored directory, `.ai-review/<id>/review-baselines/`, and changes the
layout of the gitignored `CHANGES_SINCE_REVIEW.md`. After a move back to 2.12.0:
the early sweep refusal is gone (a plan the installed sweep rejects reaches
review again), the directory is ignored and not deleted: delete
`.ai-review/<id>/review-baselines/` on downgrading (as 2.12.0's paragraph says
to delete `CHANGES_SINCE_REVIEW.md`), so the first manual round after a
re-upgrade is a full review (D-Baseline, limit (b)); and
a 2.13.0-shaped changes file still opens with the `review_content_id:` line a
2.12.0 reviewer checks, but its first section is the local one only by
convention (2.12.0 regenerates the file in its own shape at the next
generation). Nothing is lost from state, so the manifest block's `posture` is
empty and the release-history row states the paragraph.

### D-Protocol: Orchestration Protocol stays 1.4 (OD-7)

No snapshot field, row, action, envelope key or classification changes. The
sweep refusal is a command-step refusal like the anchor refusal 2.11.0 added
without a protocol bump. `WORKFLOW_RELEASE` and the tested-releases list gain
2.13.0, as in every release.

## 4. Open decisions (for the plan reviewer and the user)

| id | decision | recommendation |
| --- | --- | --- |
| OD-1 | Where the manual stage's last verdict and reviewed content are kept | **A gitignored baseline directory beside `current/`**, written at ingest (D-Baseline). Not state (INV-1, and a downgrade-clean release); not `REVIEW_FEEDBACK.md` (it is overwritten by either stage, which is the defect); not the orchestrator's archive (the Workflow cannot rely on it). |
| OD-2 | One file with a section per stage, or two files | **One file** (D-Keyed): both reviewers read the same bundle and the tarball carries one name; the preamble check readers already make stays the same line. |
| OD-3 | A manual round with no baseline | **A full review** with an explicit "not available" section, never a guess from the local round's data. |
| OD-4 | What the early sweep judges | **The plan document only**, and only when it lies in the installed sweep's corpus (D-Sweep). |
| OD-5 | Authored versus computed manifest fields, and which contract checks CI runs | **Authored in the manifest, suites computed and verified**; CI runs checks (a), (b), (c) (against committed, complete publication evidence), (e), (f) (the update fixture with the released minimum Manager) and (g) (pin equals minimum). Build (d) later if a real case asks. Check (c) makes CI red until Manager 1.13.0 is published and the evidence refreshed, which is the intended order (no Workflow release that no published Manager can read). |
| OD-6 | Downgrade posture | **Empty** (nothing in state), with the paragraph in the release-history row. |
| OD-7 | Release version and protocol | **2.13.0, `feat:`; protocol 1.4** (D-Protocol). |

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Two early fixes: the atomic ready file (#32) and the early governing-version sweep (#30 part 1) | - | 3 | 1 |
| CP2 | Stage baselines: record what the manual stage last reviewed (#35, part 1) | - | 3 | 1 |
| CP3 | The changes file, per review stage, at both stages (#35, part 2) | CP2 | 4 | 1 |
| CP4 | The Manager metadata block: authoring, measurement and CI checks | - | 4 | 1 |
| CP5 | Release 2.13.0: manifest, release constant, release history, downgrade posture | CP1, CP2, CP3, CP4 | 2 | 1 |

Every checkpoint updates the golden command-file hashes
(`_GOLDEN_COMMAND_FILE_SHA256` in `workflow_integration_test.py`) for the
command files it edits. The installation under `scripts/`, `.claude/` and
`docs/ai-workflow/`'s managed files is never edited.

**Conformance at a checkpoint** (the W4 to W8 procedure).
`release.py stage-conformance` refuses changed payload bytes while
`manifest.json` still carries 2.12.0's digests, which CP5 refreshes. CP1 to
CP4 therefore stage a scratch release from the checkpoint's own commit
(`package.stage` with the zlib-ng venv's Python, into an empty directory
outside the repository), rewrite `sha256` and `size` of every `artifacts` and
`templates` record of the scratch `manifest.json` from the bytes on disk with a
throw-away script kept outside the repository, then run
`package.stage_conformance` and the nine suites in that fixture, with `TMPDIR`
outside `/tmp`. CP5 runs the stock `release.py stage-conformance --commit <CP5
commit> --out "$(mktemp -d)/fixture"`, and the scratch digests must equal CP5's
committed ones for the same tree.

<!-- CP1 -->
### CP1 — Two early fixes: the atomic ready file and the early sweep

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/prepare-ai-review.sh`,
`payload/scripts/workflow_state_test.py`, `payload/scripts/workflow_integration_test.py`
(golden command-file hashes), `payload/scripts/workflow_fingerprint_generalization_test.py`,
`payload/.claude/commands/milestone-plan.md`, `apply-plan-review.md`,
`payload/docs/ai-workflow/PLAN_REVIEW_WORKFLOW.md`.

- `workflow_state`: `PlanGoverningVersionSweepError`, `PLAN_SWEEP_NEXT_STEP`,
  `_PLAN_EARLY_CHECK_ERRORS`, `assert_plan_governing_version_sweep` (D-Sweep).
- `prepare-ai-review.sh`: the existing early-anchor Python block also calls the
  sweep, on the pinned bytes, and catches `_PLAN_EARLY_CHECK_ERRORS`.
- The four command steps name the sweep call right after the anchor call, with
  the same refusal text shape (`error: PlanGoverningVersionSweepError: ...`).
  `/milestone-plan` also tells the author not to write a list of governing
  versions in the plan (say a feedback-only item or a two-stage item).
- `PLAN_REVIEW_WORKFLOW.md`: one paragraph beside the anchor paragraph.
- `workflow_state_test.py`: the worker source gains `publish_atomically` in its
  own constant (D-Atomic) and the holder uses it.

**Tests:** unit — a plan under `docs/ai-workflow/` that carries an enumeration
the installed sweep flags is refused with the finding's line and form and the
next step; a clean plan passes; the exemption for a bound regeneration; a
non-two-stage item and a plan outside the corpus pass; a plan reading through
`pin_dir` is judged from the pinned bytes, not the working tree. Generator — a
`prepare-ai-review.sh` run on such a plan exits 1 with the error, leaves the
previous `current/`, archive and `.pin` untouched and writes no `REJECTED`
marker, beside the 2.11.0 anchor generator tests. Publish and bind steps: the
command files name the call (the existing pattern for the anchor call). Atomic
ready file — `publish_atomically` is exercised with an observing `os.replace`:
the destination does not exist before the replace and the temporary file holds
the complete text at that moment; the real-process test passes unchanged.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Stage baselines: record what the manual stage last reviewed

**Files:** `payload/scripts/workflow_fingerprint.py`, `payload/scripts/workflow_state.py`,
`payload/scripts/workflow_fingerprint_generalization_test.py`,
`payload/scripts/workflow_state_test.py`,
`payload/docs/ai-workflow/REVIEW_PROTOCOL.md`.

- `workflow_fingerprint`: `STAGE_BASELINE_DIR`, `record_stage_baseline(repo_root,
  work_item_id, *, stage, role, verdict, review_content_id, bundle_id,
  revision, reviewed_implementation_head, classification, verdict_text, now) -> bool` and
  `read_stage_baseline(repo_root, work_item_id, role) -> dict | None` (D-Baseline,
  exact forms). The writer removes the role's old record, stages a sibling directory and
  renames it in; it catches its own errors, prints one warning and returns
  `False`, and never replaces a record with a higher `state_revision`. The reader
  applies every consistency rule of D-Baseline: at the plan stage the recomputed
  `pin/` id (`compute_review_content_id_plan_stage_from_pin`), at the
  implementation stage the recomputed content id of the reachable saved head,
  each fed the record's own `revision` and `classification` and the item's
  `base_commit` (D-Baseline's recomputation inputs, so a plan-revision bump or a
  declaration change does not invalidate it), and at both the stored verdict's identity, role and status against the record, and
  the id being known to state; any mismatch returns `None` (full review, INV-3).
- `workflow_state._ingest_two_stage_manual_verdict`: inside the mutator, after
  its refusals and before returning the new state, calls the writer for a
  `REVISE` or `APPROVE` verdict, with the revision and head it already holds; an
  exception leaving the transaction removes the new record. A feedback-only row,
  a `BLOCK` and every refusal record nothing. The returned outcome is unchanged.
- `REVIEW_PROTOCOL.md`: the baseline directory, its files and its readers, in
  "Bundle location" beside the changes-file paragraph, with the trust boundary
  and the guarantee and limits of D-Keyed and D-Baseline: a reviewer aid, never
  a gate; the latest accepted manual verdict in supported operation; limits (a)
  and (b), and the deletion on downgrade.

**Tests:** a manual `REVISE` and a manual `APPROVE` at each stage record a
baseline whose fields are exactly the D-Baseline set, whose `VERDICT.md` equals
the stored feedback and (plan stage) whose `pin/` equals the item's `.pin`; a
`BLOCK`, a malformed verdict, a stale `review_content_id` and a feedback-only
row record none and leave an earlier baseline as it was; a second verdict
replaces the first; the reader returns `None` for each malformed form (a
missing file, a symlink, extra and missing keys, a foreign work item or role, a
bad id, a missing `pin/`); a write failure leaves the ingest's state published,
removes the earlier record (the next round is a full review) and prints one
warning, at both stages; two ingests in either order never leave the earlier
verdict's record; a reachable implementation head that differs from the recorded
content id, a verdict whose identity, role or status disagrees with the record,
and an id unknown to state each return `None` and give the full-review fallback; a plan-stage baseline recorded at revision N is read, and gives the manual section a basis, when the current generation is revision N+1; an implementation-stage baseline recorded before a change to `<id>-artifacts.json` is still read and recomputes to its recorded id (the classification is the record's, not the current one); `bundle_id` and `review_content_id` are identical with
and without the directory; the protocol's `record-external-result` records one
too (it shares the ingest).
<!-- /CP2 -->

<!-- CP3 -->
### CP3 — The changes file, per review stage

**Files:** `payload/scripts/workflow_fingerprint.py`, `payload/scripts/prepare-ai-review.sh`,
`payload/scripts/workflow_fingerprint_generalization_test.py`,
`payload/scripts/workflow_integration_test.py` (golden hashes),
`payload/.claude/commands/review-plan.md`, `review-implementation.md`,
`record-manual-plan-review.md`, `record-manual-implementation-review.md`,
`milestone-plan.md`, `apply-plan-review.md`, `apply-implementation-review.md`,
`payload/docs/ai-workflow/REVIEW_PROTOCOL.md`, `PLAN_REVIEW_WORKFLOW.md`,
`IMPLEMENTATION_REVIEW_WORKFLOW.md`.

- `_render_changes_since_review` renders the D-Keyed layout from a list of
  sections; `_plan_stage_changes` and `_implementation_stage_changes` become two
  section builders each (local, manual) behind one `write_changes_since_review`,
  which keeps its signature, catches each section's error separately (a failed
  section is "the previous round cannot be identified"), and writes the file
  when at least one section has a basis. The plan-stage diff loop is shared by
  both sections; the implementation diff takes the old head as a parameter.
- `prepare-ai-review.sh`: unchanged call shape; the same-content republication
  and wrapper-only rules stay as they are.
- The command texts: `/review-plan` and `/review-implementation` say "read the
  section named for your role"; the `REVIEW_REQUEST.md` sentence (the three
  commands that write it) says the same; the two `/record-manual-*` commands
  say the manual reviewer's section is its own. `Review scope: changes` rules
  are unchanged.
- The docs: the file's layout, the two bases and the full-review fallback
  (D-Keyed, D-Baseline's consequence).

**Tests:** through the real generator, at both stages — (a) a local round 2 is
as today (basis, findings, the consumed check) with the section headings; (b)
the reported defect: local round 1, manual `REVISE`, then a local round
`REVISE`, then a regeneration: the manual section diffs from the manual
baseline's content and quotes the manual verdict, while the local section diffs
from the last generation and quotes the last local verdict; (c) a manual round
with no baseline prints `not available (no previous review of this stage is
recorded): review the whole bundle.`, and the file is still written for the
local section; (d) no basis in either section deletes the file; (e) a baseline
whose id equals this generation's id gives no manual section; (f) a corrupt
baseline, a missing `pin/` or an unreachable head fails only that section; (g)
the wrapper-only carry-forward keeps both sections, and the archive carries
the file with a `stage:` line; (h) `bundle_id` and `review_content_id`
identical with and without the file and the directory; (i) the implementation
manual section's baseline id is recomputed on the recorded classification and its
diff paths are the union of the recorded and the current protected
classifications where the declaration changed since (the section is available,
not the fallback): after an implementation baseline is recorded, amending the
declaration to protect a previously excluded file and changing that file keeps
the baseline valid, and the manual section includes that file's edits; (j) the golden command-file
hashes.
<!-- /CP3 -->

<!-- CP4 -->
### CP4 — The Manager metadata block: tools and CI

**Files:** `tools/release/manager_block.py` (new), `tools/release/release.py`,
`tools/release/release_test.py`, `.github/workflows/workflow-ci.yml`,
`docs/RELEASING.md`.

- `manager_block.py` (stdlib only): `validate(block)` (contract, schema 1, the
  closed detector vocabulary; exact messages naming the key), `measure_suites(fixture)`
  (the nine suites listed by the managed template; one subprocess per fixture,
  cwd `scripts/`, bytecode off, the loader `unittest.main()` uses, loader errors
  refused), `check(manifest, version, measured, manager_releases)` returning
  the list of problems for checks (a), (b), (c), (e) of D-Manager.
- `release.py`: `manager-block (--commit REF | --release-dir DIR) [--write]` and
  `check-manager-block --commit REF --manager-releases FILE` (checks (a), (b), (c),
  (e), (g)); exit codes as the
  other subcommands. `--release-dir DIR` measures a directory staged from the
  working tree whose digests are already refreshed, through the same
  `package.stage_conformance` as `--commit`, so CP5 can measure its own content
  before its commit exists. `--write` refuses a manifest at 2.12.0 or older.
- `release.py`: also `record-manager-releases`, `compare-manager-releases` and
  the `update-fixture` helper (D-Manager); `tools/release/manager-releases.json`
  (new, the committed evidence) (`manager-pin.json` is advanced in CP5).
- CI: `check-manager-block --commit HEAD --manager-releases
  tools/release/manager-releases.json` (offline), the live `compare-manager-releases`
  step (never fails on unavailability) and the `update-fixture` step (the
  `tooling` block).
- `RELEASING.md`: the authored and computed fields, the command, the CI check
  and what it does not check (D-Manager).
- The workflow-ci step list in this file's header comment is updated.

**Tests:** `release_test.py` — each contract rule has a passing and a failing
manifest (a missing `schema_version`, another schema, an unknown detector kind,
a bad signal name, `conformance` with only one of its two keys, `suites` with a
negative or boolean count, a malformed version string, `min_manager_version`
newer than the newest published Manager; a release list holding a prefixed tag
(`workflow-manager-v1.0.0`), a draft and a prerelease, none of which counts; the
exact record format with `isPrerelease`, a record lacking it refused, validation
passing with no network, and `compare-manager-releases` reporting consistent,
snapshot behind and unavailable as three distinct outcomes; a pin differing from
`min_manager_version` refused; the update fixture, on a synthetic previous
release and candidate, bootstraps, updates with the pinned Manager and runs the
frozen suites in the result); a block in a manifest at 2.12.0 or
older is refused and a missing block in a newer manifest is refused;
`measure_suites` on a small synthetic suite directory counts what `unittest`
loads, refuses a loader error and ignores a `*_demo_test.py` file; measured
against the published 2.12.0 release (staged from its tag), the nine counts
equal the `Ran N tests` totals of a plain `python3 -m unittest -v` run of each
suite in that same fixture (an independent cross-check of the counting method,
run once and recorded in the checkpoint's commit message, not a standing test;
the Manager holds no per-release suite table to compare with); `manager-block
--release-dir` on a tree equals `--commit` on a commit of the same tree; `--write` replaces only `suites`, keeps every other byte of the manifest
and refuses an old manifest.
<!-- /CP4 -->

<!-- CP5 -->
### CP5 — Release 2.13.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`
(`WORKFLOW_RELEASE`), `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (tested releases and the
envelope example), `docs/release-history.md`, `docs/common-problems.md`,
`docs/gates.md`, `tools/release/manager-releases.json`,
`tools/release/manager-pin.json` (advanced to 1.13.0 here, once that Manager release is published).

- `manifest.json` 2.13.0 with every digest and size refreshed, rationale text
  updated on the changed records, `counts` unchanged unless a file is added, and
  the authored `manager` block (D-Manager's values); `suites` filled in
  one commit, in this order: (1) make every other CP5 edit and refresh each
  digest and size in the working tree; (2) stage the working tree to a scratch
  directory outside the repository; (3) run `release.py manager-block
  --release-dir <that directory> --write`, which measures CP5's own content and
  writes `suites`; (4) make the single CP5 checkpoint commit. No hand-written
  count, second commit or amend. `check-manager-block --commit HEAD` then
  re-measures the committed tree as check (b) and must agree.
- `WORKFLOW_RELEASE = "2.13.0"`; the release-version assertions in
  `workflow_protocol_test.py`; the protocol stays 1.4 and says so in the
  tested-releases note.
- `docs/release-history.md`: a 2.13.0 row with D-Downgrade's paragraph, the
  `manager` block sentence (what is authored, what is computed, the minimum
  Manager) and the three closed issues (workflow#35, #32, #30 part 1; part 2 stays
  open).
- `docs/common-problems.md`: "A plan is refused before review because of a list
  of governing versions", with the one next step. `docs/gates.md` is touched
  only if a sentence there contradicts the section-per-stage file.

**Verification:** the nine suites pass in a stock `release.py stage-conformance`
fixture; `release.py build` of the commit succeeds; `check-manager-block` is
clean against the committed evidence (Manager 1.13.0 published and recorded); the
`update-fixture` step passes from the v2.12.0 bootstrap through the 1.13.0 update;
`tools/docs/check_docs.py` is clean; `workflow-manager verify .` is clean; the
tools tests pass in the zlib-ng venv.
<!-- /CP5 -->

## 6. Tests and verification summary

The nine payload suites run from a staged conformance fixture, the
`tools/release` tests run in the zlib-ng venv, and every new behaviour has its
test in the checkpoint that adds it. The public interface under test is the
real generator (`prepare-ai-review.sh`) and the real ingest, not private helpers.
`tools/docs/check_docs.py` covers the documentation pages this release edits.

## 7. Risks

- **A baseline written, then the item moves on.** The record is keyed by role,
  removed and replaced under the ingest lock by the next verdict, and read only
  when self-consistent (D-Baseline), so in supported operation a stale or
  inconsistent one yields a full review. Not detected, and declared as limits:
  an operator-edited or restored baseline file, and a baseline kept across a
  downgrade, manual review and re-upgrade (D-Downgrade says to delete it). Either
  can give a wrong basis to a `REVISE` round, costing efficiency only: the
  changes file is never a gate and every `APPROVE` is a full review (D-Keyed).
- **A manual section for content the reviewer never saw.** The baseline is
  written only for a verdict the ingest accepted against the bound, verified
  bundle (the preconditions the ingest already enforces).
- **Doubled file size** when both sections share a basis (an implementation
  diff twice). Accepted: the file is gitignored convenience and the tarball
  already holds `DIFF.patch`.
- **The sweep is stricter than review.** A plan that reached pull-request time
  clean is unaffected; a plan the sweep flags is refused earlier, which is the
  point. The sweep itself is unchanged.
- **CI check (c) is red until Manager 1.13.0 is published and recorded.** Intended (OD-5);
  the order of owner steps is Manager release, then this pull request's merge.
- **Counting method drift** between `tools/release` and the Manager's
  inventory: cross-checked once against 2.12.0's published counts (CP4).

## 8. Requirements

| id | requirement | checkpoints |
| --- | --- | --- |
| R1 | A manual external review round compares against the content that stage last reviewed and quotes that stage's own last verdict; a local round is unchanged; plan and implementation stages; the file and the baselines stay outside `bundle_id` and `review_content_id` and nothing is persisted in state | CP2, CP3, CP5 |
| R2 | The real-process test no longer reads a half-written ready file | CP1, CP5 |
| R3 | A plan revision the installed governing-version sweep would reject is refused when published, bound or turned into a bundle, with one rule, one error shape and one next step; existing approved and bound plans keep working | CP1, CP5 |
| R4 | The release carries a valid `manager` block (authored fields, computed suite counts) and CI checks it against the contract | CP4, CP5 |
| R5 | Release 2.13.0: manifest, release constant, release assertions, release history and the downgrade paragraph; the Orchestration Protocol stays 1.4 | CP5 |

## 9. Artifact classification

`docs/ai-workflow/registry/review-loop-fixes-artifacts.json`: the generated
template, plus one declared change. At the plan stage the plan
(`docs/ai-workflow/REVIEW_LOOP_FIXES_PLAN.md`), the registry and the mapping
are protected; `payload/`, `fixtures/`, `templates/`, `tools/`, `manifest.json`,
`docs/release-history.md`, `docs/common-problems.md`, `docs/RELEASING.md`,
`docs/gates.md`, `docs/glossary.md` and `.github/` are excluded
(implementation deliverables or repository-wide territory). At the
implementation stage `payload/`, `fixtures/`, `templates/`, `tools/`,
`manifest.json` and those five documents (`release-history`, `common-problems`, `RELEASING`, `gates`, `glossary`) are protected, with the declaration
itself; and `.github/workflows/workflow-ci.yml`, a deliverable of CP4, is moved
into `implementation_stage.protected_paths` as an exact path (the template
excludes the `.github/` prefix at both stages; an exact protected path is
checked first). `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md` and
`docs/ai-workflow/` stay excluded. Every path section 5 names is covered at both
stages, including the plan file itself and the new `tools/release/manager_block.py`
(under the `tools/` prefix).

## 10. Revision history

| revision | change |
| --- | --- |
| 1 | First plan. |
| 2 | Round 1 `REVISE` (local, `anthropic/claude-opus-5-5`), content `5d2edad4…`. Important (CP5 cannot measure `suites` from a commit that does not exist; `--commit` runs `verify_release`): **accepted**; `manager-block` gains `--release-dir DIR` (D-Manager, CP4, CP4 tests) and CP5 states a four-step sequence ending in one commit. Optional: baseline `pin/` recomputed by the reader: **accepted** (CP2); CP1 lists `workflow_integration_test.py`: **accepted**; 2.12.0 reference counts: **accepted**, cross-checked against each suite's own `Ran N tests` (CP4), the Manager having no such table; check (c) tag parsing: **accepted** (exact `vX.Y.Z`, no draft or prerelease) with its test; authoring location: **accepted**, stated as a deliberate departure (D-Manager); sibling corpus sweep: **accepted**, listed in the non-goals. Missing tests: both added to CP4. No checkpoint added, removed or renamed. |
| 3 | Round 2 `REVISE` (manual external, `openai/gpt-6.1-sol`), content `31db38ff…`. Important 1 (inconsistent implementation baseline): **accepted**; the reader recomputes the saved head's content id and checks the stored verdict's identity, role and status (D-Baseline, CP2 and tests). Important 2 (failed or delayed write keeps a wrong round): **accepted**; the write moves inside the ingest's state lock, invalidates first, never regresses by `state_revision`, and any failure falls to a full review (D-Baseline, CP2). Important 3 (update fixture omitted): **accepted**; check (f) is built with the released minimum Manager, plus check (g) (D-Manager, OD-5, CP4, CP5). Important 4 (CI evidence): **accepted**; complete records including `isPrerelease` in a committed snapshot validated offline, with a separate live comparison distinguishing unavailable from unsatisfied (D-Manager, CP4, CP5). Missing tests added to CP2 and CP4. No checkpoint added, removed or renamed. |
| 4 | Round 3 `REVISE` (manual external, `openai/gpt-6.1-sol`), content `c238f406…`. Important 1 (a self-consistent baseline need not be the latest manual verdict): **accepted in part**. Accepted: the first-round claim is corrected (D-Baseline's consequence), and the boundary is declared — the changes file is a reviewer aid, never a gate (D-Keyed's trust boundary, CP2's `REVIEW_PROTOCOL.md` text, section 7, D-Downgrade, which now tells the operator to delete `review-baselines/` on downgrading). Rejected: independent provenance evidence. It needs a new persisted field (INV-1 forbids it) or a new detection heuristic, and buys no safety: the file stays outside `bundle_id` and `review_content_id` (INV-2) and an `APPROVE` declaring `Review scope: changes` is refused (`payload/scripts/workflow_fingerprint.py:3807`), so a wrong baseline costs efficiency, never approval; an edited or restored gitignored file and a downgrade/re-upgrade are declared limits (a) and (b). Missing tests: not added; they test the declared limits, and CP2 already tests what the writer and reader guarantee (consistency and the fallback). No checkpoint added, removed or renamed. |
| 5 | Round 4 `REVISE` (local, `anthropic/claude-opus-5-5`), content `52aeed27…`. Important 1 (the reader recomputed the id with today's inputs): **accepted**; `BASELINE.json` stores the `classification` sets, the reader recomputes with the record's `revision`, those sets and the item's fixed `base_commit`, so a plan-revision bump or a declaration change keeps the baseline, and CP3 test (i) now expects an available manual section on the recorded classification (D-Baseline, CP2, CP3). Both missing tests added to CP2. Optional: `manager-pin.json` named in CP5's Files: **accepted**; "five documents" in section 9: **accepted**; a sentence on the early sweep refusal in `request-plan-amendment.md`: **rejected**, it is in no checkpoint's Files and amended plans already pass through `prepare-ai-review.sh`, which carries the sweep; the release-history row carries the deletion instruction: **accepted**, CP5 requires D-Downgrade's paragraph there, which says to delete `review-baselines/`. No checkpoint added, removed or renamed. |
| 6 | Round 5 `REVISE` (manual external, `openai/gpt-6.1-sol`), content `d01d8610…`. Important 1 (recorded-only diff selection omits a newly protected path's edits): **accepted**; the recorded classification is kept only to recompute the baseline's content id, and the implementation diff selects its paths from the union of the recorded and the current protected classifications, as D-Keyed and `payload/scripts/workflow_fingerprint.py:3280` already do (D-Baseline, CP3 test (i)). Missing test (amend the declaration to protect a previously excluded file after a baseline is recorded, change it; the baseline stays valid and the manual section includes its edits): **accepted**, added to CP3 test (i). Optional (header said revision 4): **accepted**, corrected. The declared baseline boundary is unchanged. No checkpoint added, removed or renamed. |
