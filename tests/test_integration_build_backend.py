from __future__ import annotations

import sys


def shared_library_filename(name: str) -> str:
    if sys.platform == "win32":
        return f"{name}.dll"
    if sys.platform == "darwin":
        return f"lib{name}.dylib"
    return f"lib{name}.so"


def test_build_generates_pcfile(project_factory) -> None:
    project_factory.copy_package_fixture("demo-basic")

    result = project_factory.build_wheel()

    assert result.returncode == 0, result.stdout + result.stderr
    assert project_factory.read("src/demo_pkg/demo.pc") == (
        "prefix=${pcfiledir}\n\n"
        "Name: demo\n"
        "Description: Demo package\n"
        "Version: 1.2.3\n"
    )


def test_build_generates_pcfile_and_init_module_for_shared_library(
    project_factory,
) -> None:
    project_factory.copy_package_fixture("demo-shared")
    project_factory.write(
        f"src/demo_pkg/lib/{shared_library_filename('demo')}",
        "not-a-real-library",
    )

    result = project_factory.build_wheel()

    assert result.returncode == 0, result.stdout + result.stderr
    assert project_factory.read("src/demo_pkg/demo.pc") == (
        "prefix=${pcfiledir}\n"
        "includedir=${prefix}/include\n"
        "libdir=${prefix}/lib\n"
        "pkgconf_pypi_initpy=demo_pkg._init_demo\n\n"
        "Name: demo\n"
        "Description: Demo package\n"
        "Version: 1.2.3\n"
        "Requires: dep1 dep2\n"
        "Requires.private: priv1 priv2\n"
        "Libs: -L${libdir} -ldemo\n"
        "Libs.private: -lm\n"
        "Cflags: -I${includedir} -DUSE_DEMO\n"
    )

    init_module = project_factory.read("src/demo_pkg/_init_demo.py")
    assert "def __load_library():" in init_module
    assert shared_library_filename("demo") in init_module
    assert (
        "cdll.LoadLibrary" in init_module
        or "CDLL(lib_path, mode=RTLD_GLOBAL)" in init_module
    )


def test_build_skips_pcfile_when_enable_if_does_not_match(project_factory) -> None:
    project_factory.copy_package_fixture("demo-enable-if")

    result = project_factory.build_wheel()

    assert result.returncode == 0, result.stdout + result.stderr
    assert (project_factory.root / "src/demo_pkg/enabled.pc").is_file()
    assert not (project_factory.root / "src/demo_pkg/skipped.pc").exists()


def test_build_fails_when_declared_shared_library_is_missing(project_factory) -> None:
    project_factory.copy_package_fixture("demo-missing-lib")

    result = project_factory.build_wheel()

    assert result.returncode != 0
    assert "shared library not found" in (result.stdout + result.stderr)


def test_build_generates_init_module_for_multiple_shared_libraries(
    project_factory,
) -> None:
    project_factory.copy_package_fixture("demo-multi-lib")
    project_factory.write(
        f"src/demo_pkg/lib/{shared_library_filename('demo')}",
        "not-a-real-library",
    )
    project_factory.write(
        f"src/demo_pkg/lib/{shared_library_filename('helper')}",
        "not-a-real-library",
    )

    result = project_factory.build_wheel()

    assert result.returncode == 0, result.stdout + result.stderr
    init_module = project_factory.read("src/demo_pkg/_init_demo.py")
    assert "libs = []" in init_module
    assert shared_library_filename("demo") in init_module
    assert shared_library_filename("helper") in init_module
    assert "return libs" in init_module


def test_build_resolves_intra_project_requires_on_first_run(project_factory) -> None:
    project_factory.copy_package_fixture("demo-editable-chain")
    project_factory.write(
        f"src/demo_pkg/lib/{shared_library_filename('provider')}",
        "not-a-real-library",
    )
    project_factory.write(
        f"src/demo_pkg/lib/{shared_library_filename('consumer')}",
        "not-a-real-library",
    )

    result = project_factory.build_wheel()

    assert result.returncode == 0, result.stdout + result.stderr
    init_module = project_factory.read("src/demo_pkg/_init_consumer.py")
    assert "import demo_pkg._init_provider" in init_module
