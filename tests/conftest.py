from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import textwrap
import zipfile
from dataclasses import dataclass

import pytest
from environment_helpers import Environment, VirtualEnvironment

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEST_PACKAGES_ROOT = REPO_ROOT / "tests" / "packages"


def shared_library_filename(name: str) -> str:
    if sys.platform == "win32":
        return f"{name}.dll"
    if sys.platform == "darwin":
        return f"lib{name}.dylib"
    return f"lib{name}.so"


def _write_text(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


@dataclass
class TempProject:
    root: pathlib.Path
    env: Environment

    def write(self, relative_path: str, content: str) -> pathlib.Path:
        path = self.root / relative_path
        _write_text(path, content)
        return path

    def read(self, relative_path: str) -> str:
        return (self.root / relative_path).read_text(encoding="utf-8")

    def copy_package_fixture(
        self, fixture_name: str, destination: str | pathlib.Path = "."
    ) -> pathlib.Path:
        src = TEST_PACKAGES_ROOT / fixture_name
        if not src.is_dir():
            raise FileNotFoundError(f"package fixture not found: {fixture_name}")

        dst = self.root / destination
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return dst

    def run(
        self, *args: str, cwd: pathlib.Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.env.interpreter), *args],
            cwd=cwd or self.root,
            env=dict(self.env.env),
            text=True,
            capture_output=True,
        )

    def install_current_project(self) -> None:
        self.env.install([str(REPO_ROOT), "build", "hatch-meson", "ninja"])

    def build_wheel(self) -> subprocess.CompletedProcess[str]:
        return self.run("-m", "build", "--wheel", "--no-isolation")

    def dist_wheels(self) -> list[pathlib.Path]:
        return sorted((self.root / "dist").glob("*.whl"))

    def wheel_contents(self, wheel: pathlib.Path) -> list[str]:
        with zipfile.ZipFile(wheel) as zf:
            return sorted(zf.namelist())

    def installed_package_root(self, package: str) -> pathlib.Path:
        code = (
            "import importlib, pathlib; "
            f"mod = importlib.import_module({package!r}); "
            "print(pathlib.Path(mod.__file__).parent)"
        )
        result = self.run("-c", code)
        result.check_returncode()
        return pathlib.Path(result.stdout.strip())


@pytest.fixture
def project_factory(tmp_path: pathlib.Path) -> TempProject:
    venv_path = tmp_path / ".venv"
    env = VirtualEnvironment.create_venv(venv_path, with_pip=True)
    project = TempProject(tmp_path, env)
    project.install_current_project()
    return project
