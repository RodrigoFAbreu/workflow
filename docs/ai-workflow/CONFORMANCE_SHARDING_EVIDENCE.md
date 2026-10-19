# Conformance sharding: measurement evidence

Deliverable of CP2 of `conformance-sharding` (plan `docs/ai-workflow/CONFORMANCE_SHARDING_PLAN.md`,
revision 5, sections 3.1 to 3.4; decision `D-Evidence-File`). Everything below was measured on
GitHub-hosted `ubuntu-latest` runners and read from the recorded job facts; nothing is estimated.
A number that was not measured is written as **not measured**.

## 1. Selected outcome

**Outcome O1: sharding is adopted. `width_cap` = 4, `shards` = 4 (variant v3).**

Produced by the kit's validator on the 45 recorded jobs (section 5, attached in full):
`status: decided`, `decision: {"G": {"v3": 0.8074226804123711}, "outcome": "O1", "shards": 4,
"undecided_not_chosen": ["v4", "v5"], "variant": "v3", "width_cap": 4}`. The rule is applied step
by step in section 8, from the per-runner-type tables of section 7, so that a reviewer can
recompute it from the step walls of section 6.

## 2. What was measured, and how

- Repository `RodrigoFAbreu/workflow`, throwaway branch `measure/conformance-sharding`, workflow
  `Measure conformance sharding`, which runs the managed step over this repository's tree, one job
  per variant and repetition, each on its own runner. Nothing was merged; the branch is not part of
  any release.
- Kit: generated from template ref `1023bce` (CP1) with `generate.py --base-ref 971ea16`.
  Variants (plan section 3.1): v1 = the control, the 2.15.0 step text with only the `start` line
  changed (W 4, N 0); v3 = W 4, N 4; v4 = W 4, N 8; v5 = W 3, N 4. No width-2 variant was measured in
  this revision (not measured).
- Per job: `nproc`, CPU model and image version from the `Record the runner` step
  (`MEASURE-FACTS`); the peak of units running at once is the largest `K` of the step's
  `start <unit> running K` lines; the step wall is the `Run the conformance suites` step's
  `completedAt` minus `startedAt` (GitHub job facts); each unit's seconds are the step's
  `done <unit> exit S in Ns` lines; the coverage line is the step's `coverage: expected T, recorded T`
  (candidates only; the control prints none). Parsing is `kit/collect.py`.
- Every one of the 45 jobs of rounds 0 to 3 concluded `success` (`gh run view`: 12, 12, 12 and 9 jobs
  successful). No run failed a gate.

## 3. The first measurement (run 39176546521, revision 4's rule): inconclusive, not counted

Branch commit `72b8d6995830e973ef0c6361df7c2d543f0b043a`; records kept outside the repository
(`~/scratch-conformance-sharding/records.json`). All 12 jobs succeeded and every sharded job
recorded 415 of 415 test ids. Under revision 4's rule the validator reported **inconclusive**: V2,
no (`nproc`, CPU model, image) triple was held by more than half of the jobs. CPU models: AMD EPYC
7763 on five jobs, AMD EPYC 9V74 on three, Intel Xeon Platinum 8573C on three, AMD EPYC 9V45 on one;
every job had `nproc` 4 and image 20261012.334.1.

| job | CPU model | peak | step wall s | coverage |
|---|---|---:|---:|---|
| v1-a | AMD EPYC 7763 | 4 | 1197 | none (control) |
| v1-b | Intel Xeon Platinum 8573C | 4 | 1031 | none (control) |
| v2-a | AMD EPYC 9V74 | 2 | 972 | none (control) |
| v2-b | AMD EPYC 9V74 | 2 | 995 | none (control) |
| v3-a | AMD EPYC 9V45 | 4 | 620 | expected 415, recorded 415 |
| v3-b | AMD EPYC 7763 | 4 | 994 | expected 415, recorded 415 |
| v4-a | AMD EPYC 7763 | 4 | 1033 | expected 415, recorded 415 |
| v4-b | Intel Xeon Platinum 8573C | 4 | 832 | expected 415, recorded 415 |
| v5-a | Intel Xeon Platinum 8573C | 3 | 747 | expected 415, recorded 415 |
| v5-b | AMD EPYC 7763 | 3 | 985 | expected 415, recorded 415 |
| v6-a | AMD EPYC 9V74 | 2 | 952 | expected 415, recorded 415 |
| v6-b | AMD EPYC 7763 | 2 | 1144 | expected 415, recorded 415 |

Its runs do **not** count toward revision 5's rule (plan section 3.4): the rule was fixed after those
numbers were seen, there were two repetitions per variant and one same-CPU pair at most. Per-unit seconds of
that run are not in this file (not recorded here); the CPU models above are abbreviated.

## 4. Revision 5's rounds

| round | kind | run id | branch commit | jobs | variants enabled |
|---:|---|---|---|---:|---|
| 0 | first round | 39182957834 | `14d393cb345cf4bf5f0b7dd74aefa8d45fc2217f` | 12 | v1, v3, v4, v5 (a, b, c) |
| 1 | top-up 1 | 39185861409 | `65c718e0f7df775563a30847db85557117ba9479` | 12 | v1, v3, v4, v5 (an empty commit: the generated workflow was byte-identical) |
| 2 | top-up 2 | 39188812102 | `7735cea52a0197cf600235f725d4d8a1fa8bb2dd` | 12 | v1, v3, v4, v5 |
| 3 | top-up 3 | 39191598752 | `eb09a53696d2b7a9977bf7375a1db3ba307d15de` | 9 | v1, v4, v5 (v3 had passed after round 2) |

Four rounds, the first and three top-ups (the bound of plan section 3.3). Top-up rounds were
requested by the validator's `status: topup` after each round while a candidate was undecided; runs
were never chosen or dropped. A run was never replaced one by one.

Runs per variant: v1 12 (rounds 0 to 3), v3 9 (rounds 0 to 2), v4 12, v5 12; 45 in all.

## 5. The validator's output (attached in full)

Command: `python3 ~/scratch-conformance-sharding/kit/validate.py ~/scratch-conformance-sharding/records-r5.json`
(kit read-only; the records are reproduced in section 10). Output, unedited:

```text
round 0 v1-a run 39182957834 wall 1203.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 0 v1-b run 39182957834 wall 1191.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 0 v1-c run 39182957834 wall 1174.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 0 v3-a run 39182957834 wall 787.0s [nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1]: valid
round 0 v3-b run 39182957834 wall 963.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 0 v3-c run 39182957834 wall 986.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 0 v4-a run 39182957834 wall 629.0s [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1]: valid
round 0 v4-b run 39182957834 wall 982.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 0 v4-c run 39182957834 wall 958.0s [nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1]: valid
round 0 v5-a run 39182957834 wall 1006.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 0 v5-b run 39182957834 wall 980.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 0 v5-c run 39182957834 wall 984.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 1 v1-a run 39185861409 wall 1223.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 1 v1-b run 39185861409 wall 1238.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 1 v1-c run 39185861409 wall 877.0s [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1]: valid
round 1 v3-a run 39185861409 wall 979.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 1 v3-b run 39185861409 wall 979.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 1 v3-c run 39185861409 wall 791.0s [nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1]: valid
round 1 v4-a run 39185861409 wall 998.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 1 v4-b run 39185861409 wall 987.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 1 v4-c run 39185861409 wall 797.0s [nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1]: valid
round 1 v5-a run 39185861409 wall 820.0s [nproc=4 cpu=INTEL(R) XEON(R) PLATINUM 8573C image=20261012.334.1]: valid
round 1 v5-b run 39185861409 wall 990.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 1 v5-c run 39185861409 wall 983.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 2 v1-a run 39188812102 wall 1222.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 2 v1-b run 39188812102 wall 790.0s [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1]: valid
round 2 v1-c run 39188812102 wall 1022.0s [nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1]: valid
round 2 v3-a run 39188812102 wall 575.0s [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1]: valid
round 2 v3-b run 39188812102 wall 1014.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 2 v3-c run 39188812102 wall 637.0s [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1]: valid
round 2 v4-a run 39188812102 wall 965.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 2 v4-b run 39188812102 wall 767.0s [nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1]: valid
round 2 v4-c run 39188812102 wall 973.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 2 v5-a run 39188812102 wall 997.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 2 v5-b run 39188812102 wall 1001.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 2 v5-c run 39188812102 wall 858.0s [nproc=4 cpu=Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz image=20261012.334.1]: valid
round 3 v1-a run 39191598752 wall 1183.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 3 v1-b run 39191598752 wall 1188.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 3 v1-c run 39191598752 wall 1215.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 3 v4-a run 39191598752 wall 995.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 3 v4-b run 39191598752 wall 958.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 3 v4-c run 39191598752 wall 1019.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 3 v5-a run 39191598752 wall 614.0s [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1]: valid
round 3 v5-b run 39191598752 wall 1008.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
round 3 v5-c run 39191598752 wall 985.0s [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1]: valid
cell v1 [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1] n=9 M=1203.0 V4 ok
cell v1 [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1] n=2 M=833.5 V4 ok
cell v1 [nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1] n=1 M=1022.0 V4 ok
cell v3 [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1] n=5 M=979.0 V4 ok
cell v3 [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1] n=2 M=606.0 V4 ok
cell v3 [nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1] n=2 M=789.0 V4 ok
cell v4 [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1] n=8 M=984.5 V4 ok
cell v4 [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1] n=1 M=629.0 V4 ok
cell v4 [nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1] n=3 M=797.0 V4 NOISY
cell v5 [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1] n=9 M=990.0 V4 ok
cell v5 [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1] n=1 M=614.0 V4 ok
cell v5 [nproc=4 cpu=INTEL(R) XEON(R) PLATINUM 8573C image=20261012.334.1] n=1 M=820.0 V4 ok
cell v5 [nproc=4 cpu=Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz image=20261012.334.1] n=1 M=858.0 V4 ok
table v3 [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1] pairs=5 qualifies=True ratio=0.8138 gain
table v3 [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1] pairs=2 qualifies=True ratio=0.7271 gain
table v3 [nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1] pairs=1 qualifies=False ratio=0.7720 no gain
table v4 [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1] pairs=8 qualifies=True ratio=0.8184 gain
table v4 [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1] pairs=1 qualifies=False ratio=0.7546 no gain
table v4 [nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1] pairs=1 qualifies=False ratio=0.7798 no gain
table v5 [nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1] pairs=9 qualifies=True ratio=0.8229 gain
table v5 [nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1] pairs=1 qualifies=False ratio=0.7367 no gain
after round 0: v3=undecided v4=undecided v5=undecided
after round 1: v3=undecided v4=undecided v5=undecided
after round 2: v3=passes v4=undecided v5=undecided
after round 3: v3=passes v4=undecided v5=undecided
status: decided
decision: {"G": {"v3": 0.8074226804123711}, "outcome": "O1", "shards": 4, "undecided_not_chosen": ["v4", "v5"], "variant": "v3", "width_cap": 4}
```

## 6. Per-job facts

Validity per run (plan section 3.3): V1 `nproc` is at least 4; V3 the recorded peak equals
`min(W, nproc)`; the step succeeded and, for a candidate, coverage is complete (gate 3). V2 is not
a per-run check in revision 5 (comparison is per runner type). **No run is invalid: every V1 and V3
check passed, so there is no invalid run to preserve and none is marked `invalid, not used`.**
**No run failed a gate.** Walls are seconds.

| round | run | job | runner (nproc / CPU model / image) | peak units running | step start (UTC) | step end (UTC) | step wall s | step | coverage | V1 | V3 | valid |
|---|---|---|---|---:|---|---|---:|---|---|---|---|---|
| 0 | 39182957834 | v1-a | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T00:55:40Z | 2026-10-19T01:15:43Z | 1203 | success | none (control: not applicable) | pass | pass | valid |
| 0 | 39182957834 | v1-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T00:55:41Z | 2026-10-19T01:15:32Z | 1191 | success | none (control: not applicable) | pass | pass | valid |
| 0 | 39182957834 | v1-c | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T00:55:40Z | 2026-10-19T01:15:14Z | 1174 | success | none (control: not applicable) | pass | pass | valid |
| 0 | 39182957834 | v3-a | 4 / AMD EPYC 9V74 80-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T00:55:40Z | 2026-10-19T01:08:47Z | 787 | success | expected 415, recorded 415 | pass | pass | valid |
| 0 | 39182957834 | v3-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T00:55:41Z | 2026-10-19T01:11:44Z | 963 | success | expected 415, recorded 415 | pass | pass | valid |
| 0 | 39182957834 | v3-c | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T00:55:40Z | 2026-10-19T01:12:06Z | 986 | success | expected 415, recorded 415 | pass | pass | valid |
| 0 | 39182957834 | v4-a | 4 / AMD EPYC 9V45 96-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:08:53Z | 2026-10-19T01:19:22Z | 629 | success | expected 415, recorded 415 | pass | pass | valid |
| 0 | 39182957834 | v4-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:11:53Z | 2026-10-19T01:28:15Z | 982 | success | expected 415, recorded 415 | pass | pass | valid |
| 0 | 39182957834 | v4-c | 4 / AMD EPYC 9V74 80-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:12:13Z | 2026-10-19T01:28:11Z | 958 | success | expected 415, recorded 415 | pass | pass | valid |
| 0 | 39182957834 | v5-a | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 3 (required 3) | 2026-10-19T01:15:22Z | 2026-10-19T01:32:08Z | 1006 | success | expected 415, recorded 415 | pass | pass | valid |
| 0 | 39182957834 | v5-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 3 (required 3) | 2026-10-19T01:15:39Z | 2026-10-19T01:31:59Z | 980 | success | expected 415, recorded 415 | pass | pass | valid |
| 0 | 39182957834 | v5-c | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 3 (required 3) | 2026-10-19T01:15:51Z | 2026-10-19T01:32:15Z | 984 | success | expected 415, recorded 415 | pass | pass | valid |
| 1 | 39185861409 | v1-a | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:33:08Z | 2026-10-19T01:53:31Z | 1223 | success | none (control: not applicable) | pass | pass | valid |
| 1 | 39185861409 | v1-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:33:08Z | 2026-10-19T01:53:46Z | 1238 | success | none (control: not applicable) | pass | pass | valid |
| 1 | 39185861409 | v1-c | 4 / AMD EPYC 9V45 96-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:33:08Z | 2026-10-19T01:47:45Z | 877 | success | none (control: not applicable) | pass | pass | valid |
| 1 | 39185861409 | v3-a | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:33:08Z | 2026-10-19T01:49:27Z | 979 | success | expected 415, recorded 415 | pass | pass | valid |
| 1 | 39185861409 | v3-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:33:08Z | 2026-10-19T01:49:27Z | 979 | success | expected 415, recorded 415 | pass | pass | valid |
| 1 | 39185861409 | v3-c | 4 / AMD EPYC 9V74 80-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:33:09Z | 2026-10-19T01:46:20Z | 791 | success | expected 415, recorded 415 | pass | pass | valid |
| 1 | 39185861409 | v4-a | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:46:29Z | 2026-10-19T02:03:07Z | 998 | success | expected 415, recorded 415 | pass | pass | valid |
| 1 | 39185861409 | v4-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:47:52Z | 2026-10-19T02:04:19Z | 987 | success | expected 415, recorded 415 | pass | pass | valid |
| 1 | 39185861409 | v4-c | 4 / AMD EPYC 9V74 80-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T01:49:34Z | 2026-10-19T02:02:51Z | 797 | success | expected 415, recorded 415 | pass | pass | valid |
| 1 | 39185861409 | v5-a | 4 / INTEL(R) XEON(R) PLATINUM 8573C / 20261012.334.1 | 3 (required 3) | 2026-10-19T01:49:34Z | 2026-10-19T02:03:14Z | 820 | success | expected 415, recorded 415 | pass | pass | valid |
| 1 | 39185861409 | v5-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 3 (required 3) | 2026-10-19T01:53:38Z | 2026-10-19T02:10:08Z | 990 | success | expected 415, recorded 415 | pass | pass | valid |
| 1 | 39185861409 | v5-c | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 3 (required 3) | 2026-10-19T01:53:54Z | 2026-10-19T02:10:17Z | 983 | success | expected 415, recorded 415 | pass | pass | valid |
| 2 | 39188812102 | v1-a | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:11:48Z | 2026-10-19T02:32:10Z | 1222 | success | none (control: not applicable) | pass | pass | valid |
| 2 | 39188812102 | v1-b | 4 / AMD EPYC 9V45 96-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:11:48Z | 2026-10-19T02:24:58Z | 790 | success | none (control: not applicable) | pass | pass | valid |
| 2 | 39188812102 | v1-c | 4 / AMD EPYC 9V74 80-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:11:48Z | 2026-10-19T02:28:50Z | 1022 | success | none (control: not applicable) | pass | pass | valid |
| 2 | 39188812102 | v3-a | 4 / AMD EPYC 9V45 96-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:11:48Z | 2026-10-19T02:21:23Z | 575 | success | expected 415, recorded 415 | pass | pass | valid |
| 2 | 39188812102 | v3-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:11:47Z | 2026-10-19T02:28:41Z | 1014 | success | expected 415, recorded 415 | pass | pass | valid |
| 2 | 39188812102 | v3-c | 4 / AMD EPYC 9V45 96-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:11:48Z | 2026-10-19T02:22:25Z | 637 | success | expected 415, recorded 415 | pass | pass | valid |
| 2 | 39188812102 | v4-a | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:21:29Z | 2026-10-19T02:37:34Z | 965 | success | expected 415, recorded 415 | pass | pass | valid |
| 2 | 39188812102 | v4-b | 4 / AMD EPYC 9V74 80-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:22:34Z | 2026-10-19T02:35:21Z | 767 | success | expected 415, recorded 415 | pass | pass | valid |
| 2 | 39188812102 | v4-c | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:25:06Z | 2026-10-19T02:41:19Z | 973 | success | expected 415, recorded 415 | pass | pass | valid |
| 2 | 39188812102 | v5-a | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 3 (required 3) | 2026-10-19T02:28:49Z | 2026-10-19T02:45:26Z | 997 | success | expected 415, recorded 415 | pass | pass | valid |
| 2 | 39188812102 | v5-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 3 (required 3) | 2026-10-19T02:28:58Z | 2026-10-19T02:45:39Z | 1001 | success | expected 415, recorded 415 | pass | pass | valid |
| 2 | 39188812102 | v5-c | 4 / Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz / 20261012.334.1 | 3 (required 3) | 2026-10-19T02:32:18Z | 2026-10-19T02:46:36Z | 858 | success | expected 415, recorded 415 | pass | pass | valid |
| 3 | 39191598752 | v1-a | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:47:22Z | 2026-10-19T03:07:05Z | 1183 | success | none (control: not applicable) | pass | pass | valid |
| 3 | 39191598752 | v1-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:47:22Z | 2026-10-19T03:07:10Z | 1188 | success | none (control: not applicable) | pass | pass | valid |
| 3 | 39191598752 | v1-c | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:47:22Z | 2026-10-19T03:07:37Z | 1215 | success | none (control: not applicable) | pass | pass | valid |
| 3 | 39191598752 | v4-a | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:47:22Z | 2026-10-19T03:03:57Z | 995 | success | expected 415, recorded 415 | pass | pass | valid |
| 3 | 39191598752 | v4-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:47:22Z | 2026-10-19T03:03:20Z | 958 | success | expected 415, recorded 415 | pass | pass | valid |
| 3 | 39191598752 | v4-c | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 4 (required 4) | 2026-10-19T02:47:22Z | 2026-10-19T03:04:21Z | 1019 | success | expected 415, recorded 415 | pass | pass | valid |
| 3 | 39191598752 | v5-a | 4 / AMD EPYC 9V45 96-Core Processor / 20261012.334.1 | 3 (required 3) | 2026-10-19T03:03:27Z | 2026-10-19T03:13:41Z | 614 | success | expected 415, recorded 415 | pass | pass | valid |
| 3 | 39191598752 | v5-b | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 3 (required 3) | 2026-10-19T03:04:05Z | 2026-10-19T03:20:53Z | 1008 | success | expected 415, recorded 415 | pass | pass | valid |
| 3 | 39191598752 | v5-c | 4 / AMD EPYC 7763 64-Core Processor / 20261012.334.1 | 3 (required 3) | 2026-10-19T03:04:28Z | 2026-10-19T03:20:53Z | 985 | success | expected 415, recorded 415 | pass | pass | valid |

### Per-unit seconds

Each unit's seconds from the step's `done` lines, in the order the lines appeared. `acceptance-KofN` is
shard K of N; `workflow_acceptance_matrix_test.py` is the unsharded acceptance unit of v1.


#### Round 0 (run 39182957834)

| job | units: seconds (exit status) |
|---|---|
| v1-a | workflow_gate_policy_test.py 334s (exit 0); workflow_state_test.py 542s (exit 0); workflow_fingerprint_generalization_test.py 215s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 15s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_protocol_test.py 714s (exit 0); workflow_acceptance_matrix_test.py 1202s (exit 0) |
| v1-b | workflow_gate_policy_test.py 332s (exit 0); workflow_state_test.py 541s (exit 0); workflow_fingerprint_generalization_test.py 215s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_fingerprint_test.py 12s (exit 0); workflow_protocol_test.py 709s (exit 0); workflow_acceptance_matrix_test.py 1191s (exit 0) |
| v1-c | workflow_gate_policy_test.py 327s (exit 0); workflow_state_test.py 529s (exit 0); workflow_fingerprint_generalization_test.py 212s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_fingerprint_test.py 12s (exit 0); workflow_protocol_test.py 697s (exit 0); workflow_acceptance_matrix_test.py 1174s (exit 0) |
| v3-a | acceptance-3of4 241s (exit 0); acceptance-2of4 293s (exit 0); acceptance-1of4 332s (exit 0); acceptance-4of4 375s (exit 0); workflow_fingerprint_generalization_test.py 167s (exit 0); workflow_state_completion_obligations_test.py 18s (exit 0); workflow_integration_test.py 15s (exit 0); workflow_fingerprint_test.py 12s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_gate_policy_test.py 271s (exit 0); workflow_state_test.py 397s (exit 0); workflow_protocol_test.py 546s (exit 0) |
| v3-b | acceptance-3of4 302s (exit 0); acceptance-2of4 373s (exit 0); acceptance-1of4 419s (exit 0); acceptance-4of4 471s (exit 0); workflow_fingerprint_generalization_test.py 214s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 329s (exit 0); workflow_state_test.py 480s (exit 0); workflow_protocol_test.py 660s (exit 0) |
| v3-c | acceptance-3of4 305s (exit 0); acceptance-2of4 375s (exit 0); acceptance-1of4 420s (exit 0); acceptance-4of4 475s (exit 0); workflow_fingerprint_generalization_test.py 219s (exit 0); workflow_state_completion_obligations_test.py 20s (exit 0); workflow_integration_test.py 15s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 337s (exit 0); workflow_state_test.py 490s (exit 0); workflow_protocol_test.py 679s (exit 0) |
| v4-a | acceptance-1of8 115s (exit 0); acceptance-3of8 115s (exit 0); acceptance-2of8 143s (exit 0); acceptance-4of8 174s (exit 0); acceptance-5of8 97s (exit 0); acceptance-6of8 125s (exit 0); acceptance-8of8 102s (exit 0); acceptance-7of8 139s (exit 0); workflow_fingerprint_generalization_test.py 133s (exit 0); workflow_state_completion_obligations_test.py 13s (exit 0); workflow_integration_test.py 10s (exit 0); workflow_fingerprint_test.py 10s (exit 0); workflow_test_harness_test.py 3s (exit 0); workflow_gate_policy_test.py 205s (exit 0); workflow_state_test.py 301s (exit 0); workflow_protocol_test.py 416s (exit 0) |
| v4-b | acceptance-1of8 175s (exit 0); acceptance-3of8 175s (exit 0); acceptance-2of8 221s (exit 0); acceptance-4of8 269s (exit 0); acceptance-5of8 156s (exit 0); acceptance-6of8 199s (exit 0); acceptance-8of8 162s (exit 0); acceptance-7of8 221s (exit 0); workflow_fingerprint_generalization_test.py 214s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 15s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 323s (exit 0); workflow_state_test.py 479s (exit 0); workflow_protocol_test.py 649s (exit 0) |
| v4-c | acceptance-1of8 168s (exit 0); acceptance-3of8 169s (exit 0); acceptance-2of8 213s (exit 0); acceptance-4of8 260s (exit 0); acceptance-5of8 149s (exit 0); acceptance-6of8 190s (exit 0); acceptance-8of8 153s (exit 0); acceptance-7of8 209s (exit 0); workflow_fingerprint_generalization_test.py 206s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 314s (exit 0); workflow_state_test.py 462s (exit 0); workflow_protocol_test.py 640s (exit 0) |
| v5-a | acceptance-3of4 260s (exit 0); acceptance-2of4 321s (exit 0); acceptance-1of4 363s (exit 0); acceptance-4of4 405s (exit 0); workflow_state_test.py 455s (exit 0); workflow_gate_policy_test.py 289s (exit 0); workflow_state_completion_obligations_test.py 17s (exit 0); workflow_integration_test.py 12s (exit 0); workflow_fingerprint_test.py 11s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_protocol_test.py 681s (exit 0); workflow_fingerprint_generalization_test.py 186s (exit 0) |
| v5-b | acceptance-3of4 257s (exit 0); acceptance-2of4 313s (exit 0); acceptance-1of4 355s (exit 0); acceptance-4of4 396s (exit 0); workflow_state_test.py 441s (exit 0); workflow_gate_policy_test.py 282s (exit 0); workflow_state_completion_obligations_test.py 16s (exit 0); workflow_integration_test.py 12s (exit 0); workflow_fingerprint_test.py 11s (exit 0); workflow_protocol_test.py 663s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_fingerprint_generalization_test.py 182s (exit 0) |
| v5-c | acceptance-3of4 257s (exit 0); acceptance-2of4 316s (exit 0); acceptance-1of4 354s (exit 0); acceptance-4of4 396s (exit 0); workflow_state_test.py 447s (exit 0); workflow_gate_policy_test.py 281s (exit 0); workflow_state_completion_obligations_test.py 16s (exit 0); workflow_integration_test.py 12s (exit 0); workflow_fingerprint_test.py 11s (exit 0); workflow_protocol_test.py 662s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_fingerprint_generalization_test.py 181s (exit 0) |

#### Round 1 (run 39185861409)

| job | units: seconds (exit status) |
|---|---|
| v1-a | workflow_gate_policy_test.py 337s (exit 0); workflow_state_test.py 544s (exit 0); workflow_fingerprint_generalization_test.py 219s (exit 0); workflow_state_completion_obligations_test.py 20s (exit 0); workflow_integration_test.py 15s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_protocol_test.py 725s (exit 0); workflow_acceptance_matrix_test.py 1223s (exit 0) |
| v1-b | workflow_gate_policy_test.py 342s (exit 0); workflow_state_test.py 553s (exit 0); workflow_fingerprint_generalization_test.py 223s (exit 0); workflow_state_completion_obligations_test.py 20s (exit 0); workflow_integration_test.py 15s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_protocol_test.py 734s (exit 0); workflow_acceptance_matrix_test.py 1238s (exit 0) |
| v1-c | workflow_gate_policy_test.py 244s (exit 0); workflow_state_test.py 381s (exit 0); workflow_fingerprint_generalization_test.py 149s (exit 0); workflow_state_completion_obligations_test.py 15s (exit 0); workflow_integration_test.py 10s (exit 0); workflow_fingerprint_test.py 10s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_protocol_test.py 508s (exit 0); workflow_acceptance_matrix_test.py 877s (exit 0) |
| v3-a | acceptance-3of4 306s (exit 0); acceptance-2of4 377s (exit 0); acceptance-1of4 421s (exit 0); acceptance-4of4 475s (exit 0); workflow_fingerprint_generalization_test.py 219s (exit 0); workflow_state_completion_obligations_test.py 20s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 6s (exit 0); workflow_gate_policy_test.py 335s (exit 0); workflow_state_test.py 487s (exit 0); workflow_protocol_test.py 672s (exit 0) |
| v3-b | acceptance-3of4 308s (exit 0); acceptance-2of4 378s (exit 0); acceptance-1of4 423s (exit 0); acceptance-4of4 476s (exit 0); workflow_fingerprint_generalization_test.py 215s (exit 0); workflow_state_completion_obligations_test.py 20s (exit 0); workflow_integration_test.py 15s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 330s (exit 0); workflow_state_test.py 485s (exit 0); workflow_protocol_test.py 669s (exit 0) |
| v3-c | acceptance-3of4 247s (exit 0); acceptance-2of4 305s (exit 0); acceptance-1of4 340s (exit 0); acceptance-4of4 383s (exit 0); workflow_fingerprint_generalization_test.py 169s (exit 0); workflow_state_completion_obligations_test.py 17s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 268s (exit 0); workflow_state_test.py 386s (exit 0); workflow_protocol_test.py 542s (exit 0) |
| v4-a | acceptance-1of8 176s (exit 0); acceptance-3of8 176s (exit 0); acceptance-2of8 223s (exit 0); acceptance-4of8 271s (exit 0); acceptance-5of8 157s (exit 0); acceptance-6of8 199s (exit 0); acceptance-8of8 163s (exit 0); acceptance-7of8 222s (exit 0); workflow_fingerprint_generalization_test.py 216s (exit 0); workflow_state_completion_obligations_test.py 20s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_fingerprint_test.py 14s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 330s (exit 0); workflow_state_test.py 489s (exit 0); workflow_protocol_test.py 664s (exit 0) |
| v4-b | acceptance-1of8 177s (exit 0); acceptance-3of8 177s (exit 0); acceptance-2of8 223s (exit 0); acceptance-4of8 271s (exit 0); acceptance-5of8 156s (exit 0); acceptance-6of8 198s (exit 0); acceptance-8of8 160s (exit 0); acceptance-7of8 220s (exit 0); workflow_fingerprint_generalization_test.py 214s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 15s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 327s (exit 0); workflow_state_test.py 481s (exit 0); workflow_protocol_test.py 652s (exit 0) |
| v4-c | acceptance-3of8 137s (exit 0); acceptance-1of8 139s (exit 0); acceptance-2of8 176s (exit 0); acceptance-4of8 213s (exit 0); acceptance-5of8 124s (exit 0); acceptance-6of8 159s (exit 0); acceptance-8of8 130s (exit 0); acceptance-7of8 175s (exit 0); workflow_fingerprint_generalization_test.py 166s (exit 0); workflow_state_completion_obligations_test.py 22s (exit 0); workflow_integration_test.py 16s (exit 0); workflow_fingerprint_test.py 12s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_gate_policy_test.py 265s (exit 0); workflow_state_test.py 388s (exit 0); workflow_protocol_test.py 535s (exit 0) |
| v5-a | acceptance-3of4 214s (exit 0); acceptance-2of4 262s (exit 0); acceptance-1of4 292s (exit 0); acceptance-4of4 326s (exit 0); workflow_state_test.py 372s (exit 0); workflow_gate_policy_test.py 236s (exit 0); workflow_state_completion_obligations_test.py 15s (exit 0); workflow_integration_test.py 9s (exit 0); workflow_fingerprint_test.py 9s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_protocol_test.py 555s (exit 0); workflow_fingerprint_generalization_test.py 154s (exit 0) |
| v5-b | acceptance-3of4 256s (exit 0); acceptance-2of4 317s (exit 0); acceptance-1of4 355s (exit 0); acceptance-4of4 397s (exit 0); workflow_state_test.py 452s (exit 0); workflow_gate_policy_test.py 287s (exit 0); workflow_state_completion_obligations_test.py 16s (exit 0); workflow_integration_test.py 12s (exit 0); workflow_fingerprint_test.py 11s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_protocol_test.py 669s (exit 0); workflow_fingerprint_generalization_test.py 180s (exit 0) |
| v5-c | acceptance-3of4 258s (exit 0); acceptance-2of4 314s (exit 0); acceptance-1of4 354s (exit 0); acceptance-4of4 396s (exit 0); workflow_state_test.py 447s (exit 0); workflow_gate_policy_test.py 281s (exit 0); workflow_state_completion_obligations_test.py 16s (exit 0); workflow_integration_test.py 12s (exit 0); workflow_fingerprint_test.py 11s (exit 0); workflow_protocol_test.py 664s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_fingerprint_generalization_test.py 181s (exit 0) |

#### Round 2 (run 39188812102)

| job | units: seconds (exit status) |
|---|---|
| v1-a | workflow_gate_policy_test.py 340s (exit 0); workflow_state_test.py 547s (exit 0); workflow_fingerprint_generalization_test.py 219s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_test_harness_test.py 6s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_protocol_test.py 724s (exit 0); workflow_acceptance_matrix_test.py 1221s (exit 0) |
| v1-b | workflow_gate_policy_test.py 218s (exit 0); workflow_state_test.py 338s (exit 0); workflow_fingerprint_generalization_test.py 132s (exit 0); workflow_state_completion_obligations_test.py 13s (exit 0); workflow_fingerprint_test.py 9s (exit 0); workflow_integration_test.py 10s (exit 0); workflow_test_harness_test.py 3s (exit 0); workflow_protocol_test.py 456s (exit 0); workflow_acceptance_matrix_test.py 790s (exit 0) |
| v1-c | workflow_gate_policy_test.py 276s (exit 0); workflow_state_test.py 437s (exit 0); workflow_fingerprint_generalization_test.py 168s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 13s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_fingerprint_test.py 12s (exit 0); workflow_protocol_test.py 577s (exit 0); workflow_acceptance_matrix_test.py 1022s (exit 0) |
| v3-a | acceptance-3of4 179s (exit 0); acceptance-2of4 220s (exit 0); acceptance-1of4 247s (exit 0); acceptance-4of4 279s (exit 0); workflow_fingerprint_generalization_test.py 125s (exit 0); workflow_state_completion_obligations_test.py 13s (exit 0); workflow_integration_test.py 9s (exit 0); workflow_fingerprint_test.py 9s (exit 0); workflow_test_harness_test.py 3s (exit 0); workflow_gate_policy_test.py 198s (exit 0); workflow_state_test.py 285s (exit 0); workflow_protocol_test.py 395s (exit 0) |
| v3-b | acceptance-3of4 316s (exit 0); acceptance-2of4 389s (exit 0); acceptance-1of4 437s (exit 0); acceptance-4of4 491s (exit 0); workflow_fingerprint_generalization_test.py 222s (exit 0); workflow_state_completion_obligations_test.py 21s (exit 0); workflow_integration_test.py 16s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 6s (exit 0); workflow_gate_policy_test.py 344s (exit 0); workflow_state_test.py 500s (exit 0); workflow_protocol_test.py 696s (exit 0) |
| v3-c | acceptance-3of4 206s (exit 0); acceptance-2of4 251s (exit 0); acceptance-1of4 281s (exit 0); acceptance-4of4 316s (exit 0); workflow_fingerprint_generalization_test.py 134s (exit 0); workflow_state_completion_obligations_test.py 14s (exit 0); workflow_integration_test.py 10s (exit 0); workflow_fingerprint_test.py 9s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_gate_policy_test.py 213s (exit 0); workflow_state_test.py 309s (exit 0); workflow_protocol_test.py 429s (exit 0) |
| v4-a | acceptance-3of8 172s (exit 0); acceptance-1of8 173s (exit 0); acceptance-2of8 218s (exit 0); acceptance-4of8 265s (exit 0); acceptance-5of8 152s (exit 0); acceptance-6of8 194s (exit 0); acceptance-8of8 158s (exit 0); acceptance-7of8 214s (exit 0); workflow_fingerprint_generalization_test.py 211s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 319s (exit 0); workflow_state_test.py 473s (exit 0); workflow_protocol_test.py 640s (exit 0) |
| v4-b | acceptance-1of8 134s (exit 0); acceptance-3of8 134s (exit 0); acceptance-2of8 169s (exit 0); acceptance-4of8 207s (exit 0); acceptance-5of8 117s (exit 0); acceptance-6of8 152s (exit 0); acceptance-8of8 123s (exit 0); acceptance-7of8 167s (exit 0); workflow_fingerprint_generalization_test.py 163s (exit 0); workflow_state_completion_obligations_test.py 15s (exit 0); workflow_integration_test.py 12s (exit 0); workflow_fingerprint_test.py 11s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 252s (exit 0); workflow_state_test.py 373s (exit 0); workflow_protocol_test.py 515s (exit 0) |
| v4-c | acceptance-1of8 175s (exit 0); acceptance-3of8 175s (exit 0); acceptance-2of8 221s (exit 0); acceptance-4of8 270s (exit 0); acceptance-5of8 154s (exit 0); acceptance-6of8 196s (exit 0); acceptance-8of8 158s (exit 0); acceptance-7of8 216s (exit 0); workflow_fingerprint_generalization_test.py 211s (exit 0); workflow_state_completion_obligations_test.py 20s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 321s (exit 0); workflow_state_test.py 471s (exit 0); workflow_protocol_test.py 643s (exit 0) |
| v5-a | acceptance-3of4 259s (exit 0); acceptance-2of4 321s (exit 0); acceptance-1of4 360s (exit 0); acceptance-4of4 403s (exit 0); workflow_state_test.py 448s (exit 0); workflow_gate_policy_test.py 284s (exit 0); workflow_state_completion_obligations_test.py 16s (exit 0); workflow_integration_test.py 13s (exit 0); workflow_fingerprint_test.py 11s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_fingerprint_generalization_test.py 187s (exit 0); workflow_protocol_test.py 675s (exit 0) |
| v5-b | acceptance-3of4 259s (exit 0); acceptance-2of4 321s (exit 0); acceptance-1of4 357s (exit 0); acceptance-4of4 401s (exit 0); workflow_state_test.py 455s (exit 0); workflow_gate_policy_test.py 291s (exit 0); workflow_state_completion_obligations_test.py 17s (exit 0); workflow_integration_test.py 12s (exit 0); workflow_fingerprint_test.py 11s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_protocol_test.py 676s (exit 0); workflow_fingerprint_generalization_test.py 188s (exit 0) |
| v5-c | acceptance-3of4 223s (exit 0); acceptance-2of4 274s (exit 0); acceptance-1of4 304s (exit 0); acceptance-4of4 339s (exit 0); workflow_state_test.py 398s (exit 0); workflow_gate_policy_test.py 244s (exit 0); workflow_state_completion_obligations_test.py 13s (exit 0); workflow_integration_test.py 9s (exit 0); workflow_fingerprint_test.py 8s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_protocol_test.py 577s (exit 0); workflow_fingerprint_generalization_test.py 156s (exit 0) |

#### Round 3 (run 39191598752)

| job | units: seconds (exit status) |
|---|---|
| v1-a | workflow_gate_policy_test.py 328s (exit 0); workflow_state_test.py 531s (exit 0); workflow_fingerprint_generalization_test.py 213s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_protocol_test.py 702s (exit 0); workflow_acceptance_matrix_test.py 1183s (exit 0) |
| v1-b | workflow_gate_policy_test.py 329s (exit 0); workflow_state_test.py 536s (exit 0); workflow_fingerprint_generalization_test.py 213s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 15s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_protocol_test.py 705s (exit 0); workflow_acceptance_matrix_test.py 1188s (exit 0) |
| v1-c | workflow_gate_policy_test.py 336s (exit 0); workflow_state_test.py 545s (exit 0); workflow_fingerprint_generalization_test.py 218s (exit 0); workflow_state_completion_obligations_test.py 20s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_fingerprint_test.py 12s (exit 0); workflow_protocol_test.py 721s (exit 0); workflow_acceptance_matrix_test.py 1215s (exit 0) |
| v4-a | acceptance-1of8 177s (exit 0); acceptance-3of8 177s (exit 0); acceptance-2of8 223s (exit 0); acceptance-4of8 270s (exit 0); acceptance-5of8 156s (exit 0); acceptance-6of8 199s (exit 0); acceptance-8of8 162s (exit 0); acceptance-7of8 221s (exit 0); workflow_fingerprint_generalization_test.py 216s (exit 0); workflow_state_completion_obligations_test.py 20s (exit 0); workflow_integration_test.py 15s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 327s (exit 0); workflow_state_test.py 484s (exit 0); workflow_protocol_test.py 661s (exit 0) |
| v4-b | acceptance-3of8 171s (exit 0); acceptance-1of8 172s (exit 0); acceptance-2of8 216s (exit 0); acceptance-4of8 262s (exit 0); acceptance-5of8 150s (exit 0); acceptance-6of8 192s (exit 0); acceptance-8of8 156s (exit 0); acceptance-7of8 213s (exit 0); workflow_fingerprint_generalization_test.py 208s (exit 0); workflow_state_completion_obligations_test.py 19s (exit 0); workflow_integration_test.py 14s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_gate_policy_test.py 316s (exit 0); workflow_state_test.py 467s (exit 0); workflow_protocol_test.py 635s (exit 0) |
| v4-c | acceptance-3of8 181s (exit 0); acceptance-1of8 181s (exit 0); acceptance-2of8 229s (exit 0); acceptance-4of8 277s (exit 0); acceptance-5of8 160s (exit 0); acceptance-6of8 204s (exit 0); acceptance-8of8 166s (exit 0); acceptance-7of8 226s (exit 0); workflow_fingerprint_generalization_test.py 222s (exit 0); workflow_state_completion_obligations_test.py 20s (exit 0); workflow_integration_test.py 15s (exit 0); workflow_fingerprint_test.py 13s (exit 0); workflow_test_harness_test.py 6s (exit 0); workflow_gate_policy_test.py 336s (exit 0); workflow_state_test.py 494s (exit 0); workflow_protocol_test.py 676s (exit 0) |
| v5-a | acceptance-3of4 162s (exit 0); acceptance-2of4 200s (exit 0); acceptance-1of4 224s (exit 0); acceptance-4of4 249s (exit 0); workflow_state_test.py 272s (exit 0); workflow_gate_policy_test.py 178s (exit 0); workflow_state_completion_obligations_test.py 11s (exit 0); workflow_fingerprint_generalization_test.py 110s (exit 0); workflow_integration_test.py 9s (exit 0); workflow_protocol_test.py 410s (exit 0); workflow_test_harness_test.py 2s (exit 0); workflow_fingerprint_test.py 7s (exit 0) |
| v5-b | acceptance-3of4 261s (exit 0); acceptance-2of4 322s (exit 0); acceptance-1of4 361s (exit 0); acceptance-4of4 403s (exit 0); workflow_state_test.py 458s (exit 0); workflow_gate_policy_test.py 287s (exit 0); workflow_state_completion_obligations_test.py 17s (exit 0); workflow_integration_test.py 12s (exit 0); workflow_fingerprint_test.py 11s (exit 0); workflow_test_harness_test.py 5s (exit 0); workflow_protocol_test.py 675s (exit 0); workflow_fingerprint_generalization_test.py 186s (exit 0) |
| v5-c | acceptance-3of4 256s (exit 0); acceptance-2of4 315s (exit 0); acceptance-1of4 351s (exit 0); acceptance-4of4 398s (exit 0); workflow_state_test.py 449s (exit 0); workflow_gate_policy_test.py 285s (exit 0); workflow_state_completion_obligations_test.py 17s (exit 0); workflow_integration_test.py 12s (exit 0); workflow_fingerprint_test.py 11s (exit 0); workflow_test_harness_test.py 4s (exit 0); workflow_fingerprint_generalization_test.py 183s (exit 0); workflow_protocol_test.py 669s (exit 0) |

## 7. Cells and the per-runner-type tables

A runner type is the recorded (`nproc`, CPU model, image) triple; the CPU model strings are kept as
the runner printed them (`INTEL(R) XEON(R) PLATINUM 8573C` and `Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz` are
distinct runner types as recorded). A cell is the set of valid runs of a variant on a runner type.

### Cells (all 45 runs, all valid)

| variant | runner type | n valid | step walls s (sorted) | median M | max-min | 20% of median | V4 |
|---|---|---:|---|---:|---:|---:|---|
| v1 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 9 | 1174, 1183, 1188, 1191, 1203, 1215, 1222, 1223, 1238 | 1203 | 64 | 240.6 | ok |
| v1 | nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1 | 2 | 790, 877 | 833.5 | 87 | 166.7 | ok |
| v1 | nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1 | 1 | 1022 | 1022 | 0 | 204.4 | ok |
| v3 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 5 | 963, 979, 979, 986, 1014 | 979 | 51 | 195.8 | ok |
| v3 | nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1 | 2 | 575, 637 | 606 | 62 | 121.2 | ok |
| v3 | nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1 | 2 | 787, 791 | 789 | 4 | 157.8 | ok |
| v4 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 8 | 958, 965, 973, 982, 987, 995, 998, 1019 | 984.5 | 61 | 196.9 | ok |
| v4 | nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1 | 1 | 629 | 629 | 0 | 125.8 | ok |
| v4 | nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1 | 3 | 767, 797, 958 | 797 | 191 | 159.4 | NOISY |
| v5 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 9 | 980, 983, 984, 985, 990, 997, 1001, 1006, 1008 | 990 | 28 | 198 | ok |
| v5 | nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1 | 1 | 614 | 614 | 0 | 122.8 | ok |
| v5 | nproc=4 cpu=INTEL(R) XEON(R) PLATINUM 8573C image=20261012.334.1 | 1 | 820 | 820 | 0 | 164 | ok |
| v5 | nproc=4 cpu=Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz image=20261012.334.1 | 1 | 858 | 858 | 0 | 171.6 | ok |

The only noisy cell (V4) is v4 on the EPYC 9V74 (767, 797 and 958 s). It matters to no outcome: v4 has one v1 run
on that runner type, so it has one same-CPU pair and does not qualify there anyway.

### Per-runner-type comparison, after each round

Rows are the runner types on which a candidate and v1 both have valid runs (a candidate with no v1 run on a
runner type has no row there). `M` are medians of the step walls of the cell, `ratio` is `M(s)/M(v1)`.
A candidate's status is frozen once it passes or is rejected (plan section 3.2): v3 was frozen `passes`
after round 2 with the ratios of the round-2 table, and v3 was not run in round 3, so its round-3 rows
below only restate the round-2 cells with the later v1 runs and **are not used** (G is taken from the round
in which it passed).


#### After round 0 (runs of rounds 0 to 0)

| candidate | runner type | same-CPU pairs P | qualifies (P>=2, both cells V4) | M(s) | M(v1) | ratio | slowest s < fastest v1 | result |
|---|---|---:|---|---:|---:|---:|---|---|
| v3 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 2 | True | 974.5 | 1191 | 0.8182 | 986.0 < 1174.0: True | gain |
| v4 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 1 | False | 982 | 1191 | 0.8245 | 982.0 < 1174.0: True | does not qualify |
| v5 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 3 | True | 984 | 1191 | 0.8262 | 1006.0 < 1174.0: True | gain |

#### After round 1 (runs of rounds 0 to 1)

| candidate | runner type | same-CPU pairs P | qualifies (P>=2, both cells V4) | M(s) | M(v1) | ratio | slowest s < fastest v1 | result |
|---|---|---:|---|---:|---:|---:|---|---|
| v3 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 4 | True | 979 | 1203 | 0.8138 | 986.0 < 1174.0: True | gain |
| v4 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 3 | True | 987 | 1203 | 0.8204 | 998.0 < 1174.0: True | gain |
| v4 | nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1 | 1 | False | 629 | 877 | 0.7172 | 629.0 < 877.0: True | does not qualify |
| v5 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 5 | True | 984 | 1203 | 0.8180 | 1006.0 < 1174.0: True | gain |

#### After round 2 (runs of rounds 0 to 2)

| candidate | runner type | same-CPU pairs P | qualifies (P>=2, both cells V4) | M(s) | M(v1) | ratio | slowest s < fastest v1 | result |
|---|---|---:|---|---:|---:|---:|---|---|
| v3 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 5 | True | 979 | 1212.5 | 0.8074 | 1014.0 < 1174.0: True | gain |
| v3 | nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1 | 2 | True | 606 | 833.5 | 0.7271 | 637.0 < 790.0: True | gain |
| v3 | nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1 | 1 | False | 789 | 1022 | 0.7720 | 791.0 < 1022.0: True | does not qualify |
| v4 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 5 | True | 982 | 1212.5 | 0.8099 | 998.0 < 1174.0: True | gain |
| v4 | nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1 | 1 | False | 629 | 833.5 | 0.7546 | 629.0 < 790.0: True | does not qualify |
| v4 | nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1 | 1 | False | 797 | 1022 | 0.7798 | 958.0 < 1022.0: True | does not qualify |
| v5 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 6 | True | 990 | 1212.5 | 0.8165 | 1006.0 < 1174.0: True | gain |

#### After round 3 (runs of rounds 0 to 3)

| candidate | runner type | same-CPU pairs P | qualifies (P>=2, both cells V4) | M(s) | M(v1) | ratio | slowest s < fastest v1 | result |
|---|---|---:|---|---:|---:|---:|---|---|
| v3 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 5 | True | 979 | 1203 | 0.8138 | 1014.0 < 1174.0: True | gain |
| v3 | nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1 | 2 | True | 606 | 833.5 | 0.7271 | 637.0 < 790.0: True | gain |
| v3 | nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1 | 1 | False | 789 | 1022 | 0.7720 | 791.0 < 1022.0: True | does not qualify |
| v4 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 8 | True | 984.5 | 1203 | 0.8184 | 1019.0 < 1174.0: True | gain |
| v4 | nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1 | 1 | False | 629 | 833.5 | 0.7546 | 629.0 < 790.0: True | does not qualify |
| v4 | nproc=4 cpu=AMD EPYC 9V74 80-Core Processor image=20261012.334.1 | 1 | False | 797 | 1022 | 0.7798 | 958.0 < 1022.0: True | does not qualify |
| v5 | nproc=4 cpu=AMD EPYC 7763 64-Core Processor image=20261012.334.1 | 9 | True | 990 | 1203 | 0.8229 | 1008.0 < 1174.0: True | gain |
| v5 | nproc=4 cpu=AMD EPYC 9V45 96-Core Processor image=20261012.334.1 | 1 | False | 614 | 833.5 | 0.7367 | 614.0 < 790.0: True | does not qualify |

## 8. The rule of section 3.2, applied

Candidate status after each round (validator, `history`): after round 0 v3, v4, v5 undecided; after round 1
all undecided; **after round 2 v3 passes**, v4 and v5 undecided; after round 3 v3 passes, v4 and v5 undecided.

1. Valid runs and cells: all 45 runs are valid (section 6), none dropped by timing.
2. Qualification (`P >= 2` and V4 on both cells). After round 2, v3 qualifies on two runner types: the AMD EPYC
   7763 (P = 5; cells v3 {963, 979, 979, 986, 1014}, v1 six runs) and the AMD EPYC 9V45 (P = 2; v3 {575, 637},
   v1 {790, 877}). The EPYC 9V74 has P = 1 and does not qualify.
3. Gain on each qualifying type (`M(s) <= 0.85 * M(v1)` and slowest s faster than fastest v1):
   EPYC 7763: M(v3) 979 against M(v1) 1212.5 (after round 2 the six v1 walls are 1174, 1191, 1203, 1222, 1223 and 1238): ratio **0.8074**,
   0.85 * 1212.5 = 1030.6 >= 979, and the slowest v3 run 1014 < the fastest v1 run 1174: gain.
   EPYC 9V45: M(v3) 606 against M(v1) 833.5: ratio **0.7271**, 0.85 * 833.5 = 708.5 >= 606, slowest v3 637 < fastest v1 790: gain.
4. Status: at least two runner types qualify and v3 shows the gain on every one of them: **v3 passes**,
   `G(v3)` = the largest ratio over its qualifying types = **0.8074226804123711** (the validator's value).
5. v4: after round 3 only the EPYC 7763 qualifies (P = 8, ratio 0.8184, gain); the EPYC 9V45 (P = 1) and 9V74
   (P = 1) do not qualify. One qualifying type is fewer than two: v4 is **undecided** and never chosen.
   v5: only the EPYC 7763 qualifies (P = 9, ratio 0.8229, gain); the 9V45, the Xeon 8573C and the Xeon 8370C each have
   one v5 run, so they have no pair of two there (the Xeons have no v1 run at all on their runner type): v5 is **undecided** and never chosen.
6. Rule 1 (O1): after the last round at least one candidate passes (v3). Rule 4: no candidate had a failed
   gate, no v1 run failed its suites. Decision order of section 3.3: no v1 failure; a candidate passes: **O1**.
7. Rule 2 (width and shard count): the passing candidates are v3 only, so `min G` = G(v3) and `G(v3) <= 1.05 * min G`;
   the smallest W, then N, among them is v3: **`width_cap` 4, `shards` 4**. Undecided v4 and v5 are listed and not chosen.

Not selected and not measured: no width-2 variant, no sharded variant at a width other than 3 and 4 and a
shard count other than 4 and 8.

## 9. Findings recorded for later checkpoints (measured, not interpreted beyond the rule)

- v3 step walls: 575 to 1014 s across runner types; on the EPYC 7763 the median 979 s against v1 1203 s (all
  v3 runs faster than all v1 runs there). On the AMD EPYC 7763 v3's longest shard unit took 475 s (v3-c, round 0, shard 4 of 4),
  and in the same job `workflow_protocol_test.py` took 679 s.
- The partition balances by test count, not time (plan section 2.4); the per-unit seconds of the four shards in section 6
  (305, 375, 420 and 475 s in v3-c of round 0) are the measured imbalance. No finer split is attempted (a class is never split).

## 10. The records the validator read

`records-r5.json` (45 records; fields as `kit/collect.py` writes them), so that sections 5 to 8 are reproducible
with `validate.py` from this file alone:

```json
[
 {
  "variant": "v3",
  "rep": "c",
  "round": 0,
  "run_id": "39182957834",
  "job": "v3-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 986.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v4",
  "rep": "b",
  "round": 0,
  "run_id": "39182957834",
  "job": "v4-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 982.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v5",
  "rep": "a",
  "round": 0,
  "run_id": "39182957834",
  "job": "v5-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 3,
  "wall": 1006.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v3",
  "rep": "b",
  "round": 0,
  "run_id": "39182957834",
  "job": "v3-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 963.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v5",
  "rep": "c",
  "round": 0,
  "run_id": "39182957834",
  "job": "v5-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 3,
  "wall": 984.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v1",
  "rep": "b",
  "round": 0,
  "run_id": "39182957834",
  "job": "v1-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 1191.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v1",
  "rep": "a",
  "round": 0,
  "run_id": "39182957834",
  "job": "v1-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 1203.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v3",
  "rep": "a",
  "round": 0,
  "run_id": "39182957834",
  "job": "v3-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V74 80-Core Processor",
  "peak": 4,
  "wall": 787.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v4",
  "rep": "a",
  "round": 0,
  "run_id": "39182957834",
  "job": "v4-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V45 96-Core Processor",
  "peak": 4,
  "wall": 629.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v5",
  "rep": "b",
  "round": 0,
  "run_id": "39182957834",
  "job": "v5-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 3,
  "wall": 980.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v1",
  "rep": "c",
  "round": 0,
  "run_id": "39182957834",
  "job": "v1-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 1174.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v4",
  "rep": "c",
  "round": 0,
  "run_id": "39182957834",
  "job": "v4-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V74 80-Core Processor",
  "peak": 4,
  "wall": 958.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v1",
  "rep": "a",
  "round": 1,
  "run_id": "39185861409",
  "job": "v1-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 1223.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v3",
  "rep": "a",
  "round": 1,
  "run_id": "39185861409",
  "job": "v3-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 979.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v4",
  "rep": "b",
  "round": 1,
  "run_id": "39185861409",
  "job": "v4-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 987.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v5",
  "rep": "b",
  "round": 1,
  "run_id": "39185861409",
  "job": "v5-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 3,
  "wall": 990.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v5",
  "rep": "a",
  "round": 1,
  "run_id": "39185861409",
  "job": "v5-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "INTEL(R) XEON(R) PLATINUM 8573C",
  "peak": 3,
  "wall": 820.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v5",
  "rep": "c",
  "round": 1,
  "run_id": "39185861409",
  "job": "v5-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 3,
  "wall": 983.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v1",
  "rep": "c",
  "round": 1,
  "run_id": "39185861409",
  "job": "v1-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V45 96-Core Processor",
  "peak": 4,
  "wall": 877.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v3",
  "rep": "b",
  "round": 1,
  "run_id": "39185861409",
  "job": "v3-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 979.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v4",
  "rep": "c",
  "round": 1,
  "run_id": "39185861409",
  "job": "v4-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V74 80-Core Processor",
  "peak": 4,
  "wall": 797.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v4",
  "rep": "a",
  "round": 1,
  "run_id": "39185861409",
  "job": "v4-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 998.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v3",
  "rep": "c",
  "round": 1,
  "run_id": "39185861409",
  "job": "v3-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V74 80-Core Processor",
  "peak": 4,
  "wall": 791.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v1",
  "rep": "b",
  "round": 1,
  "run_id": "39185861409",
  "job": "v1-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 1238.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v3",
  "rep": "b",
  "round": 2,
  "run_id": "39188812102",
  "job": "v3-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 1014.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v4",
  "rep": "c",
  "round": 2,
  "run_id": "39188812102",
  "job": "v4-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 973.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v1",
  "rep": "c",
  "round": 2,
  "run_id": "39188812102",
  "job": "v1-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V74 80-Core Processor",
  "peak": 4,
  "wall": 1022.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v5",
  "rep": "a",
  "round": 2,
  "run_id": "39188812102",
  "job": "v5-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 3,
  "wall": 997.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v3",
  "rep": "c",
  "round": 2,
  "run_id": "39188812102",
  "job": "v3-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V45 96-Core Processor",
  "peak": 4,
  "wall": 637.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v3",
  "rep": "a",
  "round": 2,
  "run_id": "39188812102",
  "job": "v3-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V45 96-Core Processor",
  "peak": 4,
  "wall": 575.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v5",
  "rep": "b",
  "round": 2,
  "run_id": "39188812102",
  "job": "v5-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 3,
  "wall": 1001.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v4",
  "rep": "a",
  "round": 2,
  "run_id": "39188812102",
  "job": "v4-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 965.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v1",
  "rep": "b",
  "round": 2,
  "run_id": "39188812102",
  "job": "v1-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V45 96-Core Processor",
  "peak": 4,
  "wall": 790.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v1",
  "rep": "a",
  "round": 2,
  "run_id": "39188812102",
  "job": "v1-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 1222.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v4",
  "rep": "b",
  "round": 2,
  "run_id": "39188812102",
  "job": "v4-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V74 80-Core Processor",
  "peak": 4,
  "wall": 767.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v5",
  "rep": "c",
  "round": 2,
  "run_id": "39188812102",
  "job": "v5-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
  "peak": 3,
  "wall": 858.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v1",
  "rep": "b",
  "round": 3,
  "run_id": "39191598752",
  "job": "v1-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 1188.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v5",
  "rep": "c",
  "round": 3,
  "run_id": "39191598752",
  "job": "v5-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 3,
  "wall": 985.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v1",
  "rep": "a",
  "round": 3,
  "run_id": "39191598752",
  "job": "v1-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 1183.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v4",
  "rep": "a",
  "round": 3,
  "run_id": "39191598752",
  "job": "v4-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 995.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v4",
  "rep": "c",
  "round": 3,
  "run_id": "39191598752",
  "job": "v4-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 1019.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v4",
  "rep": "b",
  "round": 3,
  "run_id": "39191598752",
  "job": "v4-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 958.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v5",
  "rep": "a",
  "round": 3,
  "run_id": "39191598752",
  "job": "v5-a",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 9V45 96-Core Processor",
  "peak": 3,
  "wall": 614.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 },
 {
  "variant": "v1",
  "rep": "c",
  "round": 3,
  "run_id": "39191598752",
  "job": "v1-c",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 4,
  "wall": 1215.0,
  "step_conclusion": "success",
  "coverage": null
 },
 {
  "variant": "v5",
  "rep": "b",
  "round": 3,
  "run_id": "39191598752",
  "job": "v5-b",
  "nproc": 4,
  "image": "20261012.334.1",
  "cpu": "AMD EPYC 7763 64-Core Processor",
  "peak": 3,
  "wall": 1008.0,
  "step_conclusion": "success",
  "coverage": {
   "expected": 415,
   "recorded": 415
  }
 }
]
```
