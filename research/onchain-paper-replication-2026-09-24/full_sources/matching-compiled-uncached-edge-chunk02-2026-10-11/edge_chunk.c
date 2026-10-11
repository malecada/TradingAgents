#define PY_SSIZE_T_CLEAN
#include <Python.h>
/* No floating point kernel: preserve Python/NumPy indexing, callback and
   multiplication/assignment semantics. GIL retained; never release ownership. */
static PyObject *fill(PyObject *self, PyObject *args) {
    PyObject *w,*af,*bf,*left,*right,*agreement,*progress,*indices;
    Py_ssize_t count;
    if (!PyArg_ParseTuple(args,"OOOOOnOOO",&w,&af,&bf,&left,&right,&count,
                          &agreement,&progress,&indices)) return NULL;
    if (count<1 || count>1024 || !PyList_CheckExact(progress) ||
        PyList_GET_SIZE(progress)!=1 || !PyTuple_CheckExact(indices) ||
        PyTuple_GET_SIZE(indices)!=count || !PyCallable_Check(agreement)) {
        PyErr_SetString(PyExc_ValueError,"bounded adapter arguments required");return NULL;
    }
    for (Py_ssize_t i=0;i<count;i++) {
        PyObject *index=PyTuple_GET_ITEM(indices,i);
        if (!PyLong_CheckExact(index) || PyLong_AsSsize_t(index)!=i) {
            if (!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"ordered index required");
            return NULL;
        }
    }
    PyObject *half=PyFloat_FromDouble(0.5);
    if (!half) return NULL;
    for (Py_ssize_t i=0;i<count;i++) {
        PyObject *index=PyTuple_GET_ITEM(indices,i),*li=NULL,*ri=NULL;
        PyObject *av=NULL,*bv=NULL,*value=NULL,*weight=NULL;
        if (PyList_SetItem(progress,0,Py_NewRef(index))<0) goto fail;
        li=PyObject_GetItem(left,index); if (!li) goto fail;
        av=PyObject_GetItem(af,li); if (!av) goto fail;
        ri=PyObject_GetItem(right,index); if (!ri) goto fail;
        bv=PyObject_GetItem(bf,ri); if (!bv) goto fail;
        value=PyObject_CallFunctionObjArgs(agreement,av,bv,NULL); if (!value) goto fail;
        weight=PyNumber_Multiply(half,value); if (!weight) goto fail;
        if (PyObject_SetItem(w,index,weight)<0) goto fail;
        Py_DECREF(weight);Py_DECREF(value);Py_DECREF(bv);Py_DECREF(ri);Py_DECREF(av);Py_DECREF(li);
        continue;
fail:
        Py_XDECREF(weight);Py_XDECREF(value);Py_XDECREF(bv);Py_XDECREF(ri);Py_XDECREF(av);Py_XDECREF(li);
        Py_DECREF(half);return NULL;
    }
    Py_DECREF(half);Py_RETURN_TRUE;
}
static PyMethodDef methods[]={{"fill",fill,METH_VARARGS,"Bounded ordered weight fill."},{NULL,NULL,0,NULL}};
static struct PyModuleDef module={PyModuleDef_HEAD_INIT,"_edge_chunk",NULL,-1,methods};
PyMODINIT_FUNC PyInit__edge_chunk(void){return PyModule_Create(&module);}
