# Exit codes

> For: anyone who runs the Workflow's scripts by hand or from an orchestrator. Last checked with: Workflow 2.25.5.

This is the one table of exit statuses for the scripts a person or an
orchestrator runs. Slash commands (such as `/milestone-plan`) have no exit
codes: they run inside a Claude session. Every row comes from the script's
code in `payload/scripts/` and the shipped documents.

| Script | Code | Meaning | What to do |
|---|---|---|---|
| `python3 scripts/workflow_protocol.py` | 0 | `ok: true`: the operation succeeded | read `result` in the JSON envelope; `verify` exits 0 even when `result.healthy` is `false` |
| | 1 | `internal_error`: an unexpected exception, also printed as a traceback on stderr | report it as a defect; the envelope is still printed |
| | 2 | `invalid_request`: bad arguments, or a malformed input document | fix the command line or the input |
| | 3 | a refusal with a stable error code, including `unsupported_protocol` | read `error.code` and `error.retryable` in the envelope; the codes are listed in [the protocol](../payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md#3-error-codes) |
| `./scripts/prepare-ai-review.sh` | 0 | the review bundle was generated | nothing |
| | 1 | a usage error (wrong arguments, a work item id that does not match the allowed pattern, a stage that needs an id), not inside a Git repository, a base that does not resolve, or a refusal while generating or finalizing the bundle | read the `error:` line on stderr and fix it; nothing is written when the round identity check refuses |
| | other non-zero | the script stops at the first failing step (`set -e`), with that step's status | read the output above it; no value other than 0 and 1 is documented |
| `python3 scripts/workflow_state.py --plan-review-publication-status <id>` | 0 | the publication status was printed as JSON | read it |
| | 1 | the plan-review binding is inconsistent: a JSON `error` and `message` are printed. Any other unexpected error also exits 1 with a traceback | follow the message; see the plan-review documents |
| | 2 | the arguments did not parse | give `--plan-review-publication-status <work-item-id>` |
| `python3 scripts/workflow_fingerprint.py` | 0 | the identifiers or the feedback path were printed, or the manifest or plan document was written | nothing |
| | 1 | `--finalize-bundle` found a problem (it prints `status:` and the reason), a required argument is missing (an `error:` line), or an unexpected error (a traceback) | read the output and fix the cause |
| | 2 | the arguments did not parse | check the options with `--help` |
| `python3 scripts/workflow_backlog.py` | 0 | the command succeeded, or the repository declares no backlog (`{"declared": false}`); `status` always exits 0 | read the JSON |
| | 1 | `check` found the roadmap page stale (`roadmap_stale`) | run `generate` and commit the page |
| | 2 | a refusal (`error: <code>: <message>` and `next step:` on stderr) or a usage error | follow the next step; the codes are in [the backlog file](../payload/docs/ai-workflow/BACKLOG_FILE.md#commands-and-exit-codes) |
| `python3 scripts/workflow_retention.py report` | 0 | the report was printed (also when some pull-request queries failed: those items are in `not_finished`, and also when some paths could not be read: `complete` is then `false`, `read_errors` lists them and `warning: incomplete:` is printed on stderr) | read it, and check `complete` before trusting a size or an absent archive; the command writes nothing |
| | 2 | a refusal (`error: <code>: <message>` and `next step:` on stderr: `state_missing`, `state_invalid` (also a state file that is not valid UTF-8), `repository_unknown` (also a tracked path under `.ai-review` that is not valid UTF-8), `usage`) or a usage error | follow the next step; the command is described in [the retention rule](RETENTION.md#the-report) |
| `python3 scripts/workflow_retention.py archive` | 0 | the dry run was printed (nothing was written), or the item was archived and the archive, the index line and every directory the run created are durable; the review folder is never touched | read it; run with `--apply` to archive |
| | 2 | a refusal (`error: <code>: <message>` and `next step:` on stderr). The report's codes (`state_missing`, `state_invalid`, `repository_unknown`, `usage`) and the archive's: `invalid_id`, `not_finished:<reason>`, `kept_recent`, `unknown_item`, `review_folder_absent`, `tracked_files`, `unreadable`, `archive_dir_unsafe`, `archive_inside_repository`, `path_unsafe`, `already_archived`, `already_indexed`, `index_invalid`, `index_unsafe`, `partial_present`, `unsupported_entry`, `zstd_missing`, `archive_busy` (never in a dry run), `pack_failed`, `verify_failed`, `folder_changed`, `place_failed`, `index_failed`. A stat error other than "not found" on an archive-directory entry is `unreadable`, never a traceback, and neither is a symlink in the review folder whose target cannot be read (`unreadable`, or `folder_changed` when it vanished). Every failure leaves the review folder as it was and the archive directory as it was | follow the next step; the command is described in [the archive command](RETENTION.md#the-archive-command) |
| `python3 scripts/workflow_retention.py remove` | 0 | the dry run was printed (nothing was written), or the review folder was verified against its archive and removed | read it; run with `--apply` to remove |
| | 2 | a refusal (`error: <code>: <message>` and `next step:` on stderr, nothing on stdout, `--json` included). The report's and the archive's codes, plus `not_archived`, `archive_mismatch`, `leftover_conflict`, `cross_device`, `remove_failed` and `restore_failed`. A refusal after the rename names the place the folder is in: its original place, a whole copy in `<archive-root>/<repo>/.removing/<id>`, or a smaller leftover there after a stopped delete. A stat error other than "not found" is `unreadable` (`restore_failed` while a refused verification is being undone), never a traceback; the same for a symlink in the review folder whose target cannot be read (`folder_changed` when it vanished), also while the folder is deleted | follow the next step and keep `.removing/<id>`; the command is described in [the remove command](RETENTION.md#the-remove-command) |
| `python3 scripts/workflow_retention.py prune` | 0 | the dry run was printed (nothing was written), or the named archives were removed, each one checked just before and the archive directory made durable; the index and every other file are never touched | read it; run with `--apply` to remove |
| | 2 | a refusal (`error: <code>: <message>` and `next step:` on stderr, nothing on stdout, `--json` included) or a usage error (no id, a bad `--ttl-days`). The report's and the archive's codes (`invalid_id`, `path_unsafe`, `state_missing`, `state_invalid`, `repository_unknown`, `archive_inside_repository`, `archive_dir_unsafe`, `unreadable`, `archive_busy`, `usage`) and the prune's: `not_in_report`, `removal_interrupted`, `not_prunable`, `item_not_finished`, `archive_changed` and `prune_failed`. A stat error other than "not found" is `prune_failed`, with the same lists. A refusal before the first unlink removes nothing; one after it names `removed:` and `not removed:` | follow the next step; the command is described in [the prune command](RETENTION.md#the-prune-command) |

Two scripts only tell success from failure. `prepare-ai-review.sh` documents
no status beyond 0 and 1, and `workflow_fingerprint.py` documents only 0, 1 and
the argument error 2. For `workflow_protocol.py` the envelope on standard
output is always printed, so read the envelope, not only the status.
