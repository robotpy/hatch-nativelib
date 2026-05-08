project('provider-pkg', 'c')

py = import('python').find_installation(pure: false)
provider_inc = include_directories('src/provider_pkg/include')

if meson.get_compiler('c').get_id() in ['msvc', 'clang-cl', 'intel-cl']
    export_dll_args = ['-DPROVIDER_DLL_EXPORTS']
else
    export_dll_args = []
endif

shared_library(
    'provider',
    'src/provider_pkg/provider.c',
    c_args: export_dll_args,
    include_directories: provider_inc,
    install: true,
    install_dir: py.get_install_dir() / 'provider_pkg',
)
