# Exit codes

> For: anyone who runs the Workflow's scripts by hand or from an orchestrator. Last checked with: Workflow 2.9.0.

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

Two scripts only tell success from failure. `prepare-ai-review.sh` documents
no status beyond 0 and 1, and `workflow_fingerprint.py` documents only 0, 1 and
the argument error 2. For `workflow_protocol.py` the envelope on standard
output is always printed, so read the envelope, not only the status.
