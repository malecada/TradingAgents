from pathlib import Path
import difflib,hashlib,json
H=Path(__file__).resolve().parent
S=Path('tradingagents/research/onchain_replication')
for name in ('job','resources','real_pilot_import_caller','matching_owner'):
 p=S/(name+'.py');old=p.read_text();(H/'baseline'/p.name).write_text(old);new=old
 if name=='real_pilot_import_caller':
  marker='def _finite_resources(p):'
  new=new.replace(marker,"""def _amended_host_reserve(p):
    # Exact prospective amendment only; admission remains the caller's duty.
    expected={'memory_max_bytes':6*GIB,'memory_high_bytes':5*GIB,
              'reserve_bytes':5*GIB//2,'start_reserve_bytes':17*GIB//2,
              'disk_floor_bytes':10*GIB}
    return (all(type(p.get(k)) is int and p[k]==v for k,v in expected.items())
            and type(p.get('storage_budget')) is dict
            and p['storage_budget'].get('schema_version')==2)


"""+marker)
  new=new.replace("p['reserve_bytes']>=3*GIB", "(p['reserve_bytes']>=3*GIB or _amended_host_reserve(p))")
  new=new.replace("disk_floor_bytes=limits['disk_floor_bytes'])", "disk_floor_bytes=limits['disk_floor_bytes'],pilot_context=(run.admission,job))")
 if name=='job':
  new=new.replace("    if value['reserve_bytes'] < 3*resources.GIB or value['start_reserve_bytes'] < value['memory_max_bytes']+value['reserve_bytes']:","    from .real_pilot_import_caller import _amended_host_reserve\n    amended = _amended_host_reserve(value) and pilot_context is not None\n    if (value['reserve_bytes'] < 3*resources.GIB and not amended) or value['start_reserve_bytes'] < value['memory_max_bytes']+value['reserve_bytes']:")
  key="            selected_plan=next(iter(execution['payload']['representation_jobs'].values()))"
  new=new.replace(key,"            if amended and (not ad.ready or _read(ad,'execution_job')!=execution):raise ValueError('authenticated execution job required for reserve amendment')\n"+key)
  new=new.replace("disk_floor_bytes=policy['disk_floor_bytes'])", "disk_floor_bytes=policy['disk_floor_bytes'],pilot_context=(admitted,job))")
 if name=='resources':
  new=new.replace("                          disk_floor_bytes=20*GIB):", "                          disk_floor_bytes=20*GIB,pilot_context=None):")
  line="    if live['reserve_bytes']<3*GIB or live['disk_floor_bytes']<disk_floor_bytes:raise RuntimeError('guard reserve below protocol')"
  new=new.replace(line,"""    minimum_reserve=3*GIB
    if live['reserve_bytes']<minimum_reserve and pilot_context is not None:
        from .job import resource_policy
        from .real_pilot_import_caller import _amended_host_reserve
        ad,execution=pilot_context
        policy=resource_policy(execution['resources'],ad.root,pilot_context=pilot_context)
        if (not _amended_host_reserve(policy) or any(live.get(k)!=v for k,v in policy.items())
                or live.get('memory_swap_max_bytes')!=0
                or live.get('owner_identity',{}).get('experiment')!=ad.experiment_id
                or live.get('owner_identity',{}).get('source_commit')!=ad.source):
            raise RuntimeError('guard authenticated pilot reserve differs')
        minimum_reserve=policy['reserve_bytes']
    if live['reserve_bytes']<minimum_reserve or live['disk_floor_bytes']<disk_floor_bytes:raise RuntimeError('guard reserve below protocol')""")
 if name=='matching_owner':
  new=new.replace("    live=resources.assert_guarded_worker(base/'guard',job._command(args,'worker'),", "    pilot_context=(ad,json.loads(run.read_input('execution_job'))) if p['reserve_bytes']<3*resources.GIB else None\n    live=resources.assert_guarded_worker(base/'guard',job._command(args,'worker'),",1)
  new=new.replace("disk_floor_bytes=p['disk_floor_bytes'])", "disk_floor_bytes=p['disk_floor_bytes'],pilot_context=pilot_context)",1)
 assert new!=old
 (H/p.name).write_text(new)
 (H/(p.name+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(p),tofile=str(p))))
manifest={p.name:{'baseline_sha256':hashlib.sha256((H/'baseline'/p.name).read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in H.glob('*.py') if (H/'baseline'/p.name).exists()}
(H/'SOURCE_DELTA01.json').write_text(json.dumps(manifest,indent=2)+'\n')
