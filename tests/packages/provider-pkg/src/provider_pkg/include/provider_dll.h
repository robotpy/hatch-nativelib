#pragma once

#if defined(_WIN32) && defined(PROVIDER_DLL_EXPORTS)
    #define PROVIDER_DLL __declspec(dllexport)
#elif defined(_WIN32) && defined(PROVIDER_DLL_IMPORTS)
    #define PROVIDER_DLL __declspec(dllimport)
#else
    #define PROVIDER_DLL
#endif
