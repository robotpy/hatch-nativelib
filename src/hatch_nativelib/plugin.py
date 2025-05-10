import functools
import os
import pathlib
import platform
import typing as T

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

from packaging.markers import Marker
import pkgconf

from .config import PcFileConfig
from .util import maybe_write_file
from .validate import parse_input

INITPY_VARNAME = "pkgconf_pypi_initpy"

platform_sys = platform.system()
is_windows = platform_sys == "Windows"
is_macos = platform_sys == "Darwin"


class NativelibHook(BuildHookInterface):
    PLUGIN_NAME = "nativelib"

    def initialize(self, version: str, build_data: T.Dict[str, T.Any]) -> None:

        # Don't need to generate files when creating an sdist
        if self.target_name != "wheel":
            return

        self.root_pth = pathlib.Path(self.root)

        # hatchling only knows about packages in the wheel builder, so get
        # the list from it
        # self.wheel_packages = [
        #     pathlib.Path(pathlib.PurePosixPath(pkg)).resolve()
        #     for pkg in WheelBuilder(self.root).config.packages
        # ]

        pcpaths: T.Set[str] = set()
        for pcfg in self._pcfiles:
            pcfile = self._generate_pcfile(pcfg, build_data)
            pcpaths.add(str(pcfile.parent))

        if pcpaths:
            # Add to PKG_CONFIG_PATH so that it can be resolved by other hatchling
            # plugins if desired
            pkg_config_path = os.environ.get("PKG_CONFIG_PATH")
            if pkg_config_path is not None:
                os.environ["PKG_CONFIG_PATH"] = os.pathsep.join(
                    (pkg_config_path, *pcpaths)
                )
            else:
                os.environ["PKG_CONFIG_PATH"] = os.pathsep.join(pcpaths)

    def clean(self, versions: T.List[str]) -> None:
        root = pathlib.Path(self.root)
        for pcfg in self._pcfiles:
            for relname in (pcfg.get_pc_path(), pcfg.get_init_module_path()):
                fname = root / relname
                self.app.display_debug(f"Deleting {fname}")
                fname.unlink(missing_ok=True)

    def _get_pkg_from_path(self, path: pathlib.Path) -> str:
        rel = path.relative_to(self.root_pth)
        # TODO: this seems right? is it?
        dist_pth = self.build_config.get_distribution_path(str(rel))
        return ".".join(dist_pth.split(os.sep))

    def _generate_pcfile(
        self, pcfg: PcFileConfig, build_data: T.Dict[str, T.Any]
    ) -> pathlib.Path:

        pcfile_rel = pcfg.get_pc_path()
        pcfile = self.root_pth / pcfile_rel
        prefix_rel = pcfile_rel.parent
        prefix_path = pcfile.parent

        prefix = "${pcfiledir}"

        # variables first
        variables = {}
        variables["prefix"] = prefix

        if pcfg.includedir:
            increl = pathlib.PurePosixPath(pcfg.includedir).relative_to(
                prefix_rel.as_posix()
            )
            variables["includedir"] = f"${{prefix}}/{increl}"

        if pcfg.shared_libraries:
            if pcfg.libdir:
                librel = pathlib.PurePosixPath(pcfg.libdir).relative_to(
                    prefix_rel.as_posix()
                )
                variables["libdir"] = f"${{prefix}}/{librel}"
            else:
                variables["libdir"] = "${prefix}"

        if pcfg.variables:
            for n in ("prefix", "includedir", "libdir", INITPY_VARNAME):
                if n in pcfg.variables:
                    raise ValueError(f"variables may not contain {n}")

            variables.update(variables)

        # If there are libraries, generate _init_NAME.py for each
        if pcfg.shared_libraries:
            package = self._get_pkg_from_path(prefix_path)
            variables[INITPY_VARNAME] = f"{package}.{pcfg.get_init_module()}"
            self._generate_init_py(pcfg, prefix_path, build_data)

            # .. not documented but it works?
            eps = self.metadata.core.entry_points.setdefault("pkg_config", {})
            eps[pcfg.get_name()] = package

        contents = [f"{k}={v}" for k, v in variables.items()]
        contents.append("")

        description = pcfg.description
        if description is None:
            description = self.metadata.core.description

        if not description:
            raise ValueError(
                f"tool.hatch.build.hooks.nativelib.pcfile: description not provided for {pcfg.get_name()}"
            )

        contents += [
            f"Name: {pcfg.get_name()}",
            f"Description: {description}",
        ]

        version = pcfg.version or self.metadata.version
        if version:
            contents.append(f"Version: {version}")

        libs = []
        if pcfg.shared_libraries:
            libs.append("-L${libdir}")
            libs.extend(f"-l{lib}" for lib in pcfg.shared_libraries)

        cflags = []
        if pcfg.includedir:
            cflags.append("-I${includedir}")

        if pcfg.extra_cflags:
            cflags.append(pcfg.extra_cflags)

        if pcfg.requires:
            contents.append(f"Requires: {' '.join(pcfg.requires)}")

        if pcfg.requires_private:
            contents.append(f"Requires.private: {' '.join(pcfg.requires_private)}")

        if libs:
            contents.append(f"Libs: {' '.join(libs)}")

        if pcfg.libs_private:
            contents.append(f"Libs.private: {pcfg.libs_private}")

        if cflags:
            contents.append(f"Cflags: {' '.join(cflags)}")

        self.app.display_info(f"Generating {pcfile}")

        content = ("\n".join(contents)) + "\n"
        maybe_write_file(pcfile, content)

        build_data["artifacts"].append(pcfile_rel.as_posix())
        return pcfile

    def _generate_init_py(
        self,
        pcfg: PcFileConfig,
        prefix_path: pathlib.Path,
        build_data: T.Dict[str, T.Any],
    ):
        libinit_py_rel = pcfg.get_init_module_path()
        libinit_py = self.root_pth / libinit_py_rel

        libdir = prefix_path
        if pcfg.libdir:
            libdir = self.root_pth / pathlib.PurePosixPath(pcfg.libdir)

        lib_paths = []
        assert pcfg.shared_libraries is not None
        for lib in pcfg.shared_libraries:
            lib_path = libdir / self._make_shared_lib_fname(lib)
            if not lib_path.exists():
                raise FileNotFoundError(f"shared library not found: {lib_path}")
            lib_paths.append(lib_path)

        self.app.display_info(f"Generating {libinit_py}")
        if pcfg.requires:
            requires = pcfg.requires
        else:
            requires = []

        _write_libinit_py(libinit_py, lib_paths, requires)
        build_data["artifacts"].append(libinit_py_rel.as_posix())

    def _make_shared_lib_fname(self, lib: str):
        if is_windows:
            return f"{lib}.dll"
        elif is_macos:
            return f"lib{lib}.dylib"
        else:
            return f"lib{lib}.so"

    @functools.cached_property
    def _pcfiles(self) -> T.List[PcFileConfig]:
        pcfiles = []
        for i, raw_pc in enumerate(self.config.get("pcfile", [])):
            pcfile = parse_input(
                raw_pc,
                PcFileConfig,
                "pyproject.toml",
                f"tool.hatch.build.hooks.nativelib.pcfile[{i}]",
            )

            if pcfile.enable_if and not Marker(pcfile.enable_if).evaluate():
                self.app.display_info(
                    f"{pcfile.pcfile} skipped because enable_if did not match current environment"
                )
                continue

            pcfiles.append(pcfile)

        return pcfiles


# TODO: this belongs in a separate script/api that can be used from multiple tools
def _write_libinit_py(
    init_py: pathlib.Path,
    libs: T.List[pathlib.Path],
    requires: T.List[str],
):
    """
    :param init_py: the _init module for the library(ies) that is written out
    :param libs: for each library that is being initialized, this is the
                 path to that library

    :param requires: other pkgconf packages that these libraries depend on.
                     Their init_py will be looked up and imported first.
    """

    contents = [
        "# This file is automatically generated, DO NOT EDIT",
        "# fmt: off",
        "",
    ]

    for req in requires:
        r = pkgconf.run_pkgconf(
            req, f"--variable={INITPY_VARNAME}", capture_output=True
        )
        # TODO: should this be a fatal error
        if r.returncode == 0:
            module = r.stdout.decode("utf-8").strip()  # type: ignore[arg-type, union-attr]
            contents.append(f"import {module}")

    if contents[-1] != "":
        contents.append("")

    if libs:
        contents += [
            "def __load_library():",
            "    from os.path import abspath, join, dirname, exists",
        ]

        if is_macos:
            contents += ["    from ctypes import CDLL, RTLD_GLOBAL"]
        else:
            contents += ["    from ctypes import cdll", ""]

        if len(libs) > 1:
            contents.append("    libs = []")

        contents.append("    root = abspath(dirname(__file__))")

        for lib in libs:
            rel = lib.relative_to(init_py.parent)
            components = ", ".join(map(repr, rel.parts))

            contents += [
                "",
                f"    lib_path = join(root, {components})",
                "",
                "    try:",
            ]

            if is_macos:
                load = "CDLL(lib_path, mode=RTLD_GLOBAL)"
            else:
                load = "cdll.LoadLibrary(lib_path)"

            if len(libs) > 1:
                contents.append(f"        libs.append({load})")
            else:
                contents.append(f"        return {load}")

            contents += [
                "    except FileNotFoundError:",
                f"        if not exists(lib_path):",
                f'            raise FileNotFoundError("{lib.name} was not found on your system. Is this package correctly installed?")',
            ]

            if is_windows:
                contents.append(
                    f'        raise Exception("{lib.name} could not be loaded. Do you have Visual Studio C++ Redistributible installed?")'
                )
            else:
                contents.append(
                    f'        raise FileNotFoundError("{lib.name} could not be loaded. There is a missing dependency.")'
                )

        if len(libs) > 1:
            contents += ["    return libs"]

        contents += ["", "__lib = __load_library()", ""]

    content = ("\n".join(contents)) + "\n"
    maybe_write_file(init_py, content)
