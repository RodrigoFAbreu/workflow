# Retention of finished work-item files

> For: maintainers who prune the files a finished work item leaves in the Workflow, Manager or Controller repository. Last checked with: Workflow 2.20.0.

Files of finished work keep piling up (#84): in the Controller repository, 43
finished work items leave about 240 tracked files and 140 MiB of untracked
review folders. This page is the retention rule, step 1 of #84. It is the same
rule for the three repositories: the Workflow, the Manager and the Controller.
For a work item that is finished, it says which tracked files stay in the
working tree and which move to the archive, and why the untracked review
folders are kept until their owner decides.

The rule itself changes no code, no state and no protocol. Step 2 is the
[retention report](#the-report) (roadmap row 27b, Workflow 2.20.0): a
read-only script that lists the finished items and their review folders and
archives. The command that archives a review folder (row 27c) and the prune of
old archives (row 27d) follow. The tracked-file command and the link check are
a later row, not yet scheduled. The last section says what that tooling must
guarantee.

A reader named `file:function` is in `payload/scripts/` of this repository,
unless the cell names another directory or a sibling repository. "Not
verified" means the code was not read far enough to settle the cell.

## Which items the rule applies to

A work item is **finished** when all three hold:

1. Its phase is `MILESTONE_COMPLETE`, and so is the phase of its parent and of
   every child.
2. The Workflow's own pull-request fact for the item says `merged`: a fact
   in the shape of `gate_evidence.pr`, with `provenance.source` equal to
   `workflow_gh`, and `state` equal to `merged`. This is the fact the reopen
   guard reads: `workflow_state.py:reopen_work_item` accepts a
   `MILESTONE_COMPLETE` item and refuses with `pr_merged` only when that
   fact's state is `merged`. Until then the item can still be reopened.
   Identical bytes on the default branch are not proof: a cherry-pick or
   another pull request can put them there while the item's own pull request
   is still open.
3. It is not one of the **N = 3** most recent items that meet 1 and 2,
   ordered by their `last_transition`. Every work item in the three state files has that
   field.

The stored fact is not enough on its own. It is written while the pull
request is reviewed, before the merge, and the normal completion flow does not refresh it afterwards (only an explicit `/apply-pr-review` can store a fresh one):
on 2026-10-25 every finished item's stored fact says `open` (21 here, 8 in
the Manager, 24 in the Controller) or is absent (4, 8 and 19). So the tooling
must take a fresh fact from the query `/apply-pr-review` runs
(`workflow_forge.py:query_forge_pr_facts`, which writes nothing). Whether it
also stores that fact, which is a state write
(`workflow_gate_policy.py:store_workflow_pr_fact`), is for the plan of a later
row, not yet scheduled (none of rows 27b to 27d stores it). An
item whose query fails, or finds no pull request, is not finished.

Every other work item is **open** for this rule, and the rule never touches
its files.

Why three: follow-up work usually starts from the last item or two, for
example the review follow-ups that ran one after another, and reads their
plans, evidence and review folders. Three covers that and costs little: the
largest review folders measured are 6 to 14 MiB, so three of them stay below
about 45 MiB.

## The rule

| Class | Path | Decision | Why: the reader |
| --- | --- | --- | --- |
| State entry | `work_items[<id>]` in `docs/ai-workflow/WORKFLOW_STATE.json` | **Stays** | The state is the ground truth. `workflow_protocol.py:op_verify` (check `state_valid`) runs `workflow_state.py:validate_state` over every entry, `tools/docs/check_docs.py:work_item_ids` reads the ids, and the Manager's `src/workflow_manager/compatibility.py` reads every entry. Removing an entry is a state change, which this rule does not make |
| Registry | `docs/ai-workflow/registry/<id>-registry.json` | **Stays** | `workflow_state.py:validate_state` reads the `registry_path` of every work item, finished ones included. The file must exist and be tracked, and its `work_item_id` and `plan_revision` must match the entry. Without the file, `verify` fails. The Manager's `compatibility.py:_registry_ids` reads it too |
| Plan | the entry's `plan_path`, usually `docs/ai-workflow/<NAME>_PLAN.md` | **Stays** | The state names it. `workflow_state.py:reopen_work_item` refuses (`reopen_plan_archived`) when it is missing while the item can still be reopened, and `workflow_fingerprint.py:resolve_plan_stage_metadata` reads it for the item's own plan stage. No reader was found once the pull request is merged, but the tooling never deletes a live path of the state (guarantee 2 below) |
| Requirement mapping | the entry's `mapping_path`, `docs/ai-workflow/requirements/<id>-mapping.json` | **Stays** | The state names it. `workflow_fingerprint.py:resolve_plan_stage_metadata` requires the file to be tracked for the item's own plan stage |
| Findings record | `docs/milestones/completed/<id>-findings.md` | **Stays** | The decision record: every Optional finding of the item, with its disposition. `workflow_state.py:write_finding_dispositions_record` writes it at acceptance and rewrites it at a re-acceptance. [Common problems](common-problems.md#acceptance-is-refused-because-an-optional-finding-has-no-disposition) sends readers to it, and `check_docs.py:work_item_ids` reads its name |
| Dispositions | `docs/ai-workflow/registry/<id>-dispositions.json` | **Stays** | The decision itself, which the findings record renders. `workflow_state.py:read_finding_dispositions` reads it at acceptance (and `--finding-dispositions` prints it). It is small: 61 KiB for 14 items here |
| Artifact declaration | `docs/ai-workflow/registry/<id>-artifacts.json` | **Moves** | The state names it only as a historical record, never as a live path (see [Historical and live references](#historical-and-live-references)): the item's `technical_approval.review_content_manifest` records its `exists`, `mode` and `blob` at approval time. Every live reader derives the path from the id (`workflow_fingerprint.py:artifacts_path_for_work_item`) and works on the item under review, approval or reopening (`resolve_plan_stage_metadata`, `workflow_gate_policy.py:identity_at`, `workflow_state.py:build_policy_approval_record`), which condition 2 rules out. The Manager's `compatibility.py:_item_findings` reads declarations only for items not at `MILESTONE_COMPLETE`. The tests of the three repositories build their own declarations and read no real one. Removing all 25 finished declarations in a scratch clone of this repository left `verify` healthy and `check_docs` green. The largest registry class: 642 KiB of the 728 KiB of these registry files here |
| Plan archive copy | `docs/milestones/completed/<NAME>_PLAN.md` | **Stays** | `/accept-milestone` step 5 copies the plan here so that a reopen can restore it (`reopen_plan_archived`). No Workflow code reads it after the merge, but `tools/docs/check_docs.py:work_item_ids`, and the same function in the Manager's and the Controller's `tools/check_docs.py`, takes every file name there as an internal id that user pages must not mention. Moving a copy fails no check: it silently drops the name from that check. The copy can move once `check_docs` also takes these names from the archive index (a later row, not yet scheduled: the historical-links row was dropped). Where `plan_path` no longer resolves (two finished items in the Manager, whose plans were moved here at acceptance), the copy is the only tree copy of the plan and stays in any case |
| Requirement ledger | `docs/ai-workflow/requirements/<id>-ledger.md` | **Moves** | No reader found by the reader scan below: none in `payload/scripts/`, the command files, `tools/`, the tests or the CI workflows of this repository, nor in the Manager's or the Controller's code, tests or CI. Three of this repository's six ledgers are managed files, outside the rule |
| Evidence record | `docs/ai-workflow/<NAME>_EVIDENCE.md`, declared in the item's artifact declaration | **Stays** | `tools/release/release_test.py` (`ConformanceTemplate.test_constants_are_the_outcome_the_evidence_selects`) reads `CONFORMANCE_SHARDING_EVIDENCE.md` to check the shipped sharding constants, and CI runs that file (`.github/workflows/workflow-ci.yml`, step `release_test.py`). Without the record the test fails with `FileNotFoundError`, while `verify` and `check_docs` stay green. The other two records here, `COMMAND_WORDING_EVIDENCE.md` and `INTERLEAVING_PINS_EVIDENCE.md`, have no reader in the scan, but a measured record is what a test pins, so the class stays whole. A later revision of this rule may move those two by name, after a fresh scan |
| Review folder | `.ai-review/<id>/` (untracked, one per worktree) | **Kept** until its owner decides | It holds author-written files that are never committed, so no history can recover them (see [What a review folder holds](#what-a-review-folder-holds)). Its readers work on an item under review (`workflow_fingerprint.py:resolve_bundle_dir`, `_pin_dir_for_work_item`, `record_stage_baseline`), so keeping it costs disk space only. The archival step in that section is an option for the owner, not the default |

**The reader scan.** A class moves only when a scan finds no reader of its
paths in `payload/scripts/` and the command files, in `tools/`, in every test
(`*_test.py` files and `tests/` directories), in the CI workflows
(`.github/workflows/*.yml`), and in the Manager's and the Controller's code,
tests and CI. A test that reads a path is a reader, even when it only checks
the file's content. This revision ran the scan on 2026-10-25, by searching for
each class's file names and path patterns. A reader found later moves the
class back to **Stays**.

### Historical and live references

A path in the state is either a live reference or a historical one:

- A **live** reference is a field that a reader opens in the working tree:
  `plan_path`, `registry_path` and `mapping_path`. Their classes stay.
- A **historical** reference is an entry of an approval record's
  `review_content_manifest` (in `plan_approval`, `technical_approval` and an
  amendment's `superseded_plan_approval`): the `exists`, `mode` and `blob`
  that the path had when the item was approved. It is a recorded fact and
  does not need the file. `workflow_state.py:build_approval_record` keeps it
  in the record.

The one reader that compares a manifest with the working tree is
`workflow_state.py:_assert_registry_covered_by_current_plan_approval`. It reads
`plan_approval`'s manifest only, when that item is accepted or its
implementation resumed (`complete_work_item`, `work_item_completion_status`,
`resume_implementation_state`, and `workflow_gate_policy.py:_acceptance_registry_requirement`).
A finished item reaches those again only through a reopen, which condition 2
rules out. Every other reader reads a manifest against a commit
(`assert_committed_plan_approval_closure`, `load_pre_amendment_snapshot`,
`_resolve_one_obligation`) or checks its shape (`validate_approval_record`).

The artifact declarations are named in `technical_approval` manifests only:
all 25 finished items here, and 43 entries each in the Manager and the
Controller, none in a `plan_approval` or amendment manifest. The manifests are
already out of date for many paths, without harm: of the 609 manifest entries
of finished items here, 429 differ from the working tree and one names a file
that no longer exists, and `verify` is healthy. So moving a declaration is
safe. A path that a `plan_approval` manifest names is safe only for a finished
item, for the same reason.

### What a review folder holds

The folder is not a copy of committed content. Deleting it loses:

- **Author inputs, never committed:** `plan-inputs/REVIEW_REQUEST.md`,
  `plan-inputs/TEST_RESULTS.md` and `plan-inputs/CONTEXT_FILES.txt`, which
  `/milestone-plan` and `/apply-plan-review` write there
  (`workflow_fingerprint.py:resolve_plan_review_inputs_dir`), and the
  implementation stage's `current/REVIEW_REQUEST.md`,
  `current/TEST_RESULTS.md`, `current/IMPLEMENTATION_SUMMARY.md` and
  `current/CONTEXT_FILES.txt`. The generator copies the author files into the
  bundle and its archive (`review-bundle.tar.gz`), which are no better
  preserved.
- **Review outcomes:** `feedback/REVIEW_FEEDBACK.md`, the full text of the
  last verdict, and `feedback/FUNCTIONAL_REVIEW.md`, the user's
  functional-review checklist with its results.
- **The reviewed snapshots:** `current/files/`, `DIFF.patch`, `COMMITS.txt`,
  `CHANGED_FILES.txt`, `PLAN.md`, `MANIFEST.md`, `.pin/`,
  `CHANGES_SINCE_REVIEW.md` and `AMENDMENT_DIFF.patch`. The squash merge
  keeps only the final files, so the content an earlier round reviewed is
  lost unless the forge still holds the branch's commits.

The state keeps less than every verdict. It keeps:

- `review_round_counts`: the number of `APPROVE` and `REVISE` verdicts per
  stage and role.
- The latest `APPROVE` ledger entry per stage and role: `bundle_id`, `round`
  and `completed_at`. Only when that gate is automatic does the entry also
  hold `verdict_sha256` and `run_ref`, and `reviewer_model` only when the gate
  also requires distinct models and the verdict declares one
  (`workflow_state.py:_ledger_entry`, `review_stage_audit`).
- The approval records, and, in releases that record them, the text of every
  Optional finding of an `APPROVE` or `REVISE` verdict, with its stage, role,
  round and review content id (`_record_optional_findings`).

So the state loses: every field of a `REVISE` verdict's ledger entry, since
it writes none (`record_local_implementation_review` and the other three
ledger writers); every `BLOCK` verdict, which writes nothing; each earlier
`APPROVE` entry, which a new ledger replaces; the hash and reviewer of every
verdict under a human gate; and the text of every Blocking and Important
finding.

So the default keeps the folder. The rule offers the owner one option
instead: write the folder to a tarball outside the working tree, for example
a tarball at `~/.local/share/workflow-archive/<repo>/<id>.tar.zst` (outside
every repository, the file [the report](#the-report) reads), check the archive
lists every file (`tar --zstd -tf`), and only then delete the folder. The
archive command (row 27c) writes that file. That decision belongs to
the owner of the folder's content, per repository, and is not part of the
archive commit.

Outside the rule (never touched by it):

- The **managed files** of the installation, the `managed` list of
  `.workflow-manager/installation.json`: 79 files, about 10.6 MiB, in each
  repository. They include `docs/ai-workflow/WORKFLOW_V2_PLAN.md` (3.1 MiB),
  `docs/ai-workflow/audit/`, `docs/ai-workflow/dry-run/`, and the registry and
  mapping files of the Workflow's own early work items. Only a Workflow
  release changes them, and `workflow-manager verify` checks them.
- The generated files: the state file itself, `WORKFLOW_CONFIG.json` and
  `docs/ACTIVE_MILESTONE.md`.
- Everything under `.ai-review/` that is not a finished item's folder:
  `runtime/` (the locks, journals and claims of
  [Concurrency invariants](CONCURRENCY_INVARIANTS.md)), and the top-level
  `archive/`, `feedback/` and `scenario-evidence/` of the Manager and the
  Controller. The Manager keeps each item's verdict files in its
  `archive/<id>/`. Who reads those three: not verified.
- Test fixtures: `fixtures/` here (release source, packaged by
  `tools/release/package.py`) and the Controller's `tests/workflow_releases/`
  (128 files, 8.4 MiB, read by its tests). They are test inputs, not
  work-item records.

## What each class weighs

Measured on 2026-10-25. Tracked files only, managed files excluded,
"files / KiB". This repository at Workflow 2.19.2, the Manager at its `main`,
the Controller at its milestone branch. The classes that move are marked.

| Class | Workflow (25 finished) | Manager (16 finished) | Controller (43 finished, 1 open) |
| --- | --- | --- | --- |
| State file (all entries) | 1 / 930 | 1 / 543 | 1 / 1296 |
| Registry | 25 / 25 | 16 / 100 | 43 / 116 |
| Plan at `plan_path` | 25 / 1601 | 14 / 1184 (2 no longer in the tree) | 43 / 3897 |
| Requirement mapping | 25 / 54 | 16 / 47 | 43 / 140 |
| Findings record | 14 / 165 | 5 / 38 | 12 / 142 |
| Dispositions | 14 / 61 | 5 / 15 | 12 / 43 |
| Artifact declaration (moves) | 25 / 642 | 16 / 409 | 43 / 1071 |
| Plan archive copy | 22 / 982 | 10 / 943 | 43 / 1517 |
| Requirement ledger (moves) | 3 / 110 | 2 / 99 | 0 |
| Evidence record | 3 / 85 | 0 | 0 |
| Review folders (untracked, kept) | not measured: this worktree has none, and the main checkout was not read | 12 folders / about 114 MiB | 35 folders / about 140 MiB |

What the rule frees is small: before keeping the three newest items, 28 files
(0.7 MiB) here, 18 files (0.5 MiB) in the Manager and 43 files (1.0 MiB) in
the Controller, and none of the review folders. The plan archive copies and
the evidence records stay because they have readers in `tools/`, and the
review folders are kept because they hold content no history has.

Freeing more needs changes this rule does not make:

- **A state-format change** so that the state stops naming a finished item's
  plan, registry and mapping as live paths: for example, the entry keeps
  their blobs as historical facts, and `validate_state` stops requiring the
  registry file of a `MILESTONE_COMPLETE` item. That would free the plans,
  registries and mappings (1.6, 1.3 and 4.1 MiB). A separate, planned item,
  not proposed here.
- **A ledger-format change** that writes one entry for every verdict
  (`APPROVE`, `REVISE` and `BLOCK`) with its round, hash and reviewer under
  every gate mode. That would remove one reason to keep the review folders;
  the author inputs would still need the owner's decision.
- **Tool changes:** `check_docs` reading the archived plan names from the
  index (a later row, not yet scheduled) frees the plan archive copies (1.0, 0.9 and 1.5 MiB), and a
  release test that no longer reads the evidence record frees that class.

## The archive is the default branch's history

The tracked files the rule moves are deleted from the working tree. The
archive is the default branch's own history. It is not a tag, an `archive/`
branch or a release asset.

- The history already holds every byte. A pull request is squash-merged, so
  the merged commit on the default branch carries the item's final files. A
  later commit that deletes them leaves them readable at that commit:
  `git show <commit>:<path>`.
- The history is permanent. This repository's `main` is protected with no
  deletion, no force-push and squash merges only ([Releasing](RELEASING.md)).
  The Manager's `CLAUDE.md` says its `main` is protected by a ruleset and
  merged by squash. The Controller merges by squash (its release history);
  that its `main` refuses a force-push is not verified. Where it holds, a
  commit on `main` is never rewritten.
- A tag per item would add nothing that history lacks, and would need a push
  for each item. This repository also keeps its tags for immutable releases.
- An `archive/` branch would hold the same bytes a second time, under a ref
  that can be moved or deleted unless it is protected too.
- A release asset is an upload to the forge, so it needs credentials and
  makes the record depend on the forge. It would be the only forge option for
  untracked files, but it would publish author content; the rule keeps those
  files, and the owner's option is a local tarball (see
  [What a review folder holds](#what-a-review-folder-holds)).

**The index.** One file, `docs/milestones/ARCHIVE.md`, gets one line per
archived item: the work item id, the commit on the default branch that last
holds its files, the date, and the moved paths. The file sits outside
`docs/milestones/completed/` on purpose: `check_docs.py:work_item_ids` takes
every Markdown file name there as a work-item id. A reader finds the item in
the index and runs `git show <commit>:<path>`, or opens
`https://github.com/RodrigoFAbreu/<repository>/blob/<commit>/<path>`.

## The report

```
python3 -I scripts/workflow_retention.py report [--json] [--archive-root DIR] [--ttl-days N] [--repo-root DIR]
```

It reports which work items of the repository are finished by the rule above
(the phase of the item, its parent and its children are `MILESTONE_COMPLETE`,
a fresh pull-request query says `merged`, and it is not one of the 3 most
recent), how large each one's untracked `.ai-review/<id>/` folder is, and
whether an archive of it exists at `<archive-root>/<repo>/<id>.tar.zst`
(default root `~/.local/share/workflow-archive`) and is older than the time to
live (`--ttl-days`, default 30, from 1 to 3650). The stored
`gate_evidence.pr` is ignored, because it is stale. An item whose query fails,
or finds no pull request, is not finished and appears in `not_finished` with a
reason; an item that is not at `MILESTONE_COMPLETE` is never queried.

**It writes nothing:** no archive, no removal, no state write, no stored fact.
Run as the command above it leaves no bytecode either. A program that imports
`workflow_retention` for `build_report` must set `sys.dont_write_bytecode =
True` (or run with `-B`) before the first import; otherwise Python may leave a
`__pycache__` in the scripts directory.

**The cost:** one forge query (`gh`) for each item at `MILESTONE_COMPLETE`, so
run it between work items.

`--json` prints one object, keys sorted, ending in a newline:

```
{"schema_version": 1, "kind": "<report kind>", "generated_at": "<UTC>", "repository": "<owner>/<name>",
 "archive_dir": "<path>", "ttl_days": 30, "keep_recent": 3,
 "finished":     [{"work_item_id", "last_transition", "pull_request": {"number", "url"},
                   "review_folder": {"present", "complete", "files", "bytes", "tracked_files"},
                   "archive": {"present", "readable", "bytes", "modified", "age_days", "prunable"}}],
 "kept_recent":  [{"work_item_id", "last_transition", "pull_request", "review_folder"}],
 "not_finished": [{"work_item_id", "phase", "reason"}],
 "archives":     [{"name", "work_item_id", "bytes", "modified", "age_days", "prunable", "item"}],
 "complete": true, "read_errors": [{"path", "error"}],
 "totals": {"finished", "finished_folder_bytes", "archives", "prunable"}}
```

A path that does not exist is absence; a path that exists and cannot be read
(permission denied, an I/O error) is not. The report never turns the second
into the first: the unreadable path is listed in `read_errors`, `complete`
is `false`, the folder's `review_folder.complete` or the archive's
`archive.readable` is `false`, the text form ends with an `INCOMPLETE`
section and a `warning: incomplete:` line goes to stderr. Sizes, archive
facts and the totals are then lower bounds, and an unreadable archive
directory is not evidence that there is no archive. The exit status stays 0:
the report was printed, and a caller reads `complete`.

An archive is `prunable` when its age in whole days (from the file's
modification time) is strictly greater than the time to live. `archives`
lists every `*.tar.zst` file in the archive directory, with `item` set to
`finished`, `recent`, `open` (the item exists but is not finished) or `other`
(no such item). `tracked_files` counts paths under the folder that Git tracks.
The reasons are `invalid_id`, `invalid_entry`, `open_phase`, `family_open`,
`no_anchor`, `no_pull_request`, `pr_not_merged:<state>` and
`query_failed:<code>`. Exit status 0 means the report was printed; 2 means a
refusal (`state_missing`, `state_invalid`, `repository_unknown`, `usage`). See
[Exit codes](exit-codes.md).

## What the later tooling must guarantee

The tooling that applies the rule to tracked files and links, a later row not
yet scheduled, must guarantee 1 to 6. The review-folder archive command (row
27c) keeps 1 (never touch an open item, here by the report's finished set),
the last sentence of 4 and 5:

1. **Never touch an open work item.** The tooling reads phases, parents and
   children from the state, and the merged fact from a fresh Workflow query
   (condition 2). Run between work items when possible. If an item
   is open, the dry run must show that the commit leaves the item's plan-stage
   and implementation-stage `review_content_id` unchanged, otherwise it
   refuses. A deleted file of another item must not change what an open item's
   review covers.
2. **Never delete what the state or a command still reads.** That covers
   every live path a state entry names (`plan_path`, `registry_path`,
   `mapping_path`), every managed or generated file, `.ai-review/runtime/`,
   and every path the reader scan finds a reader for. A path named only in a
   `review_content_manifest` is a historical reference and may move, but only
   for a finished item. The dry run runs, before and after the change,
   `verify`, `check_docs`, the repository's own `tools/` and docs tests (here
   `tools/release` and `tools/docs`, as CI runs them) and
   `workflow-manager verify`, and refuses if any of them gets worse.
3. **The archive commit holds the bytes.** For every moved path, the
   recorded commit is an ancestor of the default branch, and
   `git cat-file -e <commit>:<path>` succeeds with the same blob as the tree.
   This proves only that the bytes are archived, never that the pull request
   was merged: that is condition 2's fact.
4. **One commit.** The deletions, the index lines and the rewritten links go
   into one commit. It carries no Workflow trailer (`Workflow-Work-Item`,
   `Workflow-Checkpoint` and the others), so no discovery function reads it
   as a work-item event. The tooling deletes no review folder. If the owner
   takes the archival option, it happens outside the commit, in the current
   worktree only, after the tarball is written and its listing checked.
5. **Dry run by default.** Without an explicit apply flag, the command lists
   each path, its decision and its size, and changes nothing. Whether
   applying it is a user-only step is, for the archive command (row 27c), settled
by its roadmap row, and for the tracked-file command, for the plan of that
later row to decide.
6. **Links keep working.** In the same commit, every relative link to a
   moved path becomes a link to the blob at the index commit (the form
   `blob/<commit>/<path>`, which `check_docs` accepts). No stub file is left
   behind, since a stub is the clutter the rule removes. `check_docs` then
   refuses any relative link to an indexed path, in every tracked Markdown
   file outside the managed set, including the pages it skips today
   (`docs/ROADMAP.md`, `docs/RELEASING.md`). A managed page that links to a
   path blocks the move of that path, because managed pages cannot be edited
   by hand. The dry run also lists plain-text mentions of moved paths, for
   example a path in backticks in `docs/RELEASING.md`.
7. **The pile cannot regrow unnoticed.** A later row, not yet scheduled, warns
   when a finished item past the newest three still has a file the rule moves,
   and fails only above a limit that row's plan chooses. The report of row 27b
   does **not** implement this: it reports review-folder sizes and archives
   only, warns about nothing and chooses no limit.

## Not verified

- Whether the Manager's `verify` passes today with its two dangling
  `plan_path` values. It was not run, to keep that checkout untouched.
- Who reads the top-level `.ai-review/archive/`, `feedback/` and
  `scenario-evidence/` of the Manager and the Controller, and whether the
  Controller's own code reads a finished item's review folder. Its
  `controller/` package refers to `.ai-review` but was not read.
- Whether the forge keeps the branch commits of a squash-merged pull request,
  which would preserve a review folder's earlier snapshots.
- That the Controller's `main` refuses a force-push (see
  [The archive](#the-archive-is-the-default-branchs-history)).
- The size of this repository's review folders (see the table).
