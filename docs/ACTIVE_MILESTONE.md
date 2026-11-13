# Active Milestone

## Milestone

**Implementing, CP2 complete (all checkpoints done), self-review and verification next.** W49: `docs-restamp` (`process`, governing version `2.2`), branch `milestone/docs-restamp`,
roadmap row 42 (RodrigoFAbreu/workflow#147, the stamps part). The plan is `docs/ai-workflow/DOCS_RESTAMP_PLAN.md`
(revision 4, the owner's amendment, approved by gate policy).

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
- Revalidated after the amendment (revision 4): CP1's content is unchanged and still holds (`tools/docs` tests and
  `check_docs.py` pass; offline flows 2 to 7, 9 and 10 behave as expected for the pre-CP2 state). Two stamps (the retention
  and concurrency pages) are pinned by frozen release tests, so CP2 restores them to their base text; the concurrency row stays.
- CP2 is complete: the stamps of `docs/RETENTION.md` (2.25.6) and `docs/CONCURRENCY_INVARIANTS.md` (2.19.2) are back to their
  base text (frozen release tests pin them); `docs/RETENTION.md` has no diff against the base commit and the concurrency
  page's diff is exactly the added row. Final state: seven moved stamps. Checked: `tools/docs` tests, `check_docs.py`,
  `check-manager-block`, and the whole `tools/release` suite (328 tests, Python 3.12 with the pinned zlib-ng wheel) pass.
- Self-review after CP2: row 42 of the roadmap still described CP1 as first done (one checkpoint, and the retention and
  concurrency pages among the stamps moved to 2.29.3). It now says two checkpoints, seven moved stamps, and that those two
  pages were re-checked but keep 2.19.2 and 2.25.6 because frozen release tests pin them.
- Self-review, flow 5: the gates sentence followed D-Fix's wording but did not contain the phrase flow 5 checks for
  (`latest run of each check`, `GATE_POLICY.md`'s own words), so flow 5 printed `0` where the plan expects `1`. The sentence
  keeps D-Fix's wording and is now introduced with `GATE_POLICY.md`'s phrase.
- Next: the full verification of the plan and the implementation review bundle.

## Next action

Run `/milestone-implement docs-restamp` again (self-review, full verification, review bundle).
