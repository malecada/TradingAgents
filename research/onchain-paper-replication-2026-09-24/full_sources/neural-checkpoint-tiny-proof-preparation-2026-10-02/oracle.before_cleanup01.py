"""Deferred finite real-model proof. Numerical imports occur only after native readback.

Requires the coordinator's separately reviewed one-use launch. This caller does
not admit empirical work. Profile arms must each use a fresh process. No pytest.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import stat
import sys
import threading
import time
from contextlib import nullcontext

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
P=json.loads((HERE/'protocol01.json').read_bytes())
POLICY=P['execution']


def require(ok,message):
    if not ok:raise RuntimeError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()

def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def close_once(actions,primary=None):
    errors=[]
    for action in actions:
        try:action()
        except BaseException as error:errors.append(error)
    if primary is not None:
        for error in errors:primary.add_note('cleanup failed: '+repr(error))
        return
    if errors:raise errors[0]


def write_new(root,name,raw):
    require(type(raw) is bytes and len(raw)<=P['max_metadata_bytes'],'bounded body required')
    require(re.fullmatch('[a-z0-9][a-z0-9_.-]{0,95}',name) is not None,'one member name required')
    require(root.resolve()==root and stat.S_ISDIR(root.lstat().st_mode),'canonical directory required')
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);child=None
    try:
        pin=(os.fstat(fd).st_dev,os.fstat(fd).st_ino)
        child=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=fd)
        offset=0
        while offset<len(raw):
            count=os.write(child,raw[offset:offset+65536]);require(count>0,'write made no progress');offset+=count
        os.fsync(child);opened=os.fstat(child);entry=os.stat(name,dir_fd=fd,follow_symlinks=False)
        require(stat.S_ISREG(opened.st_mode) and opened.st_nlink==1 and opened.st_size==len(raw)
            and (opened.st_dev,opened.st_ino)==(entry.st_dev,entry.st_ino),'regular exclusive receipt changed')
        os.fsync(fd);now=root.lstat();require(pin==(now.st_dev,now.st_ino) and root.resolve()==root,'receipt parent changed')
    finally:close_once((() if child is None else (lambda:os.close(child),))+(lambda:os.close(fd),),sys.exception())


def native():
    require('torch' not in sys.modules and 'numpy' not in sys.modules,'native check must precede numerical imports')
    rows=[x for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::')]
    require(len(rows)==1,'one unified cgroup required');cg=Path('/sys/fs/cgroup')/rows[0][3:].lstrip('/')
    require(cg.resolve()==cg and '..' not in cg.parts,'canonical cgroup required')
    controls={k:(cg/k).read_text().strip() for k in ('memory.max','memory.high','memory.swap.max')}
    require(controls=={'memory.max':'1073741824','memory.high':'1073741824','memory.swap.max':'0'},'wrong native hard memory controls')
    require(len(os.sched_getaffinity(0))==2,'exactly two CPUs required')
    require(resource.getrlimit(resource.RLIMIT_FSIZE)==(4194304,4194304),'4 MiB hard file limit required')
    require(os.environ.get('PYTEST_DISABLE_PLUGIN_AUTOLOAD')=='1' and all(os.environ.get(k)=='' for k in ('PYTEST_PLUGINS','PYTEST_ADDOPTS')),'clean inherited plugin environment required')
    return cg,dict(cgroup=str(cg),controls=controls,cpus=sorted(os.sched_getaffinity(0)),file_limit_bytes=4194304)


class Phases:
    """Bounded scalar OS samples. No tensor hooks or backing-storage retention."""
    def __init__(self,root,cgroup,mode):
        self.root=root;self.cg=cgroup;self.mode=mode;self.index=0;self.phase='startup';self.samples={};self.count=0
        self.error=None;self.stop=threading.Event();self.lock=threading.Lock()
        self.thread=threading.Thread(target=self.sample,name='bounded-cgroup-sampler',daemon=True);self.thread.start()
    def sample(self):
        try:
            while not self.stop.is_set():
                current=int((self.cg/'memory.current').read_text())
                with self.lock:
                    require(self.count<P['max_phase_samples'],'phase sample budget exhausted');self.count+=1
                    old=self.samples.setdefault(self.phase,{'samples':0,'max_memory_current_bytes':0})
                    old['samples']+=1;old['max_memory_current_bytes']=max(old['max_memory_current_bytes'],current)
                self.stop.wait(P['phase_sample_seconds'])
        except BaseException as error:self.error=error;self.stop.set()
    def mark(self,name):
        if self.error is not None:raise self.error
        require(self.index<P['max_phase_markers'],'phase marker budget exhausted')
        with self.lock:self.phase=name
        value=dict(schema_version=1,index=self.index,phase=name,mode=self.mode,monotonic_ns=time.monotonic_ns(),
            memory_current_bytes=int((self.cg/'memory.current').read_text()),
            cumulative_cgroup_memory_peak_bytes=int((self.cg/'memory.peak').read_text()))
        write_new(self.root,f'phase-{self.index:04d}.json',encoded(value));self.index+=1
    def close(self):
        self.stop.set();self.thread.join(1);require(not self.thread.is_alive(),'sampler did not stop')
        if self.error is not None:raise self.error
    def report(self):
        return dict(phase_markers=self.index,samples=copy.deepcopy(self.samples),sample_count=self.count,
          qualification='10ms sampled maxima of whole cgroup memory.current by phase; can miss short peaks; not process-only; memory.peak is cumulative and never subtracted; sampler adds overhead')


def compare(a,b,records,path='value',exact=False):
    if isinstance(a,torch.Tensor):
        require(isinstance(b,torch.Tensor) and a.shape==b.shape and a.dtype==b.dtype,'tensor schema differs '+path)
        if a.dtype.is_floating_point:
            require(bool(torch.isfinite(a).all()) and bool(torch.isfinite(b).all()),'nonfinite '+path)
            torch.testing.assert_close(a,b,rtol=0 if exact else P['rtol'],atol=0 if exact else P['atol'])
        else:require(torch.equal(a,b),'nonfloating mismatch '+path)
        same=torch.equal(a.detach().contiguous().reshape(-1).view(torch.uint8),b.detach().contiguous().reshape(-1).view(torch.uint8))
        require(len(records)<P['max_compare_records'],'comparison record limit')
        records.append(dict(path=path,exact_required=exact,bitwise_equal=same,
            max_abs=0. if not a.numel() else float((a.detach().double()-b.detach().double()).abs().max())))
    elif isinstance(a,dict):
        require(type(b) is type(a) and a.keys()==b.keys(),'mapping differs '+path)
        for k in a:compare(a[k],b[k],records,path+'/'+str(k),exact)
    elif isinstance(a,(tuple,list)):
        require(type(b) is type(a) and len(a)==len(b),'sequence differs '+path)
        for i,(x,y) in enumerate(zip(a,b,strict=True)):compare(x,y,records,path+'/'+str(i),exact)
    else:require(type(a) is type(b) and a==b,'scalar differs '+path)


def fixture(case):
    graphs=[]
    for index in range(case['graphs']):
        n=3+index%3
        mcm=(torch.arange(n*32,dtype=torch.float32).reshape(n,32)/(n*32)+index/100).requires_grad_(case['input_grad'])
        edges=torch.tensor([(i,(i+1)%n) for i in range(n)]+[(0,0)],dtype=torch.int64).T.contiguous()
        graphs.append({'mcm':mcm,'edge_index':edges})
    sequences=[[graphs[(t//7)%2 if len(graphs)==2 else t] for t in range(28)] for _ in range(16)]
    mask=torch.ones((16,28),dtype=torch.bool);mask[0,-2:]=False;sequences[0][-2:]=[None,None]
    prices=torch.linspace(-1,1,16*28,dtype=torch.float32).reshape(16,28,1)
    labels=torch.arange(16)%2 if case['task']=='classification' else torch.linspace(-.2,.2,16).reshape(16,1)
    return graphs,sequences,prices,labels,mask


def clone_state(model,optimizer,rng):
    return {'model':copy.deepcopy(model.state_dict()),'optimizer':copy.deepcopy(optimizer.state_dict()),'rng':copy.deepcopy(capture_rng(rng))}


def make_optimizer(model):
    p=P['optimizer']
    return torch.optim.Adam(model.parameters(),lr=p['lr'],betas=tuple(p['betas']),eps=p['eps'],weight_decay=p['weight_decay'],amsgrad=p['amsgrad'],foreach=p['foreach'],fused=p['fused'])


def forward_loss(model,data):
    graphs,sequences,prices,labels,mask=data
    output=model(sequences,prices,mask)
    loss=torch.nn.functional.cross_entropy(output,labels) if model.task=='classification' else torch.nn.functional.mse_loss(output,labels)
    return output,loss


def gradients(model,data):
    result={}
    for name,p in model.named_parameters():
        require(p.grad is not None and bool(torch.isfinite(p.grad).all()),'missing/nonfinite named gradient '+name)
        result[name]=p.grad.detach().clone()
    groups=model.parameter_groups();all_ids=[id(p) for group in groups.values() for p in group]
    require(len(all_ids)==len(set(all_ids)) and set(all_ids)=={id(p) for p in model.parameters()},'parameter-group coverage differs')
    for name,group in groups.items():require(sum(float(p.grad.abs().sum()) for p in group)>0,'zero gradient group '+name)
    return dict(parameters=result,inputs=[None if g['mcm'].grad is None else g['mcm'].grad.detach().clone() for g in data[0]])


def step(model,optimizer,data,phases,label):
    optimizer.zero_grad(set_to_none=True)
    for graph in data[0]:graph['mcm'].grad=None
    phases.mark(label+'.forward');out,loss=forward_loss(model,data)
    phases.mark(label+'.backward');loss.backward()
    grad=gradients(model,data)
    if data[0][0]['mcm'].requires_grad:require(all(g is not None for g in grad['inputs']),'input gradient diagnostic missing')
    else:require(all(g is None for g in grad['inputs']),'fixed MCM unexpectedly has gradient')
    phases.mark(label+'.optimizer');optimizer.step()
    return dict(output=out.detach().clone(),loss=loss.detach().clone(),gradients=grad)


class Saved:
    """Observer intentionally retains backing storages; never a capacity sample."""
    def __init__(self):self.storages={};self.records=0;self.references=0
    def pack(self,tensor):
        require(self.records<P['max_saved_records'],'saved record bound exceeded')
        storage=tensor.untyped_storage();key=(str(tensor.device),storage.data_ptr(),storage.nbytes())
        self.storages.setdefault(key,storage);self.records+=1;self.references+=tensor.numel()*tensor.element_size()
        require(sum(s.nbytes() for s in self.storages.values())<=P['max_distinct_saved_bytes'],'diagnostic retained storage bound exceeded')
        return tensor
    def report(self):
        return dict(records=self.records,reference_bytes=self.references,distinct_storages=len(self.storages),distinct_backing_bytes=sum(s.nbytes() for s in self.storages.values()),
            qualification='outer saved hooks; storages deliberately retained for deduplication; inner checkpoint hooks hide internal recompute saves; not peak memory')


def arm(case,enabled,root,phases,identity,records):
    label=case['name']+('.true' if enabled else '.false');phases.mark(label+'.construct')
    rng=seed_all(11);config=copy.deepcopy(identity['core']);config['graph_activation_checkpointing']=enabled;config['gat_dropout']=case['dropout']
    model=ReplicationModel(config,case['task'],execution=dict(POLICY));optimizer=make_optimizer(model)
    initial=copy.deepcopy(model.state_dict());initial_rng=copy.deepcopy(capture_rng(rng));data=fixture(case)
    seen={'forward':0,'backward':0,'phase':'forward'}
    def entered(module,args):seen[seen['phase']]+=1
    hook=model.graph.register_forward_pre_hook(entered);saved=Saved();primary=None
    try:
        optimizer.zero_grad(set_to_none=True);phases.mark(label+'.forward')
        with torch.autograd.graph.saved_tensors_hooks(saved.pack,lambda t:t):
            output,loss=forward_loss(model,data);phases.mark(label+'.backward');seen['phase']='backward';loss.backward()
        grad=gradients(model,data)
        require(seen['forward']==case['graphs'],'weekly object sharing/cache differs')
        require(seen['backward']==(case['graphs'] if enabled else 0),'whole graph recompute pre-entry count differs')
        require(all((x is not None)==case['input_grad'] for x in grad['inputs']),'input gradient policy differs')
        phases.mark(label+'.optimizer');optimizer.step()
    except BaseException as error:primary=error;raise
    finally:close_once((hook.remove,),primary)
    storage=saved.report();del saved
    first=dict(output=output.detach().clone(),loss=loss.detach().clone(),gradients=grad)
    state=clone_state(model,optimizer,rng)
    provenance=dict(source_hashes=identity['source_hashes'],config_hash=sha(encoded(config)),
        input_hash=sha(encoded(case)),dictionary_hash=sha(b'synthetic-fixed-MCM-no-dictionary-fit'),
        fold_id='tiny-checkpoint-engineering',cell_id=identity['run_id']+'/'+label,source_commit=identity['source_commit'])
    checkpoint_root=root/(label+'.checkpoint');require(not checkpoint_root.exists(),'checkpoint namespace exists')
    phases.mark(label+'.save');path=save_checkpoint(checkpoint_root,model,optimizer,rng,provenance,epoch=0,batch=1,logs=[],epoch_loss=float(loss),epoch_count=16)
    restored=ReplicationModel(config,case['task'],execution=dict(POLICY));restored_optimizer=make_optimizer(restored)
    phases.mark(label+'.reload');load_checkpoint(path,restored,restored_optimizer,rng,provenance)
    compare(state,clone_state(restored,restored_optimizer,rng),records,label+'/same_arm_reload',True)
    # Identity refusal must precede mutation of parameters/optimizer/RNG.
    wrong=dict(provenance,config_hash=sha(encoded(dict(config,graph_activation_checkpointing=not enabled))))
    before=clone_state(restored,restored_optimizer,rng)
    try:load_checkpoint(path,restored,restored_optimizer,rng,wrong)
    except ValueError:pass
    else:raise RuntimeError('wrong checkpoint execution/config identity accepted')
    compare(before,clone_state(restored,restored_optimizer,rng),records,label+'/wrong_identity_unchanged',True)
    # Both continuations start from the same persisted RNG/state; first is original.
    restore_rng(state['rng'],rng);next_original=step(model,optimizer,data,phases,label+'.continue-original');end=clone_state(model,optimizer,rng)
    restore_rng(state['rng'],rng);next_restored=step(restored,restored_optimizer,data,phases,label+'.continue-restored')
    compare(next_original,next_restored,records,label+'/same_arm_continuation',True)
    compare(end,clone_state(restored,restored_optimizer,rng),records,label+'/same_arm_continuation_state',True)
    # Ordinary eval and train/no_grad use the same restored weights and RNG.
    inference={}
    for mode in ('eval','no_grad'):
        restored.train(mode=='no_grad');restore_rng(end['rng'],rng)
        phases.mark(label+'.'+mode)
        with torch.no_grad():inference[mode]=restored(data[1],data[2],data[4]).detach().clone()
        inference[mode+'_rng']=copy.deepcopy(capture_rng(rng))
    return dict(initial=initial,initial_rng=initial_rng,first=first,state=state,continuation=next_original,end=end,inference=inference),dict(case=case['name'],checkpoint=enabled,recompute=seen,storage=storage,config_sha256=sha(encoded(config)),checkpoint_directory=str(path.relative_to(root)))


def run_correctness(root,phases,identity):
    records=[];summaries=[]
    for case in P['cases']:
        baseline,one=arm(case,False,root,phases,identity,records)
        selected,two=arm(case,True,root,phases,identity,records)
        for field in baseline:
            compare(baseline[field],selected[field],records,case['name']+'/'+field,field in ('initial','initial_rng'))
        # RNG is exact throughout even when containing no floating tensors.
        compare(baseline['state']['rng'],selected['state']['rng'],records,case['name']+'/RNG-step1',True)
        compare(baseline['end']['rng'],selected['end']['rng'],records,case['name']+'/RNG-step2',True)
        summaries.extend([one,two]);phases.mark(case['name']+'.comparison_complete')
    return dict(cases=summaries,comparisons=records,bitwise_different_tensors=sum(not r['bitwise_equal'] for r in records),
        qualification='instrumented correctness/saved-storage evidence only; never process footprint; dropout case is a separate declared diagnostic')


def run_profile(root,phases,identity,enabled):
    """Fresh-process mode: no tensor/storage/module hooks and no oracle snapshots."""
    summaries=[]
    for case in [c for c in P['cases'] if c['name'] in P['profile_cases']]:
        label=case['name'];phases.mark(label+'.construct');rng=seed_all(11)
        config=copy.deepcopy(identity['core']);config['graph_activation_checkpointing']=enabled
        model=ReplicationModel(config,case['task'],execution=dict(POLICY));optimizer=make_optimizer(model);data=fixture(case)
        phases.mark(label+'.forward');out,loss=forward_loss(model,data)
        phases.mark(label+'.backward');loss.backward()
        for name,p in model.named_parameters():require(p.grad is not None and bool(torch.isfinite(p.grad).all()),'profile gradient invalid '+name)
        phases.mark(label+'.optimizer');optimizer.step()
        phases.mark(label+'.save')
        provenance=dict(source_hashes=identity['source_hashes'],config_hash=sha(encoded(config)),input_hash=sha(encoded(case)),
            dictionary_hash=sha(b'synthetic-fixed-MCM-no-dictionary-fit'),fold_id='tiny-profile',cell_id=identity['run_id']+'/'+label,source_commit=identity['source_commit'])
        path=save_checkpoint(root/(label+'.checkpoint'),model,optimizer,rng,provenance,epoch=0,batch=1,logs=[],epoch_loss=float(loss),epoch_count=16)
        # Drop first model/input/result references before reload; no inferred allocator release.
        del model,optimizer,data,out,loss
        phases.mark(label+'.reload');model=ReplicationModel(config,case['task'],execution=dict(POLICY));optimizer=make_optimizer(model)
        load_checkpoint(path,model,optimizer,rng,provenance);data=fixture(case)
        phases.mark(label+'.continuation-forward');out,loss=forward_loss(model,data)
        phases.mark(label+'.continuation-backward');loss.backward();phases.mark(label+'.continuation-optimizer');optimizer.step()
        summaries.append(dict(case=label,checkpoint=enabled,config_sha256=sha(encoded(config)),checkpoint_directory=str(path.relative_to(root))))
        del model,optimizer,data,out,loss;phases.mark(label+'.complete')
    return dict(cases=summaries,qualification='fresh-process profile mode; no tensor/module hooks or retained tensor snapshots; cgroup sampler and ordinary checkpoint serialization still incur overhead; second case inherits allocator/page-cache history of first case')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=P['modes'],required=True);parser.add_argument('--owned',type=Path,required=True)
    parser.add_argument('--source-commit',required=True);parser.add_argument('--run-id',required=True);parser.add_argument('--manifest-sha256',required=True);args=parser.parse_args()
    require(re.fullmatch('[0-9a-f]{40}',args.source_commit) is not None,'source commit required')
    require(re.fullmatch('[a-z0-9][a-z0-9-]{1,95}',args.run_id) is not None,'new engineering identity required')
    manifest_raw=(HERE/'source-manifest01.json').read_bytes();require(sha(manifest_raw)==args.manifest_sha256,'source manifest differs');manifest=json.loads(manifest_raw)
    for item in manifest['sources']:
        path=ROOT/item['path'];require(path.resolve()==path and stat.S_ISREG(path.lstat().st_mode),'source redirected')
        require(path.stat().st_size==item['bytes'] and sha(path.read_bytes())==item['sha256'],'frozen source differs '+item['path'])
    cg,controls=native();root=args.owned.absolute();require(root.resolve()==root and root.parent.is_dir(),'owned path redirected')
    require(shutil.disk_usage(root.parent).free>=P['bounds']['disk_floor_bytes'],'disk floor')
    root.mkdir(mode=0o700)  # exclusive whole mode identity; no reopening/retry
    write_new(root,'intent.json',encoded(dict(mode=args.mode,run_id=args.run_id,source_commit=args.source_commit,manifest_sha256=args.manifest_sha256,protocol_sha256=sha((HERE/'protocol01.json').read_bytes()),native=controls)))
    phases=Phases(root,cg,args.mode);primary=None;result=None
    try:
        phases.mark('numerical_import')
        global torch,ReplicationModel,seed_all,save_checkpoint,load_checkpoint,capture_rng,restore_rng
        sys.path.insert(0,str(ROOT))
        import torch
        require(torch.get_default_dtype()==torch.float32,'float32 default required')
        from tradingagents.research.onchain_replication.model import ReplicationModel
        from tradingagents.research.onchain_replication.checkpoints import seed_all,save_checkpoint,load_checkpoint,capture_rng,restore_rng
        torch.set_num_threads(2);torch.set_num_interop_threads(2);require(torch.get_num_threads()==2 and torch.get_num_interop_threads()==2,'thread readback differs')
        require(not torch.cuda.is_available(),'CPU-only proof requires no CUDA context')
        core_raw=(ROOT/P['model_input']).read_bytes();require(sha(core_raw)==P['model_sha256'],'original scientific core changed')
        identity=dict(core=json.loads(core_raw),run_id=args.run_id,source_commit=args.source_commit,source_hashes=[x['sha256'] for x in manifest['sources']])
        result=run_correctness(root,phases,identity) if args.mode=='correctness' else run_profile(root,phases,identity,args.mode=='profile_true')
        phases.mark('complete')
    except BaseException as error:primary=error
    try:phases.close()
    except BaseException as error:
        if primary is None:primary=error
        else:primary.add_note('sampler cleanup failed: '+repr(error))
    terminal=dict(schema_version=1,status='passed' if primary is None else 'failed',mode=args.mode,run_id=args.run_id,
        source_commit=args.source_commit,manifest_sha256=args.manifest_sha256,result=result,phases=phases.report(),
        error=None if primary is None else dict(type=type(primary).__name__,message=str(primary)))
    try:write_new(root,'terminal.json',encoded(terminal))
    except BaseException as error:
        if primary is None:raise
        primary.add_note('terminal receipt failed: '+repr(error))
    if primary is not None:raise primary
    return 0
if __name__=='__main__':raise SystemExit(main())
