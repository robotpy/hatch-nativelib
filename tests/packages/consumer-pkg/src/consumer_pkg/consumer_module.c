#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "consumer.h"

static PyObject *wrap_consumer_twice_plus_one(PyObject *self, PyObject *args) {
    int value;
    if (!PyArg_ParseTuple(args, "i", &value)) {
        return NULL;
    }

    return PyLong_FromLong(consumer_twice_plus_one(value));
}

static PyMethodDef consumer_methods[] = {
    {"consumer_twice_plus_one", wrap_consumer_twice_plus_one, METH_VARARGS, "Compute a provider-backed value."},
    {NULL, NULL, 0, NULL},
};

static struct PyModuleDef consumer_module = {
    PyModuleDef_HEAD_INIT,
    "_consumer_ext",
    NULL,
    -1,
    consumer_methods,
};

PyMODINIT_FUNC PyInit__consumer_ext(void) {
    return PyModule_Create(&consumer_module);
}
