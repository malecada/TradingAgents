/* Prototype only: finite nonnegative Q, dimensions1..32, nearest rounding.
   Scalar libm is not a bitwise substitute for NumPy vector transcendental ufuncs. */
#include <math.h>
#include <fenv.h>
#include <stddef.h>
static double reduce(const double *a, size_t count, size_t stride) {
    double maximum=a[0], multiplicity=0.0, sum=0.0;
    for(size_t k=1;k<count;k++) if(a[k*stride]>maximum) maximum=a[k*stride];
    for(size_t k=0;k<count;k++) {
        if(a[k*stride]==maximum) multiplicity+=1.0;
        else sum+=exp(a[k*stride]-maximum);
    }
    if(sum!=0.0)sum/=multiplicity;
    return (log1p(sum)+log(multiplicity))+maximum;
}
int normalize(const double *q,double *m,int n,int cols,double beta) {
    if(n<1||n>32||cols<1||cols>32||!isfinite(beta)||beta<=0||fegetround()!=FE_TONEAREST)return 1;
    for(int k=0;k<n*cols;k++)if(!isfinite(q[k])||q[k]<0||!isfinite(q[k]*beta))return 2;
    for(int k=0;k<n*cols;k++)m[k]=q[k]*beta;
    for(int row=0;row<n;row++) {
        double l=reduce(m+row*cols,cols,1);
        for(int col=0;col<cols;col++)m[row*cols+col]-=l;
    }
    for(int col=0;col<cols;col++) {
        double l=reduce(m+col,n,cols);
        for(int row=0;row<n;row++)m[row*cols+col]-=l;
    }
    for(int k=0;k<n*cols;k++)m[k]=exp(m[k]);
    return 0;
}
