"""Root-only post-terminal synthetic qualification. Import is stdlib-only.

No Admission/Owner is created. Root must independently establish terminal pilot
and exact source/runtime admission. Preflight proves finite body references only.
"""
import argparse,errno,hashlib,importlib.util,json,os,stat,struct,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
CHECKOUT=HERE.parents[3]
INPUT_PINS={'SOURCE_REQUIREMENTS.json':'a3c6400f925641b3c657674a2f89b0c2bcd847132c3ff286f82c2d6508c2620a','CASES.json':'7c1657349b2cb64cda9f1bbe760ab93d4819e13ed4782007cdce4cfc793335d2','matching-config.json':'b3b8d88424a56a6009a4baa447e00b971d769930299c769414f6d33d9a4e873e'}
def need(value,message):
    if not value:raise ValueError(message)
def sha(body):return hashlib.sha256(body).hexdigest()
def read(path,limit,expected=None):
    path=Path(path);need(path.is_absolute() and path.resolve()==path,'absolute nonsymlink reference required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    try:
        before=os.fstat(fd);need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=limit,'bounded regular input required')
        parts=[];remaining=before.st_size+1
        while remaining:
            part=os.read(fd,remaining)
            if not part:break
            parts.append(part);remaining-=len(part)
        body=b''.join(parts);after=os.fstat(fd)
        fields=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
        need(tuple(getattr(before,k) for k in fields)==tuple(getattr(after,k) for k in fields) and len(body)==before.st_size,'input changed')
        need(expected is None or sha(body)==expected,'exact input/source SHA256 differs: '+str(path))
        return body
    finally:os.close(fd)
def inputs():
    return {name:json.loads(read(HERE/name,65536,digest)) for name,digest in INPUT_PINS.items()}
def preflight(checkout,policy_path):
    """Stdlib body/parser checks only; fixture callers receive no run capability."""
    frozen=inputs();requirements=frozen['SOURCE_REQUIREMENTS.json'];base=Path(checkout)/'tradingagents/research/onchain_replication'
    for name,digest in requirements['installed_module_sha256'].items():read(base/name,65536,digest)
    # Exact installed metadata policy has no top-level scientific imports.
    spec=importlib.util.spec_from_file_location('_qualification_policy_metadata',base/'compiled_normalization_policy.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    policy=json.loads(read(Path(policy_path),65536));module.freeze(policy)
    need(policy is not None and policy is not False,'explicit selected runtime policy required')
    module.read_reference(policy['source_path'],module.SOURCE_SHA256,65536)
    module.read_reference(policy['library_path'],module.LIBRARY_SHA256,65536)
    runtime=module.runtime_metadata(module.read_reference(policy['runtime_path'],policy['runtime_sha256'],4096,policy['runtime_bytes']))
    return frozen,policy,{'installed_sources':requirements['installed_module_sha256'],'runtime_reference':runtime,'policy_sha256':sha(read(Path(policy_path),65536)),'authority':'NONE; Root admission and pilot terminal status remain external preconditions'}
def write(path,value):
    body=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();need(len(body)<=4194304,'report file bound')
    with Path(path).open('xb') as stream:stream.write(body)
def cgroup_membership(body,uid):
    expected='/user.slice/user-'+str(uid)+'.slice/user@'+str(uid)+'.service/app.slice/onchain-compiled-qualification-20261011-03.service'
    need(body=='0::'+expected+'\n','exact unified local qualification03 cgroup membership required')
    return expected

def native_memory_guard(cases):
    need(cases['address_space_bytes']==16*1024**3 and cases['resident_cgroup_bytes']==3*1024**3 and cases['cgroup_unit']=='onchain-compiled-qualification-20261011-03.service','fixed qualification03 memory/unit policy required')
    def kernel_read(path,limit=4096):
        with Path(path).open('rb') as stream:body=stream.read(limit+1)
        need(len(body)<=limit,'bounded kernel metadata required')
        return body.decode('ascii')
    membership=kernel_read('/proc/self/cgroup');relative=cgroup_membership(membership,os.getuid())
    root=Path('/sys/fs/cgroup'+relative)
    need(root.is_dir() and root.resolve()==root,'canonical current cgroup required')
    need('memory' in kernel_read('/sys/fs/cgroup/cgroup.controllers').split(),'actual cgroup v2 memory controller required')
    need(str(os.getpid()) in kernel_read(root/'cgroup.procs',65536).split(),'current PID absent from qualification cgroup')
    actual={name:kernel_read(root/name).strip() for name in ('memory.high','memory.max','memory.swap.max')}
    need(actual=={'memory.high':'3221225472','memory.max':'3221225472','memory.swap.max':'0'},'actual cgroup memory policy differs')
    return {'membership':membership,'path':str(root),'pid':os.getpid(),'unit':cases['cgroup_unit'],'readback':actual,'virtual_address_limit_bytes':cases['address_space_bytes'],'qualification':'actual current-process kernel membership and policy readback; no inferred physical capacity'}

def execute(output,frozen,selected,preflight_record):
    """Called only after strict current-checkout preflight and explicit CLI action."""
    import resource,signal
    cases=frozen['CASES.json'];config=frozen['matching-config.json']
    os.sched_setaffinity(0,{3});os.nice(10)
    for limit,value in ((resource.RLIMIT_AS,cases['address_space_bytes']),(resource.RLIMIT_CPU,cases['cpu_seconds']),(resource.RLIMIT_FSIZE,cases['per_file_bytes'])):resource.setrlimit(limit,(value,value))
    signal.alarm(cases['wall_seconds'])
    need(not any(n.split('.')[0] in {'numpy','scipy','torch','ctypes','tradingagents'} for n in sys.modules),'fresh standalone process required')
    need(all(os.environ.get(key)=='1' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')),'Root must provide admitted single-thread environment')
    output=Path(output);need(output.is_absolute() and output.resolve()==output and not output.exists(),'new explicit output directory required')
    output.mkdir(mode=0o700)
    memory_receipt=native_memory_guard(cases)
    record={'native_memory_policy':memory_receipt,'status':'RUNNING_SYNTHETIC_ONLY','preflight':preflight_record,'cases':[],'primitive':[],'numeric':{},'limits':cases,'actual_admission_created':False,'real_pilot_capacity_claim':False}
    write(output/'PREFLIGHT.json',record)
    started=time.perf_counter_ns()
    try:
        # No scientific imports occur above this point, including failure paths.
        sys.path.insert(0,str(CHECKOUT))
        import numpy as np
        from scipy.special import logsumexp
        from tradingagents.research.onchain_replication import matching_checkpoint as engine
        from tradingagents.research.onchain_replication import matching_annealing as annealing
        from tradingagents.research.onchain_replication import matching_immutable_session as sessions
        from tradingagents.research.onchain_replication import batched_numeric_execution as numeric
        from tradingagents.research.onchain_replication import compiled_normalization_policy as policy_module
        from tradingagents.research.onchain_replication.contracts import AttributedGraph
        # Rejoin loaded paths and bodies. Existing numeric guards remain untouched.
        for name,digest in preflight_record['installed_sources'].items():
            module=__import__('tradingagents.research.onchain_replication.'+name[:-3],fromlist=['*'])
            expected=CHECKOUT/'tradingagents/research/onchain_replication'/name
            need(Path(module.__file__).resolve()==expected,'loaded package redirected')
            read(expected,65536,digest)
        need(np.geterr()==dict(divide='warn',over='warn',under='ignore',invalid='warn'),'original NumPy error policy required')
        def disk_bound():
            paths=[p for p in output.rglob('*') if p.is_file()]
            need(len(paths)<=cases['max_output_files'] and sum(p.stat().st_size for p in paths)<=cases['max_output_bytes'] and all(p.stat().st_size<=cases['per_file_bytes'] for p in paths),'synthetic scratch envelope exceeded')
        def state_body(value):
            if isinstance(value,np.ndarray):return {'dtype':value.dtype.str,'shape':list(value.shape),'bytes':value.tobytes().hex(),'writeable':bool(value.flags.writeable)}
            if isinstance(value,dict):return {k:state_body(v) for k,v in value.items()}
            if isinstance(value,(tuple,list)):return [state_body(v) for v in value]
            if isinstance(value,np.generic):return value.item()
            return value
        def state_equal(left,right):need(state_body(left)==state_body(right),'strict whole state/chunk bytes differ')
        def score(result):return [struct.pack('>d',float(result.score)).hex(),result.iterations,result.convergence]
        def graph(case,n,side):
            ids=tuple('synthetic-'+str(i) for i in range(n));mode=case['mode']
            values=[]
            for i in range(n):
                if mode=='near_tie':values.append([1.+(i+side)*2.**-40,float(i%2)*2.**-40])
                elif mode=='extreme':values.append([(-1.)**(i+side)*100.,float(i+side)*32.])
                else:values.append([float(i+side)/7.,float((i+side)%3)/11.])
            edges=[(i,(i+1)%n) for i in range(n)]
            return AttributedGraph(ids,np.asarray(values,dtype=np.float64),np.asarray(edges,dtype=np.int64).T,np.asarray([[float(i+side)/13.] for i in range(n)],dtype=np.float64),sha(('synthetic-'+case['name']+str(side)).encode()),ids[0])
        population=[(case,graph(case,case['n'],0),graph(case,case['m'],1)) for case in cases['graph_cases']]
        pair_policy=dict(max_state_bytes=65536,normalization_chunk_entries=10,hardening_chunk_entries=3,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=16,max_checkpoint_bytes=262144,max_publications=8,total_checkpoint_bytes=1048576)
        engine_options={k:pair_policy[k] for k in ('max_state_bytes','normalization_chunk_entries','hardening_chunk_entries','hardening_buffer_bytes')}
        def checkpoint(state,path,a,b,*,retain=False):
            disk_bound();before=state_body(state)
            digest=engine.save(state,path,a,b,config,max_checkpoint_bytes=pair_policy['max_checkpoint_bytes'])
            restored=None;transferred=False
            try:
                restored=engine.load(path,a,b,config,expected_sha256=digest,**engine_options)
                need(before==state_body(restored),'checkpoint roundtrip state differs')
                if retain:
                    disk_bound();transferred=True;return digest,restored
            finally:
                if restored is not None and not transferred:engine.close(restored)
            disk_bound();return digest
        def kernel_backend(backend):
            import inspect,fcntl
            # Read actual closure state without changing globals/functions/guards.
            closure=inspect.getclosurevars(backend.lse).nonlocals
            live=inspect.getclosurevars(closure['_live']).nonlocals
            fd=live['_fd'];need(type(fd) is int and closure['_fn'] is not None,'selected native backend unavailable; fallback is not native qualification')
            st=os.fstat(fd);seals=fcntl.fcntl(fd,1034)
            need(seals==15 and (st.st_dev,st.st_ino,st.st_size)==live['_pin'],'actual sealed descriptor differs')
            need(sha(os.pread(fd,65537,0))==selected['library_sha256'],'actual same-kernel loaded body differs')
            for action in (lambda:os.write(fd,b'x'),lambda:os.ftruncate(fd,st.st_size+1)):
                try:action()
                except OSError as error:need(error.errno==errno.EPERM,'unexpected seal refusal')
                else:raise ValueError('sealed library mutation unexpectedly succeeded')
            return fd,{'device':st.st_dev,'inode':st.st_ino,'bytes':st.st_size,'seals':seals,'body_sha256':selected['library_sha256']}
        def closed_fd(fd):
            try:os.fstat(fd)
            except OSError as error:need(error.errno==errno.EBADF,'descriptor close uncertain')
            else:raise ValueError('owned descriptor still open after close')
        def numeric_backend(executor,selection,*,before=False):
            import inspect
            owner=executor.memo.executor._normalization_owner
            if selection is None:
                need(owner is None,'default numeric route unexpectedly owns backend');return None,None,None
            need(owner is executor.memo.executor._normalization_owner_pin,'numeric normalization owner redirected')
            owner.current()
            closure=inspect.getclosurevars(owner.borrow).nonlocals
            need(closure['active'] is None,'session lease remained active between numeric calls')
            backend=closure['backend']
            if before:
                need(closure['opened'] is False and backend is None,'numeric constructor eagerly opened backend')
                return owner,None,{'opened':False,'loaded':False}
            need(closure['opened'] is True and backend is not None and backend.loaded(),'selected numeric backend unavailable')
            need(backend.current(),'selected numeric backend currentness failed');fd,kernel=kernel_backend(backend)
            return owner,backend,{'opened':True,'loaded':True,'fd':fd,'kernel':kernel}
        # New actual factory/native lifetime and narrow primitive gaps only.
        owner=type('EngineeringSelection',(),{})();policy_module.attach(owner,selected)
        at=time.perf_counter_ns();backend=policy_module.open_backend(owner);record['factory_open_ns']=time.perf_counter_ns()-at
        fd=None
        try:
            fd,kernel=kernel_backend(backend);record['kernel_backend']=kernel
            for case in cases['primitive_cases']:
                x=np.asarray(case['values'],dtype=np.float64)
                original=logsumexp(x,axis=case['axis'],keepdims=True)
                actual=backend.lse(x,axis=case['axis'],keepdims=True,fallback=logsumexp)
                need(actual.dtype==original.dtype and actual.shape==original.shape and actual.tobytes()==original.tobytes(),'strict primitive bytes differ: '+case['name'])
                record['primitive'].append({'name':case['name'],'exact_bytes':True})
            with np.errstate(under='raise'):
                x=np.asarray([[0.,1.],[1.,0.]],dtype=np.float64)
                need(backend.lse(x,axis=1,keepdims=True,fallback=logsumexp).tobytes()==logsumexp(x,axis=1,keepdims=True).tobytes(),'nondefault error-policy fallback differs')
        finally:backend.close()
        closed_fd(fd);backend.close();record['descriptor_closed_no_retry']=True
        # Full state logical advance comparison using actual sessions. Each
        # route has its own state. Normalization/hardening restored states
        # continue alongside both uninterrupted states through actual sessions.
        reference_scores=[]
        for index,(case,a,b) in enumerate(population):
            states=[];owned=[];resumed=[];step=0;advance_calls=0;roundtrips=0;observed=set();open_ns=[];fds=[]
            root=output/('direct-'+case['name']);root.mkdir()
            try:
                for selection in (None,selected):
                    states.append(engine.create(a,b,config,**engine_options))
                    at=time.perf_counter_ns();session=sessions.ImmutablePairSession(a,b,config,engine=engine,annealing=annealing,edge_cache_policy=dict(annealing.ADAPTIVE_EDGE_POLICY),compiled_normalization_policy_value=selection)
                    owned.append(session);open_ns.append(time.perf_counter_ns()-at)
                    if selection is not None:
                        actualfd,kernel=kernel_backend(session._normalizer);fds.append(actualfd)
                trace=hashlib.sha256()
                while states[0]['phase']!='done':
                    need(step<cases['max_advances_per_pair'],'finite logical-advance cap')
                    budget=1 if roundtrips==0 else cases['operation_budgets'][step%len(cases['operation_budgets'])]
                    need(advance_calls+2+len(resumed)<=2*cases['max_advances_per_pair'],'original aggregate direct advance allowance exhausted by continuation')
                    used=[s.advance(state,max_operations=budget) for s,state in zip(owned,states,strict=True)]
                    advance_calls+=2
                    for restored in resumed:
                        resumed_used=owned[restored['route']].advance(restored['state'],max_operations=budget);advance_calls+=1
                        need(resumed_used==used[restored['route']],'restored operation accounting differs')
                        state_equal(restored['state'],states[restored['route']]);restored['continued_advances']+=1
                    need(used[0]==used[1],'operation budget accounting differs');state_equal(*states)
                    phase=states[0]['phase']+':'+states[0]['annealing']['phase'];observed.add(phase)
                    trace.update(json.dumps(state_body(states[0]),sort_keys=True,separators=(',',':')).encode())
                    if roundtrips<cases['max_direct_checkpoints_per_pair'] and ((roundtrips==0 and states[0]['annealing']['phase'].startswith('normalize')) or (roundtrips==1 and states[0]['phase']=='hardening') or (roundtrips==2 and states[0]['phase']=='done')):
                        for route,state in enumerate(states):
                            path=root/('checkpoint-'+str(roundtrips)+'-'+str(route))
                            if roundtrips<2:
                                digest,restored=checkpoint(state,path,a,b,retain=True)
                                try:resumed.append({'route':route,'origin_phase':phase,'state':restored,'continued_advances':0,'checkpoint_sha256':digest})
                                except BaseException:
                                    engine.close(restored);raise
                            else:checkpoint(state,path,a,b)
                        roundtrips+=1
                    step+=1
                left,right=[engine.result(state,a,b,config) for state in states]
                need(left.assignment.tobytes()==right.assignment.tobytes() and left.soft_assignment.tobytes()==right.soft_assignment.tobytes() and score(left)==score(right),'final assignment/soft/score differs')
                need(roundtrips==cases['max_direct_checkpoints_per_pair'],'required normalization/hardening/done checkpoint phases not observed')
                need(len(resumed)==4,'both routes require normalization and hardening restoration')
                resumed_records=[]
                for restored in resumed:
                    need(restored['continued_advances']>0 and restored['state']['phase']=='done','restored checkpoint did not continue to completion')
                    state_equal(restored['state'],states[restored['route']])
                    result=engine.result(restored['state'],a,b,config)
                    expected=(left,right)[restored['route']]
                    need(result.assignment.tobytes()==expected.assignment.tobytes() and result.soft_assignment.tobytes()==expected.soft_assignment.tobytes() and score(result)==score(expected),'restored final assignment/soft/score differs')
                    resumed_records.append({k:v for k,v in restored.items() if k!='state'})
                reference_scores.append(tuple(score(left)))
                record['cases'].append({'name':case['name'],'advances':step,'roundtrips_per_route':roundtrips,'phases':sorted(observed),'trace_sha256':trace.hexdigest(),'score':score(left),'session_open_ns_default_selected':open_ns,'total_direct_advance_calls':advance_calls,'continued_checkpoints':resumed_records})
            finally:
                primary=sys.exception();errors=[]
                for session in owned:
                    try:session.close()
                    except BaseException as error:errors.append(error)
                for state in states+[restored['state'] for restored in resumed]:
                    try:engine.close(state)
                    except BaseException as error:errors.append(error)
                if errors:
                    if primary is None:raise errors[0]
                    for error in errors:primary.add_note('qualification cleanup: '+repr(error))
            for actualfd in fds:closed_fd(actualfd)
        # Genuine full numeric caller, source/roster guards, memo miss and reuse,
        # publication and verification. No Owner, fake guard or authority poll.
        schedule=dict(max_checkpoints=8,calls_per_checkpoint=64,operations_per_call=17,max_total_checkpoints=128,max_total_checkpoint_bytes=64*1024**2)
        route_results=[]
        for label,selection in (('default',None),('selected',selected)):
            root=output/('numeric-'+label);root.mkdir();cp=root/'checkpoints';cp.mkdir();events=[];results=[];lifetime=[];held_owner=held_backend=None;held_fd=None
            def save(purpose,ordinal,state,a,b,unused_config,unused_policy):
                need(len(events)<cases['max_numeric_checkpoints_per_route'],'finite numeric checkpoint cap')
                digest=checkpoint(state,cp/(purpose+'-'+str(ordinal)),a,b);events.append({'purpose':purpose,'ordinal':ordinal,'sha256':digest})
            at=time.perf_counter_ns()
            cells=len(population)*cases['numeric_repeats']
            with numeric.NumericExecution(root,config,pair_policy,schedule,save,cells=cells,batch_cells=4,max_origin_bytes=9*cells,max_summary_bytes=16384,max_entries=8,max_retained_bytes=1048576,max_key_bytes=65536,authority_poll=None,binding_timing=None,binding_owner=None,edge_cache_policy=dict(annealing.ADAPTIVE_EDGE_POLICY),compiled_normalization_policy_value=selection) as executor:
                observed_owner,unused_backend,initial=numeric_backend(executor,selection,before=True)
                held_owner=observed_owner;lifetime.append({'stage':'constructed','observation':initial})
                per_occurrence=[]
                for repetition in range(cases['numeric_repeats']):
                    for index,(case,a,b) in enumerate(population):
                        at_pair=time.perf_counter_ns();value=executor(a,b,sha(('synthetic-purpose-'+str(repetition)+'-'+case['name']).encode()));per_occurrence.append(time.perf_counter_ns()-at_pair)
                        encoded=(struct.pack('>d',value[0]).hex(),value[1],value[2]);need(encoded==reference_scores[index],'full numeric caller score differs from direct state');results.append(encoded)
                        observed_owner,observed_backend,observed=numeric_backend(executor,selection)
                        need(observed_owner is held_owner,'numeric backend owner changed between occurrences')
                        if selection is not None:
                            if held_backend is None:held_backend=observed_backend;held_fd=observed['fd']
                            need(observed_backend is held_backend and observed['fd']==held_fd,'numeric backend/descriptor replaced within owner lifetime')
                        lifetime.append({'stage':'after_occurrence','repetition':repetition,'case':case['name'],'observation':observed})
                binding=executor.finish()
            elapsed=time.perf_counter_ns()-at
            if selection is not None:
                closed_fd(held_fd)
                import inspect
                closed=inspect.getclosurevars(held_owner.close).nonlocals
                need(closed['closed'] is True and closed['close_attempted'] is True and closed['close_error'] is None,'numeric owner terminal cleanup not established')
                lifetime.append({'stage':'closed','original_descriptor_closed':True})
            closure=numeric.verify(root,binding)
            need(binding['computed']==len(population) and binding['reused']==len(population),'genuine memo compute/reuse population differs')
            write(root/'binding.json',binding)
            record['numeric'][label]={'wall_ns_including_construction_publication_close':elapsed,'per_occurrence_ns_including_lazy_load_and_fresh_checks':per_occurrence,'shared_backend_lifetime':lifetime,'load_attempt_count':'NOT_OBSERVED; opened flag and stable backend/FD only; profiling forbidden by genuine guard','mapping_unload_claim':False,'timing_includes_readonly_observation_overhead':True,'checkpoint_events':events,'closure':closure,'results':results}
            route_results.append(results);disk_bound()
        need(route_results[0]==route_results[1],'selected/unselected full caller results differ')
        record['status']='PASS_FINITE_SYNTHETIC_ONLY'
    except BaseException as error:
        record['status']='FAILED_OR_UNAVAILABLE';record['error']={'type':type(error).__name__,'message':str(error),'notes':getattr(error,'__notes__',[])}
        raise
    finally:
        record['elapsed_ns']=time.perf_counter_ns()-started
        record['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        with Path('/proc/self/status').open('r') as status_stream:
            status_body=status_stream.read(65537)
        need(len(status_body)<=65536,'bounded actual process status required')
        record['measured_vm_peak_line']=next((line for line in status_body.splitlines() if line.startswith('VmPeak:')),None)
        write(output/'RESULT.json',record)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-policy',required=True,type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--execute-after-terminal',action='store_true')
    args=parser.parse_args()
    frozen,selected,record=preflight(CHECKOUT,args.runtime_policy)
    if not args.execute_after_terminal:
        print(json.dumps({'status':'SOURCE_METADATA_PREFLIGHT_ONLY','record':record},sort_keys=True));return
    need(args.output is not None,'new output directory required')
    execute(args.output,frozen,selected,record)
if __name__=='__main__':main()
