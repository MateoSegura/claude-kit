"""LLM-as-Judge — uses Claude to evaluate output quality."""

from __future__ import annotations

import json
import random
import re
from typing import Any

try:
    import anthropic
except ModuleNotFoundError:  # CI: anthropic not installed
    anthropic = None  # type: ignore[assignment]

from test.engine.config import RunResult
from test.scoring.base import ScoringResult
from test.scoring.rubric import DEFAULT_RUBRIC, Rubric

_DEFAULT_JUDGE_MODEL = "claude-sonnet-4-20250514"

_INDIVIDUAL_PROMPT = """\
You are an expert code reviewer evaluating AI-generated output quality.

## Task
The AI was asked: {prompt}

## AI Response
{response}

## Scoring Rubric
Score each dimension from 0 to 10:

{rubric_text}

## Output Format
Return ONLY a JSON object with dimension scores and a brief justification for each:
{{
{score_fields}
}}

Be precise. Use the full 0-10 scale. Do not default to middle scores."""

_PAIRWISE_PROMPT = """\
You are an expert code reviewer comparing two AI responses to the same task.

## Task
The AI was asked: {prompt}

## Response A
{response_a}

## Response B
{response_b}

## Scoring Rubric
For each dimension, score BOTH responses from 0 to 10:

{rubric_text}

## Output Format
Return ONLY a JSON object:
{{
  "winner": "A" or "B" or "tie",
  "scores_a": {{{score_fields_template}}},
  "scores_b": {{{score_fields_template}}},
  "reasoning": "Brief explanation of why the winner is better"
}}

Be precise and objective. The order of A and B is randomized to prevent bias."""


class LLMJudge:
    """Uses Claude as a judge to evaluate output quality.

    Supports two modes:
    - Individual scoring: evaluate one response on rubric dimensions
    - Pairwise comparison: compare two responses, pick a winner
    """

    def __init__(
        self,
        model: str = _DEFAULT_JUDGE_MODEL,
        rubric: Rubric | None = None,
        seed: int | None = None,
    ) -> None:
        self.model = model
        self.rubric = rubric or DEFAULT_RUBRIC
        self._rng = random.Random(seed)

    def score_individual(
        self,
        result: RunResult,
        prompt: str,
        client: anthropic.Anthropic | None = None,
    ) -> list[ScoringResult]:
        """Score a single response on all rubric dimensions.

        Args:
            result: The RunResult to evaluate.
            prompt: The original task prompt.
            client: Anthropic client (created if not provided).

        Returns:
            List of ScoringResult, one per rubric dimension.
        """
        if client is None:
            client = anthropic.Anthropic()

        response_text = "\n\n---\n\n".join(result.responses)
        rubric_text = self._format_rubric()
        score_fields = self._format_score_fields()

        judge_prompt = _INDIVIDUAL_PROMPT.format(
            prompt=prompt,
            response=response_text,
            rubric_text=rubric_text,
            score_fields=score_fields,
        )

        msg = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": judge_prompt}],
        )

        raw_output = msg.content[0].text
        scores = self._parse_individual_scores(raw_output)

        results: list[ScoringResult] = []
        for dim in self.rubric.dimensions:
            score = scores.get(dim.name, 5.0)
            justification = scores.get(f"{dim.name}_justification", "")
            results.append(
                ScoringResult(
                    scorer_name="llm_judge",
                    dimension=dim.name,
                    score=float(score),
                    confidence=0.8,
                    details={"justification": justification},
                    raw_output=raw_output,
                ),
            )

        return results

    def score_pairwise(
        self,
        result_a: RunResult,
        result_b: RunResult,
        prompt: str,
        client: anthropic.Anthropic | None = None,
    ) -> dict[str, Any]:
        """Compare two responses side-by-side.

        Randomizes A/B order to mitigate position bias.

        Args:
            result_a: First RunResult (typically "raw").
            result_b: Second RunResult (typically "kit").
            prompt: The original task prompt.
            client: Anthropic client.

        Returns:
            Dict with winner ("a", "b", or "tie"), scores, and reasoning.
            Winner labels are mapped back to original order.
        """
        if client is None:
            client = anthropic.Anthropic()

        # Randomize order to prevent position bias
        swap = self._rng.random() < 0.5
        if swap:
            first, second = result_b, result_a
        else:
            first, second = result_a, result_b

        response_a_text = "\n\n---\n\n".join(first.responses)
        response_b_text = "\n\n---\n\n".join(second.responses)
        rubric_text = self._format_rubric()
        score_fields_template = ", ".join(
            f'"{d.name}": <0-10>' for d in self.rubric.dimensions
        )

        judge_prompt = _PAIRWISE_PROMPT.format(
            prompt=prompt,
            response_a=response_a_text,
            response_b=response_b_text,
            rubric_text=rubric_text,
            score_fields_template=score_fields_template,
        )

        msg = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": judge_prompt}],
        )

        raw_output = msg.content[0].text
        parsed = self._parse_pairwise(raw_output)

        # Map winner back to original order
        winner = parsed.get("winner", "tie").upper()
        if swap:
            if winner == "A":
                winner = "B"
            elif winner == "B":
                winner = "A"
            # Also swap scores back
            parsed["scores_a"], parsed["scores_b"] = (
                parsed.get("scores_b", {}),
                parsed.get("scores_a", {}),
            )

        return {
            "winner": winner.lower(),
            "scores_a": parsed.get("scores_a", {}),
            "scores_b": parsed.get("scores_b", {}),
            "reasoning": parsed.get("reasoning", ""),
            "swapped": swap,
            "raw_output": raw_output,
        }

    def _format_rubric(self) -> str:
        lines: list[str] = []
        for dim in self.rubric.dimensions:
            lines.append(f"- **{dim.name}** (weight {dim.weight}): {dim.description}")
            if dim.scoring_guide:
                lines.append(f"  {dim.scoring_guide}")
        return "\n".join(lines)

    def _format_score_fields(self) -> str:
        lines: list[str] = []
        for dim in self.rubric.dimensions:
            lines.append(f'  "{dim.name}": <0-10>,')
            lines.append(f'  "{dim.name}_justification": "<brief reason>",')
        return "\n".join(lines)

    def _parse_individual_scores(self, raw: str) -> dict[str, Any]:
        """Parse JSON scores from judge output."""
        # Try direct parse first
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Fallback: return empty dict (all dimensions get default 5.0)
        return {}

    def _parse_pairwise(self, raw: str) -> dict[str, Any]:
        """Parse pairwise comparison JSON from judge output."""
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        return {"winner": "tie", "reasoning": "Failed to parse judge output"}
