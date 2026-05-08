from __future__ import annotations

import sys


def shared_library_filename(name: str) -> str:
    if sys.platform == "win32":
        return f"{name}.dll"
    if sys.platform == "darwin":
        return f"lib{name}.dylib"
    return f"lib{name}.so"


def test_built_wheel_contains_generated_artifacts(project_factory) -> None:
    project_factory.copy_package_fixture("demo-shared")
    project_factory.write(
        f"src/demo_pkg/lib/{shared_library_filename('demo')}",
        "not-a-real-library",
    )

    result = project_factory.build_wheel()

    assert result.returncode == 0, result.stdout + result.stderr
    wheel = project_factory.dist_wheels()[0]
    contents = project_factory.wheel_contents(wheel)
    assert "demo_pkg/demo.pc" in contents
    assert "demo_pkg/_init_demo.py" in contents


def test_installed_wheel_contains_generated_package_files(project_factory) -> None:
    project_factory.copy_package_fixture("demo-shared")
    project_factory.write(
        f"src/demo_pkg/lib/{shared_library_filename('demo')}",
        "not-a-real-library",
    )

    result = project_factory.build_wheel()

    assert result.returncode == 0, result.stdout + result.stderr
    wheel = project_factory.dist_wheels()[0]
    project_factory.env.install_wheel(wheel)

    package_root = project_factory.installed_package_root("demo_pkg")
    assert (package_root / "demo.pc").is_file()
    assert (package_root / "_init_demo.py").is_file()
