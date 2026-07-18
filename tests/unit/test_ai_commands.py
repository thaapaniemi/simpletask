"""Unit tests for AI template compatibility helpers."""

from pathlib import Path

import pytest
from simpletask.core.ai_templates import (
    get_bundled_copilot_templates,
    get_bundled_pi_templates,
    get_bundled_templates,
    get_editor_api,
    install_copilot_templates,
    install_pi_templates,
    install_templates,
)

EXPECTED_OPENCODE = {
    "simpletask.plan.md",
    "simpletask.split.md",
    "simpletask.implement.md",
    "simpletask.audit.md",
    "simpletask.review.md",
}
EXPECTED_COPILOT = {
    "simpletask.plan.prompt.md",
    "simpletask.split.prompt.md",
    "simpletask.implement.prompt.md",
    "simpletask.audit.prompt.md",
    "simpletask.review.prompt.md",
}
EXPECTED_PI = {
    "simpletask-plan.md",
    "simpletask-split.md",
    "simpletask-implement.md",
    "simpletask-audit.md",
    "simpletask-review.md",
}


@pytest.mark.parametrize(
    ("getter", "expected"),
    [
        (get_bundled_templates, EXPECTED_OPENCODE),
        (get_bundled_copilot_templates, EXPECTED_COPILOT),
        (get_bundled_pi_templates, EXPECTED_PI),
    ],
)
def test_supported_bundled_templates(getter, expected: set[str]):
    templates = getter()
    assert {template.name for template in templates} == expected
    assert all(isinstance(template, Path) for template in templates)


@pytest.mark.parametrize(
    ("installer", "expected"),
    [
        (install_templates, EXPECTED_OPENCODE),
        (install_copilot_templates, EXPECTED_COPILOT),
        (install_pi_templates, EXPECTED_PI),
    ],
)
def test_supported_installers(installer, expected: set[str], tmp_path: Path):
    installed, skipped, overwritten = installer(tmp_path / "prompts")
    assert set(installed) == expected
    assert skipped == []
    assert overwritten == []


def test_editor_api_supports_copilot(tmp_path: Path):
    api = get_editor_api("copilot")
    installed, skipped, overwritten = api.install(tmp_path / "copilot")
    assert len(installed) == 5
    assert skipped == []
    assert overwritten == []


def test_copilot_templates_are_markdown_prompts():
    assert all(template.suffix == ".md" for template in get_bundled_copilot_templates())


def test_copilot_prompts_use_supported_inputs_and_no_delegation():
    for template in get_bundled_copilot_templates():
        content = template.read_text()
        assert "${input:userInput}" in content
        assert "$ARGUMENTS" not in content
        assert "Task(" not in content
        assert "gilfoyle" not in content
