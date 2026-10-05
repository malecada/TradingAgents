from pathlib import Path
import hashlib,json,difflib,ast
D=Path(__file__).resolve().parent;M=D.parents[3];P=Path('tradingagents/research/onchain_replication');rows=[]
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def change(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b)
for name in ['real_pilot_import_caller.py','resource_fixture.py','resources.py','job.py']:
 old=(M/P/name).read_bytes();s=old.decode()
 if name=='resources.py':s=change(s,"not 0<value['file_size_bytes']<=4*1024**2", "not 0<value['file_size_bytes']<2**63")
 elif name=='resource_fixture.py':
  s=change(s,"run=owner.bound._run;job=json.loads(run.read_input(owner.bound.record['job_input']));schema(job)","run=owner.bound._run;job=json.loads(run.read_input(owner.bound.record['job_input']))\n    from . import real_pilot_import_caller\n    if real_pilot_import_caller.selected(job):\n        return real_pilot_import_caller.publication_boundary(owner,stage,job)\n    schema(job)")
 elif name=='job.py':
  s=change(s,"def _resource_limit_receipt(args,job,role,live=None):", "def _resource_worker_limits(job):\n    from . import resource_fixture, real_pilot_import_caller\n    if real_pilot_import_caller.selected(job):\n        return real_pilot_import_caller.worker_limits(job)\n    return resource_fixture.worker_limits()\n\n\ndef _resource_limit_receipt(args,job,role,live=None):")
  s=change(s,"    from . import resource_fixture\n    readback=resource_fixture.worker_limits()", "    readback=_resource_worker_limits(job)")
  s=change(s,"    if job['kind']=='compact_resource':\n        from . import resource_fixture\n        resource_fixture.worker_limits()", "    if job['kind']=='compact_resource':\n        _resource_worker_limits(job)")
 else:
  s=change(s,"require(type(p) is dict and set(p) == fields, 'pilot plan fields differ')", "require(type(p) is dict, 'pilot plan must be an object')\n    full = type(p.get('schema_version')) is int and p['schema_version'] == 2\n    require(set(p) == fields | ({'resource_policy'} if full else set()), 'pilot plan fields differ')")
  s=change(s,"p['schema_version'] == 1 and p['kind'] == KIND", "p['schema_version'] in (1, 2) and p['kind'] == KIND")
  s=change(s,"    return p\n\n\ndef schema(job):", "    if full:_finite_resources(p['resource_policy'])\n    return p\n\n\ndef schema(job):")
  start=s.index("    p = job['resources']\n",s.index('def schema'))
  end=s.index('\n\ndef _read',start)
  oldblock=s[start:end]
  tiny=oldblock.replace("    p = job['resources']\n",'')
  new='''    _finite_resources(job['resources'])


def _tiny_resources(p):
'''+tiny+'''


def _finite_resources(p):
    """Registered finite envelope, bounded by the existing job authority.

    This validates declared numbers, not available headroom or full-size capacity.
    Schema2 additionally pins this exact object in real_pilot_input at admission.
    """
    fields={'memory_max_bytes','memory_high_bytes','reserve_bytes','start_reserve_bytes',
            'disk_floor_bytes','disk_paths','wall_seconds','storage_budget','native_unit_limits'}
    require(type(p) is dict and set(p)==fields, 'explicit real pilot resource fields required')
    numeric=fields-{'disk_paths','storage_budget','native_unit_limits'}
    require(all(type(p[k]) is int and 0<p[k]<2**63 for k in numeric), 'finite integer resource limits required')
    require(p['memory_high_bytes']<=p['memory_max_bytes']<=6*GIB and p['reserve_bytes']>=3*GIB
            and p['start_reserve_bytes']>=p['memory_max_bytes']+p['reserve_bytes'], 'existing job memory/reserve authority exceeded')
    require(p['wall_seconds']<=28800 and p['disk_floor_bytes']>=10*GIB, 'existing job disk/wall authority exceeded')
    paths=p['disk_paths']
    require(type(paths) is list and bool(paths) and all(type(v) is str and Path(v).is_absolute() for v in paths)
            and len(paths)==len(set(paths)), 'explicit distinct absolute guard volumes required')
    native=p['native_unit_limits']
    require(type(native) is dict and set(native)=={'file_size_bytes'} and type(native['file_size_bytes']) is int
            and 0<native['file_size_bytes']<2**63, 'finite registered native file limit required')
    budget=p['storage_budget']
    require(type(budget) is dict and set(budget)=={'root','limits'} and type(budget['root']) is str
            and Path(budget['root']).is_absolute(), 'explicit whole-root budget required')
    limits=budget['limits']
    require(type(limits) is dict and set(limits)=={'max_allocated_bytes','max_logical_bytes','max_entries','max_depth','max_scan_seconds'}
            and all(type(v) is int and 0<v<2**63 for v in limits.values()), 'finite storage limits required')
    require(limits['max_depth']<=64 and limits['max_scan_seconds']<=5, 'existing bounded census controls exceeded')
    require(native['file_size_bytes']<=min(limits['max_logical_bytes'],limits['max_allocated_bytes']), 'native file ceiling exceeds whole-tree reservation')


def _bind_resources(ad,job,plan):
    resources=job['resources']
    if plan['schema_version']==1:
        _tiny_resources(resources)
    else:
        from .provenance import canonical_bytes
        require(canonical_bytes(plan['resource_policy'])==canonical_bytes(resources), 'pilot plan/job resource policy differs')
    from .job import resource_policy
    resource_policy(resources,ad.root)
    # Physical volume capacity is only an upper bound. Available growth and
    # completed graph/MCM reservations need separate registered entry evidence.
    if plan['schema_version']==2:
        import os
        fs=os.statvfs(ad.root);usable=fs.f_blocks*fs.f_frsize-resources['disk_floor_bytes']
        limits=resources['storage_budget']['limits']
        require(0<usable and max(limits['max_allocated_bytes'],limits['max_logical_bytes'])<=usable,
                'declared tree budget exceeds physical volume less fixed floor')


def worker_limits(job):
    """Exact selected RLIMIT; no default, adaptive increase or fallback."""
    import resource
    schema(job)
    expected=job['resources']['native_unit_limits']['file_size_bytes']
    resource.setrlimit(resource.RLIMIT_FSIZE,(expected,expected))
    require(resource.getrlimit(resource.RLIMIT_FSIZE)==(expected,expected), 'selected worker file limit not enforced')
    return {'rlimit_fsize':expected,'scope':'worker and inherited descendants; outer launcher/log limits separately required'}


def publication_boundary(owner,stage,job):
    """Actual real-route stage; never applies the synthetic failure selector."""
    from . import compact_owner
    require(type(owner) is compact_owner.Owner and type(stage) is compact_owner.Stage
            and stage.owner is owner and owner.bound.record.get('resource_only') is True, 'actual same-owner resource stage required')
    run=owner.bound._run
    run._active();run._check_source();owner.check_binding()
    _,selected_plan,plan=admitted(run.admission,job)
    require(owner.bound.record['job_input']=='execution_job' and stage.kind=='mcm'
            and stage.name in tuple('mcm-'+h for h in sorted(plan['graph_inputs']))
            and selected_plan['descriptor']['required_graphs']==sorted(plan['graph_inputs']), 'real target publication differs')
'''
  s=s[:start]+new+s[end:]
  s=change(s,"    p = validate_plan(_read(ad, s['real_pilot_input']))", "    p = validate_plan(_read(ad, s['real_pilot_input']))\n    _bind_resources(ad,job,p)")
 new=s.encode();ast.parse(new);write(D/'baseline'/name,old);write(D/'candidate'/P/name,new)
 patch=''.join(difflib.unified_diff(old.decode().splitlines(True),s.splitlines(True),fromfile='a/'+str(P/name),tofile='b/'+str(P/name)));write(D/'patches'/(name+'.patch'),patch.encode())
 a=old.decode().splitlines(True);b=s.splitlines(True)
 edits=[{'old_start':i,'old_end':j,'new_start':k,'new_end':l,'old':a[i:j],'new':b[k:l]} for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes() if op!='equal']
 inverse=b[:]
 for e in reversed(edits):assert inverse[e['new_start']:e['new_end']]==e['new'];inverse[e['new_start']:e['new_end']]=e['old']
 assert ''.join(inverse).encode()==old
 rows.append({'path':str(P/name),'baseline_sha256':hashlib.sha256(old).hexdigest(),'candidate_sha256':hashlib.sha256(new).hexdigest(),'edits':edits})
write(D/'SOURCE_DELTA01.json',(json.dumps({'schema_version':1,'files':rows,'concrete_resource_envelope_selected':False,'execution_authority':False},indent=2,sort_keys=True)+'\n').encode())
print(json.dumps({r['path']:r['candidate_sha256'] for r in rows}))
