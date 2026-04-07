# CI and Pipeline Guide

This file describes implemented quality gates for Laundry Monitor and maps them to SQR + Quality Plan requirements.

## Implemented files

- [.pre-commit-config.yaml](.pre-commit-config.yaml)
- [.flake8](.flake8)
- [.github/workflows/ci.yml](.github/workflows/ci.yml)
- [.github/workflows/release-gate.yml](.github/workflows/release-gate.yml)
- [scripts/check_complexity.py](scripts/check_complexity.py)

## 1) Pre-commit gate (local)

Scope: before each local commit.

Checks:
- `flake8` over backend + frontend code/tests
- `bandit -r backend/src -ll` (high severity gate)

Enable once locally:

```bash
pip install pre-commit
pre-commit install
```

Run manually:

```bash
pre-commit run --all-files
```

## 2) PR/Main CI gate (GitHub Actions)

Workflow: [ci.yml](.github/workflows/ci.yml)

Triggers:
- pull request to `main`
- push to `main`

### Backend quality gates (blocking)
- `flake8 src tests`
- `bandit -r src -ll`
- `python ../scripts/check_complexity.py --path src --max-complexity 8`
- `pytest --cov=src --cov-report=term-missing --cov-fail-under=70`

### Backend quality report (non-blocking)
- `radon mi src -s`

### Frontend gate
- `pytest tests`

## 3) Release gate (manual)

Workflow: [release-gate.yml](.github/workflows/release-gate.yml)

Trigger: `workflow_dispatch`

Purpose:
- Run all automated checks before demo/release
- Keep manual reminder for critical UX check:
  - reporting works
  - status view works

## Requirement coverage status

## Quality Plan (Laundry Monitor)

| Requirement | Target | Status | Evidence |
|---|---:|---|---|
| Pre-commit blockers | flake8 + high bandit | ✅ Done | [.pre-commit-config.yaml](.pre-commit-config.yaml) |
| PR blocker: tests | 100% pass | ✅ Done | [ci.yml](.github/workflows/ci.yml) |
| PR blocker: coverage | `>= 70%` | ✅ Done | [ci.yml](.github/workflows/ci.yml) |
| PR blocker: complexity | `< 8` per function | ✅ Done | [check_complexity.py](scripts/check_complexity.py), [ci.yml](.github/workflows/ci.yml) |
| PR blocker: security | high severity = 0 | ✅ Done | [ci.yml](.github/workflows/ci.yml) |
| PR blocker: approval | at least 1 reviewer | ⚠️ Needs GitHub setting | Branch protection rule (manual repo setting) |
| Release gate | all CI green + critical UX manual check | ✅ Done | [release-gate.yml](.github/workflows/release-gate.yml) |
| Maintainability Index | `> 65` (non-gate) | ✅ Reported | [ci.yml](.github/workflows/ci.yml) (`radon mi`) |

## SQR Assignment minimums (CI-related)

| Requirement | Status | Notes |
|---|---|---|
| GitHub Actions quality gates | ✅ Done | PR/main workflow configured |
| Linter warnings = 0 (flake8) | ✅ Enforced | blocking step |
| Coverage floor met | ✅ Enforced | set to 70% (above assignment floor 60%) |
| Cyclomatic complexity threshold | ✅ Enforced | strict `< 8` (above assignment floor `< 10`) |
| Security (high severity = 0) | ✅ Enforced | `bandit -ll` |
| Unit tests all green | ✅ Enforced | blocking pytest step |

## Known non-CI/manual items

- OpenAPI completeness check is manual at `/docs` (as defined by plan).
- Performance smoke (`locust`) is currently not in blocking CI (allowed by plan, non-gate).
- Dependency validation with `poetry check` is listed in plan but project currently uses `requirements.txt` and has no `pyproject.toml`.

## Branch protection settings to enable (required)

To fully enforce "No approval from another team member":

1. GitHub → Settings → Branches → Add rule for `main`
2. Enable:
   - Require a pull request before merging
   - Require approvals: at least 1
   - Require status checks to pass:
     - `Backend quality gates`
     - `Frontend unit tests`

Without this, CI runs, but reviewer approval is not technically enforced.
