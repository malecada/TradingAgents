"""Reported conventions and matched uncertainty, with explicit invalid denominators."""
import numpy as np
from sklearn.metrics import precision_recall_fscore_support,balanced_accuracy_score


def _pair(a,b):
    a=np.asarray(a);b=np.asarray(b)
    if a.ndim!=1 or a.shape!=b.shape or not len(a) or not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('nonempty finite matched one-dimensional arrays required')
    return a,b


def classification_metrics(labels,probabilities):
    y,p=_pair(labels,probabilities)
    if not np.isin(y,[0,1]).all() or ((p<0)|(p>1)).any():raise ValueError('invalid label/probability')
    pred=(p>.5).astype(int)
    precision,recall,f1,_=precision_recall_fscore_support(y,pred,labels=[0,1],zero_division=0)
    out={'accuracy':float(np.mean(y==pred)),'precision_up':float(precision[1]),'recall_up':float(recall[1]),'f1_up':float(f1[1]),'balanced_accuracy':float(recall.mean()),'brier':float(np.mean((p-y)**2))}
    for average in ('macro','weighted'):
        values=precision_recall_fscore_support(y,pred,labels=[0,1],average=average,zero_division=0)
        out.update({name+'_'+average:float(value) for name,value in zip(('precision','recall','f1'),values[:3])})
    out.update(TP=int(np.sum((y==1)&(pred==1))),TN=int(np.sum((y==0)&(pred==0))),FP=int(np.sum((y==0)&(pred==1))),FN=int(np.sum((y==1)&(pred==0))),N=len(y))
    q=np.clip(p,1e-15,1-1e-15);out['log_loss']=float(-np.mean(y*np.log(q)+(1-y)*np.log1p(-q)))
    return out


def regression_metrics(actual,predicted):
    y,p=_pair(actual,predicted)
    if (y<=0).any():raise ValueError('MAPE requires positive true price')
    error=p-y;mse=float(np.mean(error**2))
    return {'MAE':float(np.mean(np.abs(error))),'MSE':mse,'RMSE':float(np.sqrt(mse)),'MAPE_percent':float(100*np.mean(np.abs(error)/y))}


def paired_block_interval(dates,loss_a,loss_b,*,replicates=2000,block_days=14,seed=20260924):
    a,b=_pair(loss_a,loss_b);dates=np.asarray(dates,dtype='datetime64[D]')
    if dates.shape!=a.shape or np.isnat(dates).any() or (np.diff(dates).astype(int)<=0).any():raise ValueError('dates must be sorted and unique')
    years=dates.astype('datetime64[Y]');groups=[]
    for year in np.unique(years):
        index=np.flatnonzero(years==year)
        if len(index)<block_days or (np.diff(dates[index]).astype(int)!=1).any():raise ValueError('missing daily run/gap or insufficient block population')
        groups.append(index)
    if replicates<=0 or block_days<=0:raise ValueError('invalid bootstrap size')
    rng=np.random.Generator(np.random.PCG64(seed));d=a-b;values=[]
    for _ in range(replicates):
        annual=[]
        for group in groups:
            starts=rng.integers(0,len(group)-block_days+1,size=(len(group)+block_days-1)//block_days)
            selected=np.concatenate([group[s:s+block_days] for s in starts])[:len(group)]
            annual.append(float(d[selected].mean()))
        values.append(np.mean(annual))
    return tuple(float(v) for v in np.quantile(values,[.025,.975]))


def aggregate_years(rows):
    if not rows:raise ValueError('no annual metrics')
    keys=set(rows[0])
    if any(set(row)!=keys for row in rows):raise ValueError('annual metric membership mismatch')
    return {key:float(np.mean([row[key] for row in rows])) for key in sorted(keys)}
