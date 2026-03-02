"""Tests for LLM-as-Judge — all with mocked Anthropic client."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from test.engine.config import RunResult
from test.scoring.llm_judge import LLMJudge
from test.scoring.rubric import (
    DEFAULT_RUBRIC,
    Dimension,
    Rubric,
    load_rubric,
)


def _pyyaml_available() -> bool:
    """Return True only if PyYAML is installed and functional."""
    try:
        import yaml

        yaml.safe_load("")
        return True
    except Exception:
        return False


def _result(**kwargs) -> RunResult:
    defaults = {
        "config_name": "test",
        "responses": ["Hello world"],
        "turns": 1,
        "total_tokens_in": 100,
        "total_tokens_out": 50,
        "wall_clock_s": 1.0,
        "model": "claude-sonnet-4-20250514",
    }
    defaults.update(kwargs)
    return RunResult(**defaults)


def _mock_judge_response(scores: dict) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(scores))]
    return msg


# -- Rubric ---------------------------------------------------------------


def test_default_rubric_has_dimensions():
    assert len(DEFAULT_RUBRIC.dimensions) == 6
    names = [d.name for d in DEFAULT_RUBRIC.dimensions]
    assert "task_completion" in names
    assert "correctness" in names


def test_rubric_weighted_score():
    rubric = Rubric(
        name="test",
        description="test",
        dimensions=[
            Dimension(name="a", weight=2.0, description="test"),
            Dimension(name="b", weight=1.0, description="test"),
        ],
    )
    score = rubric.weighted_score({"a": 10.0, "b": 4.0})
    expected = (10.0 * 2.0 + 4.0 * 1.0) / 3.0
    assert abs(score - expected) < 0.01


def test_rubric_weighted_score_partial():
    rubric = DEFAULT_RUBRIC
    score = rubric.weighted_score({"task_completion": 8.0})
    assert score == 8.0


def test_rubric_total_weight():
    assert DEFAULT_RUBRIC.total_weight == 7.5


@pytest.mark.skipif(
    not _pyyaml_available(),
    reason="PyYAML not installed",
)
def test_load_rubric_from_yaml(tmp_path):
    yaml_content = """
name: test-rubric
description: A test rubric
dimensions:
  - name: quality
    weight: 1.0
    description: Overall quality
    scoring_guide: "10: Perfect"
"""
    rubric_file = tmp_path / "rubric.yml"
    rubric_file.write_text(yaml_content)
    rubric = load_rubric(rubric_file)
    assert rubric.name == "test-rubric"
    assert len(rubric.dimensions) == 1
    assert rubric.dimensions[0].name == "quality"


# -- LLMJudge Construction ------------------------------------------------


def test_judge_importable():
    assert callable(LLMJudge)


def test_judge_default_model():
    judge = LLMJudge()
    assert "sonnet" in judge.model


def test_judge_custom_model():
    judge = LLMJudge(model="claude-opus-4-20250514")
    assert judge.model == "claude-opus-4-20250514"


def test_judge_default_rubric():
    judge = LLMJudge()
    assert judge.rubric is DEFAULT_RUBRIC


# -- Individual Scoring ----------------------------------------------------


def test_score_individual_returns_results():
    judge = LLMJudge()
    result = _result(responses=["Created the /health endpoint"])

    scores = {
        "task_completion": 9,
        "task_completion_justification": "Completed the task",
        "correctness": 8,
        "correctness_justification": "Correct implementation",
        "instruction_adherence": 9,
        "instruction_adherence_justification": "Followed all instructions",
        "code_quality": 7,
        "code_quality_justification": "Clean code",
        "domain_awareness": 8,
        "domain_awareness_justification": "Good domain knowledge",
        "efficiency": 9,
        "efficiency_justification": "Efficient approach",
    }

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_judge_response(scores)

    results = judge.score_individual(
        result, "Add a health endpoint", client=mock_client
    )
    assert len(results) == 6
    assert all(r.scorer_name == "llm_judge" for r in results)

    # Check specific scores
    task_result = [r for r in results if r.dimension == "task_completion"][0]
    assert task_result.score == 9.0


def test_score_individual_handles_json_in_code_block():
    judge = LLMJudge()
    result = _result()

    msg = MagicMock()
    msg.content = [MagicMock(text='```json\n{"task_completion": 8}\n```')]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = msg

    results = judge.score_individual(result, "test", client=mock_client)
    task_result = [r for r in results if r.dimension == "task_completion"][0]
    assert task_result.score == 8.0


def test_score_individual_handles_parse_failure():
    judge = LLMJudge()
    result = _result()

    msg = MagicMock()
    msg.content = [MagicMock(text="This is not JSON at all")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = msg

    results = judge.score_individual(result, "test", client=mock_client)
    # All dimensions should get default 5.0
    assert all(r.score == 5.0 for r in results)


def test_score_individual_uses_configured_model():
    judge = LLMJudge(model="claude-opus-4-20250514")
    result = _result()

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_judge_response(
        {"task_completion": 8}
    )

    judge.score_individual(result, "test", client=mock_client)
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-opus-4-20250514"


# -- Pairwise Comparison --------------------------------------------------


def test_pairwise_returns_winner():
    judge = LLMJudge(seed=42)
    result_a = _result(config_name="raw", responses=["Basic response"])
    result_b = _result(config_name="kit", responses=["Better response"])

    pairwise_response = {
        "winner": "B",
        "scores_a": {"task_completion": 6},
        "scores_b": {"task_completion": 9},
        "reasoning": "Response B is more complete",
    }

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_judge_response(pairwise_response)

    output = judge.score_pairwise(result_a, result_b, "test", client=mock_client)
    assert output["winner"] in ("a", "b", "tie")
    assert "reasoning" in output


def test_pairwise_handles_tie():
    judge = LLMJudge(seed=42)
    result_a = _result(responses=["Same quality"])
    result_b = _result(responses=["Same quality"])

    pairwise_response = {
        "winner": "tie",
        "scores_a": {"task_completion": 8},
        "scores_b": {"task_completion": 8},
        "reasoning": "Both responses are equivalent",
    }

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_judge_response(pairwise_response)

    output = judge.score_pairwise(result_a, result_b, "test", client=mock_client)
    assert output["winner"] == "tie"


def test_pairwise_tracks_swap():
    judge = LLMJudge(seed=42)
    result_a = _result(responses=["A"])
    result_b = _result(responses=["B"])

    pairwise_response = {
        "winner": "A",
        "scores_a": {"task_completion": 8},
        "scores_b": {"task_completion": 6},
        "reasoning": "A is better",
    }

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_judge_response(pairwise_response)

    output = judge.score_pairwise(result_a, result_b, "test", client=mock_client)
    assert "swapped" in output
    assert isinstance(output["swapped"], bool)


def test_pairwise_handles_parse_failure():
    judge = LLMJudge(seed=42)
    result_a = _result(responses=["A"])
    result_b = _result(responses=["B"])

    msg = MagicMock()
    msg.content = [MagicMock(text="Not valid JSON")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = msg

    output = judge.score_pairwise(result_a, result_b, "test", client=mock_client)
    assert output["winner"] == "tie"
