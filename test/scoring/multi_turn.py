"""Multi-turn conversation scorers for session-driven benchmarks.

Three scorers that evaluate quality aspects unique to multi-turn
conversations driven by the SessionDriver:

- HumanSimulatorQualityScorer: Were auto-responses contextually appropriate?
- ConversationCoherenceScorer: Did the conversation flow logically?
- CompactionResilienceScorer: Did post-compaction responses maintain context?
"""

from __future__ import annotations

from typing import Any

try:
    import anthropic
except ModuleNotFoundError:
    anthropic = None  # type: ignore[assignment]

from test.engine.config import RunResult
from test.scoring.base import Scorer, ScoringResult

_JUDGE_MODEL = "claude-haiku-4-5-20251001"

_QUALITY_PROMPT = """\
You are evaluating the quality of simulated human responses in an
AI benchmark conversation.

## Conversation Transcript
{transcript}

## Simulated Human Responses
{human_responses}

## Task
Rate each simulated human response on a 0-10 scale for contextual
appropriateness. Consider:
- Does the response address what the AI asked?
- Is it realistic for a developer to respond this way?
- Is it concise and actionable?

Return a JSON object:
{{"average_score": <0-10>, "reasoning": "<brief explanation>"}}
"""

_COHERENCE_PROMPT = """\
You are evaluating the coherence of a multi-turn AI conversation.

## Conversation Transcript
{transcript}

## Task
Rate the overall conversation coherence on a 0-10 scale. Consider:
- Did the conversation flow logically toward task completion?
- Were there unnecessary detours or repeated questions?
- Did context carry forward between turns?

Return a JSON object:
{{"score": <0-10>, "reasoning": "<brief explanation>"}}
"""


class HumanSimulatorQualityScorer(Scorer):
    """LLM-judge: were human simulator responses contextually appropriate?"""

    @property
    def name(self) -> str:
        return "human_sim_quality"

    @property
    def dimension(self) -> str:
        return "interaction_quality"

    def score(self, result: RunResult, **kwargs: Any) -> ScoringResult:
        """Score human simulator response quality."""
        human_entries = [t for t in result.transcript if t.role == "human_sim"]
        if not human_entries:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=10.0,
                details={"reason": "no human interaction needed"},
            )

        if anthropic is None:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=5.0,
                confidence=0.0,
                details={"reason": "anthropic not available for judging"},
            )

        transcript_text = _format_transcript(result)
        human_text = "\n".join(
            f"- Turn {i + 1}: {e.content}" for i, e in enumerate(human_entries)
        )

        prompt = _QUALITY_PROMPT.format(
            transcript=transcript_text,
            human_responses=human_text,
        )

        try:
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model=_JUDGE_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            import json

            raw = msg.content[0].text
            parsed = json.loads(raw)
            score_val = float(parsed.get("average_score", 5.0))
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=min(10.0, max(0.0, score_val)),
                confidence=0.8,
                details={
                    "reasoning": parsed.get("reasoning", ""),
                    "human_response_count": len(human_entries),
                },
                raw_output=raw,
            )
        except Exception as exc:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=5.0,
                confidence=0.0,
                details={"error": str(exc)},
            )


class ConversationCoherenceScorer(Scorer):
    """LLM-judge: did the conversation flow logically toward completion?"""

    @property
    def name(self) -> str:
        return "conversation_coherence"

    @property
    def dimension(self) -> str:
        return "coherence"

    def score(self, result: RunResult, **kwargs: Any) -> ScoringResult:
        """Score conversation coherence."""
        if result.turns <= 1:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=10.0,
                details={"reason": "single-turn conversation"},
            )

        if anthropic is None:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=5.0,
                confidence=0.0,
                details={"reason": "anthropic not available for judging"},
            )

        transcript_text = _format_transcript(result)
        prompt = _COHERENCE_PROMPT.format(transcript=transcript_text)

        try:
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model=_JUDGE_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            import json

            raw = msg.content[0].text
            parsed = json.loads(raw)
            score_val = float(parsed.get("score", 5.0))
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=min(10.0, max(0.0, score_val)),
                confidence=0.8,
                details={"reasoning": parsed.get("reasoning", "")},
                raw_output=raw,
            )
        except Exception as exc:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=5.0,
                confidence=0.0,
                details={"error": str(exc)},
            )


class CompactionResilienceScorer(Scorer):
    """Check: did post-compaction responses maintain context?"""

    @property
    def name(self) -> str:
        return "compaction_resilience"

    @property
    def dimension(self) -> str:
        return "context_preservation"

    def score(self, result: RunResult, **kwargs: Any) -> ScoringResult:
        """Score context preservation after compaction events."""
        if result.compact_count == 0:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=10.0,
                details={"reason": "no compaction occurred"},
            )

        # Heuristic: check if post-compact assistant messages still
        # reference concepts from the original prompt
        prompt_words = set(result.transcript[0].content.lower().split())
        # Filter to meaningful words (>4 chars)
        prompt_keywords = {w for w in prompt_words if len(w) > 4}

        # Find compact events in transcript
        compact_indices = [
            i
            for i, t in enumerate(result.transcript)
            if t.role == "system" and t.subtype and "compact" in t.subtype.lower()
        ]

        if not compact_indices or not prompt_keywords:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=10.0,
                details={"reason": "no measurable compaction impact"},
            )

        # Check post-compact assistant messages for keyword retention
        last_compact = compact_indices[-1]
        post_compact_texts = [
            t.content.lower()
            for t in result.transcript[last_compact:]
            if t.role == "assistant"
        ]

        if not post_compact_texts:
            return ScoringResult(
                scorer_name=self.name,
                dimension=self.dimension,
                score=5.0,
                details={"reason": "no post-compact assistant messages"},
            )

        combined = " ".join(post_compact_texts)
        retained = sum(1 for kw in prompt_keywords if kw in combined)
        ratio = retained / len(prompt_keywords) if prompt_keywords else 1.0

        return ScoringResult(
            scorer_name=self.name,
            dimension=self.dimension,
            score=round(ratio * 10.0, 1),
            details={
                "prompt_keywords": len(prompt_keywords),
                "retained_after_compact": retained,
                "retention_ratio": round(ratio, 3),
                "compact_events": result.compact_count,
            },
        )


def _format_transcript(result: RunResult) -> str:
    """Format a RunResult transcript for LLM judge prompts."""
    lines: list[str] = []
    for entry in result.transcript[:50]:  # Cap for token limits
        role = entry.role
        content = entry.content[:300]
        if role == "tool_use":
            lines.append(f"[tool_use: {entry.tool_name}] {content}")
        elif role == "tool_result":
            status = "error" if entry.is_error else "ok"
            lines.append(f"[tool_result: {status}] {content}")
        else:
            lines.append(f"[{role}] {content}")
    return "\n".join(lines)
