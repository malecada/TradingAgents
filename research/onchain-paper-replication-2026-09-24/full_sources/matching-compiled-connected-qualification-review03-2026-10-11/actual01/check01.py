"""Actual finite outcome readback. Opaque checkpoint bytes, no scientific imports."""
import datetime,hashlib,json,os,resource,signal,stat,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parent;Q=P.parent;F=Q.parent;R=F.parents[2]
E=F/'matching-compiled-connected-qualification03-execution01-2026-10-11';C=F/'matching-compiled-connected-qualification03-2026-10-11';I=F/'matching-compiled-root-install01-2026-10-11'
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(15,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(20)
checks=[];refs={};total=0
def ck(ok,name):
    assert ok,name
    checks.append(name)
def sha(b):return hashlib.sha256(b).hexdigest()
def sig(s):return [getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')]
def read(p):
    global total
    p=Path(p);before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=4*1024**2 and p.resolve()==p
    b=p.read_bytes();total+=len(b);assert total<16*1024**2 and sig(before)==sig(p.lstat())
    refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
ck(sha(read(Q/'REVIEW01.json'))=='0e4e7868814829690bbe21c08e2e0fb5b48e8b467526cf4070db9969b9269552','frozen source/caller review')
ck(sha(read(Q/'MANIFEST01.json'))=='ec7a1e3beac27ab97e924ecfde42e3b341e379faf71f1298a1dd46fbae09adc1','frozen review manifest')
for name,row in js(Q/'MANIFEST01.json')['files'].items():
    b=read(Q/name);ck({'bytes':len(b),'sha256':sha(b)}==row,'unchanged source-review member '+name)
ck(sha(read(C/'qualify.py'))=='e3add7dd56333c0117f1e8e02728607e8f01030f4b00a5722ec71a80db6d70de','executed source pin retained')
rb=read(E/'RESULT.json');ck(sha(rb)=='3ccf01dcd5fe48c65998514a36ce6e12ffed05e6723a952ee7e161df884bca9f','external actual RESULT pin');r=json.loads(rb);pre=js(E/'PREFLIGHT.json');cases=js(C/'CASES.json')
ck(r['status']=='PASS_FINITE_SYNTHETIC_ONLY' and pre['status']=='RUNNING_SYNTHETIC_ONLY' and 'error' not in r,'actual finite pass')
ck(r['limits']==pre['limits']==cases and r['preflight']==pre['preflight'] and r['native_memory_policy']==pre['native_memory_policy'],'actual frozen preflight and resource joins')
ck(r['actual_admission_created'] is False and r['real_pilot_capacity_claim'] is False,'no admission or real pilot credit')
policy=js(F/'matching-compiled-runtime-input01-2026-10-10/POLICY01.json');ck(r['preflight']['policy_sha256']==sha(read(F/'matching-compiled-runtime-input01-2026-10-10/POLICY01.json')),'actual selected policy body')
attempt=js(I/'QUALIFICATION03_NATIVE_ATTEMPT01.json');exitrec=js(I/'QUALIFICATION03_NATIVE_EXIT01.json');closure=js(I/'QUALIFICATION03_CLOSURE01.json');caller=js(Q/'CALLER01.json')
ck(attempt['argv']==caller['argv'] and attempt['source_review_sha256']==sha(read(Q/'REVIEW01.json')) and attempt['caller_sha256']==sha(read(Q/'CALLER01.json')) and attempt['one_use'] and attempt['fresh_output_absent'],'actual exact reviewed one-use caller')
ck(exitrec['actual_systemd_client_exit_code']==0 and exitrec['outer_error'] is None and exitrec['result_present'],'actual Root exit0')
ck(read(I/'QUALIFICATION03_NATIVE01.stdout')==b'','actual empty stdout')
stderr=read(I/'QUALIFICATION03_NATIVE01.stderr').decode();ck('Running as unit: onchain-compiled-qualification-20261011-03.service' in stderr and 'Finished with result: success' in stderr and 'code=exited/status=0' in stderr,'actual native raw success/workerexit0')
memory=r['native_memory_policy'];ck(memory['pid']==closure['original_worker_pid']==1490601 and memory['unit']==attempt['unit']==exitrec['unit']=='onchain-compiled-qualification-20261011-03.service','actual PID/unit join')
ck(memory['readback']=={'memory.high':'3221225472','memory.max':'3221225472','memory.swap.max':'0'} and memory['virtual_address_limit_bytes']==16*1024**3,'actual reported native memory readback')
ck(memory['membership']=='0::'+memory['path'].removeprefix('/sys/fs/cgroup')+'\n' and memory['path']==f'/sys/fs/cgroup/user.slice/user-{os.getuid()}.slice/user@{os.getuid()}.service/app.slice/{memory["unit"]}','actual UID canonical membership receipt')
ck(closure['result_sha256']==sha(rb) and closure['actual_result_status']==r['status'] and closure['original_cgroup_absent'] and closure['original_worker_pid_absent'],'Root terminal closure joins')
ck(closure['actual_current_unit']=={'ActiveState':'inactive','ControlGroup':'','LoadState':'not-found','MainPID':'0','SubState':'dead'},'Root collected unit terminal observation')
ck(not Path(memory['path']).exists() and not Path('/proc/'+str(memory['pid'])).exists(),'independent current PID/cgroup metadata absence')
ck(r['elapsed_ns']==2286354411 and r['peak_rss_kib']==541500 and r['elapsed_ns']<cases['wall_seconds']*10**9,'finite actual process measurements')
ck(r['descriptor_closed_no_retry'] is True and r['factory_open_ns']>0 and r['kernel_backend']['seals']==15 and r['kernel_backend']['body_sha256']==policy['library_sha256'],'actual fresh factory sealed body and close observations')
ck([x['name'] for x in r['primitive']]==[x['name'] for x in cases['primitive_cases']] and all(x['exact_bytes'] is True for x in r['primitive']),'all four primitive/fallback observations retained')
files=sorted(x for x in E.rglob('*') if x.is_file());ck(len(files)<=cases['max_output_files'] and sum(x.stat().st_size for x in files)<=cases['max_output_bytes'],'actual retained scratch envelope')
members={str(p.relative_to(E)):read(p) for p in files}
def checkpoint(root):
    m=js(root/'manifest.json');expected={'manifest.json'}
    for section in ('annealing','hardening'):
        h=m[section+'_sha256']
        if h is None:ck(not (root/section).exists(),'absent inapplicable checkpoint section');continue
        sb=read(root/section/'manifest.json');ck(sha(sb)==h,'checkpoint section manifest hash');sm=json.loads(sb);expected.add(section+'/manifest.json')
        if section=='annealing':
            for name,row in sm['files'].items():
                payload=read(root/section/(name+'.npy'));ck(len(payload)==row['bytes'] and sha(payload)==row['sha256'],'opaque checkpoint NPY body hash');expected.add(section+'/'+name+'.npy')
        else:
            payload=read(root/section/'order.npy');ck(len(payload)==sm['order_bytes'] and sha(payload)==sm['order_sha256'],'opaque hardening order body hash');expected.add(section+'/order.npy')
    ck({str(x.relative_to(root)) for x in root.rglob('*') if x.is_file()}==expected,'exact checkpoint member denominator')
    return sha(read(root/'manifest.json'))
ck([x['name'] for x in r['cases']]==[x['name'] for x in cases['graph_cases']],'all four graph cases retained')
for result in r['cases']:
    name=result['name'];root=E/('direct-'+name)
    ck(0<result['advances']<=cases['max_advances_per_pair'] and result['roundtrips_per_route']==3 and result['total_direct_advance_calls']<=2*cases['max_advances_per_pair'],'fixed direct budgets '+name)
    resumed=result['continued_checkpoints'];ck(len(resumed)==4 and {x['route'] for x in resumed}=={0,1} and all(x['continued_advances']>0 for x in resumed),'four actually reported continued states '+name)
    ck(result['total_direct_advance_calls']==2*result['advances']+sum(x['continued_advances'] for x in resumed),'independent direct call denominator '+name)
    for stage in range(3):
        a=root/f'checkpoint-{stage}-0';b=root/f'checkpoint-{stage}-1';da=checkpoint(a);db=checkpoint(b)
        ck(da==db,'exact root manifests default/selected '+name+'/'+str(stage))
        amap={str(x.relative_to(a)):read(x) for x in a.rglob('*') if x.is_file()};bmap={str(x.relative_to(b)):read(x) for x in b.rglob('*') if x.is_file()};ck(amap==bmap,'exact complete raw checkpoint trees '+name+'/'+str(stage))
        if stage<2:
            rr=[x for x in resumed if x['checkpoint_sha256']==da];ck(len(rr)==2 and {x['route'] for x in rr}=={0,1} and all(x['origin_phase'].startswith('annealing:normalize' if stage==0 else 'hardening:') for x in rr),'continued states match actual checkpoint phase/hash')
scores=[x['score'] for x in r['cases']]*cases['numeric_repeats']
for label in ('default','selected'):
    root=E/('numeric-'+label);result=r['numeric'][label];binding=js(root/'binding.json');origins=read(root/'numeric-origins.bin')
    ck(result['results']==scores and len(result['results'])==8,'actual direct/numeric final score/iteration/convergence equality '+label)
    ck(binding['cells']==8 and binding['computed']==4 and binding['reused']==4 and binding['origin_bytes']==len(origins)==72 and binding['origin_sha256']==sha(origins),'independent origin complete denominator '+label)
    pairs=list(struct.iter_unpack('>BQ',origins));ck(pairs==[(0,i) for i in range(4)]+[(1,i) for i in range(4)],'actual4computed4reused origin framing '+label)
    ck(binding['origin_signature']==sig((root/'numeric-origins.bin').lstat()) and binding['stream_inode']==sig(root.lstat())[:2] and binding['batches_signature']==sig((root/'numeric-batches').lstat()),'actual binding file/directory metadata '+label)
    sh=hashlib.sha256();ih=hashlib.sha256();summarybytes=0;elapsed=0
    for i in range(2):
        path=root/'numeric-batches'/f'{i:012d}.json';body=read(path);summary=json.loads(body);chunk=origins[i*36:(i+1)*36]
        ck(raw(summary)==body and (summary['batch'],summary['start'],summary['stop'])==(i,i*4,(i+1)*4) and (summary['computed'],summary['reused'])==((4,0) if i==0 else (0,4)) and summary['origin_sha256']==sha(chunk),'actual numeric summary canonical/range/count/hash '+label+'/'+str(i))
        sh.update(struct.pack('>Q',len(body)));sh.update(body);ih.update(raw({'name':path.name,'signature':sig(path.lstat())}));summarybytes+=len(body);elapsed+=summary['elapsed_seconds']
    ck(summarybytes==binding['summary_bytes'] and sh.hexdigest()==binding['summary_sha256'] and ih.hexdigest()==binding['summary_inventory_sha256'] and elapsed==binding['elapsed_seconds'] and summary['counters']==binding['counters'],'independent summary framed-body/inventory closure '+label)
    ck(result['closure']=={k:binding[k] for k in ('cells','computed','reused','origin_bytes','summary_bytes')},'actual finish/verify receipt join '+label)
    ck(binding.get('compiled_normalization_policy')==(policy if label=='selected' else None) and binding['resume_supported'] is False and binding['old_per_occurrence_execution_credit'] is False and binding['independent_key_equivalence_recomputed'] is False,'numeric policy and explicit limits '+label)
    for event in result['checkpoint_events']:
        path=root/'checkpoints'/(event['purpose']+'-'+str(event['ordinal']));ck(checkpoint(path)==event['sha256'],'numeric actual checkpoint event body '+label)
    ck(0<len(result['checkpoint_events'])<=cases['max_numeric_checkpoints_per_route'] and len(result['per_occurrence_ns_including_lazy_load_and_fresh_checks'])==8,'numeric finite checkpoint/occurrence denominator '+label)
    ck(result['mapping_unload_claim'] is False and result['load_attempt_count'].startswith('NOT_OBSERVED'),'no invented mapping/load-count claim '+label)
    lifetime=result['shared_backend_lifetime']
    if label=='default':ck(len(lifetime)==9 and all(x['observation'] is None for x in lifetime),'default no selected owner observed')
    else:
        ck(lifetime[0]=={'stage':'constructed','observation':{'loaded':False,'opened':False}} and lifetime[-1]=={'stage':'closed','original_descriptor_closed':True},'selected fresh/terminal lifetime observations')
        observations=[x['observation'] for x in lifetime[1:-1]];ck(len(observations)==8 and all(x==observations[0] for x in observations) and observations[0]['loaded'] and observations[0]['opened'] and observations[0]['kernel']['seals']==15 and observations[0]['kernel']['body_sha256']==policy['library_sha256'],'actual stable selected FD/kernel identity each occurrence')
ck(r['numeric']['default']['results']==r['numeric']['selected']['results'],'final eight result bytes/iterations/convergence equal')
old=F/'matching-compiled-connected-qualification02-execution01-2026-10-10';ck((old/'PREFLIGHT.json').is_file() and (old/'ROOT_ACTUAL_EXIT01.json').is_file() and not (old/'RESULT.json').exists(),'original02 failed partial evidence remains')
ck(not any(n.split('.')[0] in {'numpy','scipy','torch','ctypes','tradingagents'} for n in sys.modules),'no scientific imports or numerical rerun')
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'disposition':'ACCEPT_ACTUAL_FINITE_QUALIFICATION03_ONLY','result_sha256':sha(rb),'checks':checks,'references':refs,'read_bytes':total,'retained_files':len(files),'retained_bytes':sum(len(x) for x in members.values()),'four_graph_cases':len(r['cases']),'four_primitive_cases':len(r['primitive']),'checkpoint_root_count':26,'numeric_routes':{'default':{'computed':4,'reused':4,'whole_owner_ns':r['numeric']['default']['wall_ns_including_construction_publication_close']},'selected':{'computed':4,'reused':4,'whole_owner_ns':r['numeric']['selected']['wall_ns_including_construction_publication_close']}},'actual_elapsed_ns':r['elapsed_ns'],'actual_peak_rss_kib':r['peak_rss_kib'],'actual_vm_peak_line':r['measured_vm_peak_line'],'observed_native_worker_pid':memory['pid'],'current_pid_cgroup_absent':True,'no_arrays_loaded':True,'no_numerical_rerun':True,'limitations':['Primitive exact bytes, nondefault error fallback, per-advance state/assignment comparisons and rejected FD writes/growth are successful assertions of the authenticated executed harness; individual transient numerical bodies are not separately retained for independent recomputation.','Independent readback verifies all opaque checkpoint bodies, paired tree equality, continued-state receipt joins, full numeric origins and framed summary/inventory bindings.','Per-occurrence receipt bodies are not retained; receipt_sha256 provenance is preserved but cannot be independently rebuilt from summary alone.','Native memory/FD readbacks were recorded by the actual exited process, authenticated through result/source/caller; no current live-FD or kernel-reenforcement test was performed.','Exact factory/load-attempt count, loader unmapping, general equivalence and sustained real-data performance/capacity remain unproved.','Tiny single-run times include construction, publication, close and read-only observation; no statistically supported speed claim.','No real-data successor, financial admission, experiment ledger/budget or production authority is granted.']}
with (P/'REVIEW01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','references','limitations')}));print('checks',len(checks))
