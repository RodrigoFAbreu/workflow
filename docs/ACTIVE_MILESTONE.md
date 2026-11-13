# Active Milestone

## Milestone

**Self-reviewing the implementation, CP1 complete.** W49: `docs-restamp` (`process`, governing version `2.2`), branch `milestone/docs-restamp`,
roadmap row 42 (RodrigoFAbreu/workflow#147, the stamps part). The plan is `docs/ai-workflow/DOCS_RESTAMP_PLAN.md`
(revision 3, approved by gate policy).

## Goal

Every user page with a `Last checked with` line says the release it was really re-checked against. Docs only: no
`payload/`, `tools/` or behaviour change, so no release (a `docs:` pull request, impact none; the manifest keeps 2.29.3).

## Outcome

- CP1 is complete: nine pages re-read and re-stamped to Workflow 2.29.3 (Workflow Manager 1.18.1 on `README.md`, overview,
  install, gates and glossary; 1.18.1 is the latest release read with `gh release list`). Fixed: the README's wording of how
  the Manager installs, one sentence in `docs/gates.md` on the latest run of each check, a row for the retention engine's
  archive-directory lock in `docs/CONCURRENCY_INVARIANTS.md` (cells the code does not settle say `not verified`), and the
  roadmap (open-defects rows for #50 and #55 dropped, row 24 and row 27a statuses, row 42 added as `Current`).
- Checked in CP1: `tools/docs` tests and `check_docs.py` pass; the kept pages, `docs/RELEASING.md` and the release source
  have no diff against the base commit; every `file:function` reference on the two maintainer pages resolves.
- Self-review: the concurrency row's test cell said the `prune --apply` refusal was not verified, but
  `workflow_state_completion_obligations_test.py::RetentionPrune` (`test_p3b_the_lock_and_the_re_read_under_it`) holds the
  lock and expects `archive_busy`; the cell now names it.
- Next: the full verification of the plan, then the implementation review bundle.

## Next action

Run `/milestone-implement docs-restamp` again (step 2 onward).
