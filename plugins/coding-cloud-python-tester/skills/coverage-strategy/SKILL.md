---
name: coding-cloud-python-tester:coverage-strategy
description: "Coverage measurement strategy for Python cloud services: 80% threshold enforcement with pytest-cov, branch coverage, exclusion pragmas, JSON report parsing for gap analysis, and prioritization of high-value coverage gaps."
---

# Coverage Strategy — Quick Reference

80% total coverage is the enforced floor. Branch coverage is always enabled. Coverage is measured in CI and fails the build if the threshold is not met.

## Enforcement Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = [
    "--cov=src",
    "--cov-branch",
    "--cov-report=term-missing",
    "--cov-report=json:coverage.json",
    "--cov-fail-under=80",
    "--cov-config=pyproject.toml",
]

[tool.coverage.run]
branch = true
source = ["src"]
omit = [
    "*/migrations/*",
    "*/conftest.py",
    "*/__init__.py",
    "src/main.py",
    "*/settings*.py",
]

[tool.coverage.report]
fail_under = 80
precision = 1
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
    "@(abc\\.)?abstractmethod",
    "\\.\\.\\.",
]

[tool.coverage.json]
output = "coverage.json"
pretty_print = true
```

## Inline Exclusions

Use `# pragma: no cover` for code that is genuinely untestable or not worth testing:

```python
# Acceptable exclusions
class AbstractBase(ABC):
    @abstractmethod
    def process(self) -> None:  # pragma: no cover
        ...

def create_app() -> FastAPI:  # pragma: no cover
    """Entry point — tested via integration, not unit coverage."""
    app = FastAPI()
    app.include_router(router)
    return app

if TYPE_CHECKING:  # pragma: no cover
    from app.types import SomeType
```

Never use `pragma: no cover` to hide real business logic gaps.

## Gap Prioritization

When coverage is below 80%, focus on gaps in this order:

| Priority | Target | Rationale |
|----------|--------|-----------|
| 1 | Service layer (`services/`) | Business rules — highest defect risk |
| 2 | Repository layer (`repositories/`) | Data access — critical for correctness |
| 3 | API handlers (`routers/`) | Contract surface — user-visible behavior |
| 4 | Utilities (`utils/`) | Shared helpers — high reuse, high blast radius |
| 5 | Schema validation | Pydantic validators often have edge cases |
| 6 | Configuration + startup | Low risk, hard to test — exclude via pragma |

## Useful Coverage Commands

```bash
# Run full suite with coverage
pytest --cov=src --cov-branch --cov-fail-under=80

# HTML report for browsing
pytest --cov=src --cov-report=html:htmlcov && open htmlcov/index.html

# View per-file summary in terminal
pytest --cov=src --cov-report=term-missing

# Check coverage without running tests (on existing .coverage data)
coverage report --fail-under=80

# Parse JSON report to find lowest-coverage files
python -c "
import json, sys
data = json.load(open('coverage.json'))
files = [(f, d['summary']['percent_covered']) for f, d in data['files'].items()]
for f, pct in sorted(files, key=lambda x: x[1])[:10]:
    print(f'{pct:5.1f}%  {f}')
"
```

## Additional Resources

- [reference.md](reference.md) — Full JSON report schema, coverage.py config options, exclusion patterns, per-module threshold strategies, CI integration
