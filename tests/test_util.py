from __future__ import annotations

from hatch_nativelib.util import maybe_write_file


def test_maybe_write_file_writes_new_file(tmp_path) -> None:
    path = tmp_path / "demo.txt"

    assert maybe_write_file(path, "hello") is True
    assert path.read_text(encoding="utf-8") == "hello"


def test_maybe_write_file_creates_parent_directories(tmp_path) -> None:
    path = tmp_path / "nested" / "demo.txt"

    assert maybe_write_file(path, "hello") is True
    assert path.read_text(encoding="utf-8") == "hello"


def test_maybe_write_file_returns_false_when_content_is_unchanged(tmp_path) -> None:
    path = tmp_path / "demo.txt"
    path.write_text("hello", encoding="utf-8")

    assert maybe_write_file(path, "hello") is False


def test_maybe_write_file_returns_true_when_content_changes(tmp_path) -> None:
    path = tmp_path / "demo.txt"
    path.write_text("before", encoding="utf-8")

    assert maybe_write_file(path, "after") is True
    assert path.read_text(encoding="utf-8") == "after"
