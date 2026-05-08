from __future__ import annotations

import pathlib

import pytest

from hatch_nativelib.config import PcFileConfig


def test_get_pc_path_accepts_relative_pcfile() -> None:
    cfg = PcFileConfig(pcfile="src/demo_pkg/demo.pc")

    assert cfg.get_pc_path() == pathlib.Path("src/demo_pkg/demo.pc")


def test_get_pc_path_rejects_absolute_path() -> None:
    cfg = PcFileConfig(pcfile="/tmp/demo.pc")

    with pytest.raises(ValueError, match="must not be absolute"):
        cfg.get_pc_path()


def test_get_pc_path_requires_pc_extension() -> None:
    cfg = PcFileConfig(pcfile="src/demo_pkg/demo.txt")

    with pytest.raises(ValueError, match="must end with .pc"):
        cfg.get_pc_path()


def test_get_name_prefers_explicit_name() -> None:
    cfg = PcFileConfig(pcfile="src/demo_pkg/demo.pc", name="custom-name")

    assert cfg.get_name() == "custom-name"


def test_get_name_defaults_to_pc_filename() -> None:
    cfg = PcFileConfig(pcfile="src/demo_pkg/demo.pc")

    assert cfg.get_name() == "demo"


def test_get_init_module_auto_normalizes_filename() -> None:
    cfg = PcFileConfig(pcfile="src/demo_pkg/demo-name.v1.pc")

    assert cfg.get_init_module() == "_init_demo_name_v1"


def test_get_init_module_rejects_invalid_identifier() -> None:
    cfg = PcFileConfig(pcfile="src/demo_pkg/demo.pc", init_module="not-valid-module")

    with pytest.raises(ValueError, match="valid python identifier"):
        cfg.get_init_module()


def test_get_init_module_path_places_module_next_to_pcfile() -> None:
    cfg = PcFileConfig(pcfile="src/demo_pkg/demo.pc")

    assert cfg.get_init_module_path() == pathlib.Path("src/demo_pkg/_init_demo.py")
