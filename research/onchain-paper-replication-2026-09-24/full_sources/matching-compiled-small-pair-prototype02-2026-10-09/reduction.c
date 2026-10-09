#include <math.h>
#include <fenv.h>
/* Finite float64 block,1..4 each axis, strides in double elements. */
int small_lse(const double *x,double *out,int n,int m,int s0,int s1,int axis) {
 if(n<1||n>4||m<1||m>4||s0<1||s1<1||(axis!=0&&axis!=1)||fegetround()!=FE_TONEAREST)return 1;
 for(int i=0;i<n;i++)for(int j=0;j<m;j++)if(!isfinite(x[i*s0+j*s1])||fabs(x[i*s0+j*s1])>256.)return 2;
 int outer=axis==1?n:m,count=axis==1?m:n,step=axis==1?s1:s0;
 for(int a=0;a<outer;a++) {
  const double *row=x+a*(axis==1?s0:s1);double maximum=row[0],sum=0.,multiplicity=0.;
  for(int k=1;k<count;k++)if(row[k*step]>maximum)maximum=row[k*step];
  for(int k=0;k<count;k++)if(row[k*step]==maximum)multiplicity+=1.;else sum+=exp(row[k*step]-maximum);
  if(sum!=0.)sum/=multiplicity;
  out[a]=(log1p(sum)+log(multiplicity))+maximum;
 }
 return 0;
}
