#pragma once

#if defined(_WIN32) && defined(CONSUMER_DLL_EXPORTS)
    #define CONSUMER_DLL __declspec(dllexport)
#elif defined(_WIN32) && defined(CONSUMER_DLL_IMPORTS)
    #define CONSUMER_DLL __declspec(dllimport)
#else
    #define CONSUMER_DLL
#endif
