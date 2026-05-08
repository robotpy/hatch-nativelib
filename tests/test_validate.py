from __future__ import annotations

import pytest

from hatch_nativelib.config import PcFileConfig
from hatch_nativelib.validate import ValidationError, parse_input


def test_parse_input_builds_pcfile_config() -> None:
    cfg = parse_input(
        {"pcfile": "src/demo_pkg/demo.pc", "description": "Demo package"},
        PcFileConfig,
        "pyproject.toml",
        "tool.hatch.build.hooks.nativelib.pcfile[0]",
    )

    assert cfg == PcFileConfig(
        pcfile="src/demo_pkg/demo.pc",
        description="Demo package",
    )


def test_parse_input_wraps_validation_errors_with_context() -> None:
    with pytest.raises(ValidationError) as excinfo:
        parse_input(
            {"description": "missing pcfile"},
            PcFileConfig,
            "pyproject.toml",
            "tool.hatch.build.hooks.nativelib.pcfile[0]",
        )

    message = str(excinfo.value)
    assert "pyproject.toml: tool.hatch.build.hooks.nativelib.pcfile[0]" in message
    assert "pcfile" in message
