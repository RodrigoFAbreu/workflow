# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W39: `unclassified-path-message` (`process`, governing
version `2.2`), branch `milestone/unclassified-path-message`, roadmap row 34 (RodrigoFAbreu/workflow#146). The plan is
`docs/ai-workflow/UNCLASSIFIED_PATH_MESSAGE_PLAN.md` (revision 5, approved by gate policy); an archive copy is in
`docs/milestones/completed/`. The previous milestone, W38 `retention-report-unreadable` (Workflow 2.25.6), is complete.

## Goal

Workflow 2.25.7 (a `fix:` patch, released after the merge of pull request #153): an unclassified path is refused with a
message that names the path, the artifact-declaration file that must list it and the sanctioned route that adds it,
qualified by stage and phase. The class, where it is raised, who catches it and every exit code stay as they are.

## Outcome

- CP1 (the message, tests and page) and CP2 (release 2.25.7) are complete; the technical approval was recorded by policy.
- Functional flows 1 to 9 are recorded passed (flow 8 by an independent run; the skips are the suites' own version-gated
  guards). The 18 recorded Optional findings are dispositioned (7 follow-ups in RodrigoFAbreu/workflow#152, 5 fixed,
  6 dropped); see `docs/milestones/completed/unclassified-path-message-findings.md`.

## Next action

No milestone is scheduled. Every remaining roadmap row is waiting on the Controller or is later and unscheduled
(rows 12, 13, 24, 26c, 27). The release of 2.25.7 follows the merge of pull request #153. Pick the next item, then
`/milestone-plan`.
