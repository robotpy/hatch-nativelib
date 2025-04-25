from hatchling.plugin import hookimpl

from .plugin import NativelibHook


@hookimpl
def hatch_register_build_hook():
    return NativelibHook
