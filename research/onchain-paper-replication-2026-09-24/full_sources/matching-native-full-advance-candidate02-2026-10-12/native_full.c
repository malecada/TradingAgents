/* UNINSTALLED ENGINEERING PROTOTYPE. No admission/Owner/runtime authority.
 * Compile only through reviewed Root hook; no fast-math or FP contraction.
 * Agreements call the supplied, Python-wrapper-pinned original CPython function.
 * Native normalization is C05 qualification-only, NOT universal bitwise SciPy.
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <math.h>
#include <fenv.h>
#include <stdint.h>
#include <string.h>
#pragma STDC FP_CONTRACT OFF

static int putlong(PyObject *s,const char *key,long x) {
    PyObject *v=PyLong_FromLong(x); if(!v)return -1;
    int r=PyDict_SetItemString(s,key,v);Py_DECREF(v);return r;
}
static int putfloat(PyObject *s,const char *key,double x) {
    PyObject *v=PyFloat_FromDouble(x);if(!v)return -1;
    int r=PyDict_SetItemString(s,key,v);Py_DECREF(v);return r;
}
static int phase(PyObject *s,const char *name,long cursor) {
    PyObject *v=PyUnicode_FromString(name);if(!v)return -1;
    int r=PyDict_SetItemString(s,"phase",v);Py_DECREF(v);
    if(r<0)return -1;return putlong(s,"cursor",cursor);
}
static void failure_cursor(PyObject *s,long cursor) {
    /* A cursor-allocation failure must not replace the agreement exception. */
    PyObject *kind,*value,*trace;PyErr_Fetch(&kind,&value,&trace);
    if(putlong(s,"cursor",cursor)<0)PyErr_Clear();
    PyErr_Restore(kind,value,trace);
}
static int agreement(PyObject *fn,PyObject *a,PyObject *b,long i,long j,double *out) {
    PyObject *ki=NULL,*kj=NULL,*x=NULL,*y=NULL,*v=NULL;int result=-1;
    ki=PyLong_FromLong(i);kj=PyLong_FromLong(j);if(!ki||!kj)goto done;
    x=PyObject_GetItem(a,ki);y=PyObject_GetItem(b,kj);if(!x||!y)goto done;
    v=PyObject_CallFunctionObjArgs(fn,x,y,NULL);if(!v)goto done;
    if(!PyFloat_CheckExact(v)){PyErr_SetString(PyExc_TypeError,"original agreement float required");goto done;}
    *out=PyFloat_AS_DOUBLE(v);
    if(!isfinite(*out)||*out<0.0||*out>1.0){PyErr_SetString(PyExc_ValueError,"agreement outside proved domain");goto done;}
    result=0;
done:Py_XDECREF(v);Py_XDECREF(y);Py_XDECREF(x);Py_XDECREF(kj);Py_XDECREF(ki);return result;
}
/* NumPy-style eight-lane sum for <=32 contiguous terms; slow-axis sequential.
 * This does NOT imply bitwise equivalence of libm vs NumPy ufunc exp/log/log1p.
 */
static double reduce(const double *x,int n,int pairwise) {
    if(!pairwise||n<8){double s=-0.0;for(int k=0;k<n;k++)s+=x[k];return s;}
    double r[8];for(int k=0;k<8;k++)r[k]=x[k];int k=8;
    for(;k+7<n;k+=8)for(int j=0;j<8;j++)r[j]+=x[k+j];
    double s=((r[0]+r[1])+(r[2]+r[3]))+((r[4]+r[5])+(r[6]+r[7]));
    for(;k<n;k++)s+=x[k];return s;
}
static double lse(const double *x,int n,int stride,int pairwise) {
    double maximum=x[0],terms[32];int maxima=0;
    for(int k=1;k<n;k++)if(x[k*stride]>maximum)maximum=x[k*stride];
    for(int k=0;k<n;k++){
        double v=x[k*stride];
        if(v==maximum){terms[k]=0.0;maxima++;}else terms[k]=exp(v-maximum);
    }
    double sum=reduce(terms,n,pairwise);
    if(sum!=0.0)sum/=maxima;
    return (log1p(sum)+log((double)maxima))+maximum;
}
static int buffer(PyObject *o,Py_buffer *v,const char *format,int ndim,int writable) {
    if(PyObject_GetBuffer(o,v,PyBUF_FORMAT|PyBUF_STRIDES|(writable?PyBUF_WRITABLE:0))<0)return -1;
    if(v->ndim!=ndim||!v->format||strcmp(v->format,format)||v->itemsize!=8||
       !PyBuffer_IsContiguous(v,'C')||((uintptr_t)v->buf%8)){
        PyErr_SetString(PyExc_ValueError,"native buffer contract differs");return -1;
    }return 0;
}
static PyObject *run(PyObject *self,PyObject *args) {
    PyObject *s,*nf1,*nf2,*ef1,*ef2,*ei1,*ei2,*fn;long budget;
    double alpha,beta,rate,final;int maxiter;
    if(!PyArg_ParseTuple(args,"OOOOOOOOlddddi",&s,&nf1,&nf2,&ef1,&ef2,&ei1,&ei2,&fn,
                         &budget,&alpha,&beta,&rate,&final,&maxiter))return NULL;
    if(!PyDict_CheckExact(s)||!PyCallable_Check(fn)||fegetround()!=FE_TONEAREST||
       alpha!=1.0||beta!=1.0||rate!=.075||final!=30.0||maxiter!=50){
        PyErr_SetString(PyExc_ValueError,"fixed native prototype domain required");return NULL;
    }
    Py_buffer views[9]={{0}};PyObject *out=NULL;
    PyObject *objects[9]={PyDict_GetItemString(s,"V"),PyDict_GetItemString(s,"M"),PyDict_GetItemString(s,"Q"),ei1,ei2,nf1,nf2,ef1,ef2};
    for(int k=0;k<9;k++)if(!objects[k]||buffer(objects[k],&views[k],(k==3||k==4)?"l":"d",2,k<3)<0)goto done;
    int n=(int)views[0].shape[0],m=(int)views[0].shape[1];
    if(n<1||n>32||m<1||m>32||views[1].shape[0]!=n||views[1].shape[1]!=m||views[2].shape[0]!=n||views[2].shape[1]!=m||views[3].shape[0]!=2||views[4].shape[0]!=2)goto bad;
    long ea=views[3].shape[1],eb=views[4].shape[1];
    if(ea<1||eb<1||ea>1024||eb>1024||ea*eb>1024)goto bad;
    if(views[5].shape[0]!=n||views[6].shape[0]!=m||views[7].shape[0]!=ea||views[8].shape[0]!=eb)goto bad;
    for(int k=5;k<9;k++)if(views[k].shape[1]<1||views[k].shape[1]>4)goto bad;
    if(views[5].shape[1]!=views[6].shape[1]||views[7].shape[1]!=views[8].shape[1])goto bad;
    for(int k=0;k<3;k++)for(int j=k+1;j<9;j++){
        uintptr_t a=(uintptr_t)views[k].buf,b=(uintptr_t)views[j].buf;
        if(a<b+views[j].len&&b<a+views[k].len)goto bad;
    }
    for(int k=5;k<9;k++){
        const double *x=views[k].buf;for(Py_ssize_t j=0;j<views[k].len/8;j++)if(!isfinite(x[j])||fabs(x[j])>256.0)goto bad;
    }
    int64_t *le=views[3].buf,*re=views[4].buf;
    for(long k=0;k<2*ea;k++)if(le[k]<0||le[k]>=n)goto bad;
    for(long k=0;k<2*eb;k++)if(re[k]<0||re[k]>=m)goto bad;
    double stop=beta;int iterations=0;
    while(stop<=final&&iterations<maxiter){stop*=1.0+rate;iterations++;}
    long total=ea*eb,needed=n*m+iterations*(1+total+4);
    if(iterations!=48||budget<needed)goto bad;
    PyObject *p=PyDict_GetItemString(s,"phase"),*cursor=PyDict_GetItemString(s,"cursor"),
             *it=PyDict_GetItemString(s,"iterations"),*cap=PyDict_GetItemString(s,"max_chunk_entries");
    if(!p||!PyUnicode_CheckExact(p)||PyUnicode_CompareWithASCIIString(p,"nodes")!=0||
       !cursor||!PyLong_CheckExact(cursor)||PyLong_AsLong(cursor)!=0||
       !it||!PyLong_CheckExact(it)||PyLong_AsLong(it)!=0||
       !cap||!PyLong_CheckExact(cap)||PyLong_AsLong(cap)<n*m||
       PyDict_GetItemString(s,"safe")!=Py_True)goto bad;
    /* All structural/numeric admission and views obtained before mutation.
     * Fixed stack scratch weights8192 + reductions512 + small locals <16KiB.
     */
    double weights[1024],norms[32],*V=views[0].buf,*M=views[1].buf,*Q=views[2].buf;
    if(PyDict_SetItemString(s,"safe",Py_False)<0)goto done;
    for(int u=0;u<n;u++)for(int i=0;i<m;i++){
        long at=u*m+i;double value;
        if(agreement(fn,nf1,nf2,u,i,&value)<0)goto done;
        V[at]=value;if(putlong(s,"cursor",at+1)<0)goto done;
    }
    memcpy(M,V,(size_t)n*m*sizeof(double));if(phase(s,"outer",0)<0)goto done;
    for(int t=0;t<iterations;t++){
        for(int k=0;k<n*m;k++)Q[k]=alpha*V[k];
        if(phase(s,"edges",0)<0)goto done;
        for(long k=0;k<ea;k++)for(long l=0;l<eb;l++){
            long at=k*eb+l;double value;
            if(t==0 || total<8){
                if(agreement(fn,ef1,ef2,k,l,&value)<0){failure_cursor(s,at);goto done;}
                weights[at]=.5*value;
            }
            volatile double contribution=weights[at]*M[le[ea+k]*m+re[eb+l]];
            Q[le[k]*m+re[l]]+=contribution;
        }
        if(phase(s,"normalize_scale",0)<0)goto done;
        for(int k=0;k<n*m;k++)M[k]=Q[k]*beta;
        if(phase(s,"normalize_rows",0)<0)goto done;
        for(int u=0;u<n;u++)norms[u]=lse(M+u*m,m,1,1);
        for(int u=0;u<n;u++)for(int i=0;i<m;i++)M[u*m+i]-=norms[u];
        if(phase(s,"normalize_columns",0)<0)goto done;
        for(int i=0;i<m;i++)norms[i]=lse(M+i,n,m,m==1);
        for(int u=0;u<n;u++)for(int i=0;i<m;i++)M[u*m+i]-=norms[i];
        if(phase(s,"normalize_exp",0)<0)goto done;
        for(int k=0;k<n*m;k++)M[k]=exp(M[k]);
        beta*=1.0+rate;
        if(putfloat(s,"beta",beta)<0||putlong(s,"iterations",t+1)<0||phase(s,"outer",0)<0)goto done;
    }
    if(budget>needed&&phase(s,"done",0)<0)goto done;
    if(PyDict_SetItemString(s,"safe",Py_True)<0)goto done;
    out=PyLong_FromLong(needed);goto done;
bad:PyErr_SetString(PyExc_ValueError,"native structural/budget domain refused");
done:for(int k=0;k<9;k++)if(views[k].obj)PyBuffer_Release(&views[k]);return out;
}
static PyMethodDef methods[]={{"run",run,METH_VARARGS,"Uninstalled checked-buffer whole single-pair annealing prototype."},{NULL,NULL,0,NULL}};
static struct PyModuleDef module={PyModuleDef_HEAD_INIT,"_native_full",NULL,-1,methods};
PyMODINIT_FUNC PyInit__native_full(void){return PyModule_Create(&module);}
