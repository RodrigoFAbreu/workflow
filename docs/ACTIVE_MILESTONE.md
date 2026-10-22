# Active Milestone

## Milestone

**In progress** (implementing). W18: `review-followups-4` (`process`, governing version `2.2`),
branch `milestone/review-followups-4`, roadmap row 22 (RodrigoFAbreu/workflow#50). Plan:
`docs/ai-workflow/REVIEW_FOLLOWUPS_4_PLAN.md` (revision 7, approved by gate policy). The goal is
Workflow 2.18.4, a patch release (`fix:`). The previous milestone, W17 `review-followups-3`, is
accepted (its record is in git history and `docs/release-history.md`).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The managed conformance runs longest first | **complete** |
| CP2 | The unknown-id wording in the two command files | pending |
| CP3 | Release 2.18.4 | pending |

### CP1 verified state

- The managed conformance step (`templates/.github/workflows/workflow-conformance.yml`, and the
  same text in both steps of `.github/workflows/workflow-ci.yml`) builds its queue from a fixed
  `longest` list taken from measured durations, with the duration table in a comment; a name that
  is not a unit of the run is skipped, and every other unit keeps its order. The header says
  "longest first, in a fixed order taken from measured durations". `docs/RELEASING.md` says the
  same.
- `tools/release/release_test.py`: the stale `units[:2]` pins follow the new order; new tests pin
  the measured table (start order, width-4 simulation within 1% of the lower bound and 120 s under
  the old order), the names in `longest`, and the fallback for an emptied or unmatched list.
  Red first: 8 failures against the unedited step.
- Verified in a disposable clone (D-Staging); the results are in the implementation bundle.
