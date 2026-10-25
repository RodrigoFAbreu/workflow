# Retention of finished work-item files

> For: maintainers who prune the files a finished work item leaves in the Workflow, Manager or Controller repository. Last checked with: Workflow 2.19.2.

Files of finished work keep piling up (#84): in the Controller repository, 43
finished work items leave about 240 tracked files and 140 MiB of untracked
review folders. This page is the retention rule, step 1 of #84. It is the same
rule for the three repositories: the Workflow, the Manager and the Controller.
For a work item that reached `MILESTONE_COMPLETE`, it says which files stay in
the working tree, which move to the archive and which are deleted.

This page changes no code, no state and no protocol. Steps 2 to 4 (the
`verify` report, the command that applies the rule, and the link check) are
later roadmap rows. The last section says what they must guarantee.

A reader named `file:function` is in `payload/scripts/` of this repository,
unless the cell names a sibling repository. "Not verified" means the code was
not read far enough to settle the cell.

## Which items the rule applies to

A work item is **finished** when all three hold:

1. Its phase is `MILESTONE_COMPLETE`, and so is the phase of its parent and of
   every child.
2. Its pull request is merged into the default branch. Until then the item can
   still be reopened: `workflow_state.py:reopen_work_item` accepts a
   `MILESTONE_COMPLETE` item and refuses with `pr_merged` only once the pull
   request is merged. The proof is the archive commit (see
   [The archive](#the-archive-is-the-default-branchs-history)): every file the
   rule moves must be in a commit of the default branch, with the same bytes.
3. It is not one of the **N = 3** most recent items that meet 1 and 2,
   ordered by their `last_transition`. Every work item in the three state files has that
   field.

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
| Plan | the entry's `plan_path`, usually `docs/ai-workflow/<NAME>_PLAN.md` | **Stays** | The state names it. `workflow_state.py:reopen_work_item` refuses (`reopen_plan_archived`) when it is missing while the item can still be reopened, and `workflow_fingerprint.py:resolve_plan_stage_metadata` reads it for the item's own plan stage. No reader was found once the pull request is merged, but the tooling never deletes what the state names (guarantee 2 below) |
| Requirement mapping | the entry's `mapping_path`, `docs/ai-workflow/requirements/<id>-mapping.json` | **Stays** | The state names it. `workflow_fingerprint.py:resolve_plan_stage_metadata` requires the file to be tracked for the item's own plan stage |
| Findings record | `docs/milestones/completed/<id>-findings.md` | **Stays** | The decision record: every Optional finding of the item, with its disposition. `workflow_state.py:write_finding_dispositions_record` writes it at acceptance and rewrites it at a re-acceptance. [Common problems](common-problems.md#acceptance-is-refused-because-an-optional-finding-has-no-disposition) sends readers to it, and `check_docs.py:work_item_ids` reads its name |
| Dispositions | `docs/ai-workflow/registry/<id>-dispositions.json` | **Stays** | The decision itself, which the findings record renders. `workflow_state.py:read_finding_dispositions` reads it at acceptance (and `--finding-dispositions` prints it). It is small: 61 KiB for 14 items here |
| Artifact declaration | `docs/ai-workflow/registry/<id>-artifacts.json` | **Moves** | Not named by the state: `workflow_fingerprint.py:artifacts_path_for_work_item` derives the path from the id. Every reader works on the item under review, approval or reopening (`resolve_plan_stage_metadata`, `workflow_gate_policy.py:identity_at`, `workflow_state.py:build_policy_approval_record`). The Manager's `compatibility.py:_load_declarations` reads it for every item and takes an absent file as no declarations; what its report then says for that item is not verified. The largest registry class: 642 KiB of the 728 KiB of these registry files here |
| Plan archive copy | `docs/milestones/completed/<NAME>_PLAN.md` | **Moves**, but only while the plan at `plan_path` is in the tree | `/accept-milestone` step 5 copies the plan here so that a reopen can restore it (`reopen_plan_archived`). Here 21 of the 22 copies are byte-identical to the plan at `plan_path`. Where `plan_path` no longer resolves (two finished items in the Manager, whose plans were moved here at acceptance), the copy is the only tree copy of the plan and stays |
| Requirement ledger | `docs/ai-workflow/requirements/<id>-ledger.md` | **Moves** | No reader in `payload/scripts/` or the command files |
| Evidence record | `docs/ai-workflow/<NAME>_EVIDENCE.md`, declared in the item's artifact declaration | **Moves** | The item's own artifact declaration lists it as protected implementation-stage content, so it counts while that item is reviewed. No code reads it afterwards: grep of `payload/scripts/` and the command files finds no reader |
| Review folder | `.ai-review/<id>/` (untracked, one per worktree) | **Deleted** | Every reader works on an item under review (`workflow_fingerprint.py:resolve_bundle_dir`, `_pin_dir_for_work_item`, `record_stage_baseline`). The bundle, its archive, pin, plan inputs, baselines and changes file are copies of committed content. The verdict files are not copies: the state keeps each verdict's outcome, round, `verdict_sha256` and reviewer, and, from Workflow 2.14.0, every Optional finding's text. The text of a `REVISE` verdict's Blocking and Important findings is lost. That is accepted: the folder is gitignored scratch by design |

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
  [Concurrency invariants](CONCURRENCY_INVARIANTS.md)), and the Controller's
  top-level `archive/`, `feedback/` and `scenario-evidence/`. Who reads those
  three: not verified.
- Test fixtures: `fixtures/` here (release source, packaged by
  `tools/release/package.py`) and the Controller's `tests/workflow_releases/`
  (128 files, 8.4 MiB, read by its tests). They are test inputs, not
  work-item records.

## What each class weighs

Measured on 2026-10-25. Tracked files only, managed files excluded,
"files / KiB". This repository at Workflow 2.19.2, the Manager at its `main`,
the Controller at its milestone branch.

| Class | Workflow (25 finished) | Manager (16 finished) | Controller (43 finished, 1 open) |
| --- | --- | --- | --- |
| State file (all entries) | 1 / 930 | 1 / 543 | 1 / 1296 |
| Registry | 25 / 25 | 16 / 100 | 43 / 116 |
| Plan at `plan_path` | 25 / 1601 | 14 / 1184 (2 no longer in the tree) | 43 / 3897 |
| Requirement mapping | 25 / 54 | 16 / 47 | 43 / 140 |
| Findings record | 14 / 165 | 5 / 38 | 12 / 142 |
| Dispositions | 14 / 61 | 5 / 15 | 12 / 43 |
| Artifact declaration | 25 / 642 | 16 / 409 | 43 / 1071 |
| Plan archive copy | 22 / 982 | 10 / 943 | 43 / 1517 |
| Requirement ledger | 3 / 110 | 2 / 99 | 0 |
| Evidence record | 3 / 85 | 0 | 0 |
| Review folders (untracked) | not measured: this worktree has none, and the main checkout was not read | 12 folders / about 114 MiB | 35 folders / about 140 MiB |

What the rule frees, before keeping the three newest items: 53 files (1.8 MiB)
here, 28 files (1.4 MiB) in the Manager and 86 files (2.5 MiB) in the
Controller, plus nearly all of the review folders. The plans, registries and
mappings (1.6, 1.3 and 4.1 MiB) stay while the state names them. Freeing them
needs a state change that stops naming them: a separate, planned item, not
proposed here.

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
  makes the record depend on the forge. It would be the only option for
  untracked files, but the rule deletes those (they are copies, see the
  table).

**The index.** One file, `docs/milestones/ARCHIVE.md`, gets one line per
archived item: the work item id, the commit on the default branch that last
holds its files, the date, and the moved paths. The file sits outside
`docs/milestones/completed/` on purpose: `check_docs.py:work_item_ids` takes
every Markdown file name there as a work-item id. A reader finds the item in
the index and runs `git show <commit>:<path>`, or opens
`https://github.com/RodrigoFAbreu/<repository>/blob/<commit>/<path>`.

## What the later tooling must guarantee

Rows 27b (`verify` reports the clutter), 27c (a command applies the rule) and
27d (historical links keep working) must guarantee:

1. **Never touch an open work item.** The tooling reads phases, parents and
   children from the state. Run between work items when possible. If an item
   is open, the dry run must show that the commit leaves the item's plan-stage
   and implementation-stage `review_content_id` unchanged, otherwise it
   refuses. A deleted file of another item must not change what an open item's
   review covers.
2. **Never delete what the state or a command still reads.** That covers
   every path a state entry names (`plan_path`, `registry_path`,
   `mapping_path`), every managed or generated file, and `.ai-review/runtime/`.
   The dry run runs `verify` before and after the change and refuses if any
   check gets worse. It also runs `workflow-manager verify`.
3. **The archive commit holds the bytes.** For every moved path, the
   recorded commit is an ancestor of the default branch, and
   `git cat-file -e <commit>:<path>` succeeds with the same blob as the tree.
   This is also the proof that the pull request was merged.
4. **One commit.** The deletions, the index lines and the rewritten links go
   into one commit. It carries no Workflow trailer (`Workflow-Work-Item`,
   `Workflow-Checkpoint` and the others), so no discovery function reads it
   as a work-item event. Deleting untracked review folders is not part of
   the commit: it happens in the current worktree only, after the dry run
   has listed every folder.
5. **Dry run by default.** Without an explicit apply flag, the command lists
   each path, its decision and its size, and changes nothing. Whether
   applying it is a user-only step is for row 27c's plan to decide.
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
7. **The pile cannot regrow unnoticed.** Row 27b's `verify` check warns when
   a finished item past the newest three still has a file the rule moves, or
   a review folder. It fails only above a limit that row 27b's plan chooses.

## Not verified

- Whether the Manager's compatibility report changes for an item whose
  artifact declaration is gone. Guarantee 2 makes the dry run check it.
- Whether the Manager's `verify` passes today with its two dangling
  `plan_path` values. It was not run, to keep that checkout untouched.
- Who reads the Controller's top-level `.ai-review/archive/`, `feedback/` and
  `scenario-evidence/`, and whether the Controller's own code reads a
  finished item's review folder. Its `controller/` package refers to
  `.ai-review` but was not read.
- That the Controller's `main` refuses a force-push (see
  [The archive](#the-archive-is-the-default-branchs-history)).
- The size of this repository's review folders (see the table).
