#!/usr/bin/env python3
"""Tests for the gate policy model (workflow-2.8.0, `gate-policy-and-reopening`,
CP1): `workflow_gate_policy.py`, the state fields and writers that
`workflow_state.py` adds for it, `/adopt-gate-policy`, item-scoped staging and
`verify`'s `gate_policy` check.

Scratch repositories are real Git repositories built here (`PolicyRepo`),
including branches, update merges and squash merges, because the policy's
provenance is read from Git history by content and chain, never from a commit
message.

Stdlib-only. Run: python3 scripts/workflow_gate_policy_test.py
"""

from __future__ import annotations

import contextlib
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import workflow_gate_policy as g
import workflow_protocol as wp
import workflow_state as ws
import workflow_test_harness as h

STATE_REL = "docs/ai-workflow/WORKFLOW_STATE.json"
POLICY_REL = "docs/ai-workflow/GATE_POLICY.json"
SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent

HUMAN = {"schema_version": 1, "human_approval": True}
PLAN_HUMAN = {"schema_version": 1, "gates": {"plan_approval": {"human": True}}}
ACCEPTANCE_HUMAN = {"schema_version": 1, "gates": {"acceptance": {"human": True}}}
AUTOMATIC = {"schema_version": 1, "human_approval": False}
NO_REQUIRE = {"schema_version": 1, "gates": {"plan_approval": {"require": []},
                                             "technical_approval": {"require": []}}}


_CLOCK = [0]


def now() -> str:
    """A strictly increasing fake clock: two records written by one test
    never share a `recorded_at`/`adopted_at`."""
    _CLOCK[0] += 1
    return f"2026-10-03T12:{_CLOCK[0] // 60 % 60:02d}:{_CLOCK[0] % 60:02d}Z"


def confirmation_for(policy: dict) -> str:
    return f"I adopt gate_policy {g.policy_digest(policy)[:12]}"


class PolicyRepo:
    """A disposable Git repository with a committed state file, the state
    helpers the policy needs, and branch/merge/squash builders."""

    def __enter__(self) -> "PolicyRepo":
        g.clear_caches()
        self.scratch = h.ScratchRepo().__enter__()
        self.root = self.scratch.root
        (self.root / ".gitignore").write_text(".ai-review/\n__pycache__/\n")
        (self.root / "docs/ai-workflow").mkdir(parents=True)
        self.write_state(h.base_state())
        self.git("add", ".gitignore", STATE_REL)
        self.git("commit", "-q", "-m", "state")
        self.git("branch", "-M", "main")
        return self

    def __exit__(self, *exc) -> None:
        self.scratch.__exit__(*exc)
        g.clear_caches()

    # -- plumbing ----------------------------------------------------------

    def git(self, *args: str, check: bool = True) -> str:
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True)
        if check and result.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}{result.stdout}")
        return result.stdout.strip()

    def head(self) -> str:
        return self.git("rev-parse", "HEAD")

    def state(self) -> dict:
        return json.loads((self.root / STATE_REL).read_text())

    def write_state(self, state: dict) -> None:
        (self.root / STATE_REL).write_bytes(ws._serialize_state(state))

    def write_policy(self, body) -> None:
        text = body if isinstance(body, str) else json.dumps(body, indent=2)
        (self.root / POLICY_REL).write_text(text)

    def remove_policy(self) -> None:
        (self.root / POLICY_REL).unlink()

    def commit(self, subject: str, *paths: str, trailers: dict | None = None, body: str = "") -> str:
        self.git("add", "--", *(paths or (STATE_REL,)))
        message = [subject]
        if body:
            message.append(body)
        if trailers:
            message.append("\n".join(f"{k}: {v}" for k, v in trailers.items()))
        args = ["commit", "-q"]
        for part in message:
            args += ["-m", part]
        self.git(*args)
        return self.head()

    def commit_policy(self, body, subject: str = "policy file") -> str:
        self.write_policy(body)
        return self.commit(subject, POLICY_REL)

    def delete_policy_and_commit(self) -> str:
        self.git("rm", "-q", "--", POLICY_REL)
        self.git("commit", "-q", "-m", "delete policy file")
        return self.head()

    def hand_state_commit(self, mutate, subject: str = "hand edit", trailers: dict | None = None,
                          body: str = "") -> str:
        state = self.state()
        mutate(state)
        self.write_state(state)
        return self.commit(subject, STATE_REL, trailers=trailers, body=body)

    def adopt(self, policy: dict) -> str:
        """The real `/adopt-gate-policy` path on a file holding `policy`."""
        self.write_policy(policy)
        return ws.adopt_gate_policy(self.root, confirmation=confirmation_for(policy), now=now())

    def adoption_state(self, policy: dict, *, lowered: list | None = None) -> dict:
        """The state `record_gate_policy_adoption` returns for `policy`."""
        state = self.state()
        before = gate_lowering(state, policy)
        return ws.record_gate_policy_adoption(
            state, policy=policy, confirmation=confirmation_for(policy), now=now(),
            lowered=before if lowered is None else lowered)

    def hand_adopt(self, policy: dict, *, lowered: list | None = None, trailer: bool = True) -> str:
        """A hand-built, self-consistent adoption commit (the Blocking
        finding's attempt): built from the writer's own record, committed
        without `adopt_gate_policy`."""
        new_state = self.adoption_state(policy, lowered=lowered)
        self.write_state(new_state)
        digest = new_state[ws.GATE_POLICY_ADOPTION_KEY]["sha256"]
        return self.commit(f"hand adoption {digest[:12]}", STATE_REL,
                           trailers={ws.GATE_POLICY_ADOPTION_TRAILER: digest} if trailer else None)

    def record_floor(self) -> str | None:
        return ws.commit_gate_policy_floor(self.root, now=now())

    def eff(self) -> dict:
        g.clear_caches()
        return g.effective_policy(self.root, self.state())

    def human_gates(self) -> set[str]:
        return {gate for gate in g.GATE_IDS if self.eff()["policy"][gate]["human"]}

    def prov(self) -> dict:
        g.clear_caches()
        return g.verify_gate_policy_provenance(self.root)

    # -- branches ----------------------------------------------------------

    def branch(self, name: str, start: str | None = None) -> None:
        self.git("checkout", "-q", "-b", name, *([start] if start else []))

    def checkout(self, name: str) -> None:
        self.git("checkout", "-q", name)

    def merge(self, other: str, resolver=None) -> str:
        """An update merge (`--no-ff`) whose state file is written by
        `resolver(ours, theirs, base)`; with no resolver the merge must be
        clean."""
        base = self.git("merge-base", "HEAD", other)
        ours = self.state()
        theirs = json.loads(self.git("show", f"{other}:{STATE_REL}"))
        base_state = json.loads(self.git("show", f"{base}:{STATE_REL}"))
        result = subprocess.run(["git", "merge", "--no-ff", "--no-commit", other], cwd=self.root,
                                capture_output=True, text=True)
        if resolver is not None:
            self.write_state(resolver(ours, theirs, base_state))
            self.git("add", "--", STATE_REL)
        elif result.returncode != 0:
            raise AssertionError(f"merge conflicted: {result.stdout}")
        self.git("commit", "-q", "--no-edit", "-m", f"update from {other}")
        return self.head()

    def squash(self, branch: str, subject: str = "squash") -> str:
        """Recreates this repository's squash merge: one commit on the
        current branch with the branch's net diff and a blank body."""
        self.git("merge", "--squash", branch)
        self.git("commit", "-q", "-m", subject)
        return self.head()


def gate_lowering(state: dict, policy: dict) -> list[str]:
    return ws.gate_policy_adoption_lowering(
        state.get(ws.GATE_POLICY_ADOPTION_KEY), state.get(ws.GATE_POLICY_FLOOR_KEY), policy)


def resolved_equal_or_stricter(a: dict, b: dict) -> bool:
    return not g.loosened_fields(a, b)


# ---------------------------------------------------------------------------
# the schema, the default and the resolved form
# ---------------------------------------------------------------------------


class TestPolicySchema(unittest.TestCase):
    def test_default_policy_is_valid_and_automatic(self):
        g.validate_policy(g.DEFAULT_POLICY)
        resolved = g.DEFAULT_RESOLVED
        for gate in g.GATE_IDS:
            self.assertFalse(resolved[gate]["human"], gate)

    def test_all_human_configuration_is_valid(self):
        g.validate_policy(HUMAN)
        resolved = g.resolve_policy(HUMAN)
        self.assertTrue(all(resolved[gate]["human"] for gate in g.GATE_IDS))

    def test_master_switch_and_per_gate_overrides_resolve_as_specified(self):
        plan_only = g.resolve_policy(PLAN_HUMAN)
        self.assertEqual([gate for gate in g.GATE_IDS if plan_only[gate]["human"]], ["plan_approval"])
        acceptance_only = g.resolve_policy(ACCEPTANCE_HUMAN)
        self.assertEqual([gate for gate in g.GATE_IDS if acceptance_only[gate]["human"]], ["acceptance"])
        mixed = g.resolve_policy({"human_approval": True, "gates": {
            "plan_approval": {"human": False}, "technical_approval": {"human": False}}})
        self.assertEqual([gate for gate in g.GATE_IDS if mixed[gate]["human"]], ["acceptance"])

    def test_the_default_require_applies_and_is_listed_under_all_human(self):
        self.assertEqual(g.DEFAULT_RESOLVED["plan_approval"]["require"], ["distinct_reviewer_models"])
        self.assertEqual(g.DEFAULT_RESOLVED["technical_approval"]["require"], ["distinct_reviewer_models"])
        self.assertEqual(g.resolve_policy(HUMAN)["plan_approval"]["require"], ["distinct_reviewer_models"])
        self.assertEqual(g.resolve_policy(NO_REQUIRE)["plan_approval"]["require"], [])

    def test_acceptance_and_pr_review_defaults(self):
        resolved = g.DEFAULT_RESOLVED
        self.assertEqual(resolved["acceptance"], {
            "human": False, "require_ci": True, "requires_pr_approved": False, "required_flows": []})
        self.assertEqual(resolved["pr_review"], {
            "enabled": True, "reopen_on": ["changes_requested", "checks_failed"]})

    def test_closed_vocabulary_refuses_unknown_keys_at_every_level(self):
        cases = [
            {"surprise": 1},
            {"gates": {"nope": {}}},
            {"gates": {"plan_approval": {"surprise": 1}}},
            {"gates": {"plan_approval": {"required_flows": []}}},
            {"gates": {"acceptance": {"require": []}}},
            {"pr_review": {"surprise": 1}},
        ]
        for policy in cases:
            with self.assertRaises(g.InvalidGatePolicyError, msg=policy):
                g.validate_policy(policy)

    def test_value_validation(self):
        cases = [
            [1, 2], {"schema_version": 2}, {"schema_version": True}, {"human_approval": "yes"},
            {"human_approval": 1}, {"gates": []}, {"gates": {"plan_approval": []}},
            {"gates": {"plan_approval": {"human": "no"}}},
            {"gates": {"plan_approval": {"require": ["other"]}}},
            {"gates": {"plan_approval": {"require": "distinct_reviewer_models"}}},
            {"gates": {"plan_approval": {"require": ["distinct_reviewer_models", "distinct_reviewer_models"]}}},
            {"gates": {"acceptance": {"required_flows": ["Bad Flow"]}}},
            {"gates": {"acceptance": {"required_flows": ["ok", "ok"]}}},
            {"gates": {"acceptance": {"required_flows": [3]}}},
            {"gates": {"acceptance": {"require_ci": "yes"}}},
            {"pr_review": {"enabled": "yes"}},
            {"pr_review": {"reopen_on": ["merged"]}},
            {"pr_review": []},
        ]
        for policy in cases:
            with self.assertRaises(g.InvalidGatePolicyError, msg=policy):
                g.validate_policy(policy)
        g.validate_policy({"gates": {"acceptance": {"required_flows": ["migration-suite", "e2e_suite"]}},
                           "pr_review": {"enabled": False, "reopen_on": []}})

    def test_resolved_form_is_flat_sorted_and_complete(self):
        resolved = g.resolve_policy({"gates": {"acceptance": {"required_flows": ["b", "a"]}}})
        self.assertEqual(resolved["acceptance"]["required_flows"], ["a", "b"])
        self.assertEqual(g.resolved_errors(resolved), [])
        broken = copy.deepcopy(resolved)
        broken["acceptance"]["required_flows"] = ["b", "a"]
        self.assertTrue(g.resolved_errors(broken))

    def test_stricter_and_loosened_fields(self):
        base = g.DEFAULT_RESOLVED
        human = g.resolve_policy(HUMAN)
        self.assertEqual(g.loosened_fields(human, base),
                         ["plan_approval.human", "technical_approval.human", "acceptance.human"])
        self.assertEqual(g.loosened_fields(base, human), [])
        self.assertEqual(g.tightened_fields(base, human),
                         ["plan_approval.human", "technical_approval.human", "acceptance.human"])
        self.assertEqual(g.stricter(base, human), human)
        flows = g.resolve_policy({"gates": {"acceptance": {"required_flows": ["x"]}}})
        self.assertEqual(g.loosened_fields(flows, base), ["acceptance.required_flows"])
        self.assertEqual(g.stricter(base, flows)["acceptance"]["required_flows"], ["x"])
        no_require = g.resolve_policy(NO_REQUIRE)
        self.assertEqual(g.loosened_fields(base, no_require),
                         ["plan_approval.require", "technical_approval.require"])
        ci_off = g.resolve_policy({"gates": {"acceptance": {"require_ci": False}}})
        self.assertEqual(g.loosened_fields(base, ci_off), ["acceptance.require_ci"])
        pr_off = g.resolve_policy({"pr_review": {"enabled": False, "reopen_on": ["changes_requested"]}})
        self.assertEqual(g.loosened_fields(base, pr_off), ["pr_review.enabled", "pr_review.reopen_on"])

    def test_digest_is_canonical(self):
        a = {"schema_version": 1, "human_approval": True}
        b = {"human_approval": True, "schema_version": 1}
        self.assertEqual(g.policy_digest(a), g.policy_digest(b))
        self.assertNotEqual(g.policy_digest(a), g.policy_digest({"schema_version": 1}))
        self.assertRegex(g.policy_digest(a), r"^[0-9a-f]{64}$")


class TestConfirmation(unittest.TestCase):
    def test_confirmation_needs_the_literal_and_the_digest_prefix(self):
        digest = g.policy_digest(HUMAN)
        ws.validate_gate_policy_confirmation(f"gate_policy {digest[:12]}", digest)
        ws.validate_gate_policy_confirmation(f"yes, adopt gate_policy with {digest[:12]} please", digest)
        for text in ("", "   ", f"adopt {digest[:12]}", "gate_policy", f"gate_policy {digest[:11]}",
                     f"gate_policy {'0' * 12}", None):
            with self.assertRaises(g.GatePolicyConfirmationRejectedError, msg=text):
                ws.validate_gate_policy_confirmation(text, digest)

    def test_approval_stages_and_user_confirmation_are_untouched(self):
        self.assertNotIn("gate_policy", ws.APPROVAL_STAGES)
        with self.assertRaises(ws.InvalidApprovalRecordError):
            ws.validate_user_confirmation("gate_policy", work_item_id="wi", stage="gate_policy")

    def test_the_command_is_user_only_and_a_state_writer(self):
        raw = (REPO_ROOT / ".claude/commands/adopt-gate-policy.md").read_text()
        text = " ".join(raw.split())
        front = raw.split("---")[1]
        self.assertIn("disable-model-invocation: true", front)
        self.assertIn("state_writer: true", front)
        self.assertIn("review-subject: none", front)
        for needle in ("validate_gate_policy_confirmation", "gate_policy_adoption_preview",
                       "adopt_gate_policy", "stage_scoped_state", "Workflow-Gate-Policy-Adoption",
                       "validate_gate_policy_adoption_commit", "DirtyIndexBeforeStagingError",
                       "gate-lowering event", "/milestone-plan", "/recover-implementation-provenance"):
            self.assertIn(needle, text, needle)


class TestRecordShapes(unittest.TestCase):
    def adoption(self, policy=HUMAN, **overrides) -> dict:
        digest = g.policy_digest(policy)
        record = {"sha256": digest, "adopted_at": now(), "confirmation": f"gate_policy {digest[:12]}",
                  "policy": policy, "history": [], "lowered": []}
        record.update(overrides)
        return record

    def test_a_well_formed_adoption_has_no_errors(self):
        self.assertEqual(g.adoption_record_errors(self.adoption()), [])

    def test_adoption_record_errors(self):
        other = g.policy_digest(AUTOMATIC)
        cases = {
            "unknown key": {"extra": 1},
            "digest of another policy": {"sha256": other},
            "confirmation without digest": {"confirmation": "gate_policy"},
            "history not hex": {"history": ["abc"]},
            "lowered unknown field": {"lowered": ["nope.field"]},
            "lowered out of order": {"lowered": ["technical_approval.human", "plan_approval.human"]},
            "invalid policy": {"policy": {"surprise": 1}},
            "no adopted_at": {"adopted_at": ""},
        }
        for label, override in cases.items():
            self.assertTrue(g.adoption_record_errors(self.adoption(**override)), label)
        self.assertTrue(g.adoption_record_errors([]))
        missing = self.adoption()
        del missing["history"]
        self.assertTrue(g.adoption_record_errors(missing))

    def test_floor_record_errors(self):
        resolved = g.resolve_policy(HUMAN)
        floor = {"policy": resolved, "digest": g.policy_digest(resolved), "recorded_at": now(), "observed": []}
        self.assertEqual(g.floor_record_errors(floor), [])
        self.assertTrue(g.floor_record_errors(dict(floor, digest="0" * 64)))
        self.assertTrue(g.floor_record_errors(dict(floor, observed="x")))
        self.assertTrue(g.floor_record_errors(dict(floor, extra=1)))
        self.assertTrue(g.floor_record_errors(dict(floor, policy={"plan_approval": {}})))
        self.assertTrue(g.floor_record_errors("floor"))

    def test_validate_state_accepts_a_round_tripped_adoption_and_refuses_a_broken_one(self):
        state = h.base_state()
        self.assertNotIn(ws.GATE_POLICY_ADOPTION_KEY, state)
        ws.validate_state(state)
        adopted = ws.record_gate_policy_adoption(
            state, policy=HUMAN, confirmation=confirmation_for(HUMAN), now=now(), lowered=[])
        ws.validate_state(json.loads(ws._serialize_state(adopted)))
        broken = copy.deepcopy(adopted)
        broken[ws.GATE_POLICY_ADOPTION_KEY]["sha256"] = "0" * 64
        with self.assertRaises(ws.InvalidGatePolicyStateError):
            ws.validate_state(broken)
        broken = copy.deepcopy(adopted)
        broken[ws.GATE_POLICY_FLOOR_KEY]["digest"] = "0" * 64
        with self.assertRaises(ws.InvalidGatePolicyStateError):
            ws.validate_state(broken)

    def test_record_gate_policy_adoption_chains_history_and_resets_the_floor(self):
        state = h.base_state()
        first = ws.record_gate_policy_adoption(
            state, policy=HUMAN, confirmation=confirmation_for(HUMAN), now=now(), lowered=[])
        self.assertEqual(first[ws.GATE_POLICY_ADOPTION_KEY]["history"], [])
        self.assertEqual(first[ws.GATE_POLICY_FLOOR_KEY]["policy"], g.resolve_policy(HUMAN))
        self.assertNotIn(ws.GATE_POLICY_ADOPTION_KEY, state)
        second = ws.record_gate_policy_adoption(
            first, policy=AUTOMATIC, confirmation=confirmation_for(AUTOMATIC), now=now(),
            lowered=["plan_approval.human"])
        self.assertEqual(second[ws.GATE_POLICY_ADOPTION_KEY]["history"], [g.policy_digest(HUMAN)])
        self.assertEqual(second[ws.GATE_POLICY_FLOOR_KEY]["policy"], g.resolve_policy(AUTOMATIC))

    def test_record_gate_policy_adoption_refuses_a_bad_policy_or_confirmation(self):
        with self.assertRaises(ws.InvalidGatePolicyAdoptionError):
            ws.record_gate_policy_adoption(
                h.base_state(), policy={"surprise": 1}, confirmation="gate_policy", now=now(), lowered=[])
        with self.assertRaises(g.GatePolicyConfirmationRejectedError):
            ws.record_gate_policy_adoption(
                h.base_state(), policy=HUMAN, confirmation="adopt it", now=now(), lowered=[])
        with self.assertRaises(ws.InvalidGatePolicyAdoptionError):
            ws.record_gate_policy_adoption(
                h.base_state(), policy=HUMAN, confirmation=confirmation_for(HUMAN), now=now(),
                lowered=["nope"])


# ---------------------------------------------------------------------------
# the effective policy
# ---------------------------------------------------------------------------


class TestEffectivePolicy(unittest.TestCase):
    def test_no_file_every_gate_automatic_and_source_default(self):
        with PolicyRepo() as repo:
            eff = repo.eff()
            self.assertEqual(eff["source"], "default")
            self.assertEqual(eff["policy"], g.DEFAULT_RESOLVED)
            self.assertEqual(repo.human_gates(), set())
            self.assertFalse(eff["file"]["present"])

    def test_the_master_switch_makes_every_gate_human_at_once(self):
        with PolicyRepo() as repo:
            repo.write_policy(HUMAN)
            eff = repo.eff()
            self.assertEqual(eff["source"], "file_tightened")
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))

    def test_each_per_gate_override_resolves_as_specified(self):
        with PolicyRepo() as repo:
            repo.write_policy(PLAN_HUMAN)
            self.assertEqual(repo.human_gates(), {"plan_approval"})
            repo.write_policy(ACCEPTANCE_HUMAN)
            self.assertEqual(repo.human_gates(), {"acceptance"})
            repo.write_policy({"human_approval": True, "gates": {
                "plan_approval": {"human": False}, "technical_approval": {"human": False}}})
            self.assertEqual(repo.human_gates(), {"acceptance"})

    def test_a_file_that_adds_a_requirement_a_flow_or_requires_pr_approval_is_effective_at_once(self):
        with PolicyRepo() as repo:
            repo.write_policy({"gates": {"acceptance": {
                "required_flows": ["e2e-suite"], "requires_pr_approved": True}}})
            eff = repo.eff()
            self.assertEqual(eff["source"], "file_tightened")
            self.assertEqual(eff["policy"]["acceptance"]["required_flows"], ["e2e-suite"])
            self.assertTrue(eff["policy"]["acceptance"]["requires_pr_approved"])

    def test_a_loosening_in_the_file_is_ignored_and_never_removes_the_default_require(self):
        with PolicyRepo() as repo:
            repo.write_policy(NO_REQUIRE)
            eff = repo.eff()
            self.assertEqual(eff["source"], "file_loosening_ignored")
            self.assertEqual(eff["policy"]["plan_approval"]["require"], ["distinct_reviewer_models"])
            self.assertEqual(eff["ignored_fields"], ["plan_approval.require", "technical_approval.require"])

    def test_an_invalid_file_never_raises_and_leaves_the_default(self):
        with PolicyRepo() as repo:
            for body in ("{not json", json.dumps({"surprise": 1}), "[]", '"x"'):
                repo.write_policy(body)
                eff = repo.eff()
                self.assertEqual(eff["source"], "invalid", body)
                self.assertEqual(eff["policy"], g.DEFAULT_RESOLVED)
                self.assertTrue(eff["file"]["errors"])

    def test_a_non_regular_policy_file_is_invalid(self):
        with PolicyRepo() as repo:
            (repo.root / POLICY_REL).symlink_to("elsewhere.json")
            self.assertEqual(repo.eff()["source"], "invalid")

    def test_a_file_equal_to_the_default_reports_default(self):
        with PolicyRepo() as repo:
            repo.write_policy(g.DEFAULT_POLICY)
            self.assertEqual(repo.eff()["source"], "default")
            repo.write_policy(AUTOMATIC)
            self.assertEqual(repo.eff()["source"], "default")

    def test_a_repository_with_no_commits_still_resolves(self):
        g.clear_caches()
        root = Path(tempfile.mkdtemp(prefix="gp-empty-"))
        try:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            self.assertEqual(g.effective_policy(root, {})["source"], "default")
            self.assertTrue(g.verify_gate_policy_provenance(root)["ok"])
            self.assertIsNone(g.gate_lowering_event(root))
        finally:
            shutil.rmtree(root, ignore_errors=True)


class TestTightenOnlyAfterAdoption(unittest.TestCase):
    def adopted_human(self, repo: PolicyRepo) -> None:
        repo.adopt(HUMAN)

    def test_every_row_of_the_table_after_an_adopted_human_policy(self):
        with PolicyRepo() as repo:
            self.adopted_human(repo)
            eff = repo.eff()
            self.assertEqual(eff["source"], "adopted")
            self.assertEqual(eff["base"]["sha256"], g.policy_digest(HUMAN))
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))
            # file equal to the adopted policy: adopted
            repo.write_policy(HUMAN)
            self.assertEqual(repo.eff()["source"], "adopted")
            # an edit back to automatic: the adopted value stays
            repo.write_policy(AUTOMATIC)
            eff = repo.eff()
            self.assertEqual(eff["source"], "file_loosening_ignored")
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))
            # an invalid file
            repo.write_policy("{broken")
            self.assertEqual(repo.eff()["source"], "invalid")
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))
            # a deleted file: adopted, nothing stricter
            repo.remove_policy()
            self.assertEqual(repo.eff()["source"], "adopted")
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))

    def test_a_tightening_over_an_adopted_automatic_policy_is_file_tightened(self):
        with PolicyRepo() as repo:
            repo.adopt(AUTOMATIC)
            self.assertEqual(repo.eff()["source"], "adopted")
            repo.write_policy(PLAN_HUMAN)
            self.assertEqual(repo.eff()["source"], "file_tightened")
            self.assertEqual(repo.human_gates(), {"plan_approval"})

    def test_re_adoption_of_a_looser_file_is_the_only_path_to_a_looser_policy(self):
        with PolicyRepo() as repo:
            self.adopted_human(repo)
            repo.write_policy(AUTOMATIC)
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))
            ws.adopt_gate_policy(repo.root, confirmation=confirmation_for(AUTOMATIC), now=now())
            self.assertEqual(repo.human_gates(), set())
            state = repo.state()
            adoption = state[ws.GATE_POLICY_ADOPTION_KEY]
            self.assertEqual(adoption["policy"], AUTOMATIC)
            self.assertEqual(adoption["history"], [g.policy_digest(HUMAN)])
            self.assertEqual(state[ws.GATE_POLICY_FLOOR_KEY]["policy"], g.resolve_policy(AUTOMATIC))

    def test_the_adoption_record_stores_the_body_so_a_deleted_file_cannot_loosen_it(self):
        with PolicyRepo() as repo:
            repo.adopt(PLAN_HUMAN)
            repo.remove_policy()
            self.assertEqual(repo.human_gates(), {"plan_approval"})
            self.assertEqual(repo.state()[ws.GATE_POLICY_ADOPTION_KEY]["policy"], PLAN_HUMAN)


class TestFloorRatchet(unittest.TestCase):
    """B1: a user-activated human setting survives removal."""

    def test_a_committing_evaluation_records_the_floor_and_each_removal_keeps_it(self):
        for removal in ("delete", "edit_back", "delete_and_commit"):
            with self.subTest(removal), PolicyRepo() as repo:
                repo.write_policy(PLAN_HUMAN)
                commit = repo.record_floor()
                self.assertIsNotNone(commit)
                self.assertEqual(repo.git("log", "-1", "--format=%B").splitlines()[-1],
                                 f"{ws.GATE_POLICY_FLOOR_TRAILER}: {repo.state()[ws.GATE_POLICY_FLOOR_KEY]['digest']}")
                self.assertEqual(repo.human_gates(), {"plan_approval"})
                if removal == "delete":
                    repo.remove_policy()
                elif removal == "edit_back":
                    repo.write_policy(AUTOMATIC)
                else:
                    repo.commit_policy(PLAN_HUMAN, "commit the file")
                    repo.delete_policy_and_commit()
                eff = repo.eff()
                self.assertEqual(repo.human_gates(), {"plan_approval"})
                self.assertIn(eff["source"], {"floor", "file_loosening_ignored"})

    def test_no_stricter_setting_writes_nothing_and_makes_no_commit(self):
        with PolicyRepo() as repo:
            head = repo.head()
            self.assertIsNone(repo.record_floor())
            repo.write_policy(AUTOMATIC)
            self.assertIsNone(repo.record_floor())
            self.assertEqual(repo.head(), head)
            self.assertNotIn(ws.GATE_POLICY_FLOOR_KEY, repo.state())

    def test_a_read_only_evaluation_computes_the_same_floor_virtually(self):
        with PolicyRepo() as repo:
            repo.write_policy(PLAN_HUMAN)
            virtual = repo.eff()
            self.assertTrue(virtual["floor"]["present"])
            self.assertTrue(virtual["floor"]["pending"])
            self.assertNotIn(ws.GATE_POLICY_FLOOR_KEY, repo.state())
            repo.record_floor()
            recorded = repo.eff()
            self.assertEqual(recorded["floor"]["digest"], virtual["floor"]["digest"])
            self.assertFalse(recorded["floor"]["pending"])

    def test_a_file_committed_once_and_deleted_before_any_evaluation_is_seen_through_history(self):
        with PolicyRepo() as repo:
            repo.commit_policy(PLAN_HUMAN)
            repo.delete_policy_and_commit()
            eff = repo.eff()
            self.assertEqual(repo.human_gates(), {"plan_approval"})
            self.assertEqual(eff["source"], "floor")
            # a committing evaluation records it durably
            self.assertIsNotNone(repo.record_floor())
            self.assertEqual(repo.state()[ws.GATE_POLICY_FLOOR_KEY]["policy"]["plan_approval"]["human"], True)

    def test_only_adoption_lowers_the_floor(self):
        with PolicyRepo() as repo:
            repo.write_policy(HUMAN)
            repo.record_floor()
            repo.remove_policy()
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))
            repo.adopt(AUTOMATIC)
            self.assertEqual(repo.human_gates(), set())
            self.assertEqual(repo.eff()["source"], "adopted")

    def test_the_floor_is_never_loosened_by_a_later_recording(self):
        with PolicyRepo() as repo:
            repo.write_policy(PLAN_HUMAN)
            repo.record_floor()
            repo.write_policy(ACCEPTANCE_HUMAN)
            repo.record_floor()
            self.assertEqual(repo.human_gates(), {"plan_approval", "acceptance"})

    def test_a_working_tree_floor_edit_to_a_looser_value_is_ignored(self):
        with PolicyRepo() as repo:
            repo.write_policy(HUMAN)
            repo.record_floor()
            repo.remove_policy()
            state = repo.state()
            state[ws.GATE_POLICY_FLOOR_KEY]["policy"] = copy.deepcopy(g.DEFAULT_RESOLVED)
            state[ws.GATE_POLICY_FLOOR_KEY]["digest"] = g.policy_digest(g.DEFAULT_RESOLVED)
            repo.write_state(state)
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))

    def test_the_recorded_floor_restores_a_working_tree_removal_of_it(self):
        with PolicyRepo() as repo:
            repo.write_policy(HUMAN)
            repo.record_floor()
            state = repo.state()
            del state[ws.GATE_POLICY_FLOOR_KEY]
            repo.write_state(state)
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))
            restored = g.record_gate_policy_floor(repo.root, state, now())
            self.assertEqual(restored[ws.GATE_POLICY_FLOOR_KEY], json.loads(
                repo.git("show", f"HEAD:{STATE_REL}"))[ws.GATE_POLICY_FLOOR_KEY])

    def test_a_human_setting_committed_and_deleted_inside_one_squashed_branch_is_not_recovered(self):
        """The documented residual: no committing evaluation recorded it, and
        the squash leaves no trace of it on `main`."""
        with PolicyRepo() as repo:
            repo.branch("feature")
            repo.commit_policy(HUMAN)
            repo.delete_policy_and_commit()
            (repo.root / "feature.txt").write_text("feature work\n")
            repo.commit("feature work", "feature.txt")
            repo.checkout("main")
            repo.squash("feature")
            eff = repo.eff()
            self.assertEqual(eff["source"], "default")
            self.assertEqual(repo.human_gates(), set())
            status, _ = g.verify_check(repo.root, repo.state())
            self.assertEqual(status, "pass")


# ---------------------------------------------------------------------------
# provenance by content and chain (B2)
# ---------------------------------------------------------------------------


def failed_fields(prov: dict) -> list[str]:
    return [f["field"] for f in prov["failures"]]


def loosened_floor(state: dict, *fields: str) -> dict:
    """`state` with the recorded floor loosened in `fields` (digest kept
    self-consistent: a loosening a hand-built commit would make)."""
    state = copy.deepcopy(state)
    floor = state[ws.GATE_POLICY_FLOOR_KEY]
    for field in fields:
        section, key = field.split(".")
        floor["policy"][section][key] = False if isinstance(floor["policy"][section][key], bool) else []
    floor["digest"] = g.policy_digest(floor["policy"])
    return state


class TestProvenance(unittest.TestCase):
    def test_working_tree_edits_of_either_field_change_nothing(self):
        with PolicyRepo() as repo:
            repo.adopt(PLAN_HUMAN)
            for edit in ("remove_adoption", "replace_adoption", "loosen_floor", "remove_floor"):
                state = repo.state()
                if edit == "remove_adoption":
                    del state[ws.GATE_POLICY_ADOPTION_KEY]
                elif edit == "replace_adoption":
                    state = ws.record_gate_policy_adoption(
                        state, policy=AUTOMATIC, confirmation=confirmation_for(AUTOMATIC), now=now(),
                        lowered=[])
                elif edit == "loosen_floor":
                    state = loosened_floor(state, "plan_approval.human")
                else:
                    del state[ws.GATE_POLICY_FLOOR_KEY]
                repo.write_state(state)
                eff = repo.eff()
                self.assertEqual(eff["source"], "adopted", edit)
                self.assertEqual(repo.human_gates(), {"plan_approval"}, edit)
                self.assertTrue(repo.prov()["ok"], edit)
                repo.git("checkout", "--", STATE_REL)

    def broken_adoption_edits(self):
        def other_policy(state):
            record = ws.record_gate_policy_adoption(
                h.base_state(), policy=AUTOMATIC, confirmation=confirmation_for(AUTOMATIC), now=now(),
                lowered=[])
            state[ws.GATE_POLICY_ADOPTION_KEY] = record[ws.GATE_POLICY_ADOPTION_KEY]
        def broken_digest(state):
            state[ws.GATE_POLICY_ADOPTION_KEY]["sha256"] = "0" * 64
        def removed(state):
            del state[ws.GATE_POLICY_ADOPTION_KEY]
        def no_digest_in_confirmation(state):
            state[ws.GATE_POLICY_ADOPTION_KEY]["confirmation"] = "gate_policy please"
        def spliced_history(state):
            state[ws.GATE_POLICY_ADOPTION_KEY]["history"] = ["1" * 64]
        return {"replaced (no chain)": other_policy, "broken digest": broken_digest,
                "removed": removed, "confirmation": no_digest_in_confirmation,
                "spliced history": spliced_history}

    def test_a_commit_changing_the_adoption_without_a_valid_chain_fails_closed(self):
        for with_trailer in (False, True):
            for label, edit in self.broken_adoption_edits().items():
                with self.subTest(label, trailer=with_trailer), PolicyRepo() as repo:
                    repo.adopt(HUMAN)
                    trailers = {ws.GATE_POLICY_ADOPTION_TRAILER: "0" * 64} if with_trailer else None
                    commit = repo.hand_state_commit(edit, "hand edit", trailers=trailers)
                    prov = repo.prov()
                    self.assertFalse(prov["ok"])
                    self.assertIn(g.ADOPTION_KEY, failed_fields(prov))
                    self.assertEqual(prov["failures"][0]["commit"], commit)
                    eff = repo.eff()
                    self.assertEqual(eff["source"], "provenance_failed")
                    self.assertEqual(repo.human_gates(), set(g.GATE_IDS))
                    status, detail = g.verify_check(repo.root, repo.state())
                    self.assertEqual(status, "fail")
                    self.assertIn(g.ADOPTION_KEY, detail)
                    self.assertIn(commit[:12], detail)
                    self.assertIn("/adopt-gate-policy", detail)

    def test_a_new_adoption_restores_a_normal_state(self):
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            repo.hand_state_commit(self.broken_adoption_edits()["broken digest"])
            self.assertFalse(repo.prov()["ok"])
            repo.adopt(PLAN_HUMAN)
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.eff()["source"], "adopted")
            self.assertEqual(repo.human_gates(), {"plan_approval"})

    def test_a_commit_loosening_or_removing_the_floor_fails_closed(self):
        edits = {
            "loosened": lambda state: state.update(loosened_floor(state, "plan_approval.human")),
            "emptied require": lambda state: state.update(loosened_floor(state, "plan_approval.require")),
            "removed": lambda state: state.pop(ws.GATE_POLICY_FLOOR_KEY),
            "digest broken": lambda state: state[ws.GATE_POLICY_FLOOR_KEY].update(digest="0" * 64),
        }
        for label, edit in edits.items():
            for with_trailer in (False, True):
                with self.subTest(label, trailer=with_trailer), PolicyRepo() as repo:
                    repo.adopt(HUMAN)
                    trailers = {ws.GATE_POLICY_FLOOR_TRAILER: "0" * 64} if with_trailer else None
                    repo.hand_state_commit(edit, "hand edit", trailers=trailers)
                    prov = repo.prov()
                    self.assertFalse(prov["ok"])
                    self.assertIn(g.FLOOR_KEY, failed_fields(prov))
                    self.assertEqual(repo.eff()["source"], "provenance_failed")
                    self.assertEqual(repo.human_gates(), set(g.GATE_IDS))
                    status, detail = g.verify_check(repo.root, repo.state())
                    self.assertEqual(status, "fail")
                    self.assertIn(g.FLOOR_KEY, detail)

    def test_a_trailer_that_disagrees_with_the_adoption_digest_is_a_failure(self):
        with PolicyRepo() as repo:
            state = repo.adoption_state(HUMAN)
            repo.write_state(state)
            repo.commit("adoption", STATE_REL, trailers={ws.GATE_POLICY_ADOPTION_TRAILER: "f" * 64})
            prov = repo.prov()
            self.assertFalse(prov["ok"])
            self.assertIn("trailer", prov["failures"][0]["reason"])

    def test_a_self_consistent_chained_adoption_with_no_trailer_verifies(self):
        with PolicyRepo() as repo:
            repo.hand_adopt(HUMAN, trailer=False)
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.eff()["source"], "adopted")

    def test_a_floor_tightening_verifies_by_monotonicity(self):
        with PolicyRepo() as repo:
            repo.adopt(AUTOMATIC)

            def tighten(state):
                floor = state[ws.GATE_POLICY_FLOOR_KEY]
                floor["policy"]["plan_approval"]["human"] = True
                floor["digest"] = g.policy_digest(floor["policy"])
            repo.hand_state_commit(tighten, "tighten")
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.human_gates(), {"plan_approval"})

    def test_the_floors_range_a_later_tightening_in_another_field_hides_nothing(self):
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            repo.hand_state_commit(lambda state: state.update(loosened_floor(state, "plan_approval.human")),
                                   "hand loosening")
            self.assertFalse(repo.prov()["ok"])

            def tighten_other(state):
                floor = state[ws.GATE_POLICY_FLOOR_KEY]
                floor["policy"]["acceptance"]["required_flows"] = ["extra"]
                floor["digest"] = g.policy_digest(floor["policy"])
            repo.hand_state_commit(tighten_other, "a later /satisfy-gate style tightening")
            prov = repo.prov()
            self.assertFalse(prov["ok"], "each floor change is compared with its own first parent")
            self.assertEqual(len(prov["failures"]), 1)

    def test_a_loosening_before_a_valid_adoption_stops_failing_once_the_adoption_is_newest(self):
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            repo.hand_state_commit(lambda state: state.update(loosened_floor(state, "plan_approval.human")))
            self.assertFalse(repo.prov()["ok"])
            repo.adopt(PLAN_HUMAN)
            self.assertTrue(repo.prov()["ok"])

    def test_a_loosening_after_the_adoption_fails(self):
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            self.assertTrue(repo.prov()["ok"])
            repo.hand_state_commit(lambda state: state.update(loosened_floor(state, "acceptance.human")))
            self.assertFalse(repo.prov()["ok"])

    def test_with_no_adoption_ever_the_range_runs_to_the_root(self):
        with PolicyRepo() as repo:
            repo.write_policy(PLAN_HUMAN)
            repo.record_floor()
            self.assertTrue(repo.prov()["ok"])
            repo.hand_state_commit(lambda state: state.update(loosened_floor(state, "plan_approval.human")))
            self.assertFalse(repo.prov()["ok"])
            repo.write_policy(AUTOMATIC)
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))

    def test_unvalidated_commits_are_checked_by_the_assert(self):
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            plain = repo.hand_state_commit(lambda state: state.setdefault("note", 1), "unrelated")
            ws.assert_gate_policy_fields_unchanged_or_tightened(repo.root, plain)
            tightened = repo.hand_state_commit(lambda state: (
                state[ws.GATE_POLICY_FLOOR_KEY]["policy"]["acceptance"].update(required_flows=["f"]),
                state[ws.GATE_POLICY_FLOOR_KEY].update(
                    digest=g.policy_digest(state[ws.GATE_POLICY_FLOOR_KEY]["policy"]))), "tighten")
            ws.assert_gate_policy_fields_unchanged_or_tightened(repo.root, tightened)
            loosened = repo.hand_state_commit(lambda state: state.update(
                loosened_floor(state, "plan_approval.human")), "loosen")
            with self.assertRaises(g.GatePolicyFieldsChangedError) as raised:
                ws.assert_gate_policy_fields_unchanged_or_tightened(repo.root, loosened)
            self.assertEqual(raised.exception.failures[0]["field"], g.FLOOR_KEY)
            bad_adoption = repo.hand_state_commit(
                self.broken_adoption_edits()["broken digest"], "break the adoption")
            with self.assertRaises(g.GatePolicyFieldsChangedError):
                ws.assert_gate_policy_fields_unchanged_or_tightened(repo.root, bad_adoption)

    def test_verify_plan_approval_commit_applies_the_check_to_its_commit(self):
        from unittest import mock
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            commit = repo.hand_state_commit(lambda state: state.update(
                loosened_floor(state, "plan_approval.human")), "approval that rides a loosening")
            state = repo.state()
            state["work_items"]["wi"] = h.base_work_item(plan_approval={"review_content_manifest": []})
            repo.write_state(state)
            commit = repo.commit("approval", STATE_REL)
            journal = {"expected_post_state_sha256": "x", "work_item_id": "wi",
                       "expected_review_content_id": "y", "base_commit": repo.scratch.base,
                       "applicable_paths": [], "fifth_member_applies": False, "removal_paths": []}
            with mock.patch.object(ws, "verify_committed_plan_approval_state_blob"), \
                    mock.patch.object(ws, "verify_post_approval_manifest_match"), \
                    mock.patch.object(ws, "assert_committed_path_set_matches"), \
                    mock.patch.object(ws, "assert_committed_plan_approval_closure"):
                # the loosening is in the earlier commit; this one is clean
                ws.verify_plan_approval_commit(repo.root, journal, commit)
                bad = repo.hand_state_commit(lambda s: s.update(loosened_floor(s, "acceptance.human")), "loosen")
                with self.assertRaises(g.GatePolicyFieldsChangedError):
                    ws.verify_plan_approval_commit(repo.root, journal, bad)
        source = Path(ws.__file__).read_text()
        body = source[source.index("def verify_plan_approval_commit("):]
        body = body[:body.index("\ndef classify_post_commit_verification_failure")]
        self.assertIn("assert_gate_policy_fields_unchanged_or_tightened(repo_root, commit)", body)


# ---------------------------------------------------------------------------
# the squash case (`LPR-R9-001`), with this repository's merge settings
# ---------------------------------------------------------------------------


class TestSquashMerge(unittest.TestCase):
    def feature(self, repo: PolicyRepo) -> None:
        repo.branch("feature")

    def test_an_adoption_keeps_verifying_after_a_squash_and_on_a_new_branch(self):
        with PolicyRepo() as repo:
            self.feature(repo)
            repo.adopt(HUMAN)
            repo.checkout("main")
            squash = repo.squash("feature")
            self.assertEqual(repo.git("log", "-1", "--format=%b").strip(), "", "a blank squash body")
            self.assertEqual(g.ADOPTION_TRAILER, ws.GATE_POLICY_ADOPTION_TRAILER)
            self.assertNotIn(g.ADOPTION_TRAILER, repo.git("log", "-1", "--format=%B"))
            for branch in (None, "next"):
                if branch:
                    repo.branch(branch)
                self.assertTrue(repo.prov()["ok"], branch)
                eff = repo.eff()
                self.assertEqual(eff["source"], "adopted")
                self.assertEqual(repo.human_gates(), set(g.GATE_IDS))
            self.assertEqual(repo.git("rev-list", "--count", "main"), "3")
            self.assertTrue(squash)

    def test_an_adoption_lowered_floor_survives_a_squash(self):
        with PolicyRepo() as repo:
            repo.write_policy(HUMAN)
            repo.record_floor()
            repo.remove_policy()
            repo.branch("feature")
            repo.adopt(AUTOMATIC)
            repo.checkout("main")
            repo.squash("feature")
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.eff()["source"], "adopted")
            self.assertEqual(repo.human_gates(), set())
            self.assertEqual(repo.state()[ws.GATE_POLICY_FLOOR_KEY]["policy"], g.resolve_policy(AUTOMATIC))
            repo.branch("next")
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.human_gates(), set())

    def test_a_squash_with_a_broken_adoption_or_a_loosened_floor_fails_closed(self):
        edits = {
            "broken digest": lambda state: state[ws.GATE_POLICY_ADOPTION_KEY].update(sha256="0" * 64),
            "broken chain": lambda state: state[ws.GATE_POLICY_ADOPTION_KEY].update(history=["2" * 64]),
            "removed record": lambda state: state.pop(ws.GATE_POLICY_ADOPTION_KEY),
        }
        for label, edit in edits.items():
            with self.subTest(label), PolicyRepo() as repo:
                repo.adopt(PLAN_HUMAN)
                repo.branch("feature")
                repo.adopt(HUMAN)
                repo.hand_state_commit(edit, "hand edit")
                repo.checkout("main")
                repo.squash("feature")
                prov = repo.prov()
                self.assertFalse(prov["ok"])
                self.assertEqual(repo.eff()["source"], "provenance_failed")
        with self.subTest("floor loosened without an adoption"), PolicyRepo() as repo:
            repo.adopt(HUMAN)
            repo.branch("feature")
            repo.hand_state_commit(lambda state: state.update(loosened_floor(state, "plan_approval.human")))
            repo.checkout("main")
            repo.squash("feature")
            self.assertFalse(repo.prov()["ok"])
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))

    def test_two_adoptions_folded_into_one_squash_verify_through_the_chain(self):
        with PolicyRepo() as repo:
            repo.branch("feature")
            repo.adopt(HUMAN)
            repo.adopt(PLAN_HUMAN)
            repo.checkout("main")
            repo.squash("feature")
            self.assertTrue(repo.prov()["ok"])
            adoption = repo.state()[ws.GATE_POLICY_ADOPTION_KEY]
            self.assertEqual(adoption["history"], [g.policy_digest(HUMAN)])
            self.assertEqual(repo.human_gates(), {"plan_approval"})

    def test_a_floor_recorded_on_a_branch_survives_its_squash_and_a_later_file_deletion(self):
        with PolicyRepo() as repo:
            repo.branch("feature")
            repo.write_policy(PLAN_HUMAN)
            repo.record_floor()
            repo.remove_policy()
            repo.checkout("main")
            repo.squash("feature")
            repo.branch("next")
            repo.write_policy(AUTOMATIC)
            repo.remove_policy()
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.human_gates(), {"plan_approval"})
            self.assertEqual(repo.eff()["source"], "floor")


# ---------------------------------------------------------------------------
# concurrent branches (`LPR-R10-004`)
# ---------------------------------------------------------------------------


def stricter_floor(first: dict, second: dict) -> dict:
    result = copy.deepcopy(first)
    merged = g.stricter(first[ws.GATE_POLICY_FLOOR_KEY]["policy"], second[ws.GATE_POLICY_FLOOR_KEY]["policy"])
    result[ws.GATE_POLICY_FLOOR_KEY]["policy"] = merged
    result[ws.GATE_POLICY_FLOOR_KEY]["digest"] = g.policy_digest(merged)
    return result


def with_floor(state: dict, floor: dict) -> dict:
    state = copy.deepcopy(state)
    state[ws.GATE_POLICY_FLOOR_KEY] = copy.deepcopy(floor)
    return state


def take_theirs(ours, theirs, base):
    return copy.deepcopy(theirs)


def take_ours(ours, theirs, base):
    return copy.deepcopy(ours)


def only_fields(state: dict, keep_from: dict, fields: list[str]) -> dict:
    """`state` with each named floor field taken from `keep_from`'s floor."""
    state = copy.deepcopy(state)
    floor = state[ws.GATE_POLICY_FLOOR_KEY]["policy"]
    for field in fields:
        section, key = field.split(".")
        floor[section][key] = copy.deepcopy(keep_from[ws.GATE_POLICY_FLOOR_KEY]["policy"][section][key])
    state[ws.GATE_POLICY_FLOOR_KEY]["digest"] = g.policy_digest(floor)
    return state


class TestConcurrentBranches(unittest.TestCase):
    def two_floor_branches(self, repo: PolicyRepo):
        """Two branches from one base record different floors; the first is
        squash-merged into `main`. Returns each branch's floor state."""
        repo.branch("A")
        repo.write_policy(PLAN_HUMAN)
        repo.record_floor()
        repo.remove_policy()
        floor_a = repo.state()
        repo.checkout("main")
        repo.branch("B")
        repo.write_policy(ACCEPTANCE_HUMAN)
        repo.record_floor()
        repo.remove_policy()
        floor_b = repo.state()
        repo.checkout("main")
        repo.squash("A")
        repo.checkout("B")
        return floor_a, floor_b

    def test_a_floor_conflict_resolved_to_the_stricter_of_both_sides_verifies_and_squashes(self):
        with PolicyRepo() as repo:
            floor_a, floor_b = self.two_floor_branches(repo)
            repo.merge("main", lambda ours, theirs, base: stricter_floor(ours, theirs))
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.human_gates(), {"plan_approval", "acceptance"})
            repo.checkout("main")
            repo.squash("B")
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.human_gates(), {"plan_approval", "acceptance"})

    def test_a_floor_conflict_resolved_to_the_looser_side_fails_the_squash_closed(self):
        with PolicyRepo() as repo:
            floor_a, floor_b = self.two_floor_branches(repo)
            repo.merge("main", take_ours)
            repo.checkout("main")
            repo.squash("B")
            prov = repo.prov()
            self.assertFalse(prov["ok"])
            self.assertEqual(repo.eff()["source"], "provenance_failed")
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))
            repo.branch("fix")
            repo.adopt(PLAN_HUMAN)
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.eff()["source"], "adopted")

    def two_adoption_branches(self, repo: PolicyRepo):
        repo.branch("A")
        repo.adopt(HUMAN)
        repo.checkout("main")
        repo.branch("B")
        repo.adopt(PLAN_HUMAN)
        repo.checkout("main")
        repo.squash("A")
        repo.checkout("B")

    def test_a_concurrent_second_adoption_fails_closed_and_is_re_adopted_after_updating(self):
        with PolicyRepo() as repo:
            self.two_adoption_branches(repo)
            repo.merge("main", take_ours)
            repo.checkout("main")
            repo.squash("B")
            self.assertFalse(repo.prov()["ok"])
            self.assertIn(g.ADOPTION_KEY, failed_fields(repo.prov()))
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS))
        with self.subTest("take main's record, then re-adopt"), PolicyRepo() as repo:
            self.two_adoption_branches(repo)
            repo.merge("main", take_theirs)
            repo.adopt(PLAN_HUMAN)
            adoption = repo.state()[ws.GATE_POLICY_ADOPTION_KEY]
            self.assertEqual(len(adoption["history"]), 1)
            self.assertTrue(repo.prov()["ok"])
            repo.checkout("main")
            repo.squash("B")
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.eff()["source"], "adopted")
            self.assertEqual(repo.human_gates(), {"plan_approval"})
        with self.subTest("keeping the branch's record and re-adopting still fails"), PolicyRepo() as repo:
            self.two_adoption_branches(repo)
            repo.merge("main", take_ours)
            repo.adopt(AUTOMATIC)
            repo.checkout("main")
            repo.squash("B")
            self.assertFalse(repo.prov()["ok"])

    def adoption_on_main_while_b_is_in_flight(self, repo: PolicyRepo, *, b_floor_edit=None):
        """`main` holds a human floor; `A` adopts the automatic policy
        (lowering it) and is squash-merged; `B`, cut earlier, either
        recorded a stricter floor or recorded nothing."""
        repo.write_policy(HUMAN)
        repo.record_floor()
        repo.remove_policy()
        repo.branch("B")
        if b_floor_edit is not None:
            b_floor_edit(repo)
        else:
            (repo.root / "b.txt").write_text("b work\n")
            repo.commit("b work", "b.txt")
        repo.checkout("main")
        repo.branch("A")
        repo.adopt(AUTOMATIC)
        repo.checkout("main")
        repo.squash("A")
        repo.checkout("B")

    def record_flows_floor(self, repo: PolicyRepo):
        repo.write_policy({"human_approval": True, "gates": {"acceptance": {"required_flows": ["x"]}}})
        repo.record_floor()
        repo.remove_policy()

    def test_an_adoption_on_main_dropping_a_floor_b_recorded_fails_closed_at_the_merge(self):
        with PolicyRepo() as repo:
            self.adoption_on_main_while_b_is_in_flight(repo, b_floor_edit=self.record_flows_floor)
            repo.merge("main", take_theirs)
            prov = repo.prov()
            self.assertFalse(prov["ok"])
            self.assertEqual(failed_fields(prov), [g.FLOOR_KEY])
            self.assertEqual(prov["failures"][0]["commit"], repo.head(), "fails at the merge, before any squash")

    def test_resolving_stricter_for_the_fields_b_recorded_or_re_adopting_restores_a_normal_state(self):
        with PolicyRepo() as repo:
            self.adoption_on_main_while_b_is_in_flight(repo, b_floor_edit=self.record_flows_floor)
            floor_b = repo.state()
            repo.merge("main", lambda ours, theirs, base: only_fields(theirs, ours, ["acceptance.required_flows"]))
            self.assertTrue(repo.prov()["ok"])
            policy = repo.eff()["policy"]
            self.assertEqual(policy["acceptance"]["required_flows"], ["x"])
            self.assertFalse(policy["plan_approval"]["human"], "the fields b did not record take main's value")
            self.assertTrue(floor_b)
        with self.subTest("re-adopting"), PolicyRepo() as repo:
            self.adoption_on_main_while_b_is_in_flight(repo, b_floor_edit=self.record_flows_floor)
            repo.merge("main", take_theirs)
            self.assertFalse(repo.prov()["ok"])
            repo.adopt(AUTOMATIC)
            self.assertTrue(repo.prov()["ok"])

    def test_the_failure_message_names_the_re_adoption_remedy(self):
        with PolicyRepo() as repo:
            self.adoption_on_main_while_b_is_in_flight(repo, b_floor_edit=self.record_flows_floor)
            repo.merge("main", take_theirs)
            status, detail = g.verify_check(repo.root, repo.state())
            self.assertEqual(status, "fail")
            self.assertIn("/adopt-gate-policy", detail)

    def test_an_adoption_on_main_while_b_recorded_nothing_verifies_and_stays_lowered(self):
        with PolicyRepo() as repo:
            self.adoption_on_main_while_b_is_in_flight(repo)
            repo.merge("main")
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.human_gates(), set(), "the gate the adoption made automatic stays automatic")
            repo.checkout("main")
            repo.squash("B")
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.state()[ws.GATE_POLICY_FLOOR_KEY]["policy"], g.resolve_policy(AUTOMATIC))

    def test_a_variant_where_b_recorded_one_stricter_field_keeps_it_and_takes_mains_for_the_rest(self):
        with PolicyRepo() as repo:
            self.adoption_on_main_while_b_is_in_flight(repo, b_floor_edit=self.record_flows_floor)
            repo.merge("main", lambda ours, theirs, base: only_fields(theirs, ours, ["acceptance.required_flows"]))
            self.assertTrue(repo.prov()["ok"])
            floor = repo.state()[ws.GATE_POLICY_FLOOR_KEY]["policy"]
            self.assertEqual(floor["acceptance"]["required_flows"], ["x"])
            self.assertEqual({gate for gate in g.GATE_IDS if floor[gate]["human"]}, set())

    def criss_cross(self, repo: PolicyRepo):
        repo.branch("X")
        repo.write_policy(PLAN_HUMAN)
        repo.record_floor()
        repo.remove_policy()
        repo.checkout("main")
        repo.branch("Y")
        repo.write_policy(ACCEPTANCE_HUMAN)
        repo.record_floor()
        repo.remove_policy()
        x_tip = repo.git("rev-parse", "X")
        y_tip = repo.git("rev-parse", "Y")
        both = lambda ours, theirs, base: stricter_floor(ours, theirs)
        repo.checkout("X")
        repo.git("checkout", "-q", "-b", "m2", x_tip)
        repo.merge(y_tip, both)
        m2 = repo.head()
        repo.checkout("Y")
        repo.git("checkout", "-q", "-b", "m1", y_tip)
        repo.merge(x_tip, both)
        return m2

    def test_a_criss_cross_merge_with_two_merge_bases_fails_closed(self):
        with PolicyRepo() as repo:
            m2 = self.criss_cross(repo)
            self.assertEqual(len(repo.git("merge-base", "--all", "HEAD", m2).split()), 2)

            def extra(ours, theirs, base):
                state = stricter_floor(ours, theirs)
                floor = state[ws.GATE_POLICY_FLOOR_KEY]["policy"]
                floor["acceptance"]["required_flows"] = ["extra"]
                state[ws.GATE_POLICY_FLOOR_KEY]["digest"] = g.policy_digest(floor)
                return state
            merge = repo.merge(m2, extra)
            prov = repo.prov()
            self.assertFalse(prov["ok"])
            self.assertEqual(prov["failures"][0]["commit"], merge)
            self.assertIn("merge base", prov["failures"][0]["reason"])

    def test_the_same_history_with_one_merge_base_verifies(self):
        with PolicyRepo() as repo:
            repo.branch("X")
            repo.write_policy(PLAN_HUMAN)
            repo.record_floor()
            repo.remove_policy()
            repo.checkout("main")
            repo.branch("Y")
            repo.write_policy(ACCEPTANCE_HUMAN)
            repo.record_floor()
            repo.remove_policy()
            repo.merge("X", lambda ours, theirs, base: stricter_floor(ours, theirs))
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(len(repo.git("merge-base", "--all", "HEAD", "X").split()), 1)

    def test_a_loosening_before_an_adoption_bringing_update_merge_stays_in_range(self):
        with PolicyRepo() as repo:
            repo.branch("A")
            repo.adopt(AUTOMATIC)
            repo.checkout("main")
            repo.branch("B")
            repo.write_policy(HUMAN)
            repo.record_floor()
            repo.remove_policy()
            repo.hand_state_commit(lambda state: state.update(loosened_floor(state, "plan_approval.human")),
                                   "hand loosening on B")
            self.assertFalse(repo.prov()["ok"])
            repo.checkout("main")
            repo.squash("A")
            repo.checkout("B")
            repo.merge("main", lambda ours, theirs, base: stricter_floor(ours, theirs))
            prov = repo.prov()
            self.assertFalse(prov["ok"], "the update merge is not an adoption-introducing commit")
            repo.adopt(AUTOMATIC)
            self.assertTrue(repo.prov()["ok"], "a re-adoption restores a normal state")

    def test_a_human_file_committed_on_b_before_an_adoption_merge_is_still_scanned(self):
        with PolicyRepo() as repo:
            repo.branch("A")
            repo.adopt(AUTOMATIC)
            repo.checkout("main")
            repo.branch("B")
            repo.commit_policy(HUMAN)
            repo.delete_policy_and_commit()
            repo.checkout("main")
            repo.squash("A")
            repo.checkout("B")
            repo.merge("main")
            self.assertTrue(repo.prov()["ok"])
            self.assertEqual(repo.human_gates(), set(g.GATE_IDS), "the history scan still sees B's human file")
            self.assertEqual(repo.eff()["source"], "floor")

    def test_the_imported_lowering_stays_visible_after_an_update_merge(self):
        with PolicyRepo() as repo:
            repo.adopt(PLAN_HUMAN)
            repo.branch("B")
            (repo.root / "b.txt").write_text("b\n")
            repo.commit("b work", "b.txt")
            repo.checkout("main")
            repo.branch("A")
            repo.adopt(AUTOMATIC)
            a_digest = g.policy_digest(AUTOMATIC)
            repo.checkout("main")
            repo.squash("A")
            repo.checkout("B")
            merge = repo.merge("main")
            self.assertTrue(repo.prov()["ok"])
            g.clear_caches()
            event = g.gate_lowering_event(repo.root, repo.state())
            self.assertEqual(event["sha256"], a_digest)
            self.assertEqual(event["lowered"], ["plan_approval.human"])
            self.assertEqual(event["commit"], merge)
            self.assertNotEqual(event["sha256"], g.policy_digest(PLAN_HUMAN))
            status, detail = g.verify_check(repo.root, repo.state())
            self.assertEqual(status, "warn")
            self.assertIn(a_digest[:12], detail)
            self.assertIn("plan_approval.human", detail)
            self.assertEqual(repo.eff()["gate_lowering"]["sha256"], a_digest)


# ---------------------------------------------------------------------------
# the adoption commit and its validators (`LPR-R3-002`, `LPR-R9-003`)
# ---------------------------------------------------------------------------


def two_item_state(**per_item) -> dict:
    items = {
        "a": h.base_work_item(work_item_id="a", governing_workflow_version="2.2",
                              phase="AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW", state_revision=1),
        "b": h.base_work_item(work_item_id="b", governing_workflow_version="2.2",
                              phase="AWAITING_LOCAL_IMPLEMENTATION_REVIEW", state_revision=1),
    }
    for key, overrides in per_item.items():
        items[key].update(overrides)
    return h.base_state(**items)


class TestAdoptionCommit(unittest.TestCase):
    def test_the_command_commit_changes_exactly_two_top_level_keys_with_the_trailer(self):
        with PolicyRepo() as repo:
            before = repo.state()
            commit = repo.adopt(HUMAN)
            ws.validate_gate_policy_adoption_commit(repo.root, commit)
            after = repo.state()
            changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
            self.assertEqual(changed, {g.ADOPTION_KEY, g.FLOOR_KEY})
            self.assertEqual(ws._commit_trailers(repo.root, commit),
                             {ws.GATE_POLICY_ADOPTION_TRAILER: g.policy_digest(HUMAN)})
            self.assertEqual(ws._commit_own_changed_paths(repo.root, commit), {STATE_REL})

    def test_an_adoption_that_lowers_a_recorded_floor_passes_with_the_two_key_diff(self):
        with PolicyRepo() as repo:
            repo.write_policy(HUMAN)
            repo.record_floor()
            repo.remove_policy()
            before = repo.state()[g.FLOOR_KEY]
            commit = repo.adopt(AUTOMATIC)
            ws.validate_gate_policy_adoption_commit(repo.root, commit)
            self.assertNotEqual(repo.state()[g.FLOOR_KEY], before)
            self.assertEqual(repo.state()[g.FLOOR_KEY]["policy"], g.resolve_policy(AUTOMATIC))

    def hand_commit(self, repo: PolicyRepo, state: dict, trailer: str | None = "digest", extra: dict | None = None):
        repo.write_state(state)
        digest = state.get(g.ADOPTION_KEY, {}).get("sha256", "0" * 64)
        trailers = {ws.GATE_POLICY_ADOPTION_TRAILER: digest} if trailer == "digest" else (
            {ws.GATE_POLICY_ADOPTION_TRAILER: trailer} if trailer else None)
        return repo.commit("hand adoption", STATE_REL, *(extra or {}), trailers=trailers)

    def test_the_validator_refuses_each_malformed_adoption_commit(self):
        cases = {}

        def adoption_only(repo):
            state = repo.adoption_state(HUMAN)
            state.pop(g.FLOOR_KEY)
            return state

        def floor_only(repo):
            state = repo.state()
            state[g.FLOOR_KEY] = repo.adoption_state(HUMAN)[g.FLOOR_KEY]
            return state

        def third_key(repo):
            state = repo.adoption_state(HUMAN)
            state["note"] = "third key"
            return state

        def work_item_change(repo):
            state = repo.adoption_state(HUMAN)
            state["work_items"]["a"]["phase"] = "AWAITING_FUNCTIONAL_REVIEW"
            return state

        def stricter_floor_than_adopted(repo):
            state = repo.adoption_state(AUTOMATIC)
            state[g.FLOOR_KEY]["policy"]["plan_approval"]["human"] = True
            state[g.FLOOR_KEY]["digest"] = g.policy_digest(state[g.FLOOR_KEY]["policy"])
            return state

        cases = {"adoption key alone": adoption_only, "floor alone": floor_only, "a third key": third_key,
                 "a work item change": work_item_change,
                 "a floor that is not the reset": stricter_floor_than_adopted}
        for label, build in cases.items():
            with self.subTest(label), PolicyRepo() as repo:
                repo.write_state(two_item_state())
                repo.commit("two items", STATE_REL)
                state = build(repo)
                commit = self.hand_commit(repo, state)
                with self.assertRaises(ws.MalformedGatePolicyAdoptionCommitError):
                    ws.validate_gate_policy_adoption_commit(repo.root, commit)
        with self.subTest("no trailer"), PolicyRepo() as repo:
            commit = self.hand_commit(repo, repo.adoption_state(HUMAN), trailer=None)
            with self.assertRaises(ws.MalformedGatePolicyAdoptionCommitError):
                ws.validate_gate_policy_adoption_commit(repo.root, commit)
        with self.subTest("trailer for another digest"), PolicyRepo() as repo:
            commit = self.hand_commit(repo, repo.adoption_state(HUMAN), trailer="e" * 64)
            with self.assertRaises(ws.MalformedGatePolicyAdoptionCommitError):
                ws.validate_gate_policy_adoption_commit(repo.root, commit)
        with self.subTest("another path in the commit"), PolicyRepo() as repo:
            (repo.root / "other.txt").write_text("x\n")
            commit = self.hand_commit(repo, repo.adoption_state(HUMAN), extra={"other.txt": None})
            with self.assertRaises(ws.MalformedGatePolicyAdoptionCommitError):
                ws.validate_gate_policy_adoption_commit(repo.root, commit)
        with self.subTest("a broken chain"), PolicyRepo() as repo:
            repo.adopt(HUMAN)
            state = repo.adoption_state(PLAN_HUMAN)
            state[g.ADOPTION_KEY]["history"] = []
            commit = self.hand_commit(repo, state)
            with self.assertRaises(ws.MalformedGatePolicyAdoptionCommitError):
                ws.validate_gate_policy_adoption_commit(repo.root, commit)

    def test_the_floor_commit_validator_refuses_what_is_not_a_floor_commit(self):
        with PolicyRepo() as repo:
            repo.write_policy(PLAN_HUMAN)
            commit = repo.record_floor()
            ws.validate_gate_policy_floor_commit(repo.root, commit)
            self.assertEqual(ws._commit_trailers(repo.root, commit),
                             {ws.GATE_POLICY_FLOOR_TRAILER: repo.state()[g.FLOOR_KEY]["digest"]})
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            loosened = loosened_floor(repo.state(), "plan_approval.human")
            repo.write_state(loosened)
            commit = repo.commit("floor", STATE_REL,
                                 trailers={ws.GATE_POLICY_FLOOR_TRAILER: loosened[g.FLOOR_KEY]["digest"]})
            with self.assertRaises(ws.MalformedGatePolicyFloorCommitError):
                ws.validate_gate_policy_floor_commit(repo.root, commit)
        with PolicyRepo() as repo:
            state = repo.adoption_state(HUMAN)
            repo.write_state(state)
            commit = repo.commit("adoption as floor", STATE_REL,
                                 trailers={ws.GATE_POLICY_FLOOR_TRAILER: state[g.FLOOR_KEY]["digest"]})
            with self.assertRaises(ws.MalformedGatePolicyFloorCommitError):
                ws.validate_gate_policy_floor_commit(repo.root, commit)

    def test_a_technical_approval_or_generation_commit_that_also_carries_an_adoption_is_refused(self):
        with PolicyRepo() as repo:
            repo.write_state(two_item_state())
            repo.commit("two items", STATE_REL)
            state = repo.adoption_state(HUMAN)
            state["work_items"]["a"].update(
                technical_approval={"status": "CURRENT"}, phase="AWAITING_FUNCTIONAL_REVIEW", state_revision=2)
            repo.write_state(state)
            commit = repo.commit("technical approval", STATE_REL, trailers={
                "Workflow-Technical-Approval": "1" * 64, "Workflow-Work-Item": "a"})
            with self.assertRaises(ws.MalformedTechnicalApprovalCommitError):
                ws.validate_technical_approval_commit(repo.root, commit, "a")
        with PolicyRepo() as repo:
            repo.write_state(two_item_state())
            repo.commit("two items", STATE_REL)
            state = repo.adoption_state(HUMAN)
            state["work_items"]["a"].update(
                phase="AWAITING_LOCAL_IMPLEMENTATION_REVIEW", implementation_revision=1,
                reviewed_implementation_head="0" * 40, state_revision=2)
            repo.write_state(state)
            commit = repo.commit("generation record", STATE_REL, trailers={
                "Workflow-Bundle-Generation-Record": "a/1", "Workflow-Work-Item": "a"})
            with self.assertRaises(ws.MalformedBundleGenerationRecordCommitError):
                ws.validate_bundle_generation_record_commit(repo.root, commit, "a")

    def test_item_267_is_not_weakened_another_items_change_or_a_top_level_field_is_still_refused(self):
        with PolicyRepo() as repo:
            repo.write_state(two_item_state())
            repo.commit("two items", STATE_REL)
            for label, mutate in {
                "another item's phase": lambda s: s["work_items"]["b"].update(
                    phase="AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"),
                "another item's approval": lambda s: s["work_items"]["b"].update(
                    plan_approval={"status": "CURRENT"}),
                "a top-level field": lambda s: s.update(active_work_item_id=None, extra_top="x"),
            }.items():
                with self.subTest(label):
                    repo.git("checkout", "--", STATE_REL)
                    state = repo.state()
                    state["work_items"]["a"].update(
                        technical_approval={"status": "CURRENT"}, phase="AWAITING_FUNCTIONAL_REVIEW",
                        state_revision=2)
                    mutate(state)
                    repo.write_state(state)
                    commit = repo.commit("technical approval", STATE_REL, trailers={
                        "Workflow-Technical-Approval": "1" * 64, "Workflow-Work-Item": "a"})
                    with self.assertRaises(ws.MalformedTechnicalApprovalCommitError):
                        ws.validate_technical_approval_commit(repo.root, commit, "a")
                    repo.git("reset", "-q", "--hard", "HEAD~1")


class TestAdoptionCommand(unittest.TestCase):
    def test_an_empty_or_non_naming_confirmation_is_refused_and_writes_nothing(self):
        with PolicyRepo() as repo:
            repo.write_policy(HUMAN)
            head = repo.head()
            before = (repo.root / STATE_REL).read_bytes()
            for text in ("", "adopt it", "gate_policy", f"gate_policy {'0' * 12}", f"{g.policy_digest(HUMAN)[:12]}"):
                with self.assertRaises(g.GatePolicyConfirmationRejectedError, msg=text):
                    ws.adopt_gate_policy(repo.root, confirmation=text, now=now())
            self.assertEqual(repo.head(), head)
            self.assertEqual((repo.root / STATE_REL).read_bytes(), before)

    def test_an_absent_or_invalid_file_cannot_be_adopted(self):
        with PolicyRepo() as repo:
            with self.assertRaises(ws.GatePolicyFileInvalidError):
                ws.adopt_gate_policy(repo.root, confirmation="gate_policy 000000000000", now=now())
            repo.write_policy(json.dumps({"surprise": 1}))
            with self.assertRaises(ws.GatePolicyFileInvalidError) as raised:
                ws.gate_policy_adoption_preview(repo.root)
            self.assertTrue(raised.exception.errors)

    def test_a_non_empty_index_apart_from_the_state_path_is_refused_before_anything_is_written(self):
        with PolicyRepo() as repo:
            repo.write_policy(HUMAN)
            (repo.root / "draft.md").write_text("a staged plan draft\n")
            repo.git("add", "draft.md")
            before = (repo.root / STATE_REL).read_bytes()
            head = repo.head()
            with self.assertRaises(ws.DirtyIndexBeforeStagingError) as raised:
                ws.adopt_gate_policy(repo.root, confirmation=confirmation_for(HUMAN), now=now())
            self.assertIn("draft.md", str(raised.exception))
            self.assertEqual(repo.head(), head)
            self.assertEqual((repo.root / STATE_REL).read_bytes(), before)
        with PolicyRepo() as repo:
            repo.write_policy(PLAN_HUMAN)
            (repo.root / "draft.md").write_text("draft\n")
            repo.git("add", "draft.md")
            with self.assertRaises(ws.DirtyIndexBeforeStagingError):
                ws.commit_gate_policy_floor(repo.root, now=now())

    def test_the_preview_shows_the_digest_the_difference_the_lowering_and_the_floor(self):
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            repo.write_policy(PLAN_HUMAN)
            preview = ws.gate_policy_adoption_preview(repo.root)
            self.assertEqual(preview["digest"], g.policy_digest(PLAN_HUMAN))
            self.assertEqual(preview["digest_prefix"], preview["digest"][:12])
            self.assertEqual(preview["loosened"], ["technical_approval.human", "acceptance.human"])
            self.assertEqual(preview["tightened"], [])
            self.assertEqual(preview["lowered"], ["technical_approval.human", "acceptance.human"])
            self.assertEqual(preview["floor_reset_to"], g.resolve_policy(PLAN_HUMAN))
            self.assertEqual(preview["current"]["source"], "adopted")
            self.assertTrue(preview["provenance_ok"])
        with PolicyRepo() as repo:
            repo.write_policy(HUMAN)
            preview = ws.gate_policy_adoption_preview(repo.root)
            self.assertEqual(preview["tightened"], ["plan_approval.human", "technical_approval.human",
                                                    "acceptance.human"])
            self.assertEqual(preview["loosened"], [])
            self.assertEqual(preview["lowered"], [])

    def test_the_preview_lists_every_open_bundle_the_adoption_commit_will_stale(self):
        with PolicyRepo() as repo:
            state = h.base_state(
                plan=h.base_work_item(work_item_id="plan", governing_workflow_version="2.2",
                                      phase="AWAITING_PLAN_APPROVAL"),
                impl=h.base_work_item(work_item_id="impl", governing_workflow_version="2.2",
                                      phase="AWAITING_LOCAL_IMPLEMENTATION_REVIEW"),
                busy=h.base_work_item(work_item_id="busy", governing_workflow_version="2.2",
                                      phase="IMPLEMENTING"),
                done=h.base_work_item(work_item_id="done", governing_workflow_version="2.2",
                                      phase="MILESTONE_COMPLETE"),
            )
            repo.write_state(state)
            repo.commit("items", STATE_REL)
            repo.write_policy(HUMAN)
            stales = ws.gate_policy_adoption_preview(repo.root)["stales"]
            self.assertEqual([(s["work_item_id"], s["stage"]) for s in stales],
                             [("impl", "implementation"), ("plan", "plan")])
            self.assertIn("/milestone-plan plan", stales[1]["way_out"])
            self.assertIn("/recover-implementation-provenance impl", stales[0]["way_out"])

    def test_an_adoption_with_no_foreign_residue_commits_exactly_the_working_tree_bytes(self):
        with PolicyRepo() as repo:
            commit = repo.adopt(HUMAN)
            committed = repo.git("show", f"{commit}:{STATE_REL}")
            self.assertEqual(committed.encode(), (repo.root / STATE_REL).read_bytes().rstrip(b"\n"))

    def test_adoption_with_residue_stages_only_the_two_top_level_keys(self):
        with PolicyRepo() as repo:
            repo.write_state(two_item_state())
            repo.commit("two items", STATE_REL)
            state = repo.state()
            state["work_items"]["a"]["gate_evidence"] = {"functional": {"ok": True}}
            state["work_items"]["b"].update(
                phase="AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW",
                implementation_review_stages={"LOCAL_MODEL_IMPLEMENTATION_REVIEW": {"verdict": "APPROVE"}})
            repo.write_state(state)
            commit = repo.adopt(HUMAN)
            ws.validate_gate_policy_adoption_commit(repo.root, commit)
            committed = json.loads(repo.git("show", f"{commit}:{STATE_REL}"))
            self.assertEqual(committed["work_items"], two_item_state()["work_items"])
            self.assertIn(g.ADOPTION_KEY, committed)
            working = repo.state()
            self.assertEqual(working["work_items"]["a"]["gate_evidence"], {"functional": {"ok": True}})
            self.assertEqual(working["work_items"]["b"]["phase"], "AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW")
            self.assertIn(g.ADOPTION_KEY, working)

    def test_a_floor_commit_never_carries_an_items_or_the_adoptions_residue(self):
        with PolicyRepo() as repo:
            repo.write_state(two_item_state())
            repo.commit("two items", STATE_REL)
            state = repo.state()
            state["work_items"]["a"]["gate_evidence"] = {"pr": {"x": 1}}
            repo.write_state(state)
            repo.write_policy(PLAN_HUMAN)
            commit = repo.record_floor()
            ws.validate_gate_policy_floor_commit(repo.root, commit)
            committed = json.loads(repo.git("show", f"{commit}:{STATE_REL}"))
            self.assertNotIn("gate_evidence", committed["work_items"]["a"])
            self.assertEqual(repo.state()["work_items"]["a"]["gate_evidence"], {"pr": {"x": 1}})


class TestGateLoweringEvents(unittest.TestCase):
    ALL_HUMAN_FIELDS = ["plan_approval.human", "technical_approval.human", "acceptance.human"]

    def test_an_adoption_that_lowers_a_gate_writes_a_non_empty_label(self):
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            self.assertEqual(repo.state()[g.ADOPTION_KEY]["lowered"], [])
            repo.adopt(AUTOMATIC)
            self.assertEqual(repo.state()[g.ADOPTION_KEY]["lowered"], self.ALL_HUMAN_FIELDS)

    def test_an_adoption_that_lowers_nothing_writes_an_empty_label(self):
        with PolicyRepo() as repo:
            repo.adopt(AUTOMATIC)
            self.assertEqual(repo.state()[g.ADOPTION_KEY]["lowered"], [])
            repo.adopt(PLAN_HUMAN)
            self.assertEqual(repo.state()[g.ADOPTION_KEY]["lowered"], [])
            repo.adopt(PLAN_HUMAN)
            self.assertEqual(repo.state()[g.ADOPTION_KEY]["lowered"], [])
            self.assertIsNone(g.gate_lowering_event(repo.root, repo.state()))

    def test_removing_the_default_require_by_adoption_is_a_lowering_event(self):
        with PolicyRepo() as repo:
            repo.adopt(NO_REQUIRE)
            self.assertEqual(repo.state()[g.ADOPTION_KEY]["lowered"],
                             ["plan_approval.require", "technical_approval.require"])
            self.assertEqual(repo.eff()["policy"]["plan_approval"]["require"], [])
            status, detail = g.verify_check(repo.root, repo.state())
            self.assertEqual(status, "warn")
            self.assertIn("plan_approval.require", detail)
            self.assertIn(g.policy_digest(NO_REQUIRE)[:12], detail)

    def test_verify_warns_naming_the_digest_the_commit_and_the_lowered_fields(self):
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            commit = repo.adopt(AUTOMATIC)
            event = g.gate_lowering_event(repo.root, repo.state())
            self.assertEqual(event["lowered"], self.ALL_HUMAN_FIELDS)
            self.assertEqual(event["sha256"], g.policy_digest(AUTOMATIC))
            self.assertEqual(event["commit"], commit)
            self.assertTrue(event["label_agrees"])
            status, detail = g.verify_check(repo.root, repo.state())
            self.assertEqual(status, "warn")
            self.assertIn(g.policy_digest(AUTOMATIC)[:12], detail)
            self.assertIn(commit[:12], detail)
            self.assertIn("acceptance.human", detail)
            self.assertEqual(repo.eff()["gate_lowering"]["lowered"], self.ALL_HUMAN_FIELDS)

    def hand_built_lowering(self, repo: PolicyRepo, **kwargs) -> str:
        repo.write_policy(HUMAN)
        repo.record_floor()
        repo.remove_policy()
        return repo.hand_adopt(AUTOMATIC, **kwargs)

    def test_a_hand_built_self_consistent_adoption_resetting_a_human_floor_is_accepted_and_reported(self):
        """The threat model's accepted limit, pinned rather than implied: the
        user's `/adopt-gate-policy` and a perfect hand-built forgery are the
        same bytes. What the Workflow does is report it."""
        for label, kwargs in {"empty label": {"lowered": []}, "omitted label": {"lowered": None}}.items():
            with self.subTest(label), PolicyRepo() as repo:
                if label == "omitted label":
                    repo.write_policy(HUMAN)
                    repo.record_floor()
                    repo.remove_policy()
                    state = repo.adoption_state(AUTOMATIC)
                    del state[g.ADOPTION_KEY]["lowered"]
                    repo.write_state(state)
                    commit = repo.commit("hand adoption", STATE_REL, trailers={
                        ws.GATE_POLICY_ADOPTION_TRAILER: state[g.ADOPTION_KEY]["sha256"]})
                else:
                    commit = self.hand_built_lowering(repo, **kwargs)
                prov = repo.prov()
                self.assertTrue(prov["ok"], "provenance accepts it, as the threat model states")
                self.assertEqual(repo.human_gates(), set())
                event = g.gate_lowering_event(repo.root, repo.state())
                self.assertEqual(event["lowered"], self.ALL_HUMAN_FIELDS)
                self.assertFalse(event["label_agrees"])
                status, detail = g.verify_check(repo.root, repo.state())
                self.assertEqual(status, "warn")
                self.assertIn("disagrees", detail, "a second warn for the label")
                self.assertIn(commit[:12], detail)

    def test_the_same_adoption_squash_merged_reports_the_same_event_against_the_squashs_parent(self):
        with PolicyRepo() as repo:
            repo.write_policy(HUMAN)
            repo.record_floor()
            repo.remove_policy()
            repo.branch("feature")
            repo.hand_adopt(AUTOMATIC, lowered=[])
            repo.checkout("main")
            squash = repo.squash("feature")
            event = g.gate_lowering_event(repo.root, repo.state())
            self.assertEqual(event["commit"], squash)
            self.assertEqual(event["lowered"], self.ALL_HUMAN_FIELDS)
            self.assertTrue(repo.prov()["ok"])

    def test_the_label_is_not_read_as_a_precondition(self):
        with PolicyRepo() as repo:
            self.hand_built_lowering(repo, lowered=["pr_review.enabled"])
            self.assertTrue(repo.prov()["ok"])
            event = g.gate_lowering_event(repo.root, repo.state())
            self.assertEqual(event["lowered"], self.ALL_HUMAN_FIELDS)
            self.assertEqual(event["label_lowered"], ["pr_review.enabled"])
            self.assertFalse(event["label_agrees"])

    def test_the_gate_lowering_is_carried_by_the_effective_policy_report(self):
        with PolicyRepo() as repo:
            self.assertIsNone(repo.eff()["gate_lowering"])
            repo.adopt(HUMAN)
            self.assertIsNone(repo.eff()["gate_lowering"])
            repo.adopt(AUTOMATIC)
            self.assertEqual(repo.eff()["gate_lowering"]["sha256"], g.policy_digest(AUTOMATIC))


# ---------------------------------------------------------------------------
# item-scoped staging (`LPR-R4-002`, `LPR-R5-001`, `LPR-R5-002`)
# ---------------------------------------------------------------------------


class TestStageScopedState(unittest.TestCase):
    def staged_state(self, repo: PolicyRepo) -> dict:
        return json.loads(repo.git("show", f":{STATE_REL}"))

    def seeded(self, repo: PolicyRepo) -> None:
        repo.write_state(two_item_state())
        repo.commit("two items", STATE_REL)

    def test_item_scope_takes_only_that_items_entry_from_the_working_tree(self):
        with PolicyRepo() as repo:
            self.seeded(repo)
            state = repo.state()
            state["work_items"]["a"].update(state_revision=2, phase="AWAITING_FUNCTIONAL_REVIEW")
            state["work_items"]["b"].update(state_revision=9, phase="AWAITING_PLAN_APPROVAL")
            state["active_work_item_id"] = "a"
            state[g.FLOOR_KEY] = repo.adoption_state(HUMAN)[g.FLOOR_KEY]
            repo.write_state(state)
            before = (repo.root / STATE_REL).read_bytes()
            self.assertTrue(ws.stage_scoped_state(repo.root, "a"))
            staged = self.staged_state(repo)
            self.assertEqual(staged["work_items"]["a"], state["work_items"]["a"])
            self.assertEqual(staged["work_items"]["b"], two_item_state()["work_items"]["b"])
            self.assertIsNone(staged["active_work_item_id"], "every top-level field comes from HEAD")
            self.assertNotIn(g.FLOOR_KEY, staged, "a pending floor is never carried by an item's commit")
            self.assertEqual((repo.root / STATE_REL).read_bytes(), before, "the working tree is untouched")
            self.assertEqual(repo.git("diff", "--cached", "--name-only"), STATE_REL)

    def test_it_is_a_no_op_when_only_that_items_entry_differs(self):
        with PolicyRepo() as repo:
            self.seeded(repo)
            state = repo.state()
            state["work_items"]["a"]["state_revision"] = 2
            repo.write_state(state)
            self.assertFalse(ws.stage_scoped_state(repo.root, "a"))
            self.assertEqual(repo.git("diff", "--cached", "--name-only"), "")
            repo.git("checkout", "--", STATE_REL)
            self.assertFalse(ws.stage_scoped_state(repo.root, "a"), "nothing differs at all")

    def test_it_refuses_a_state_path_already_staged_with_a_difference(self):
        with PolicyRepo() as repo:
            self.seeded(repo)
            state = repo.state()
            state["work_items"]["a"]["state_revision"] = 2
            repo.write_state(state)
            repo.git("add", STATE_REL)
            state["work_items"]["b"]["state_revision"] = 2
            repo.write_state(state)
            with self.assertRaises(ws.DirtyIndexBeforeStagingError):
                ws.stage_scoped_state(repo.root, "a")

    def test_the_adoption_scope_takes_exactly_the_two_top_level_keys(self):
        with PolicyRepo() as repo:
            self.seeded(repo)
            state = repo.adoption_state(HUMAN)
            state["work_items"]["b"]["state_revision"] = 5
            state["active_work_item_id"] = "b"
            repo.write_state(state)
            self.assertTrue(ws.stage_scoped_state(repo.root, ws.GATE_POLICY_ADOPTION_SCOPE))
            staged = self.staged_state(repo)
            self.assertEqual(staged[g.ADOPTION_KEY], state[g.ADOPTION_KEY])
            self.assertEqual(staged[g.FLOOR_KEY], state[g.FLOOR_KEY])
            self.assertEqual(staged["work_items"], two_item_state()["work_items"])
            self.assertIsNone(staged["active_work_item_id"])

    def test_the_floor_scope_takes_the_floor_alone(self):
        with PolicyRepo() as repo:
            self.seeded(repo)
            state = repo.adoption_state(HUMAN)
            repo.write_state(state)
            self.assertTrue(ws.stage_scoped_state(repo.root, ws.GATE_POLICY_FLOOR_SCOPE))
            staged = self.staged_state(repo)
            self.assertEqual(staged[g.FLOOR_KEY], state[g.FLOOR_KEY])
            self.assertNotIn(g.ADOPTION_KEY, staged)

    def test_a_repository_with_no_committed_state_is_left_to_the_ordinary_add(self):
        g.clear_caches()
        scratch = h.ScratchRepo().__enter__()
        try:
            (scratch.root / "docs/ai-workflow").mkdir(parents=True)
            (scratch.root / STATE_REL).write_bytes(ws._serialize_state(h.base_state()))
            self.assertFalse(ws.stage_scoped_state(scratch.root, "a"))
        finally:
            scratch.__exit__(None, None, None)

    def test_two_concurrent_items_between_review_stages_commit_scoped_where_a_plain_add_is_refused(self):
        """Delta 8 (`LPR-R6-002`): item `a`'s generation-record commit, made
        while item `b` holds uncommitted review-round residue."""
        for scoped in (False, True):
            with self.subTest(scoped=scoped), PolicyRepo() as repo:
                base = two_item_state(a={"phase": "SELF_REVIEWING_IMPLEMENTATION"})
                repo.write_state(base)
                repo.commit("two items", STATE_REL)
                state = ws.record_bundle_generation(
                    repo.state(), "a", stage="implementation", head=repo.head(), now="t-gen")
                state["work_items"]["b"].update(
                    phase="AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW", state_revision=7)
                repo.write_state(state)
                if scoped:
                    self.assertTrue(ws.stage_scoped_state(repo.root, "a"))
                else:
                    repo.git("add", "--", STATE_REL)
                revision = state["work_items"]["a"]["implementation_revision"]
                repo.git("commit", "-q", "-m", "record bundle generation", "-m",
                         f"Workflow-Bundle-Generation-Record: a/{revision}\nWorkflow-Work-Item: a")
                commit = repo.head()
                if scoped:
                    ws.validate_bundle_generation_record_commit(repo.root, commit, "a")
                    self.assertEqual(repo.state()["work_items"]["b"]["state_revision"], 7,
                                     "the residue stays in the working tree")
                else:
                    with self.assertRaises(ws.MalformedBundleGenerationRecordCommitError):
                        ws.validate_bundle_generation_record_commit(repo.root, commit, "a")


class TestCommandSentences(unittest.TestCase):
    COMMANDS = REPO_ROOT / ".claude" / "commands"
    #: The commit steps whose validator calls `_forbidden_state_mutation`
    #: (`validate_technical_approval_commit`,
    #: `validate_bundle_generation_record_commit`), plus the adoption.
    SCOPED = {"approve-review.md", "milestone-implement.md", "apply-implementation-review.md",
              "apply-functional-review.md", "recover-implementation-provenance.md",
              "adopt-gate-policy.md", "satisfy-gate.md"}
    #: `bootstrap-workflow-v2.md` is the one-time driver for `workflow-v2-1-core`
    #: and is not part of any 2.8.0 flow.
    NOT_PART_OF_THE_FLOW = {"bootstrap-workflow-v2.md"}

    def text(self, name: str) -> str:
        return " ".join((self.COMMANDS / name).read_text().split())

    def test_the_scoped_staging_sentence_is_exactly_where_the_rule_names_it(self):
        found = {p.name for p in self.COMMANDS.glob("*.md") if "stage_scoped_state" in p.read_text()}
        self.assertEqual(found, self.SCOPED)

    def test_the_list_is_derived_from_the_rule(self):
        """Every command that commits a `Workflow-Bundle-Generation-Record` or
        `Workflow-Technical-Approval` trailer by staging the state path alone
        is in the scoped set (or is named as outside the flow)."""
        committing = set()
        for path in self.COMMANDS.glob("*.md"):
            text = " ".join(path.read_text().split())
            commits_generation = bool(
                "stage exactly" in text and "WORKFLOW_STATE.json" in text
                and re.search(r"Workflow-Bundle-Generation-Record:\s*<work_item_id>", text))
            if commits_generation or "Workflow-Technical-Approval:" in text:
                committing.add(path.name)
        self.assertEqual(committing - self.NOT_PART_OF_THE_FLOW - {"adopt-gate-policy.md"}, self.SCOPED - {"adopt-gate-policy.md"})

    def test_unvalidated_state_commits_keep_whole_file_staging_and_the_content_check(self):
        for name, count in (("milestone-implement.md", 2), ("request-plan-amendment.md", 1)):
            text = self.text(name)
            self.assertEqual(text.count("keeps whole-file staging"), count, name)
            self.assertEqual(text.count("assert_gate_policy_fields_unchanged_or_tightened"), count, name)
        text = self.text("approve-review.md")
        self.assertIn("The plan-approval commit is not scoped", text)
        self.assertIn("verify_plan_approval_commit", text)
        for name in ("request-plan-amendment.md",):
            self.assertNotIn("stage_scoped_state", self.text(name))


# ---------------------------------------------------------------------------
# verify's `gate_policy` check
# ---------------------------------------------------------------------------


class TestVerifyCheck(unittest.TestCase):
    def verify(self, repo: PolicyRepo) -> dict:
        g.clear_caches()
        body, code = wp.run(["--repo-root", str(repo.root), "verify"])
        self.assertEqual(code, wp.EXIT_OK, body)
        return {c["id"]: c for c in body["result"]["checks"]} | {"_healthy": body["result"]["healthy"]}

    def test_the_check_is_the_eighth_and_advisory(self):
        self.assertEqual(wp.VERIFY_CHECK_IDS[-1], "gate_policy")
        self.assertIn("gate_policy", wp.ADVISORY_VERIFY_CHECKS)
        with PolicyRepo() as repo:
            checks = self.verify(repo)
            self.assertEqual(checks["gate_policy"]["status"], "pass")
            self.assertTrue(checks["_healthy"])
            self.assertEqual(checks["protocol_ready"]["status"], "pass")

    def test_pass_warn_and_fail_and_none_changes_the_overall_status(self):
        cases = []
        with PolicyRepo() as repo:
            cases.append(("no file", self.verify(repo)))
            repo.write_policy(PLAN_HUMAN)
            cases.append(("an unadopted differing file", self.verify(repo)))
            repo.write_policy(NO_REQUIRE)
            cases.append(("an ignored loosening", self.verify(repo)))
            repo.write_policy(PLAN_HUMAN)
            repo.record_floor()
            repo.remove_policy()
            cases.append(("an orphaned floor", self.verify(repo)))
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            repo.write_policy(HUMAN)
            cases.append(("a file equal to the adopted policy", self.verify(repo)))
            repo.write_policy("{broken")
            cases.append(("an invalid file", self.verify(repo)))
        with PolicyRepo() as repo:
            repo.adopt(HUMAN)
            repo.hand_state_commit(lambda state: state[g.ADOPTION_KEY].update(history=["2" * 64]))
            cases.append(("a failed provenance", self.verify(repo)))
        expected = {
            "no file": "pass", "an unadopted differing file": "warn", "an ignored loosening": "warn",
            "an orphaned floor": "warn", "a file equal to the adopted policy": "pass",
            "an invalid file": "fail", "a failed provenance": "fail",
        }
        for label, checks in cases:
            self.assertEqual(checks["gate_policy"]["status"], expected[label], label)
            self.assertTrue(checks["_healthy"], f"{label}: the advisory check never changes the overall status")
            self.assertEqual(checks["protocol_ready"]["status"], "pass", label)

    def test_an_unrecorded_floor_is_a_warn(self):
        with PolicyRepo() as repo:
            repo.write_policy(PLAN_HUMAN)
            detail = self.verify(repo)["gate_policy"]["detail"]
            self.assertIn("not yet recorded", detail)

    def test_a_git_refusal_inside_the_check_is_a_failed_advisory_check_not_a_crash(self):
        from unittest import mock
        with PolicyRepo() as repo:
            error = subprocess.CalledProcessError(128, ["git", "rev-list"], stderr="bad object")
            with mock.patch.object(g, "verify_check", side_effect=error):
                checks = self.verify(repo)
            self.assertEqual(checks["gate_policy"]["status"], "fail")
            self.assertIn("bad object", checks["gate_policy"]["detail"])
            self.assertTrue(checks["_healthy"])
            with mock.patch.object(g, "verify_check", side_effect=g.GatePolicyError("refused")):
                self.assertEqual(self.verify(repo)["gate_policy"]["status"], "fail")
            with mock.patch.object(g, "verify_check", side_effect=KeyError("defect")):
                with self.assertRaises(KeyError):
                    wp.op_verify(repo.root, None)

    def test_the_check_never_raises_on_a_bad_file(self):
        with PolicyRepo() as repo:
            for body in ("", "null", "[1]", "{"):
                repo.write_policy(body)
                self.assertEqual(self.verify(repo)["gate_policy"]["status"], "fail", body)


class TestAllHumanEquivalence(unittest.TestCase):
    def test_an_adopted_all_human_policy_changes_only_the_top_level_fields(self):
        """D-GP-Compat's delta 7: the adoption adds the two top-level keys and
        nothing else; `state_identity` covers the item only, so `next-action`
        is unchanged."""
        with PolicyRepo() as repo:
            repo.write_state(h.base_state(wi=h.base_work_item(state_revision=1)))
            repo.commit("item", STATE_REL)
            before = repo.state()
            plain, _ = wp.run(["--repo-root", str(repo.root), "next-action", "--work-item", "wi"])
            repo.adopt(HUMAN)
            after = repo.state()
            self.assertEqual({k for k in set(before) | set(after) if before.get(k) != after.get(k)},
                             {g.ADOPTION_KEY, g.FLOOR_KEY})
            self.assertEqual(before["work_items"], after["work_items"])
            self.assertEqual(wp.state_identity("wi", before), wp.state_identity("wi", after))
            adopted, _ = wp.run(["--repo-root", str(repo.root), "next-action", "--work-item", "wi"])
            for body in (plain, adopted):
                body["result"]["basis"].pop("head", None)
            self.assertEqual(plain["result"], adopted["result"])

    def test_a_repository_that_adopts_nothing_has_no_policy_keys(self):
        with PolicyRepo() as repo:
            self.assertNotIn(g.ADOPTION_KEY, repo.state())
            self.assertNotIn(g.FLOOR_KEY, repo.state())
            repo.write_policy(HUMAN)
            repo.eff()
            self.assertNotIn(g.FLOOR_KEY, repo.state(), "reading never writes the floor")


class TestEvaluateGateHuman(unittest.TestCase):
    def test_a_human_gate_evaluates_to_the_human_result(self):
        with PolicyRepo() as repo:
            repo.write_state(h.base_state(wi=h.base_work_item(governing_workflow_version="2.2")))
            repo.commit("item", STATE_REL)
            repo.write_policy(PLAN_HUMAN)
            result = g.evaluate_gate(repo.root, repo.state(), "wi", "plan_approval")
            self.assertEqual(result["mode"], "human")
            self.assertFalse(result["satisfiable"])
            self.assertEqual([r["id"] for r in result["requirements"]], ["human_gate"])
            self.assertEqual(result["source"], "file_tightened")
            self.assertEqual(result["policy_digest"], repo.eff()["digest"])

    def test_the_governing_version_table_makes_some_gates_always_human(self):
        with PolicyRepo() as repo:
            state = h.base_state(
                v1=h.base_work_item(work_item_id="v1", governing_workflow_version="1"),
                v21=h.base_work_item(work_item_id="v21", governing_workflow_version="2.1"),
                v22=h.base_work_item(work_item_id="v22", governing_workflow_version="2.2"))
            effective = g.effective_policy(repo.root, state)
            modes = {(wi, gate): g.gate_mode(effective, gate, state["work_items"][wi]["governing_workflow_version"])
                     for wi in ("v1", "v21", "v22") for gate in g.GATE_IDS}
            self.assertEqual(modes[("v1", "plan_approval")], "human")
            self.assertEqual(modes[("v1", "technical_approval")], "human")
            self.assertEqual(modes[("v21", "technical_approval")], "human")
            self.assertEqual(modes[("v21", "plan_approval")], "automatic")
            self.assertEqual(modes[("v22", "plan_approval")], "automatic")
            self.assertEqual(modes[("v22", "technical_approval")], "automatic")
            for wi in ("v1", "v21", "v22"):
                self.assertEqual(modes[(wi, "acceptance")], "automatic", "acceptance reads no ledger")

    def test_unknown_gate_and_item_are_refused(self):
        with PolicyRepo() as repo:
            state = h.base_state(wi=h.base_work_item())
            with self.assertRaises(g.GatePolicyError):
                g.evaluate_gate(repo.root, state, "wi", "nope")
            with self.assertRaises(g.GatePolicyError):
                g.evaluate_gate(repo.root, state, "missing", "plan_approval")


# ---------------------------------------------------------------------------
# CP2: automatic plan and technical approvals, with audit evidence
# ---------------------------------------------------------------------------

import workflow_fingerprint as fingerprint

WI = "wi"
CLAUDE = "anthropic/claude-opus-5-5"
OPENAI = "openai/gpt-5"
LOCAL_PLAN = "LOCAL_MODEL_PLAN_REVIEW"
MANUAL_PLAN = "MANUAL_EXTERNAL_PLAN_REVIEW"
LOCAL_IMPL = "LOCAL_MODEL_IMPLEMENTATION_REVIEW"
MANUAL_IMPL = "MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"


def verdict_text(status: str, *, rcid: str, role: str, bundle: str | None = None, model: str | None = None,
                 base: str | None = None, body_model: str | None = None) -> str:
    lines = ["# Review Decision", "", f"Status: {status}", "", f"Reviewer role: {role}"]
    if model is not None:
        lines.append(f"Reviewer model: {model}")
    if bundle is not None:
        lines.append(f"Reviewed bundle ID: {bundle}")
    if base is not None:
        lines.append(f"Reviewed base commit: {base}")
    lines += [f"Work item: {WI}", f"{fingerprint.FEEDBACK_REVIEW_CONTENT_ID_LABEL} {rcid}", "",
              "## Blocking findings", "", "None."]
    if body_model is not None:
        lines += ["", f"Reviewer model: {body_model}"]
    return "\n".join(lines) + "\n"


def feedback_file(repo: h.ScratchRepo) -> Path:
    return repo.root / ".ai-review" / WI / "feedback" / "REVIEW_FEEDBACK.md"


def put_feedback(repo: h.ScratchRepo, text: str) -> Path:
    path = feedback_file(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def state_bytes(repo: h.ScratchRepo) -> bytes:
    return (repo.root / STATE_REL).read_bytes()


def record_local(repo: h.ScratchRepo, stage: str, rcid: str, bundle: str, *, model: str | None = CLAUDE) -> str:
    """The local stage as the command records it: the verdict written, the
    audit computed from the state read, the real writer."""
    role = LOCAL_PLAN if stage == "plan" else LOCAL_IMPL
    text = verdict_text("APPROVE", rcid=rcid, role=role, bundle=bundle, model=model, base=repo.base)
    path = put_feedback(repo, text)
    state = h.read_state(repo)
    audit = ws.local_review_audit(repo.root, state, WI, stage, feedback_text=text, feedback_path=str(path))
    writer = ws.record_local_plan_review if stage == "plan" else ws.record_local_implementation_review
    h.write_state(repo, writer(state, WI, verdict="APPROVE", bundle_id=bundle, review_content_id=rcid,
                               round=1, now="t-local", audit=audit))
    return text


def plan_at_manual(repo: h.ScratchRepo, *, gate_policy=None, local_model: str | None = CLAUDE,
                   version: str = "2.2") -> tuple[str, str]:
    """A two-stage item at `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW`; the default
    gate policy unless `gate_policy` says otherwise. Returns `(P, B)`."""
    h.seed_bundle_item(repo, governing_workflow_version=version, phase="PLANNING", gate_policy=gate_policy)
    P, B = h.publish_and_bind_plan_bundle(repo)
    record_local(repo, "plan", P, B, model=local_model)
    return P, B


def implementation_at_manual(repo: h.ScratchRepo, *, gate_policy=None, local_model: str | None = CLAUDE) -> tuple[str, str]:
    h.seed_bundle_item(repo, governing_workflow_version="2.2", phase="SELF_REVIEWING_IMPLEMENTATION",
                       gate_policy=gate_policy)
    repo.commit("implement", filename=h.BUNDLE_ITEM_IMPLEMENTATION_PATH)
    rcid = h.generate_implementation_bundle(repo)
    bundle = fingerprint.compute_bundle_id(repo.root / ".ai-review" / WI / "current")[0]
    record_local(repo, "implementation", rcid, bundle, model=local_model)
    return rcid, bundle


def ingest(repo: h.ScratchRepo, stage: str, text: str, *, run_ref: str | None = "run-7") -> dict:
    return ws.ingest_manual_review_verdict(
        repo.root, WI, stage=stage, verdict_text=text, now="t-manual", two_stage_only=True, run_ref=run_ref)


def manual_text(stage: str, rcid: str, bundle: str, status: str = "APPROVE", model: str | None = OPENAI,
                base: str | None = None) -> str:
    role = MANUAL_PLAN if stage == "plan" else MANUAL_IMPL
    return verdict_text(status, rcid=rcid, role=role, bundle=bundle, model=model, base=base)


def ledger_of(repo: h.ScratchRepo, stage: str) -> dict:
    return h.read_state(repo)["work_items"][WI]["plan_review_stages" if stage == "plan" else "implementation_review_stages"]


class TestReviewerModelParsing(unittest.TestCase):
    def test_the_family_is_the_vendor_up_to_the_first_separator(self):
        self.assertEqual(g.reviewer_family("Anthropic/Claude-Opus-5-5"), "anthropic")
        self.assertEqual(g.reviewer_family("anthropic:opus"), "anthropic")
        self.assertEqual(g.reviewer_family("gpt-5 turbo"), "gpt-5")
        self.assertEqual(g.reviewer_family("  OpenAI/x "), "openai")
        self.assertIsNone(g.reviewer_family(None))
        self.assertIsNone(g.reviewer_family("   "))

    def test_two_models_of_one_vendor_are_one_family(self):
        met, detail = g.distinct_reviewer_models({"reviewer_model": "anthropic/opus"},
                                                 {"reviewer_model": "anthropic/sonnet"})
        self.assertFalse(met)
        self.assertIn("anthropic", detail)
        self.assertTrue(g.distinct_reviewer_models({"reviewer_model": CLAUDE}, {"reviewer_model": OPENAI})[0])
        self.assertFalse(g.distinct_reviewer_models({"reviewer_model": CLAUDE}, {})[0])
        self.assertFalse(g.distinct_reviewer_models(None, None)[0])

    def test_the_line_is_read_from_the_header_and_never_from_the_body(self):
        header = verdict_text("APPROVE", rcid="a" * 64, role=MANUAL_PLAN, model=CLAUDE)
        self.assertEqual(fingerprint.parse_review_feedback_header(header)["reviewer_model"], CLAUDE)
        body = verdict_text("APPROVE", rcid="a" * 64, role=MANUAL_PLAN, body_model=OPENAI)
        self.assertIsNone(fingerprint.parse_review_feedback_header(body)["reviewer_model"])


class TestAuditKeysAndTheIngestRefusal(unittest.TestCase):
    def test_the_default_refuses_a_manual_approve_without_a_model_and_writes_nothing(self):
        for stage, build in (("plan", plan_at_manual), ("implementation", implementation_at_manual)):
            with self.subTest(stage=stage), h.ScratchRepo() as repo:
                rcid, bundle = build(repo)
                before = state_bytes(repo)
                phase = h.read_state(repo)["work_items"][WI]["phase"]
                text = manual_text(stage, rcid, bundle, model=None)
                with self.assertRaises(ws.DistinctReviewerModelsRequiredError) as caught:
                    ingest(repo, stage, text)
                self.assertEqual(state_bytes(repo), before)
                self.assertEqual(h.read_state(repo)["work_items"][WI]["phase"], phase)
                self.assertFalse(feedback_file(repo).read_text() == text)
                message = str(caught.exception)
                self.assertIn("no `Reviewer model:`", message)
                self.assertIn("second declared family", message)
                self.assertIn("human_approval", message)
                self.assertNotIn("adopt", message.lower(), "LPR-R19-001: the adoption is not a remedy here")

    def test_an_equal_family_is_refused_naming_the_value(self):
        with h.ScratchRepo() as repo:
            P, B = plan_at_manual(repo)
            before = state_bytes(repo)
            with self.assertRaises(ws.DistinctReviewerModelsRequiredError) as caught:
                ingest(repo, "plan", manual_text("plan", P, B, model="Anthropic/claude-sonnet-5-5"))
            self.assertEqual(state_bytes(repo), before)
            self.assertIn("'anthropic'", str(caught.exception))

    def test_remedy_one_a_second_family_is_recorded_with_the_audit_keys(self):
        for stage, build in (("plan", plan_at_manual), ("implementation", implementation_at_manual)):
            with self.subTest(stage=stage), h.ScratchRepo() as repo:
                rcid, bundle = build(repo)
                text = manual_text(stage, rcid, bundle)
                ingest(repo, stage, text)
                ledger = ledger_of(repo, stage)
                entry = ledger[MANUAL_PLAN if stage == "plan" else MANUAL_IMPL]
                self.assertEqual(entry["reviewer_model"], OPENAI)
                self.assertEqual(entry["run_ref"], "run-7")
                self.assertEqual(entry["verdict_sha256"], __import__("hashlib").sha256(text.encode()).hexdigest())
                local = ledger[LOCAL_PLAN if stage == "plan" else LOCAL_IMPL]
                self.assertEqual(local["reviewer_model"], CLAUDE)
                self.assertTrue(local["run_ref"].startswith(ws.LOCAL_RUN_REF_PREFIX + " "))
                self.assertEqual(h.read_state(repo)["work_items"][WI]["phase"],
                                 "AWAITING_PLAN_APPROVAL" if stage == "plan" else "AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW")

    def test_remedy_two_the_gate_turned_human_admits_the_same_verdict_with_2_7_0_bytes(self):
        with h.ScratchRepo() as repo:
            P, B = plan_at_manual(repo)
            text = manual_text("plan", P, B, model=None)
            with self.assertRaises(ws.DistinctReviewerModelsRequiredError):
                ingest(repo, "plan", text)
            (repo.root / POLICY_REL).write_text(json.dumps(PLAN_HUMAN))
            ingest(repo, "plan", text)
            entry = ledger_of(repo, "plan")[MANUAL_PLAN]
            self.assertEqual(set(entry), {"bundle_id", "verdict", "round", "completed_at"})

    def test_a_revise_is_admitted_with_no_line(self):
        with h.ScratchRepo() as repo:
            P, B = plan_at_manual(repo)
            ingest(repo, "plan", manual_text("plan", P, B, status="REVISE", model=None))
            self.assertEqual(h.read_state(repo)["work_items"][WI]["phase"], "REVISING_PLAN")

    def test_all_human_writes_no_line_no_key_and_no_refusal(self):
        for stage, build in (("plan", plan_at_manual), ("implementation", implementation_at_manual)):
            with self.subTest(stage=stage), h.ScratchRepo() as repo:
                rcid, bundle = build(repo, gate_policy=HUMAN, local_model=None)
                ingest(repo, stage, manual_text(stage, rcid, bundle, model=None))
                ledger = ledger_of(repo, stage)
                for entry in (v for k, v in ledger.items() if k != "review_content_id"):
                    self.assertEqual(set(entry), {"bundle_id", "verdict", "round", "completed_at"})

    def test_no_require_adopted_before_the_bundle_admits_one_family(self):
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, governing_workflow_version="2.2", phase="PLANNING", gate_policy=None)
            (repo.root / POLICY_REL).write_text(json.dumps(NO_REQUIRE))
            ws.adopt_gate_policy(repo.root, confirmation=confirmation_for(NO_REQUIRE), now=now())
            P, B = h.publish_and_bind_plan_bundle(repo)
            record_local(repo, "plan", P, B, model=None)
            ingest(repo, "plan", manual_text("plan", P, B, model=None))
            entry = ledger_of(repo, "plan")[MANUAL_PLAN]
            self.assertIn("verdict_sha256", entry)
            self.assertNotIn("reviewer_model", entry)
            self.assertTrue(g.evaluate_gate(repo.root, h.read_state(repo), WI, "plan_approval")["satisfiable"])

    def test_an_adoption_at_the_open_phase_is_not_a_remedy(self):
        with h.ScratchRepo() as repo:
            P, B = plan_at_manual(repo)
            (repo.root / POLICY_REL).write_text(json.dumps(NO_REQUIRE))
            ws.adopt_gate_policy(repo.root, confirmation=confirmation_for(NO_REQUIRE), now=now())
            before = state_bytes(repo)
            with self.assertRaises(fingerprint.WorktreeOrHeadMismatchError):
                ingest(repo, "plan", manual_text("plan", P, B, model=None))
            self.assertEqual(state_bytes(repo), before)

    def test_the_audit_validators_refuse_malformed_keys(self):
        with h.ScratchRepo() as repo:
            plan_at_manual(repo)
            state = h.read_state(repo)
            state["work_items"][WI]["plan_review_stages"][LOCAL_PLAN]["verdict_sha256"] = "nope"
            with self.assertRaises(ws.InvalidLedgerAuditError):
                ws.validate_state(state)


class TestEvaluateGateAutomatic(unittest.TestCase):
    def at_approval(self, repo):
        P, B = plan_at_manual(repo)
        text = manual_text("plan", P, B, base=repo.base)
        ingest(repo, "plan", text)
        return P, B

    def met(self, evaluation) -> dict:
        return {r["id"]: r["met"] for r in evaluation["requirements"]}

    def test_a_satisfied_plan_gate(self):
        with h.ScratchRepo() as repo:
            P, B = self.at_approval(repo)
            ev = g.evaluate_gate(repo.root, h.read_state(repo), WI, "plan_approval")
            self.assertEqual(ev["mode"], "automatic")
            self.assertTrue(ev["satisfiable"], ev["requirements"])
            self.assertEqual(self.met(ev), {"gate_reachable": True, "verdict_approve_bound": True,
                                            "distinct_reviewer_models": True, "review_evidence_audited": True})
            self.assertEqual(ev["bundle_id"], B)
            self.assertEqual(ev["evidence"]["review_content_id"], P)
            self.assertEqual(ev["obtainable"], [])

    def test_each_failing_input_is_unsatisfiable(self):
        with h.ScratchRepo() as repo:
            self.at_approval(repo)
            state = h.read_state(repo)
            base = g.evaluate_gate(repo.root, state, WI, "plan_approval")
            self.assertTrue(base["satisfiable"])

            drifted = copy.deepcopy(state)
            stages = drifted["work_items"][WI]["plan_review_stages"]
            stages["review_content_id"] = "f" * 64
            self.assertFalse(g.evaluate_gate(repo.root, drifted, WI, "plan_approval")["satisfiable"])

            unaudited = copy.deepcopy(state)
            del unaudited["work_items"][WI]["plan_review_stages"][MANUAL_PLAN]["verdict_sha256"]
            ev = g.evaluate_gate(repo.root, unaudited, WI, "plan_approval")
            self.assertFalse(ev["satisfiable"])
            self.assertFalse(self.met(ev)["review_evidence_audited"])
            self.assertIn("human_approval", [r["detail"] for r in ev["requirements"]
                                             if r["id"] == "review_evidence_audited"][0])

            same = copy.deepcopy(state)
            same["work_items"][WI]["plan_review_stages"][MANUAL_PLAN]["reviewer_model"] = "anthropic/other"
            ev = g.evaluate_gate(repo.root, same, WI, "plan_approval")
            self.assertFalse(self.met(ev)["distinct_reviewer_models"])

            put_feedback(repo, manual_text("plan", "e" * 64, "d" * 64, status="REVISE"))
            ev = g.evaluate_gate(repo.root, state, WI, "plan_approval")
            self.assertFalse(ev["satisfiable"])
            self.assertFalse(self.met(ev)["verdict_approve_bound"])

    def test_a_human_gate_never_satisfies(self):
        with h.ScratchRepo() as repo:
            self.at_approval(repo)
            (repo.root / POLICY_REL).write_text(json.dumps(PLAN_HUMAN))
            ev = g.evaluate_gate(repo.root, h.read_state(repo), WI, "plan_approval")
            self.assertEqual((ev["mode"], ev["satisfiable"]), ("human", False))
            with self.assertRaises(ws.GateNotSatisfiableError):
                ws.build_policy_approval_record(repo.root, h.read_state(repo), WI, "plan", now="t-sat")

    def test_governing_versions_that_have_no_ledger_stay_human(self):
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, governing_workflow_version="2.1", phase="AWAITING_PLAN_APPROVAL", gate_policy=None)
            state = h.read_state(repo)
            self.assertEqual(g.evaluate_gate(repo.root, state, WI, "technical_approval")["mode"], "human")
            self.assertEqual(g.evaluate_gate(repo.root, state, WI, "plan_approval")["mode"], "automatic")


class TestPolicySatisfiedRecord(unittest.TestCase):
    def build_plan(self, repo):
        P, B = plan_at_manual(repo)
        ingest(repo, "plan", manual_text("plan", P, B, base=repo.base))
        return P, B, ws.build_policy_approval_record(repo.root, h.read_state(repo), WI, "plan", now="t-sat")

    def test_the_plan_record_is_valid_and_complete(self):
        with h.ScratchRepo() as repo:
            P, B, record = self.build_plan(repo)
            ws.validate_approval_record(record, stage="plan")
            self.assertEqual(record["basis"], ws.POLICY_SATISFIED)
            self.assertEqual(record["approved_review_content_id"], P)
            self.assertEqual(record["reviewed_bundle_id"], B)
            self.assertIsNone(record["reviewed_content_commit"])
            evidence = record["policy_evidence"]
            self.assertEqual(set(ws.POLICY_EVIDENCE_KEYS) - set(evidence), set())
            self.assertEqual(record["user_confirmation"], f"policy:{evidence['policy_digest']}")
            self.assertEqual(evidence["trust"], {"review_verdicts": "orchestrator"})
            self.assertEqual(evidence["policy_source"], "default")
            self.assertTrue(evidence["requirements"] and all(r["met"] for r in evidence["requirements"]))
            ledger = evidence["inputs"]["ledger"]
            for name in ("local", "manual"):
                self.assertEqual(set(ledger[name]), {"bundle_id", "verdict", "round", "verdict_sha256",
                                                     "ledger_entry_sha256", "run_ref", "reviewer_model"})
                self.assertTrue(ledger[name]["verdict_sha256"] and ledger[name]["ledger_entry_sha256"])
            self.assertEqual(evidence["inputs"]["review_content_id"], P)
            self.assertEqual(ws.gate_satisfied_by_trailer(record), "policy:" + evidence["policy_digest"][:12])
            state = ws.apply_plan_approval(h.read_state(repo), WI, record, "t-sat")
            self.assertEqual(state["work_items"][WI]["phase"], "IMPLEMENTING")
            self.assertEqual(state["work_items"][WI]["plan_approval"]["basis"], "POLICY_SATISFIED")

    def test_the_record_shape_rules(self):
        with h.ScratchRepo() as repo:
            _P, _B, record = self.build_plan(repo)
            bad = copy.deepcopy(record)
            bad["user_confirmation"] = "I approve wi at the plan stage"
            with self.assertRaises(ws.InvalidApprovalRecordError):
                ws.validate_approval_record(bad, stage="plan")
            bad = copy.deepcopy(record)
            del bad["policy_evidence"]
            with self.assertRaises(ws.InvalidApprovalRecordError):
                ws.validate_approval_record(bad, stage="plan")
            bad = copy.deepcopy(record)
            del bad["policy_evidence"]["trust"]
            with self.assertRaises(ws.InvalidApprovalRecordError):
                ws.validate_approval_record(bad, stage="plan")
            bad = copy.deepcopy(record)
            bad["basis"] = "EXTERNAL_APPROVE"
            with self.assertRaises(ws.InvalidApprovalRecordError):
                ws.validate_approval_record(bad, stage="plan")
            with self.assertRaises(ws.InvalidApprovalRecordError):
                ws.validate_approval_record(record, stage="gate_policy")
            with self.assertRaises(ws.InvalidApprovalRecordError):
                ws.validate_policy_satisfied_confirmation("policy:other", "a" * 64)

    def test_resolve_policy_approval_basis_never_returns_a_user_override(self):
        with h.ScratchRepo() as repo:
            P, B = plan_at_manual(repo)
            ingest(repo, "plan", manual_text("plan", P, B, base=repo.base))
            state = h.read_state(repo)
            ev = g.evaluate_gate(repo.root, state, WI, "plan_approval")
            self.assertEqual(ws.resolve_policy_approval_basis(state, WI, "plan", ev), ws.POLICY_SATISFIED)
            override_case = dict(ev, satisfiable=False)
            with self.assertRaises(ws.GateNotSatisfiableError):
                ws.resolve_policy_approval_basis(state, WI, "plan", override_case)
            with self.assertRaises(ws.GateNotSatisfiableError):
                ws.resolve_policy_approval_basis(state, WI, "plan", dict(ev, gate="technical_approval"))

    def test_a_pinned_block_refuses_the_technical_gate(self):
        with h.ScratchRepo() as repo:
            rcid, bundle = implementation_at_manual(repo)
            ingest(repo, "implementation", manual_text("implementation", rcid, bundle, base=repo.base))
            state = ws.record_technical_review_block_pin(
                h.read_state(repo), WI, bundle_id=bundle, review_content_id=rcid, now="t-pin")
            ev = {"gate": "technical_approval", "mode": "automatic", "satisfiable": True,
                  "requirements": [], "bundle_id": bundle}
            with self.assertRaises(ws.BlockCannotApproveError):
                ws.resolve_policy_approval_basis(state, WI, "implementation", ev)

    def test_the_toggle_turned_human_meanwhile_refuses_inside_the_transaction(self):
        with h.ScratchRepo() as repo:
            _P, _B, record = self.build_plan(repo)
            state = h.read_state(repo)
            ws.assert_policy_still_satisfied(repo.root, state, WI, "plan", record)
            before = state_bytes(repo)
            (repo.root / POLICY_REL).write_text(json.dumps(PLAN_HUMAN))
            with self.assertRaises(ws.GateNotSatisfiableError):
                ws.assert_policy_still_satisfied(repo.root, state, WI, "plan", record)
            with self.assertRaises(ws.GateNotSatisfiableError):
                ws.state_transaction(repo.root, lambda st: ws.apply_technical_approval(
                    st, WI, ws.build_policy_approval_record(repo.root, st, WI, "plan", now="t"), "t"))
            self.assertEqual(state_bytes(repo), before)

    def test_a_changed_effective_policy_is_refused_even_when_still_automatic(self):
        with h.ScratchRepo() as repo:
            _P, _B, record = self.build_plan(repo)
            tighter = {"schema_version": 1, "gates": {"technical_approval": {"human": True}}}
            (repo.root / POLICY_REL).write_text(json.dumps(tighter))
            with self.assertRaises(ws.GateNotSatisfiableError):
                ws.assert_policy_still_satisfied(repo.root, h.read_state(repo), WI, "plan", record)

    def test_the_technical_commit_passes_its_validator(self):
        with h.ScratchRepo() as repo:
            rcid, bundle = implementation_at_manual(repo)
            ingest(repo, "implementation", manual_text("implementation", rcid, bundle, base=repo.base))
            record = ws.build_policy_approval_record(repo.root, h.read_state(repo), WI, "implementation", now="t-sat")
            self.assertEqual(record["reviewed_content_commit"],
                             h.read_state(repo)["work_items"][WI]["reviewed_implementation_head"])
            ws.state_transaction(repo.root, lambda st: ws.apply_technical_approval(st, WI, record, "t-sat"))
            commit = h.commit_state(repo, "technical approval by policy", {
                "Workflow-Technical-Approval": rcid, "Workflow-Work-Item": WI,
                "Workflow-Gate-Satisfied-By": ws.gate_satisfied_by_trailer(record)})
            ws.validate_technical_approval_commit(repo.root, commit, WI)
            work_item = h.read_state(repo)["work_items"][WI]
            ws.verify_post_approval_manifest_match(
                repo.root, work_item, stage="implementation", base_commit=work_item["base_commit"], commit=commit)
            self.assertEqual(work_item["phase"], "AWAITING_FUNCTIONAL_REVIEW")
            self.assertEqual(work_item["technical_approval"]["basis"], "POLICY_SATISFIED")
            self.assertEqual(ws.discover_technical_approval_commit(repo.root, WI, rcid, work_item["base_commit"]), commit)

    def test_all_human_approve_review_records_are_unchanged(self):
        with h.ScratchRepo() as repo:
            rcid, _bundle = implementation_at_manual(repo, gate_policy=HUMAN, local_model=None)
            record = ws.build_approval_record(
                basis="EXTERNAL_APPROVE", stage="implementation", user_confirmation=f"wi implementation",
                now="t", reviewed_bundle_id="b" * 64, approved_review_content_id=rcid,
                review_content_manifest=[{"path": "x"}])
            self.assertNotIn("policy_evidence", record)
            self.assertEqual(g.evaluate_gate(repo.root, h.read_state(repo), WI, "technical_approval")["mode"], "human")


class TestTrustBoundaryAndPlanCommit(unittest.TestCase):
    """INV-9: a fabricated manual `APPROVE` satisfies an automatic gate (the
    boundary is stated), names its hash and reporter, and satisfies nothing
    under the human toggle or the master switch."""

    def test_a_fabricated_manual_approve_satisfies_an_automatic_gate_and_is_named(self):
        with h.ScratchRepo() as repo:
            P, B = plan_at_manual(repo)
            ingest(repo, "plan", manual_text("plan", P, B, base=repo.base), run_ref="orchestrator:fabricated-1")
            state = h.read_state(repo)
            ev = g.evaluate_gate(repo.root, state, WI, "plan_approval")
            self.assertTrue(ev["satisfiable"], ev["requirements"])
            record = ws.build_policy_approval_record(repo.root, state, WI, "plan", now="t-sat")
            manual = record["policy_evidence"]["inputs"]["ledger"]["manual"]
            self.assertEqual(manual["run_ref"], "orchestrator:fabricated-1")
            self.assertEqual(len(manual["verdict_sha256"]), 64)
            self.assertEqual(record["policy_evidence"]["trust"], {"review_verdicts": "orchestrator"})

    def test_the_same_inputs_satisfy_nothing_under_the_toggle_or_the_master_switch(self):
        for policy in (PLAN_HUMAN, HUMAN):
            with h.ScratchRepo() as repo:
                P, B = plan_at_manual(repo, gate_policy=policy, local_model=None)
                ingest(repo, "plan", manual_text("plan", P, B, base=repo.base, model=None))
                ev = g.evaluate_gate(repo.root, h.read_state(repo), WI, "plan_approval")
                self.assertEqual((ev["mode"], ev["satisfiable"]), ("human", False))
                with self.assertRaises(ws.GateNotSatisfiableError):
                    ws.build_policy_approval_record(repo.root, h.read_state(repo), WI, "plan", now="t-sat")

    def test_a_mismatched_bundle_id_does_not_satisfy(self):
        with h.ScratchRepo() as repo:
            P, B = plan_at_manual(repo)
            ingest(repo, "plan", manual_text("plan", P, B, base=repo.base))
            put_feedback(repo, manual_text("plan", P, "0" * 64, base=repo.base))
            ev = g.evaluate_gate(repo.root, h.read_state(repo), WI, "plan_approval")
            self.assertFalse(ev["satisfiable"])
            self.assertFalse({r["id"]: r["met"] for r in ev["requirements"]}["verdict_approve_bound"])

    def test_the_plan_commit_carries_the_trailers_and_the_policy_trailer(self):
        with h.ScratchRepo() as repo:
            P, B = plan_at_manual(repo)
            ingest(repo, "plan", manual_text("plan", P, B, base=repo.base))
            record = ws.build_policy_approval_record(repo.root, h.read_state(repo), WI, "plan", now="t-sat")
            ws.state_transaction(repo.root, lambda st: ws.apply_plan_approval(st, WI, record, "t-sat"))
            commit = h.commit_state(repo, "approve the plan by policy", {
                "Workflow-Plan-Approval": P, "Workflow-Work-Item": WI,
                "Workflow-Gate-Satisfied-By": ws.gate_satisfied_by_trailer(record)})
            message = h.git(repo, "log", "-1", "--format=%B", commit)
            work_item = h.read_state(repo)["work_items"][WI]
            self.assertEqual(work_item["plan_approval"]["basis"], "POLICY_SATISFIED")
            self.assertEqual(work_item["phase"], "IMPLEMENTING")
            self.assertIn("Workflow-Gate-Satisfied-By: policy:", message)
            self.assertIn("Workflow-Plan-Approval: " + P, message)


class TestVerifyWarnsOnAnUnreferencedRun(unittest.TestCase):
    def test_a_null_run_ref_is_a_warning_and_a_given_one_is_not(self):
        with h.ScratchRepo() as repo:
            P, B = plan_at_manual(repo)
            ingest(repo, "plan", manual_text("plan", P, B, base=repo.base), run_ref=None)
            state = h.read_state(repo)
            status, detail = g.verify_check(repo.root, state)
            self.assertEqual(status, "warn")
            self.assertIn("without a run_ref", detail)
            self.assertIn(f"{WI}/{MANUAL_PLAN}", detail)
            self.assertNotIn(f"{WI}/{LOCAL_PLAN}", detail, "the local stage records session:local")
        with h.ScratchRepo() as repo:
            P, B = plan_at_manual(repo)
            ingest(repo, "plan", manual_text("plan", P, B, base=repo.base), run_ref="orchestrator:run-1")
            self.assertEqual(g.verify_check(repo.root, h.read_state(repo))[0], "pass")


class TestCommandTextAgreement(unittest.TestCase):
    COMMANDS = REPO_ROOT / ".claude" / "commands"

    def text(self, name: str) -> str:
        return " ".join((self.COMMANDS / name).read_text().split())

    def test_satisfy_gate_is_a_non_user_only_writer_citing_approve_review_steps(self):
        raw = (self.COMMANDS / "satisfy-gate.md").read_text()
        front = raw.split("---")[1]
        self.assertNotIn("disable-model-invocation", front)
        self.assertIn("state_writer: true", front)
        text = self.text("satisfy-gate.md")
        for sentence in ("resolve_policy_approval_basis", "build_policy_approval_record",
                         "assert_policy_still_satisfied", "Workflow-Gate-Satisfied-By",
                         "Workflow-Plan-Approval", "Workflow-Technical-Approval",
                         "validate_technical_approval_commit", "verify_post_approval_manifest_match",
                         "`/approve-review` stays the human path", "step 7", "I21"):
            self.assertIn(sentence, text if sentence != "step 7" else text.replace("Step 7", "step 7"))

    def test_every_approve_review_step_cited_exists(self):
        satisfy = self.text("satisfy-gate.md")
        approve = (self.COMMANDS / "approve-review.md").read_text()
        steps = set(re.findall(r"(?m)^(\d+[a-z]?\d?)\. \*\*", approve))
        cited = set(re.findall(r"[Ss]teps? (\d+[a-z]?)", satisfy)) | set(re.findall(r"6\.(\d)", satisfy))
        for step in cited - {"1", "2", "3", "4", "6", "7", "5"}:
            self.assertIn(step, steps | {"4a", "4b", "4c", "6a", "6b", "6c", "6d"})

    def test_the_reviewer_commands_request_the_line_only_for_an_automatic_requiring_gate(self):
        for name in ("review-plan.md", "review-implementation.md"):
            text = self.text(name)
            self.assertIn("Reviewer model: <vendor>/<model>", text, name)
            self.assertIn("requires_distinct", text, name)
            self.assertIn("2.7.0", text, name)
        for name in ("record-manual-plan-review.md", "record-manual-implementation-review.md"):
            text = self.text(name)
            self.assertIn("DistinctReviewerModelsRequiredError", text, name)
            self.assertIn("byte-identical", text, name)
            self.assertNotIn("/adopt-gate-policy", text, name)
        for name in ("milestone-plan.md", "apply-plan-review.md", "milestone-implement.md",
                     "apply-implementation-review.md"):
            text = self.text(name)
            self.assertIn("Reviewer model: <vendor>/<model>", text, name)
            self.assertIn("LPR-R16-003", text, name)
        protocol = " ".join((REPO_ROOT / "docs/ai-workflow/REVIEW_PROTOCOL.md").read_text().split())
        self.assertIn("`Reviewer model:` (workflow-2.8.0, optional)", protocol)

    def test_the_protocol_ingest_passes_the_reporters_run_ref(self):
        with h.ScratchRepo() as repo:
            P, B = plan_at_manual(repo)
            text = manual_text("plan", P, B, base=repo.base)
            put_feedback(repo, text)
            import io, contextlib
            out = io.StringIO()
            outside = tempfile.TemporaryDirectory()
            self.addCleanup(outside.cleanup)
            path = Path(outside.name) / "verdict.md"
            path.write_text(text)
            with contextlib.redirect_stdout(out):
                code = wp.main(["--repo-root", str(repo.root), "record-external-result", "--work-item", WI,
                                "--kind", "plan_review_verdict", "--input", str(path), "--run-ref", "orchestrator:run-42"])
            self.assertEqual(code, 0, out.getvalue())
            self.assertEqual(ledger_of(repo, "plan")[MANUAL_PLAN]["run_ref"], "orchestrator:run-42")


# ---------------------------------------------------------------------------
# CP3: the forge module, functional evidence, pull-request facts, the cause
# table, the query trigger and the stale-evidence table.
# ---------------------------------------------------------------------------

import hashlib
import os
import stat
from unittest import mock

import workflow_forge as forge

FAKE_GH = {"path": "/usr/local/bin/gh", "sha256": "a" * 64}
PROTECTED = h.BUNDLE_ITEM_IMPLEMENTATION_PATH


def pr_checks(kind: str = "success", failing=("ci",)) -> list:
    if kind == "success":
        return [{"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"}]
    if kind == "failure":
        return [{"name": n, "status": "COMPLETED", "conclusion": "FAILURE"} for n in failing]
    if kind == "pending":
        return [{"name": "ci", "status": "IN_PROGRESS", "conclusion": ""}]
    return []


def pr_record(head: str, *, number: int = 7, state: str = "OPEN", decision: str = "", reviews=None,
              checks: str = "success", failing=("ci",)) -> dict:
    return {"number": number, "url": f"https://github.com/o/r/pull/{number}", "state": state,
            "headRefOid": head, "reviewDecision": decision, "reviews": reviews or [],
            "statusCheckRollup": pr_checks(checks, failing)}


def changes_requested(head: str, review_id: str = "R1", body: str = "please fix x") -> list:
    return [{"id": review_id, "state": "CHANGES_REQUESTED", "body": body, "commit": {"oid": head}}]


def reported_payload(records, queried: str, *, repository: str = "o/r", run_ref: str | None = "run-9") -> dict:
    raw = records if isinstance(records, str) else json.dumps(records)
    return {"forge": {"source": "github", "query": "pr-list-v1", "repository": repository,
                      "queried_commit": queried, "fetched_at": "2026-10-03T12:00:00Z",
                      "fetched_by": {"name": "controller-forge", "version": "1"},
                      "raw": raw, "raw_sha256": hashlib.sha256(raw.encode()).hexdigest()},
            "run_ref": run_ref}


def functional_record(head: str, *, flow_id: str = "migration-suite", status: str = "passed", **over) -> dict:
    record = {"flow_id": flow_id, "status": status, "head": head, "ran_at": "2026-10-03T12:00:00Z",
              "summary": {"passed": 120, "failed": 0, "skipped": 2}, "log_digest": "b" * 64,
              "run_ref": "run-3", "reporter": "controller"}
    record.update(over)
    return record


class EvidenceRepo:
    """A real repository holding one implemented, bundle-generated item and an
    `origin` on github.com, so identities are the Workflow's own recomputation."""

    def __enter__(self) -> "EvidenceRepo":
        g.clear_caches()
        self.repo = h.ScratchRepo().__enter__()
        h.seed_bundle_item(self.repo, governing_workflow_version="2.2",
                           phase="SELF_REVIEWING_IMPLEMENTATION", gate_policy=None)
        self.repo.commit("implement", filename=PROTECTED)
        self.rcid = h.generate_implementation_bundle(self.repo)
        self.root = self.repo.root
        h.git(self.repo, "remote", "add", "origin", "https://github.com/o/r.git")
        self.anchor = self.state()["work_items"][WI]["reviewed_implementation_head"]
        self.policy = g.DEFAULT_RESOLVED
        return self

    def __exit__(self, *exc) -> None:
        self.repo.__exit__(*exc)
        g.clear_caches()

    def state(self) -> dict:
        return h.read_state(self.repo)

    def item(self) -> dict:
        return self.state()["work_items"][WI]

    def evidence(self) -> dict:
        return g.gate_evidence_of(self.item())

    def protected_commit(self, text: str) -> str:
        return self.repo.commit(text, filename=PROTECTED)

    def excluded_commit(self) -> str:
        return self.repo.commit("notes", filename="docs/ai-workflow/notes.txt")

    def report(self, records, queried: str | None = None, **kw) -> dict:
        return ws.record_pr_fact(self.root, WI, reported_payload(records, queried or self.anchor, **kw), now=now())

    def query(self, records, *, queried: str | None = None) -> dict:
        calls = []

        def run(argv, timeout):
            calls.append((argv, timeout))
            return records if isinstance(records, str) else json.dumps(records)

        self.calls = calls
        return ws.query_and_store_pr_fact(self.root, WI, now=now(), run=run, resolve=lambda root: dict(FAKE_GH))

    def set_state(self, **item_fields) -> None:
        state = self.state()
        state["work_items"][WI].update(item_fields)
        h.write_state(self.repo, state)

    def position(self, head: str) -> str | None:
        return g.position_of(self.root, WI, self.item(), head)


class TestForgeParser(unittest.TestCase):
    HEAD = "c" * 40

    def test_the_argv_is_the_fixed_constant_with_an_explicit_limit(self):
        argv = forge.gh_argv("o/r", self.HEAD, "/abs/gh")
        self.assertEqual(argv, ["/abs/gh", "pr", "list", "--repo", "o/r", "--state", "all", "--search", self.HEAD,
                                "--limit", "200", "--json",
                                "number,url,state,headRefOid,reviewDecision,reviews,statusCheckRollup"])
        self.assertEqual(forge.FORGE_PR_LIST_LIMIT, 200)

    def test_every_field_is_derived_from_raw(self):
        raw = json.dumps([pr_record(self.HEAD, decision="CHANGES_REQUESTED", checks="failure", failing=("b", "a"),
                                    reviews=changes_requested(self.HEAD, "R9", "fix it"))])
        fact = forge.parse_forge_raw(raw, "o/r", self.HEAD)
        self.assertEqual(fact, {
            "pr": {"number": 7, "url": "https://github.com/o/r/pull/7"}, "state": "open", "head": self.HEAD,
            "review_decision": "CHANGES_REQUESTED", "reviewed_head": self.HEAD,
            "checks": {"state": "failure", "failing": ["a", "b"]}, "review_id": "R9", "findings": "fix it"})

    def test_a_decision_on_an_earlier_head_reads_review_required(self):
        raw = json.dumps([pr_record(self.HEAD, decision="APPROVED",
                                    reviews=[{"id": "R1", "state": "APPROVED", "body": "", "commit": {"oid": "d" * 40}}])])
        fact = forge.parse_forge_raw(raw, "o/r", self.HEAD)
        self.assertEqual((fact["review_decision"], fact["reviewed_head"]), ("REVIEW_REQUIRED", "d" * 40))

    def test_the_checks_state_failure_pending_success_and_none_reported(self):
        for kind, expected in (("success", "success"), ("failure", "failure"), ("pending", "pending"),
                               ("none", "pending")):
            fact = forge.parse_forge_raw(json.dumps([pr_record(self.HEAD, checks=kind)]), "o/r", self.HEAD)
            self.assertEqual(fact["checks"]["state"], expected, kind)

    def test_two_open_pull_requests_are_undecidable_and_a_closed_one_is_not_in_the_way(self):
        two = json.dumps([pr_record(self.HEAD, number=1), pr_record(self.HEAD, number=2)])
        with self.assertRaises(forge.ForgeUndecidableError):
            forge.parse_forge_raw(two, "o/r", self.HEAD)
        mixed = json.dumps([pr_record(self.HEAD, number=1, state="CLOSED"), pr_record(self.HEAD, number=2)])
        self.assertEqual(forge.parse_forge_raw(mixed, "o/r", self.HEAD)["pr"]["number"], 2)

    def test_a_full_page_is_undecidable_and_a_short_page_is_not(self):
        full = json.dumps([pr_record(self.HEAD, number=1)] + [pr_record(self.HEAD, number=n, state="CLOSED")
                                                              for n in range(2, 201)])
        with self.assertRaises(forge.ForgeUndecidableError):
            forge.parse_forge_raw(full, "o/r", self.HEAD)
        short = json.dumps([pr_record(self.HEAD, number=1)] + [pr_record(self.HEAD, number=n, state="CLOSED")
                                                               for n in range(2, 200)])
        self.assertEqual(forge.parse_forge_raw(short, "o/r", self.HEAD)["state"], "open")

    def test_no_pull_request_is_state_none_and_garbage_is_unparseable(self):
        self.assertEqual(forge.parse_forge_raw("[]", "o/r", self.HEAD)["state"], "none")
        for bad in ("not json", "{}", "[1]", json.dumps([{"state": "OPEN"}])):
            with self.assertRaises(forge.ForgeUnparseableError, msg=bad):
                forge.parse_forge_raw(bad, "o/r", self.HEAD)

    def test_the_newest_merged_pull_request_stands_when_none_is_open(self):
        raw = json.dumps([pr_record(self.HEAD, number=3, state="CLOSED"), pr_record(self.HEAD, number=5, state="MERGED")])
        fact = forge.parse_forge_raw(raw, "o/r", self.HEAD)
        self.assertEqual((fact["state"], fact["pr"]["number"]), ("merged", 5))


class TestResolveGh(unittest.TestCase):
    """`resolve_gh` decides on resolution only; the executable is never run."""

    def make_gh(self, directory: Path, mode: int = 0o755) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "gh"
        path.write_text("#!/bin/sh\nexit 0\n")
        path.chmod(mode)
        return path

    def resolve(self, repo_root: Path, directory: Path, *, safe_roots: bool = False):
        env = {"PATH": f"{directory}{os.pathsep}{os.environ['PATH']}"}
        patches = [mock.patch.dict(os.environ, env)]
        if safe_roots:
            patches += [mock.patch.object(forge, "_temp_roots", return_value=[]),
                        mock.patch.object(forge, "_worktree_roots", return_value=[Path("/nonexistent-repo")])]
        with contextlib.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            return forge.resolve_gh(repo_root)

    def test_a_gh_inside_the_repository_a_worktree_or_the_temp_directory_is_refused(self):
        with EvidenceRepo() as ev:
            inside = self.make_gh(ev.root / "bin")
            with self.assertRaises(forge.ForgeUndecidableError) as caught:
                self.resolve(ev.root, inside.parent)
            self.assertIn(str(inside), str(caught.exception))
            tempdir = Path(tempfile.mkdtemp(prefix="wf-gh-"))
            self.addCleanup(shutil.rmtree, tempdir, ignore_errors=True)
            temp_gh = self.make_gh(tempdir)
            with self.assertRaises(forge.ForgeUndecidableError):
                self.resolve(Path("/nonexistent-repo"), temp_gh.parent)
            worktree = Path(tempfile.mkdtemp(prefix="wf-wt-"))
            self.addCleanup(shutil.rmtree, worktree, ignore_errors=True)
            wt_gh = self.make_gh(worktree / "tools")
            with mock.patch.object(forge, "_worktree_roots", return_value=[worktree]), \
                    mock.patch.object(forge, "_temp_roots", return_value=[]), \
                    mock.patch.dict(os.environ, {"PATH": str(wt_gh.parent)}), \
                    self.assertRaises(forge.ForgeUndecidableError):
                forge.resolve_gh(ev.root)

    def test_a_world_writable_directory_or_executable_is_refused_and_a_safe_path_is_accepted(self):
        with EvidenceRepo() as ev:
            base = Path(tempfile.mkdtemp(prefix="wf-gh-"))
            self.addCleanup(shutil.rmtree, base, ignore_errors=True)
            open_dir = base / "open"
            self.make_gh(open_dir)
            open_dir.chmod(0o777)
            with self.assertRaises(forge.ForgeUndecidableError):
                self.resolve(ev.root, open_dir, safe_roots=True)
            loose = self.make_gh(base / "loose", 0o757)
            with self.assertRaises(forge.ForgeUndecidableError):
                self.resolve(ev.root, loose.parent, safe_roots=True)
            safe = self.make_gh(base / "safe")
            found = self.resolve(ev.root, safe.parent, safe_roots=True)
            self.assertEqual(found, {"path": str(safe.resolve()),
                                     "sha256": hashlib.sha256(safe.read_bytes()).hexdigest()})

    def test_a_symlink_in_a_safe_directory_is_refused_by_its_resolved_target(self):
        with EvidenceRepo() as ev:
            target = self.make_gh(ev.root / "bin")
            base = Path(tempfile.mkdtemp(prefix="wf-gh-"))
            self.addCleanup(shutil.rmtree, base, ignore_errors=True)
            (base / "gh").symlink_to(target)
            with self.assertRaises(forge.ForgeUndecidableError):
                self.resolve(ev.root, base, safe_roots=False)

    def test_a_gh_that_is_not_found_is_unavailable(self):
        empty = Path(tempfile.mkdtemp(prefix="wf-gh-"))
        self.addCleanup(shutil.rmtree, empty, ignore_errors=True)
        with mock.patch.dict(os.environ, {"PATH": str(empty)}), self.assertRaises(forge.ForgeUnavailableError):
            forge.resolve_gh(Path("/nonexistent-repo"))


class TestWorkflowQuery(unittest.TestCase):
    def test_the_query_runs_the_absolute_path_with_the_fixed_argv_and_a_timeout(self):
        with EvidenceRepo() as ev:
            ev.query([pr_record(ev.anchor)])
            argv, timeout = ev.calls[0]
            self.assertEqual(argv, forge.gh_argv("o/r", ev.anchor, FAKE_GH["path"]))
            self.assertTrue(os.path.isabs(argv[0]))
            self.assertEqual(timeout, 30)
            fact = ev.evidence()["pr"]
            self.assertEqual(fact["provenance"]["source"], "workflow_gh")
            self.assertEqual((fact["provenance"]["gh_path"], fact["provenance"]["gh_sha256"]),
                             (FAKE_GH["path"], FAKE_GH["sha256"]))
            self.assertEqual(fact["queried_commit"], ev.anchor)

    def test_no_pull_request_stores_state_none(self):
        with EvidenceRepo() as ev:
            ev.query([])
            fact = ev.evidence()["pr"]
            self.assertEqual((fact["state"], fact["pr"]), ("none", None))
            self.assertEqual(g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy), [])

    def test_every_failure_raises_and_writes_nothing(self):
        failures = (forge.ForgeUnavailableError("gh is not installed"), forge.ForgeUnavailableError("exit 1"),
                    forge.ForgeUnavailableError("timed out"))
        with EvidenceRepo() as ev:
            before = state_bytes(ev.repo)
            for exc in failures:
                def run(argv, timeout, exc=exc):
                    raise exc
                with self.assertRaises(forge.ForgeUnavailableError):
                    ws.query_and_store_pr_fact(ev.root, WI, now=now(), run=run, resolve=lambda r: dict(FAKE_GH))
            for bad, error in (("not json", forge.ForgeUnparseableError),
                               (json.dumps([pr_record(ev.anchor, number=1), pr_record(ev.anchor, number=2)]),
                                forge.ForgeUndecidableError)):
                with self.assertRaises(error):
                    ev.query(bad)
            with self.assertRaises(forge.ForgeUndecidableError):
                ws.query_and_store_pr_fact(
                    ev.root, WI, now=now(), run=lambda a, t: "[]",
                    resolve=lambda r: (_ for _ in ()).throw(forge.ForgeUndecidableError("unsafe gh")))
            self.assertEqual(state_bytes(ev.repo), before)

    def test_a_full_page_stores_nothing(self):
        with EvidenceRepo() as ev:
            before = state_bytes(ev.repo)
            page = [pr_record(ev.anchor, number=1)] + [pr_record(ev.anchor, number=n, state="CLOSED") for n in range(2, 201)]
            with self.assertRaises(forge.ForgeUndecidableError):
                ev.query(page)
            self.assertIn("--limit", ev.calls[0][0])
            self.assertEqual(ev.calls[0][0][ev.calls[0][0].index("--limit") + 1], "200")
            self.assertEqual(state_bytes(ev.repo), before)

    def test_an_unresolvable_or_foreign_head_stores_nothing(self):
        with EvidenceRepo() as ev:
            before = state_bytes(ev.repo)
            with self.assertRaises(g.EvidenceRefusedError) as caught:
                ev.query([pr_record("e" * 40)])
            self.assertEqual(caught.exception.code, "pr_head_unknown")
            h.git(ev.repo, "checkout", "-q", "-b", "other", ev.repo.base)
            other = ev.repo.commit("elsewhere", filename="elsewhere.txt")
            h.git(ev.repo, "checkout", "-q", "-")
            with self.assertRaises(g.EvidenceRefusedError) as caught:
                ev.query([pr_record(other)])
            self.assertEqual(caught.exception.code, "pr_head_not_in_branch")
            self.assertEqual(state_bytes(ev.repo), before)

    def test_the_replaced_slot_keeps_the_key_sets(self):
        with EvidenceRepo() as ev:
            ev.query([pr_record(ev.anchor)])
            state = ev.state()
            state["work_items"][WI]["gate_evidence"]["pr_keys"].update(reopened_for=["k1"], applied=["k0"])
            h.write_state(ev.repo, state)
            ev.query([pr_record(ev.anchor, checks="failure")])
            keys = ev.evidence()["pr_keys"]
            self.assertEqual((keys["reopened_for"], keys["applied"], keys["ingest_seq"]), (["k1"], ["k0"], 2))


class TestFunctionalEvidence(unittest.TestCase):
    def test_identity_is_recomputed_at_head_and_a_reporters_claim_is_never_read(self):
        with EvidenceRepo() as ev:
            result = ws.record_functional_evidence(ev.root, WI, functional_record(ev.anchor), now=now())
            self.assertEqual(result["identity"], ev.rcid)
            self.assertEqual(result["stored"]["identity"], ev.rcid)
            with self.assertRaises(g.EvidenceRefusedError) as caught:
                ws.record_functional_evidence(ev.root, WI, functional_record(ev.anchor, identity="f" * 64), now=now())
            self.assertEqual(caught.exception.code, "evidence_malformed")

    def test_the_audit_keys_are_kept_and_a_fabricated_record_is_the_stated_boundary(self):
        with EvidenceRepo() as ev:
            ws.record_functional_evidence(ev.root, WI, functional_record(ev.anchor, flow_id="never-ran"), now=now())
            stored = ev.evidence()["functional"]["never-ran"]
            self.assertEqual((stored["log_digest"], stored["reporter"], stored["run_ref"]), ("b" * 64, "controller", "run-3"))
            self.assertTrue(g.functional_record_current(ev.root, WI, ev.item(), stored))

    def test_an_excluded_only_commit_keeps_it_current_and_protected_content_stales_it(self):
        with EvidenceRepo() as ev:
            ws.record_functional_evidence(ev.root, WI, functional_record(ev.anchor), now=now())
            ev.excluded_commit()
            record = ev.evidence()["functional"]["migration-suite"]
            self.assertEqual(g.identity_at(ev.root, WI, ev.item(), "HEAD"), ev.rcid)
            self.assertTrue(g.functional_record_current(ev.root, WI, ev.item(), record))
            moved = ev.protected_commit("changed implementation")
            ws.record_functional_evidence(ev.root, WI, functional_record(moved, flow_id="later"), now=now())
            self.assertTrue(g.functional_record_current(ev.root, WI, ev.item(), record), "judged against the anchor")
            self.assertFalse(g.functional_record_current(
                ev.root, WI, ev.item(), ev.evidence()["functional"]["later"]), "new content differs from the anchor")

    def test_a_failed_run_is_recorded_and_not_current_and_a_rereport_replaces_it(self):
        with EvidenceRepo() as ev:
            ws.record_functional_evidence(ev.root, WI, functional_record(ev.anchor, status="failed"), now=now())
            self.assertFalse(g.functional_record_current(ev.root, WI, ev.item(), ev.evidence()["functional"]["migration-suite"]))
            ws.record_functional_evidence(ev.root, WI, functional_record(ev.anchor), now=now())
            record = ev.evidence()["functional"]["migration-suite"]
            self.assertEqual(record["status"], "passed")
            self.assertEqual(len(ev.evidence()["functional"]), 1)

    def test_an_unresolvable_head_or_one_outside_the_branch_refuses_and_writes_nothing(self):
        with EvidenceRepo() as ev:
            before = state_bytes(ev.repo)
            with self.assertRaises(g.EvidenceRefusedError) as caught:
                ws.record_functional_evidence(ev.root, WI, functional_record("e" * 40), now=now())
            self.assertEqual(caught.exception.code, "evidence_head_unknown")
            h.git(ev.repo, "checkout", "-q", "-b", "other", ev.repo.base)
            other = ev.repo.commit("elsewhere", filename="elsewhere.txt")
            h.git(ev.repo, "checkout", "-q", "-")
            with self.assertRaises(g.EvidenceRefusedError) as caught:
                ws.record_functional_evidence(ev.root, WI, functional_record(other), now=now())
            self.assertEqual(caught.exception.code, "evidence_head_not_in_branch")
            self.assertEqual(state_bytes(ev.repo), before)

    def test_malformed_records_are_refused(self):
        with EvidenceRepo() as ev:
            for bad in (functional_record(ev.anchor, flow_id="Bad Id"), functional_record(ev.anchor, status="skipped"),
                        functional_record(ev.anchor, log_digest="short"), "text"):
                with self.assertRaises(g.EvidenceRefusedError):
                    ws.record_functional_evidence(ev.root, WI, bad, now=now())

    def test_it_is_accepted_under_the_all_human_policy_too(self):
        with EvidenceRepo() as ev:
            (ev.root / POLICY_REL).parent.mkdir(parents=True, exist_ok=True)
            (ev.root / POLICY_REL).write_text(json.dumps(HUMAN))
            ws.record_functional_evidence(ev.root, WI, functional_record(ev.anchor), now=now())
            self.assertIn("migration-suite", ev.evidence()["functional"])


class TestReportedPullRequestFacts(unittest.TestCase):
    def test_a_self_consistent_report_is_stored_in_its_own_slot_as_orchestrator_forge(self):
        with EvidenceRepo() as ev:
            result = ev.report([pr_record(ev.anchor)])
            evidence = ev.evidence()
            self.assertIsNone(evidence["pr"])
            fact = evidence["pr_reported"]
            self.assertEqual(result["slot"], "pr_reported")
            self.assertEqual(fact["provenance"]["source"], "orchestrator_forge")
            self.assertEqual(fact["provenance"]["fetched_by"], {"name": "controller-forge", "version": "1"})
            self.assertEqual(fact["provenance"]["run_ref"], "run-9")
            self.assertEqual(fact["head"], ev.anchor)
            self.assertEqual(fact["ingest_seq"], 1)

    def test_provenance_refusals_write_nothing(self):
        with EvidenceRepo() as ev:
            before = state_bytes(ev.repo)
            good = reported_payload([pr_record(ev.anchor)], ev.anchor)
            cases = []
            cases.append((forge.ForgeProvenanceRequiredError, {"run_ref": "x"}))
            cases.append((forge.ForgeProvenanceRequiredError, {"forge": {"raw": "[]"}, "run_ref": "x"}))
            tampered = copy.deepcopy(good)
            tampered["forge"]["raw_sha256"] = "0" * 64
            cases.append((forge.ForgeDigestMismatchError, tampered))
            cases.append((forge.ForgeRepositoryMismatchError,
                          reported_payload([pr_record(ev.anchor)], ev.anchor, repository="other/repo")))
            cases.append((forge.ForgeUnparseableError, reported_payload("not json", ev.anchor)))
            cases.append((forge.ForgeUndecidableError, reported_payload(
                [pr_record(ev.anchor, number=1), pr_record(ev.anchor, number=2)], ev.anchor)))
            for error, payload in cases:
                with self.assertRaises(error):
                    ws.record_pr_fact(ev.root, WI, payload, now=now())
            self.assertEqual(state_bytes(ev.repo), before)

    def test_reporter_supplied_fields_are_not_read(self):
        with EvidenceRepo() as ev:
            payload = reported_payload([pr_record(ev.anchor, checks="failure")], ev.anchor)
            payload.update(state="merged", head="1" * 40, review_decision="APPROVED", checks={"state": "success"})
            payload["forge"].update(state="merged")
            ws.record_pr_fact(ev.root, WI, payload, now=now())
            fact = ev.evidence()["pr_reported"]
            self.assertEqual((fact["state"], fact["head"], fact["checks"]["state"]), ("open", ev.anchor, "failure"))

    def test_an_unresolvable_head_or_one_outside_the_branch_refuses(self):
        with EvidenceRepo() as ev:
            with self.assertRaises(g.EvidenceRefusedError) as caught:
                ev.report([pr_record("e" * 40)])
            self.assertEqual(caught.exception.code, "pr_head_unknown")

    def test_a_reported_fact_is_tighten_only_and_read_by_no_decision(self):
        with EvidenceRepo() as ev:
            ev.report([pr_record(ev.anchor, decision="APPROVED",
                                 reviews=[{"id": "R1", "state": "APPROVED", "body": "", "commit": {"oid": ev.anchor}}])])
            fact = ev.evidence()["pr_reported"]
            for cause in g.CAUSES:
                self.assertFalse(g.pr_key_actionable(ev.policy, fact, cause))
            self.assertEqual(g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy), [])

    def test_a_red_report_reopens_nothing_by_itself_it_arms_the_trigger(self):
        with EvidenceRepo() as ev:
            phase_before = ev.item()["phase"]
            ev.report([pr_record(ev.anchor, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor))])
            state = ev.state()
            self.assertEqual(g.actionable_pr_keys(ev.root, state, WI, ev.policy), [])
            self.assertTrue(g.pr_query_trigger(state, WI, ev.policy))
            self.assertEqual(state["work_items"][WI]["phase"], phase_before)
            self.assertNotIn("reopenings", state["work_items"][WI])

    def test_one_slot_per_source_and_a_green_report_never_hides_a_red_workflow_fact(self):
        with EvidenceRepo() as ev:
            ev.query([pr_record(ev.anchor, checks="failure")])
            ev.report([pr_record(ev.anchor)])
            evidence = ev.evidence()
            self.assertEqual(evidence["pr"]["checks"]["state"], "failure")
            self.assertEqual(evidence["pr_reported"]["checks"]["state"], "success")
            keys = g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy)
            self.assertEqual([k["cause"] for k in keys], ["checks_failed"])

    def test_ingest_seq_is_assigned_by_the_workflow_strictly_increasing(self):
        with EvidenceRepo() as ev:
            ev.report([pr_record(ev.anchor)])
            ev.query([pr_record(ev.anchor)])
            ev.report([pr_record(ev.anchor)], run_ref=None)
            evidence = ev.evidence()
            self.assertEqual((evidence["pr_reported"]["ingest_seq"], evidence["pr"]["ingest_seq"]), (3, 2))
            self.assertEqual(evidence["pr_keys"], {"reopened_for": [], "applied": [], "ingest_seq": 3})
            self.assertIsNone(evidence["pr_reported"]["provenance"]["run_ref"])

    def test_a_pr_review_result_is_recorded_at_every_phase_with_no_state_effect(self):
        for phase in ("IMPLEMENTING", "AWAITING_LOCAL_IMPLEMENTATION_REVIEW", "AWAITING_FUNCTIONAL_REVIEW",
                      "MILESTONE_COMPLETE", "PLANNING"):
            with self.subTest(phase=phase), EvidenceRepo() as ev:
                ev.set_state(phase=phase)
                ev.query([pr_record(ev.anchor, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor))])
                item = ev.item()
                self.assertEqual(item["phase"], phase)
                self.assertNotIn("reopenings", item)
                self.assertEqual(item.get("technical_approval"), None)
                keys = g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy)
                self.assertEqual([k["cause"] for k in keys], ["changes_requested"],
                                 "recorded now, actionable once the item reaches a reopenable phase")


class TestCauseTable(unittest.TestCase):
    def facts(self, ev: EvidenceRepo, **kw) -> dict:
        ev.query([pr_record(ev.anchor, **kw)])
        return ev.evidence()["pr"]

    def test_the_three_key_functions_are_deterministic_and_independent_of_observed_at(self):
        with EvidenceRepo() as ev:
            fact = self.facts(ev, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor, "R4"),
                              checks="failure", failing=("z", "a"))
            self.assertEqual(g.cause_key("changes_requested", fact),
                             g.key_string(7, "changes_requested", ev.anchor, ev.anchor, "R4"))
            self.assertEqual(g.cause_key("checks_failed", fact), g.key_string(7, "checks_failed", ev.anchor, ["a", "z"]))
            self.assertEqual(g.cause_key("content_changed", fact),
                             g.key_string(7, "content_changed", ev.anchor, ev.rcid))
            again = copy.deepcopy(fact)
            again.update(observed_at="later", ingest_seq=99, findings="reworded")
            for cause in g.CAUSES:
                self.assertEqual(g.cause_key(cause, again), g.cause_key(cause, fact))

    def test_repolling_the_same_unchanged_fact_is_idempotent_on_the_key(self):
        with EvidenceRepo() as ev:
            self.facts(ev, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor), checks="failure")
            first = g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy)
            self.facts(ev, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor), checks="failure")
            self.assertEqual(g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy), first)
            self.assertEqual(ev.evidence()["pr_keys"]["ingest_seq"], 2, "still stamped with a fresh seq")

    def test_a_new_review_a_new_head_or_a_new_failing_set_is_a_new_key(self):
        with EvidenceRepo() as ev:
            a = self.facts(ev, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor, "R1"))
            b = self.facts(ev, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor, "R2"))
            self.assertNotEqual(g.cause_key("changes_requested", a), g.cause_key("changes_requested", b))
            c = self.facts(ev, checks="failure", failing=("x",))
            d = self.facts(ev, checks="failure", failing=("x", "y"))
            self.assertNotEqual(g.cause_key("checks_failed", c), g.cause_key("checks_failed", d))

    def test_content_changed_is_tested_first_and_acts_on_nothing_else(self):
        with EvidenceRepo() as ev:
            ahead = ev.protected_commit("pr carries new content")
            ev.query([pr_record(ahead, decision="CHANGES_REQUESTED", reviews=changes_requested(ahead), checks="failure")])
            keys = g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy)
            self.assertEqual([k["cause"] for k in keys], ["content_changed"])
            self.assertEqual(keys[0]["key"], g.cause_key("content_changed", ev.evidence()["pr"]))

    def test_actionability_honors_the_policy_the_state_and_applied_keys(self):
        with EvidenceRepo() as ev:
            self.facts(ev, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor), checks="failure")
            state = ev.state()
            self.assertEqual({k["cause"] for k in g.actionable_pr_keys(ev.root, state, WI, ev.policy)},
                             {"changes_requested", "checks_failed"})
            off = g.resolve_policy({"schema_version": 1, "pr_review": {"enabled": False}})
            self.assertEqual(g.actionable_pr_keys(ev.root, state, WI, off), [])
            only_checks = g.resolve_policy({"schema_version": 1, "pr_review": {"enabled": True, "reopen_on": ["checks_failed"]}})
            self.assertEqual([k["cause"] for k in g.actionable_pr_keys(ev.root, state, WI, only_checks)], ["checks_failed"])
            applied = g.cause_key("checks_failed", ev.evidence()["pr"])
            state["work_items"][WI]["gate_evidence"]["pr_keys"]["applied"] = [applied]
            self.assertEqual([k["cause"] for k in g.actionable_pr_keys(ev.root, state, WI, ev.policy)], ["changes_requested"])
            self.assertEqual(g.actionable_pr_keys(ev.root, state, WI, off), [], "re-evaluated on the current policy")

    def test_a_closed_unmerged_or_merged_pr_is_recorded_and_never_actionable(self):
        for pr_state in ("CLOSED", "MERGED"):
            with self.subTest(pr_state), EvidenceRepo() as ev:
                self.facts(ev, state=pr_state, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor))
                self.assertEqual(g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy), [])
                re_opened = self.facts(ev, state="OPEN", decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor))
                self.assertEqual(re_opened["state"], "open")
                self.assertEqual(len(g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy)), 1,
                                 "a fresh query finding the PR open makes the same key actionable again")

    def test_a_content_changed_head_on_a_completed_item_is_actionable_and_stales_nothing(self):
        with EvidenceRepo() as ev:
            approval = {"status": "CURRENT"}
            ev.set_state(phase="MILESTONE_COMPLETE")
            ahead = ev.protected_commit("post-completion content")
            ev.query([pr_record(ahead)])
            item = ev.item()
            self.assertEqual(item["phase"], "MILESTONE_COMPLETE")
            self.assertEqual([k["cause"] for k in g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy)],
                             ["content_changed"])
            self.assertNotEqual(item.get("technical_approval"), {"status": "STALE"})
            del approval

    def test_failed_checks_pending_checks_and_a_stale_head_are_recorded_and_not_current_and_passing(self):
        with EvidenceRepo() as ev:
            moved = ev.protected_commit("new content")
            for kwargs, head in (({"checks": "failure"}, ev.anchor), ({"checks": "pending"}, ev.anchor),
                                 ({"checks": "success"}, moved)):
                ev.query([pr_record(head, **kwargs)])
                fact = ev.evidence()["pr"]
                current = g.current_at_anchor(ev.root, WI, ev.item(), fact["head"], identity_at_head=fact["identity_at_head"])
                passing = fact["checks"]["state"] == "success"
                self.assertFalse(current and passing, (kwargs, head))


class TestPositionRelativeToTheAnchor(unittest.TestCase):
    def test_equal_ahead_and_behind(self):
        with EvidenceRepo() as ev:
            self.assertEqual(ev.position(ev.anchor), "equal")
            self.assertEqual(ev.position(ev.excluded_commit()), "equal")
            ahead = ev.protected_commit("new protected content")
            self.assertEqual(ev.position(ahead), "ahead")
            ev.set_state(reviewed_implementation_head=ahead)
            self.assertEqual(ev.position(ahead), "equal")
            self.assertEqual(ev.position(ev.anchor), "behind", "an unpushed bounded fix moved the anchor")

    def test_the_technical_approval_commit_is_the_anchor_when_there_is_one(self):
        with EvidenceRepo() as ev:
            ahead = ev.protected_commit("approved content")
            ev.set_state(technical_approval={"status": "CURRENT", "reviewed_content_commit": ahead,
                                             "approved_review_content_id": g.identity_at(ev.root, WI, ev.item(), ahead)})
            self.assertEqual(g.anchor_of(ev.root, WI, ev.item())["commit"], ahead)
            self.assertEqual(ev.position(ev.anchor), "behind")

    def test_a_behind_fact_is_recorded_not_actionable_and_not_the_content_changed_cause(self):
        with EvidenceRepo() as ev:
            ahead = ev.protected_commit("approved content")
            ev.set_state(reviewed_implementation_head=ahead)
            ev.query([pr_record(ev.anchor, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor), checks="failure")])
            fact = ev.evidence()["pr"]
            self.assertEqual(g.apply_invalidation(ev.root, ev.state(), WI, fact)["rule"], "behind")
            self.assertEqual(g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy), [])
            self.assertFalse(g.current_at_anchor(ev.root, WI, ev.item(), fact["head"],
                                                 identity_at_head=fact["identity_at_head"]))

    def test_an_ahead_head_still_reopens_with_content_changed(self):
        with EvidenceRepo() as ev:
            ahead = ev.protected_commit("pr content")
            ev.query([pr_record(ahead)])
            self.assertEqual(g.apply_invalidation(ev.root, ev.state(), WI, ev.evidence()["pr"])["rule"], "ahead")

    def test_no_anchor_means_no_position_and_no_actionable_key(self):
        with EvidenceRepo() as ev:
            ev.set_state(reviewed_implementation_head=None)
            self.assertIsNone(g.anchor_of(ev.root, WI, ev.item()))
            self.assertIsNone(ev.position(ev.anchor))


class TestInvalidationTable(unittest.TestCase):
    def rule(self, ev: EvidenceRepo, head: str | None = None, **kw) -> dict:
        previous = ev.evidence()["pr"]
        ev.query([pr_record(head or ev.anchor, **kw)])
        return g.apply_invalidation(ev.root, ev.state(), WI, ev.evidence()["pr"], previous=previous)

    def test_every_row_of_the_table(self):
        with EvidenceRepo() as ev:
            rows = {}
            rows["merged"] = self.rule(ev, state="MERGED")
            rows["closed"] = self.rule(ev, state="CLOSED")
            rows["changes_requested"] = self.rule(ev, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor))
            rows["checks_failed"] = self.rule(ev, checks="failure")
            rows["approved"] = self.rule(ev, decision="APPROVED", reviews=[
                {"id": "R1", "state": "APPROVED", "body": "", "commit": {"oid": ev.anchor}}])
            rows["same"] = self.rule(ev, head=ev.excluded_commit())
            rows["ahead"] = self.rule(ev, head=ev.protected_commit("new content"))
            self.assertEqual({k: v["rule"] for k, v in rows.items()},
                             {"merged": "merged", "closed": "closed", "changes_requested": "changes_requested",
                              "checks_failed": "checks_failed", "approved": "approved",
                              "same": "head_changed_same_identity", "ahead": "ahead"})
            self.assertEqual({r["id"] for r in g.INVALIDATION_RULES} - {v["rule"] for v in rows.values()}, {"behind"})
            self.assertIn("technical_approval", rows["same"]["stays"])
            self.assertIn("functional", rows["ahead"]["stale"])
            self.assertNotIn("technical_approval", rows["ahead"]["stale"], "never staled at ingest")
            self.assertEqual(rows["changes_requested"]["causes"], ["changes_requested"])

    def test_an_outdated_review_reads_review_required_and_is_not_changes_requested(self):
        with EvidenceRepo() as ev:
            earlier = ev.anchor
            later = ev.excluded_commit()
            result = self.rule(ev, head=later, decision="CHANGES_REQUESTED", reviews=changes_requested(earlier))
            self.assertEqual(ev.evidence()["pr"]["review_decision"], "REVIEW_REQUIRED")
            self.assertEqual(result["causes"], [])

    def test_a_reopened_pr_is_a_new_fact(self):
        with EvidenceRepo() as ev:
            ev.query([pr_record(ev.anchor, state="CLOSED")])
            result = self.rule(ev, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor))
            self.assertIn("a reopened PR is a new fact", result["effect"])

    def test_no_ci_produced_evidence_kind_is_offered_anywhere(self):
        text = (SCRIPTS / "workflow_gate_policy.py").read_text() + (SCRIPTS / "workflow_forge.py").read_text()
        for word in ("ci_functional", "ci_evidence", "ci_review", "ci_result"):
            self.assertNotIn(word, text)
        self.assertEqual(set(g._TOP_KEYS), {"schema_version", "human_approval", "gates", "pr_review"})
        self.assertNotIn("ci_produced", json.dumps(g.DEFAULT_POLICY))


class TestQueryTrigger(unittest.TestCase):
    def red(self, ev, **kw):
        return [pr_record(ev.anchor, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor), **kw)]

    def test_a_newer_differing_report_arms_it_and_the_query_clears_it(self):
        with EvidenceRepo() as ev:
            ev.query([pr_record(ev.anchor, state="CLOSED")])
            ev.report(self.red(ev))
            self.assertTrue(g.pr_query_trigger(ev.state(), WI, ev.policy))
            ev.query([pr_record(ev.anchor, state="CLOSED")])
            self.assertFalse(g.pr_query_trigger(ev.state(), WI, ev.policy), "any successful query clears it")

    def test_an_older_or_equal_report_arms_nothing(self):
        with EvidenceRepo() as ev:
            ev.report(self.red(ev))
            ev.query([pr_record(ev.anchor, state="MERGED")])
            self.assertFalse(g.pr_query_trigger(ev.state(), WI, ev.policy), "the older reported key is never actionable")
            ev.report([pr_record(ev.anchor, state="MERGED")])
            self.assertFalse(g.pr_query_trigger(ev.state(), WI, ev.policy), "equal to the stored fact")

    def test_an_empty_pr_slot_or_state_none_differs_from_any_report(self):
        with EvidenceRepo() as ev:
            self.assertFalse(g.pr_query_trigger(ev.state(), WI, ev.policy), "no report")
            ev.report([pr_record(ev.anchor)])
            self.assertTrue(g.pr_query_trigger(ev.state(), WI, ev.policy))
            ev.query([])
            self.assertFalse(g.pr_query_trigger(ev.state(), WI, ev.policy))
            ev.report([pr_record(ev.anchor)])
            self.assertTrue(g.pr_query_trigger(ev.state(), WI, ev.policy))

    def test_a_reported_merged_closed_or_open_fact_never_decides_a_stored_key(self):
        for reported_state in ("MERGED", "CLOSED"):
            with self.subTest(reported_state), EvidenceRepo() as ev:
                ev.query(self.red(ev))
                stored_keys = g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy)
                ev.report([pr_record(ev.anchor, state=reported_state)])
                self.assertEqual(g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy), stored_keys,
                                 "the stored workflow_gh key stays actionable")
                self.assertTrue(g.pr_query_trigger(ev.state(), WI, ev.policy))
        with EvidenceRepo() as ev:
            ev.query([pr_record(ev.anchor, state="CLOSED")])
            ev.report(self.red(ev))
            self.assertEqual(g.actionable_pr_keys(ev.root, ev.state(), WI, ev.policy), [],
                             "a reported open key never makes a closed workflow_gh fact actionable")
            self.assertTrue(g.pr_query_trigger(ev.state(), WI, ev.policy))

    def test_with_pr_review_disabled_nothing_arms_and_the_fact_is_still_recorded(self):
        with EvidenceRepo() as ev:
            ev.report(self.red(ev))
            off = g.resolve_policy({"schema_version": 1, "pr_review": {"enabled": False}})
            self.assertFalse(g.pr_query_trigger(ev.state(), WI, off))
            self.assertIsNotNone(ev.evidence()["pr_reported"])

    def test_one_report_is_at_most_one_successful_query(self):
        with EvidenceRepo() as ev:
            ev.report(self.red(ev))
            self.assertTrue(g.pr_query_trigger(ev.state(), WI, ev.policy))
            ev.query(self.red(ev))
            self.assertFalse(g.pr_query_trigger(ev.state(), WI, ev.policy))
            self.assertFalse(g.pr_query_trigger(ev.state(), WI, ev.policy))

    def test_an_unavailable_gh_leaves_the_trigger_armed(self):
        with EvidenceRepo() as ev:
            ev.report(self.red(ev))

            def run(argv, timeout):
                raise forge.ForgeUnavailableError("gh is not installed")

            with self.assertRaises(forge.ForgeUnavailableError):
                ws.query_and_store_pr_fact(ev.root, WI, now=now(), run=run, resolve=lambda r: dict(FAKE_GH))
            self.assertTrue(g.pr_query_trigger(ev.state(), WI, ev.policy))


class TestGateEvidenceShape(unittest.TestCase):
    def test_the_shape_round_trips_through_validate_state_and_an_unknown_key_is_rejected(self):
        with EvidenceRepo() as ev:
            ev.query([pr_record(ev.anchor)])
            ev.report([pr_record(ev.anchor)])
            ws.record_functional_evidence(ev.root, WI, functional_record(ev.anchor), now=now())
            state = ev.state()
            ws.validate_state(state)
            self.assertEqual(set(state["work_items"][WI]["gate_evidence"]),
                             {"functional", "pr", "pr_reported", "pr_keys"})
            bad = copy.deepcopy(state)
            bad["work_items"][WI]["gate_evidence"]["extra"] = {}
            with self.assertRaises(ws.InvalidGateEvidenceError):
                ws.validate_state(bad)
            bad = copy.deepcopy(state)
            del bad["work_items"][WI]["gate_evidence"]["pr"]["provenance"]["gh_sha256"]
            with self.assertRaises(ws.InvalidGateEvidenceError):
                ws.validate_state(bad)
            bad = copy.deepcopy(state)
            bad["work_items"][WI]["gate_evidence"]["pr_reported"]["provenance"]["source"] = "workflow_gh"
            with self.assertRaises(ws.InvalidGateEvidenceError):
                ws.validate_state(bad)
            bad = copy.deepcopy(state)
            bad["work_items"][WI]["gate_evidence"]["pr_keys"]["ingest_seq"] = 0
            with self.assertRaises(ws.InvalidGateEvidenceError):
                ws.validate_state(bad)

    def test_a_state_without_the_key_is_byte_identical_to_before(self):
        with EvidenceRepo() as ev:
            self.assertNotIn("gate_evidence", ev.item())
            ws.validate_state(ev.state())

    def test_pr_keys_never_holds_a_key_derived_from_a_reported_fact(self):
        with EvidenceRepo() as ev:
            ev.report([pr_record(ev.anchor, decision="CHANGES_REQUESTED", reviews=changes_requested(ev.anchor))])
            self.assertEqual(ev.evidence()["pr_keys"]["reopened_for"], [])
            self.assertEqual(ev.evidence()["pr_keys"]["applied"], [])


class TestGateEvidenceCommitContracts(unittest.TestCase):
    """`gate_evidence` joins the three field sets for the same item; another
    item's residue is kept out of a commit by item-scoped staging, and no
    validator is widened for it (item 267 unweakened)."""

    def residue(self, state: dict, item: str) -> None:
        evidence = g.empty_gate_evidence()
        evidence["functional"]["flow"] = {k: "x" for k in g._FUNCTIONAL_FIELDS}
        evidence["functional"]["flow"].update(flow_id="flow", status="passed", summary={})
        state["work_items"][item]["gate_evidence"] = evidence

    def generation_commit(self, repo: PolicyRepo, scoped: bool) -> str:
        repo.write_state(two_item_state(a={"phase": "SELF_REVIEWING_IMPLEMENTATION"}))
        repo.commit("two items", STATE_REL)
        state = ws.record_bundle_generation(repo.state(), "a", stage="implementation", head=repo.head(), now="t-gen")
        self.residue(state, "a")
        self.residue(state, "b")
        repo.write_state(state)
        if scoped:
            self.assertTrue(ws.stage_scoped_state(repo.root, "a"))
        else:
            repo.git("add", "--", STATE_REL)
        revision = state["work_items"]["a"]["implementation_revision"]
        repo.git("commit", "-q", "-m", "record bundle generation", "-m",
                 f"Workflow-Bundle-Generation-Record: a/{revision}\nWorkflow-Work-Item: a")
        return repo.head()

    def test_the_three_field_sets_admit_the_items_own_gate_evidence(self):
        for fields in (ws.TECHNICAL_APPROVAL_COMMIT_FIELDS, ws.ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS,
                       ws.RECOVERED_BUNDLE_GENERATION_RECORD_FIELDS):
            self.assertIn("gate_evidence", fields)

    def test_the_items_own_residue_passes_and_the_foreign_residue_stays_out_when_scoped(self):
        with PolicyRepo() as repo:
            commit = self.generation_commit(repo, scoped=True)
            ws.validate_bundle_generation_record_commit(repo.root, commit, "a")
            committed = json.loads(repo.git("show", f"{commit}:{STATE_REL}"))
            self.assertIn("gate_evidence", committed["work_items"]["a"])
            self.assertNotIn("gate_evidence", committed["work_items"]["b"], "no change to the other item")
            self.assertIn("gate_evidence", repo.state()["work_items"]["b"], "still in the working tree")

    def test_foreign_residue_in_an_unscoped_commit_is_still_refused(self):
        with PolicyRepo() as repo:
            commit = self.generation_commit(repo, scoped=False)
            with self.assertRaises(ws.MalformedBundleGenerationRecordCommitError):
                ws.validate_bundle_generation_record_commit(repo.root, commit, "a")

    def test_a_hand_built_commit_carrying_a_foreign_unrelated_field_is_still_refused(self):
        with PolicyRepo() as repo:
            repo.write_state(two_item_state(a={"phase": "SELF_REVIEWING_IMPLEMENTATION"}))
            repo.commit("two items", STATE_REL)
            state = ws.record_bundle_generation(repo.state(), "a", stage="implementation", head=repo.head(), now="t-gen")
            state["work_items"]["b"]["phase"] = "AWAITING_FUNCTIONAL_REVIEW"
            repo.write_state(state)
            repo.git("add", "--", STATE_REL)
            revision = state["work_items"]["a"]["implementation_revision"]
            repo.git("commit", "-q", "-m", "x", "-m",
                     f"Workflow-Bundle-Generation-Record: a/{revision}\nWorkflow-Work-Item: a")
            with self.assertRaises(ws.MalformedBundleGenerationRecordCommitError):
                ws.validate_bundle_generation_record_commit(repo.root, repo.head(), "a")


if __name__ == "__main__":
    unittest.main()
