# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json
import typing


class EvidenceAdjudicator(gl.Contract):
    claim: str
    verdict: str
    confidence: int
    rationale: str
    source_a: str
    source_b: str

    def __init__(self):
        self.claim = ""
        self.verdict = ""
        self.confidence = 0
        self.rationale = ""
        self.source_a = ""
        self.source_b = ""

    def _analyze(self, claim: str, source_a: str, source_b: str) -> dict:
        def fetch_and_judge():
            a = gl.nondet.web.get(source_a)
            b = gl.nondet.web.get(source_b)

            text_a = a.body.decode("utf-8")[:10000]
            text_b = b.body.decode("utf-8")[:10000]

            prompt = f"""
You are an evidence adjudicator.

Evaluate the CLAIM using ONLY the two supplied public sources.

CLAIM:
{claim}

SOURCE A URL:
{source_a}

SOURCE A CONTENT:
{text_a}

SOURCE B URL:
{source_b}

SOURCE B CONTENT:
{text_b}

Your task is to determine whether the two sources, taken together, support
the claim.

Return ONLY valid JSON with exactly these fields:
{{
  "verdict": "SUPPORTED" | "REFUTED" | "UNCERTAIN",
  "confidence": 0,
  "rationale": "2-4 concise sentences grounded in the supplied sources"
}}

Rules:
- SUPPORTED means the sources provide direct or strong evidence for the claim.
- REFUTED means the sources directly contradict the claim.
- UNCERTAIN means the sources are insufficient, ambiguous, inaccessible,
  or conflicting.
- confidence must be an integer from 0 to 100.
- Never invent facts, quotations, dates, or source content.
- Do not use knowledge outside the supplied source text.
- If a source is inaccessible or empty, prefer UNCERTAIN.
"""
            raw = gl.nondet.exec_prompt(prompt).strip()

            data = json.loads(raw)

            verdict = data.get("verdict")
            confidence = data.get("confidence")
            rationale = data.get("rationale")

            if verdict not in ("SUPPORTED", "REFUTED", "UNCERTAIN"):
                raise gl.vm.UserError("Invalid verdict")

            if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
                raise gl.vm.UserError("Invalid confidence")

            if not isinstance(rationale, str) or not rationale.strip():
                raise gl.vm.UserError("Missing rationale")

            return {
                "verdict": verdict,
                "confidence": confidence,
                "rationale": rationale.strip(),
            }

        return fetch_and_judge()

    @gl.public.write
    def adjudicate(
        self,
        claim: str,
        source_a: str,
        source_b: str,
    ) -> typing.Any:
        if not claim.strip():
            raise gl.vm.UserError("Claim cannot be empty")
        if not source_a.startswith(("http://", "https://")):
            raise gl.vm.UserError("Source A must be an HTTP(S) URL")
        if not source_b.startswith(("http://", "https://")):
            raise gl.vm.UserError("Source B must be an HTTP(S) URL")

        def leader_fn():
            return self._analyze(claim, source_a, source_b)

        def validator_fn(leader_result):
            if not isinstance(leader_result, gl.vm.Return):
                return False

            try:
                independent = self._analyze(claim, source_a, source_b)
            except Exception:
                return False

            proposed = leader_result.calldata

            # The validator independently re-fetches both sources and
            # independently derives the verdict. The consensus-critical
            # decision field must agree. Explanations may differ naturally.
            if proposed.get("verdict") != independent.get("verdict"):
                return False

            # Keep confidence disagreement tolerant because LLM scoring
            # can vary even when the substantive decision agrees.
            proposed_conf = proposed.get("confidence")
            independent_conf = independent.get("confidence")
            if not isinstance(proposed_conf, int) or not isinstance(independent_conf, int):
                return False

            return abs(proposed_conf - independent_conf) <= 20

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        self.claim = claim
        self.verdict = result["verdict"]
        self.confidence = result["confidence"]
        self.rationale = result["rationale"]
        self.source_a = source_a
        self.source_b = source_b

        return result

    @gl.public.view
    def get_result(self) -> dict:
        return {
            "claim": self.claim,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "source_a": self.source_a,
            "source_b": self.source_b,
        }
