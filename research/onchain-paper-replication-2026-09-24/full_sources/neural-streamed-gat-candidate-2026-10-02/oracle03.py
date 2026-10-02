"""Prospective bounded synthetic RED/GREEN oracle. Do not run before release."""
import argparse
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import random
import shutil
import sys
import traceback
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
F32={'rtol':1e-5,'atol':1e-6}
F64={'rtol':1e-9,'atol':1e-10}
BLOCK_MAX=65536


def classify_saved_storage(records,*,nodes,input_edges,effective_edges,heads,width,input_width,block_edges):
    """Fixed tiny-fixture extent policy; shapes never authorize oversized backing.

    All prospective legitimate node, scalar, parameter, index and bounded-block
    storage ceilings are below one complete edge/head/width backing allocation.
    Unknown dtypes/extents fail closed. Views inherit the full backing extent.
    """
    edge_wide_bytes=effective_edges*heads*width*4
    limits={
      'torch.float32':max(nodes*heads*width*4,nodes*input_width*4,
                          effective_edges*heads*4,heads*input_width*width*4,
                          min(block_edges,effective_edges)*heads*width*4),
      'torch.int64':max(2*input_edges,2*effective_edges,nodes)*8,
      'torch.bool':max(input_edges,effective_edges,nodes)}
    if not all(0<=v<edge_wide_bytes for v in limits.values()):
        raise ValueError('diagnostic fixture cannot separate legitimate and edge-wide extents')
    full=[];unknown=[]
    for index,record in enumerate(records):
        size=record['storage_bytes'];dtype=record['dtype']
        if type(size) is not int or size<0:raise ValueError('invalid backing extent')
        if size>=edge_wide_bytes:full.append(index)
        elif dtype not in limits or size>limits[dtype]:unknown.append(index)
    return {'edge_wide_bytes':edge_wide_bytes,'legitimate_backing_byte_ceilings':limits,
            'full_edge_wide_backing_records':full,'unclassified_extent_records':unknown,
            'accepted':not full and not unknown}


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
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('red','green'),required=True);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    native=native_envelope(args.report)
    # All numerical imports occur only after the independently released guard.
    import copy
    import numpy as np
    import torch
    from baseline.gat import GraphAttention as BaselineLayer
    from baseline import model as reference_model
    torch.set_num_threads(2)
    config=json.loads((HERE/'model.json').read_text())|{'graph_activation_checkpointing':False}
    if args.mode=='green':
        path=HERE/'candidate02.py';spec=importlib.util.spec_from_file_location('streamed_gat_candidate',path)
        candidate=importlib.util.module_from_spec(spec);sys.modules[spec.name]=candidate;spec.loader.exec_module(candidate)
        selected_layer=candidate.GraphAttention;aggregate=candidate.weighted_aggregate
    else:
        selected_layer=BaselineLayer
        def aggregate(h,a,src,dst,*,block_edges=BLOCK_MAX,audit=None):
            if type(block_edges) is not int or not 0<block_edges<=BLOCK_MAX:raise ValueError('block limit')
            # Actual eager baseline, not a falsely successful streaming stub.
            return torch.zeros_like(h).index_add(0,dst,h[src]*a[:,:,None])
    results={};checks=[]
    def mark(name):checks.append(name);print('PASS '+name,flush=True)
    def compare(a,b,tol=F32):
        if isinstance(a,torch.Tensor):
            if a.dtype.is_floating_point:
                assert torch.isfinite(a).all() and torch.isfinite(b).all()
                torch.testing.assert_close(a,b,**tol)
            else:assert torch.equal(a,b)
        elif isinstance(a,dict):
            assert a.keys()==b.keys()
            for k in a:compare(a[k],b[k],tol)
        elif isinstance(a,(list,tuple)):
            assert len(a)==len(b)
            for x,y in zip(a,b,strict=True):compare(x,y,tol)
        else:assert a==b
    def layer(cls,block=7,dropout=0.):
        kwargs={'concat':True,'activation':'elu','dropout':dropout,'slope':.2}
        if cls is not BaselineLayer:kwargs['block_edges']=block
        return cls(32,16,4,**kwargs)
    def edges(n):
        pairs=[(i,j) for i in range(1,n) for j in range(1,n) if (i+3*j)%5<2]
        return torch.tensor(pairs,dtype=torch.long).reshape(-1,2).T.contiguous()
    def layer_run(cls,edge,mask=None,dropout=0.,double=False):
        torch.manual_seed(11);m=layer(cls,dropout=dropout)
        if double:m=m.double()
        n=19;x=torch.randn(n,32,dtype=torch.float64 if double else torch.float32,requires_grad=True)
        initial={k:v.detach().clone() for k,v in m.state_dict().items()};rng_before=torch.get_rng_state().clone()
        out=m(x,edge,mask);loss=out.square().mean();loss.backward()
        return {'initial':initial,'rng_before':rng_before,'rng_after':torch.get_rng_state(),'output':out.detach(),'loss':loss.detach(),'input_grad':x.grad,'gradients':{k:p.grad for k,p in m.named_parameters()}}
    def model_run(cls):
        random.seed(11);np.random.seed(11);rng=np.random.Generator(np.random.PCG64(11));torch.manual_seed(11)
        if cls is BaselineLayer:m=reference_model.ReplicationModel(config,'classification')
        else:
            def factory(*a,**k):return cls(*a,**k,block_edges=7)
            with patch.object(reference_model,'GraphAttention',factory):m=reference_model.ReplicationModel(config,'classification')
        initial=copy.deepcopy(m.state_dict())
        graphs=[{'mcm':torch.rand(n,32,requires_grad=True),'edge_index':edges(n)} for n in (11,17)]
        sequences=[[graphs[(b+t)%2] for t in range(28)] for b in range(16)]
        mask=torch.ones((16,28),dtype=torch.bool);mask[0,-2:]=False;sequences[0][-2:]=[None,None]
        prices=torch.linspace(-1,1,16*28).reshape(16,28,1);labels=torch.arange(16)%2
        optimizer=torch.optim.Adam(m.parameters(),lr=.001);out=m(sequences,prices,mask)
        loss=torch.nn.functional.cross_entropy(out,labels);loss.backward()
        gradients={k:p.grad.detach().clone() for k,p in m.named_parameters()}
        for name,parameters in m.parameter_groups().items():
            assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in parameters),name
            assert sum(float(p.grad.abs().sum()) for p in parameters)>0,name
        input_grad=[g['mcm'].grad.detach().clone() for g in graphs]
        optimizer.step();state={'model':copy.deepcopy(m.state_dict()),'optimizer':copy.deepcopy(optimizer.state_dict()),'torch_rng':torch.get_rng_state().clone(),'pcg64_rng':copy.deepcopy(rng.bit_generator.state),'python_rng':random.getstate()}
        buffer=io.BytesIO();torch.save(state,buffer);assert buffer.tell()<1024**2;buffer.seek(0)
        restored=torch.load(buffer,weights_only=True,map_location='cpu');compare(restored,state,{'rtol':0,'atol':0})
        m.load_state_dict(restored['model'],strict=True);optimizer.load_state_dict(restored['optimizer']);compare(m.state_dict(),state['model'],{'rtol':0,'atol':0});compare(optimizer.state_dict(),state['optimizer'],{'rtol':0,'atol':0})
        return {'initial':initial,'output':out.detach(),'loss':loss.detach(),'gradients':gradients,'input_grad':input_grad,'updated':state}
    def saved(cls):
        torch.manual_seed(11);m=layer(cls,block=17);x=torch.randn(257,32,requires_grad=True);edge=edges(257)
        eprime=int((edge[0]!=edge[1]).sum())+257;records=[];storages={};phase='forward'
        def pack(t):
            storage=t.untyped_storage();key=(str(t.device),storage.data_ptr(),storage.nbytes())
            # Keep observed backing storages alive until the diagnostic ends so
            # allocator address reuse cannot merge two different observations.
            # This observer changes retention; it is not a process-peak measure.
            storages.setdefault(key,storage)
            records.append({'phase':phase,'dtype':str(t.dtype),'shape':list(t.shape),
              'reference_bytes':t.numel()*t.element_size(),'storage_bytes':storage.nbytes(),
              'storage_identity':key});return t
        with torch.autograd.graph.saved_tensors_hooks(pack,lambda t:t):
            out=m(x,edge);loss=out.square().mean()
            phase='backward';loss.backward()
        distinct={key:storage.nbytes() for key,storage in storages.items()}
        phases={}
        for name in ('forward','backward'):
            rows=[r for r in records if r['phase']==name]
            unique={tuple(r['storage_identity']):r['storage_bytes'] for r in rows}
            phases[name]={'save_count':len(rows),'reference_bytes':sum(r['reference_bytes'] for r in rows),
                         'distinct_storages':len(unique),'distinct_storage_bytes':sum(unique.values())}
        classification=classify_saved_storage(records,nodes=257,input_edges=edge.shape[1],
            effective_edges=eprime,heads=4,width=16,input_width=32,block_edges=17)
        return {'reference_bytes':sum(r['reference_bytes'] for r in records),
            'distinct_storage_bytes':sum(distinct.values()),'distinct_storages':len(distinct),
            'phases':phases,'classification':classification,'effective_edges':eprime,
            'saved_records':[{k:v for k,v in r.items() if k!='storage_identity'} for r in records],
            'qualification':'hooks cover forward and backward; backing storage retained by observer to disambiguate identity; not process peak'}
    try:
        for case,edge,mask in [('mixed_self_isolated',edges(19),None),('zero_edges',torch.empty(2,0,dtype=torch.long),None),('masked',edges(19),torch.tensor([True]*17+[False]*2))]:
            base=layer_run(BaselineLayer,edge,mask);actual=layer_run(selected_layer,edge,mask);compare(base,actual);compare(base['initial'],actual['initial'],{'rtol':0,'atol':0});assert torch.equal(base['rng_after'],actual['rng_after']);mark('layer_'+case)
        compare(layer_run(BaselineLayer,edges(19),double=True),layer_run(selected_layer,edges(19),double=True),F64);mark('layer_float64')
        a=layer_run(BaselineLayer,edges(19),dropout=.2);b=layer_run(selected_layer,edges(19),dropout=.2);compare(a,b);assert torch.equal(a['rng_after'],b['rng_after']);mark('dropout_rng')
        for cls in (BaselineLayer,selected_layer):
            torch.manual_seed(11);m=layer(cls)
            try:m(torch.zeros(3,32),torch.tensor([[0,0],[1,1]],dtype=torch.long))
            except ValueError:pass
            else:raise AssertionError('duplicate edge silently accepted')
        mark('duplicate_refusal')
        baseline=model_run(BaselineLayer);actual=model_run(selected_layer);compare(baseline,actual);compare(baseline['initial'],actual['initial'],{'rtol':0,'atol':0});mark('full_model_16x28_all_gradients_Adam_RNG_reload')
        torch.manual_seed(11);h=torch.randn(5,2,3,dtype=torch.float64,requires_grad=True);a=torch.rand(9,2,dtype=torch.float64,requires_grad=True)
        src=torch.tensor([0,1,2,3,4,0,2,1,4]);dst=torch.tensor([1,1,1,2,2,3,4,0,4]);audit={}
        expected=torch.zeros_like(h).index_add(0,dst,h[src]*a[:,:,None]);actual=aggregate(h,a,src,dst,block_edges=3,audit=audit);compare(expected,actual,F64)
        left=torch.autograd.grad(expected.square().sum(),(h,a));right=torch.autograd.grad(actual.square().sum(),(h,a));compare(left,right,F64);mark('aggregation_output_all_gradients')
        assert torch.autograd.gradcheck(lambda x,y:aggregate(x,y,src,dst,block_edges=3),(h,a),eps=1e-6,atol=1e-5,rtol=1e-4);mark('independent_gradcheck')
        weight=torch.arange(30,dtype=torch.float64).reshape(5,2,3)/30
        scalar=(aggregate(h,a,src,dst,block_edges=3)*weight).sum();dh,da=torch.autograd.grad(scalar,(h,a));eps=1e-6
        for which,index,gradient in [(0,(1,0,2),dh),(1,(1,0),da)]:
            plus=[h.detach().clone(),a.detach().clone()];minus=[h.detach().clone(),a.detach().clone()];plus[which][index]+=eps;minus[which][index]-=eps
            fd=float(((aggregate(*plus,src,dst,block_edges=3)-aggregate(*minus,src,dst,block_edges=3))*weight).sum()/(2*eps));analytic=float(gradient[index]);assert abs(fd-analytic)<=1e-7+1e-5*abs(fd)
        mark('independent_central_difference')
        for bad in (0,-1,65537,True,1.5):
            try:aggregate(h,a,src,dst,block_edges=bad)
            except (ValueError,TypeError):pass
            else:raise AssertionError('invalid block limit accepted')
        mark('invalid_block_refusal')
        results['baseline_saved']=saved(BaselineLayer);results['selected_saved']=saved(selected_layer);results['block_audit']=audit
        if args.mode=='green':
            assert audit=={'forward_max_edges':3,'backward_max_edges':3,'forward_blocks':3,'backward_blocks':3},audit
            # Explicit first-order-only behavior: differentiating returned first
            # gradients must refuse instead of fabricating a second derivative.
            z=aggregate(h,a,src,dst,block_edges=3).square().sum();first=torch.autograd.grad(z,h,create_graph=True)[0]
            try:torch.autograd.grad(first.sum(),h)
            except RuntimeError:pass
            else:raise AssertionError('higher-order derivative was not explicitly refused')
            mark('bounded_blocks_first_order_contract')
        # This is the single named expected RED failure on the unchanged source.
        assert results['selected_saved']['classification']['accepted'] and results['selected_saved']['distinct_storage_bytes']<results['baseline_saved']['distinct_storage_bytes'],'RESOURCE_EDGE_WIDE_SAVED_TENSORS'
        mark('RESOURCE_EDGE_WIDE_SAVED_TENSORS_removed')
        status='passed';error=None;exitcode=0
    except BaseException as exc:
        status='failed';error={'type':type(exc).__name__,'message':str(exc)[:4096],'traceback':traceback.format_exc()[-16384:]};exitcode=1
        print('FAIL '+error['type']+': '+error['message'],flush=True)
    report={'schema_version':1,'mode':args.mode,'status':status,'passed_checks':checks,'error':error,'results':results,'native':native,'scope':'tiny synthetic engineering; no empirical capacity or financial fit','tolerances':{'float32':F32,'float64':F64},'torch_version':torch.__version__}
    raw=(json.dumps(report,indent=2,sort_keys=True)+'\n').encode();assert len(raw)<=65536
    with args.report.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return exitcode

if __name__=='__main__':raise SystemExit(main())
