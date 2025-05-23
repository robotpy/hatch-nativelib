hatch-nativelib
===============

Hatchling plugin with utilities for native libraries.

pkgconf dependency generation
-----------------------------

By adding `[[tool.hatch.build.hooks.nativelib.pcfile]]` to your hatchling project's
`pyproject.toml`, this plugin will do a couple of things:

* Automatically generate the .pc file from the `pyproject.toml` config section
* Register the .pc file so that [pkgconf-pypi](https://github.com/pypackaging-native/pkgconf-pypi)
  will find it and things such as meson can use it for dependency resolution
  - Also sets `PKG_CONFIG_PATH` so that other hatchling plugins can resolve it
* Generates a python module that uses ctypes to load the library when imported. The
  library can be found via pkgconf, in the variable `pkgconf_pypi_initpy`

See [config](src/hatch_nativelib/config.py) for `pyproject.toml` configuration.