"""Unexecuted four-arm diagnostic; numerical imports require released native guard."""
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import shutil
import traceback
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
F32={'rtol':1e-5,'atol':1e-6}
NAME='temporal.lstm.weight_ih_l0'
COORD=(136,9)
ARMS=('eager_eager','einsum_eager','eager_streamed','einsum_streamed')
REPORT_LIMIT=1024**2

def native_envelope(report):
    # Parent owns single-use identity, 120s systemd deadline and descendant cleanup.
    # This is actual inherited native readback before numerical imports.
    row=[x for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::')]
    if len(row)!=1:raise RuntimeError('unified cgroup required')
    suffix=row[0][3:];cg=Path('/sys/fs/cgroup')/suffix.lstrip('/')
    if '..' in Path(suffix).parts or cg.resolve()!=cg:raise RuntimeError('cgroup path redirected')
    expected={'memory.max':'1073741824','memory.high':'1073741824','memory.swap.max':'0'}
    actual={k:(cg/k).read_text().strip() for k in expected}
    if actual!=expected or len(os.sched_getaffinity(0))!=2:raise RuntimeError('unreleased native numerical envelope')
    import resource
    if resource.getrlimit(resource.RLIMIT_FSIZE)!=(4*1024**2,4*1024**2):raise RuntimeError('finite file cap required')
    if not report.parent.is_dir() or report.exists() or report.is_symlink():raise RuntimeError('new report under owned root required')
    if shutil.disk_usage(report.parent).free<10*1024**3:raise RuntimeError('disk floor')
    return {'cgroup':str(cg),'controls':actual,'cpus':sorted(os.sched_getaffinity(0)),'rlimit_fsize':list(resource.getrlimit(resource.RLIMIT_FSIZE))}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    native=native_envelope(args.report)
    import copy
    import numpy as np
    import torch
    from baseline.gat import GraphAttention as BaselineLayer
    from baseline import model as reference_model
    from einsum_eager import GraphAttention as EinsumEager
    from eager_streamed import GraphAttention as EagerStreamed
    from candidate01 import GraphAttention as CandidateLayer
    torch.set_num_threads(2)
    config=json.loads((HERE/'model.json').read_text())|{'graph_activation_checkpointing':False}
    classes=(BaselineLayer,EinsumEager,EagerStreamed,CandidateLayer)
    def edges(n):
        pairs=[(i,j) for i in range(1,n) for j in range(1,n) if (i+3*j)%5<2]
        return torch.tensor(pairs,dtype=torch.long).reshape(-1,2).T.contiguous()
    def rng_record(rng):
        legacy=np.random.get_state()
        return {'torch':hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest(),
          'python':hashlib.sha256(repr(random.getstate()).encode()).hexdigest(),
          'numpy_legacy':hashlib.sha256(legacy[1].tobytes()+repr((legacy[0],*legacy[2:])).encode()).hexdigest(),
          'pcg64':copy.deepcopy(rng.bit_generator.state)}
    def run(cls):
        random.seed(11);np.random.seed(11);rng=np.random.Generator(np.random.PCG64(11));torch.manual_seed(11)
        if cls is BaselineLayer:m=reference_model.ReplicationModel(config,'classification')
        else:
            def factory(*a,**k):
                return cls(*a,**k,**({'block_edges':7} if cls in (EagerStreamed,CandidateLayer) else {}))
            with patch.object(reference_model,'GraphAttention',factory):m=reference_model.ReplicationModel(config,'classification')
        initial=copy.deepcopy(m.state_dict())
        graphs=[{'mcm':torch.rand(n,32,requires_grad=True),'edge_index':edges(n)} for n in (11,17)]
        sequences=[[graphs[(b+t)%2] for t in range(28)] for b in range(16)]
        mask=torch.ones((16,28),dtype=torch.bool);mask[0,-2:]=False;sequences[0][-2:]=[None,None]
        prices=torch.linspace(-1,1,16*28).reshape(16,28,1);labels=torch.arange(16)%2
        optimizer=torch.optim.Adam(m.parameters(),lr=.001);before_rng=rng_record(rng)
        out=m(sequences,prices,mask);loss=torch.nn.functional.cross_entropy(out,labels);loss.backward()
        gradients={k:p.grad.detach().clone() for k,p in m.named_parameters()}
        for name,parameters in m.parameter_groups().items():
            assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in parameters),name
            assert sum(float(p.grad.abs().sum()) for p in parameters)>0,name
        input_grad=[g['mcm'].grad.detach().clone() for g in graphs]
        optimizer.step();state={'model':copy.deepcopy(m.state_dict()),'optimizer':copy.deepcopy(optimizer.state_dict()),'torch_rng':torch.get_rng_state().clone(),'pcg64_rng':copy.deepcopy(rng.bit_generator.state),'python_rng':random.getstate()}
        # Retain unchanged save/reload path, with exact tensor verification.
        buffer=io.BytesIO();torch.save(state,buffer);assert buffer.tell()<1024**2;buffer.seek(0)
        restored=torch.load(buffer,weights_only=True,map_location='cpu')
        def exact(a,b):
            if isinstance(a,torch.Tensor):assert torch.equal(a,b)
            elif isinstance(a,dict):
                assert a.keys()==b.keys()
                for k in a:exact(a[k],b[k])
            elif isinstance(a,(list,tuple)):
                assert len(a)==len(b)
                for x,y in zip(a,b,strict=True):exact(x,y)
            else:assert a==b
        exact(restored,state);m.load_state_dict(restored['model'],strict=True);optimizer.load_state_dict(restored['optimizer'])
        exact(m.state_dict(),state['model']);exact(optimizer.state_dict(),state['optimizer'])
        names=[name for name,_ in m.named_parameters()]
        ids=[i for group in state['optimizer']['param_groups'] for i in group['params']]
        assert len(names)==len(ids)==len(set(ids)) and len(names)<=64
        named_state={name:state['optimizer']['state'][i] for name,i in zip(names,ids,strict=True)}
        p0=initial[NAME][COORD];g=gradients[NAME][COORD];slot=named_state[NAME]
        group=state['optimizer']['param_groups'][0];b1,b2=group['betas'];step=float(slot['step'])
        assert step==1 and group['weight_decay']==0 and not group['amsgrad'] and group['lr']==.001
        # Tensor first-step replay matches Adam's scalar update operation order;
        # binary64 formula below independently exposes epsilon amplification.
        mt=torch.zeros_like(g).lerp_(g,1-b1)
        vt=torch.zeros_like(g).mul_(b2).addcmul_(g,g,value=1-b2)
        denom=vt.sqrt().div_((1-b2)**.5).add_(group['eps'])
        replay=p0.clone().addcdiv_(mt,denom,value=-group['lr']/(1-b1))
        scalar_update=group['lr']*float(g)/(abs(float(g))+group['eps'])
        actual=state['model'][NAME][COORD]
        coordinate={'parameter':NAME,'shape':list(initial[NAME].shape),'coordinate':list(COORD),
          'optimizer_parameter_id':ids[names.index(NAME)],'initial':float(p0),'gradient':float(g),
          'exp_avg':float(slot['exp_avg'][COORD]),'exp_avg_sq':float(slot['exp_avg_sq'][COORD]),
          'step':step,'updated':float(actual),'actual_delta':float(actual-p0),
          'reconstructed_m':float(mt),'reconstructed_v':float(vt),'reconstructed_updated':float(replay),
          'reconstruction_delta':float(actual-replay),'binary64_formula_updated':float(p0)-scalar_update,
          'betas':list(group['betas']),'eps':group['eps'],'lr':group['lr'],
          'm_equal':bool(torch.equal(mt,slot['exp_avg'][COORD])),
          'v_equal':bool(torch.equal(vt,slot['exp_avg_sq'][COORD]))}
        return {'initial':initial,'output':out.detach(),'loss':loss.detach(),'gradients':gradients,
          'input_grad':input_grad,'updated':state['model'],'adam':named_state},coordinate,{'before':before_rng,'after':rng_record(rng)},dict(zip(names,ids,strict=True))
    def compare(reference,actual):
        rows=[]
        def visit(a,b,path):
            if isinstance(a,torch.Tensor):
                assert a.shape==b.shape and a.dtype==b.dtype
                if a.is_floating_point():
                    finite=bool(torch.isfinite(a).all() and torch.isfinite(b).all())
                    delta=(a-b).abs();allowed=F32['atol']+F32['rtol']*b.abs()
                    mask=(delta>allowed)|~torch.isfinite(a)|~torch.isfinite(b)
                    indices=mask.flatten().nonzero().flatten()[:4]
                    details=[]
                    for index in indices:
                        flat=int(index);coord=[];remaining=flat
                        for width in reversed(a.shape):coord.insert(0,remaining%width);remaining//=width
                        details.append({'index':coord,'reference':float(a.flatten()[flat]),'actual':float(b.flatten()[flat]),'absolute_error':float(delta.flatten()[flat])})
                    rows.append({'path':path,'shape':list(a.shape),'elements':a.numel(),'finite':finite,
                      'mismatches':int(mask.sum()),'max_absolute_error':float(delta.max()) if delta.numel() else 0.,
                      'first_mismatches':details})
                else:rows.append({'path':path,'shape':list(a.shape),'mismatches':int((a!=b).sum())})
            elif isinstance(a,dict):
                assert a.keys()==b.keys()
                for k in a:visit(a[k],b[k],path+'.'+str(k))
            elif isinstance(a,(list,tuple)):
                assert len(a)==len(b)
                for i,(x,y) in enumerate(zip(a,b,strict=True)):visit(x,y,path+'.'+str(i))
            else:assert a==b
        visit(reference,actual,'root');assert len(rows)<=512
        return rows
    records={};reference=None
    for name,cls in zip(ARMS,classes,strict=True):
        try:
            values,coordinate,rng,ids=run(cls)
            if name=='eager_eager':reference=values
            rows=compare(reference,values) if reference is not None else None
            records[name]={'status':'observed','coordinate':coordinate,'rng':rng,'parameter_ids':ids,
              'comparisons_to_eager_eager':rows,'disagreement':None if rows is None else any(r['mismatches'] for r in rows),
              'initial_exact':None if reference is None else all(torch.equal(reference['initial'][k],values['initial'][k]) for k in reference['initial']),
              'rng_matches_baseline':True if name=='eager_eager' else rng==records.get('eager_eager',{}).get('rng')}
            print('OBSERVED '+name,flush=True)
            if name!='eager_eager':del values
        except BaseException as exc:
            records[name]={'status':'error','error':{'type':type(exc).__name__,'message':str(exc)[:2048],'traceback':traceback.format_exc()[-8192:]}}
            print('ERROR '+name+': '+type(exc).__name__,flush=True)
            # Never attempt another arm after fatal interruption or memory exhaustion.
            if not isinstance(exc,Exception) or isinstance(exc,MemoryError):break
    operational=tuple(records)==ARMS and all(x['status']=='observed' for x in records.values())
    disagreement=any(x.get('disagreement') for x in records.values())
    report={'schema_version':1,'status':'observed_disagreement' if operational and disagreement else ('observed_agreement' if operational else 'diagnostic_incomplete'),
      'scope':'tiny synthetic diagnosis only; no candidate acceptance or capacity claim','arms':records,
      'arm_order':list(ARMS),'tolerances':F32,'native':native,'torch_version':torch.__version__,
      'pooled_vectors':'not collected: preserve uninstrumented model path','reconstruction':'float32 Adam scalar-order replay plus binary64 first-step formula; differences are reported, never normalized away'}
    raw=(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n').encode();assert len(raw)<=REPORT_LIMIT
    with args.report.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return 0 if operational else 1

if __name__=='__main__':raise SystemExit(main())
