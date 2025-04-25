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
* On macOS, will adjust any libraries mentioned in the .pc file to have a `@loader_path`
  pointing at their dependencies (as specified in the .pc file)

See [config](src/hatch_nativelib/config.py) for `pyproject.toml` configuration.