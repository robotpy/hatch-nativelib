project('consumer-pkg', 'c')

py = import('python').find_installation(pure: false)
consumer_inc = include_directories('src/consumer_pkg/include')
provider_dep = dependency('provider', method: 'pkg-config')

if meson.get_compiler('c').get_id() in ['msvc', 'clang-cl', 'intel-cl']
    export_dll_args = ['-DCONSUMER_DLL_EXPORTS']
    import_dll_args = ['-DCONSUMER_DLL_IMPORTS']
else
    export_dll_args = []
    import_dll_args = []
endif

consumer_lib = shared_library(
    'consumer',
    'src/consumer_pkg/consumer.c',
    c_args: export_dll_args,
    dependencies: [provider_dep],
    include_directories: consumer_inc,
    install: true,
    install_dir: py.get_install_dir() / 'consumer_pkg',
)

consumer_dep = declare_dependency(
    compile_args: import_dll_args,
    include_directories: consumer_inc,
    link_with: consumer_lib,
)

py.extension_module(
    '_consumer_ext',
    'src/consumer_pkg/consumer_module.c',
    dependencies: [consumer_dep],
    install: true,
    subdir: 'consumer_pkg',
)
