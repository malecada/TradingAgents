from pathlib import Path
import hashlib,json,difflib,ast
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=Path('tradingagents/research/onchain_replication');F=D.parent
bases={'original_import_stage.py':ROOT/P/'original_import_stage.py','archive_dispatch.py':ROOT/P/'archive_dispatch.py','real_pilot_import_caller.py':F/'real-data-pilot-main-functional-composition02-2026-10-06/candidate'/P/'real_pilot_import_caller.py'}
edits={n:[] for n in bases}
def edit(n,old,new):edits[n].append({'old':old,'new':new})
n='original_import_stage.py'
edit(n,'def attach(prepared,*,policy_input,stage_policy_input):','def attach(prepared,*,policy_input,stage_policy_input,archive_transport=None):')
edit(n,"    policy=resource_binding.import_policy(original.parse(original._read_registered(run,stage_policy_input)))",'''    archive_name=selected.get('compact_archive_input')
    archive_selected=archive_name is not None or item.get('compact_archive_input') is not None
    require(archive_selected==(archive_transport is not None),'registered archive requires genuine preimport transport; local route cannot accept one')
    if archive_selected:
        from . import archive_dispatch,archive_owner_policy,archive_owner_operations
        from .real_pilot_import_caller import admitted
        _,current,pilot=admitted(run.admission,original.parse(original._read_registered(run,prepared._job_input)))
        require(pilot['schema_version']==2 and canonical_bytes(current)==canonical_bytes(selected),'exact schema2 real-pilot archive selection required')
        require(type(archive_transport) is archive_dispatch.View and type(archive_transport._context) is archive_dispatch.Context,'genuine archive dispatch view required')
        context=archive_transport._context
        require(context._run is run and context.view(bound.record['representation']) is archive_transport and context._record['job_input']==prepared._job_input,'archive view belongs to another original Run/representation')
        context._outer();prepared._check()
    policy=resource_binding.import_policy(original.parse(original._read_registered(run,stage_policy_input)))''')
edit(n,'    return owner,complete_import(owner,prepared,stage_policy=policy)', '''    if archive_transport is None:return owner,complete_import(owner,prepared,stage_policy=policy)
    try:
        # Real selection and durable ledger birth occur while Owner is still empty.
        archive_owner_operations.attach(archive_owner_policy.select(owner,input_name=archive_name,transport=archive_transport))
        context._outer();prepared._check()
        return owner,complete_import(owner,prepared,stage_policy=policy)
    except BaseException as primary:
        owner.poisoned=True
        ledger=getattr(owner,'_archive_operations',None)
        if ledger is not None:
            ledger._poisoned=True
            io._close_after_failure(ledger.close,primary)
        raise''')
n='archive_dispatch.py'
edit(n,"    require(execution['kind']=='fit' and canonical_bytes(execution['payload'])==canonical_bytes(payload),'archive dispatch actual job differs')",'''    if execution.get('kind')=='compact_resource':
        require(type(run) is ResearchRun,'actual real-pilot archive Run required')
        run._active();run._check_source()
        from .real_pilot_import_caller import admitted
        name,selected,pilot=admitted(run.admission,execution)
        require(pilot['schema_version']==2 and 'archive_inputs' in pilot and compact_routes=={name:True},'explicit schema2 real-pilot archive dispatch required')
        require(canonical_bytes(execution['payload'])==canonical_bytes(payload),'archive dispatch actual job differs')
    else:
        require(execution['kind']=='fit' and canonical_bytes(execution['payload'])==canonical_bytes(payload),'archive dispatch actual job differs')''')
n='real_pilot_import_caller.py'
edit(n,"    interval='imported_authority_lease_input' in p",'''    archive='archive_inputs' in p
    if archive:
        refs=p['archive_inputs']
        require(full and type(refs) is dict and set(refs)=={'policy_input','transport_input'} and all(type(v) is str and v for v in refs.values()) and len(set(refs.values()))==2,'explicit schema2 archive input pair required')
    interval='imported_authority_lease_input' in p''')
edit(n," | ({'imported_authority_lease_input'} if interval else set()), 'pilot plan fields differ')", " | ({'imported_authority_lease_input'} if interval else set()) | ({'archive_inputs'} if archive else set()), 'pilot plan fields differ')")
edit(n,"    require(type(s) is dict and set(s) == KEYS and s['operation'] == 'produce'\n            and all(type(s[k]) is str and s[k] for k in KEYS-{'descriptor','operation'}), 'pilot producer selection differs')",'''    archive_keys={'compact_archive_input','compact_archive_transport_input'}
    keys=KEYS | (archive_keys if archive_keys & set(s) else set())
    require(type(s) is dict and set(s) == keys and s['operation'] == 'produce'
            and all(type(s[k]) is str and s[k] for k in keys-{'descriptor','operation'}), 'pilot producer selection differs')''')
edit(n,"    _bind_resources(ad,job,p)\n",'''    _bind_resources(ad,job,p)
    expected_archive={'policy_input':s['compact_archive_input'],'transport_input':s['compact_archive_transport_input']} if 'compact_archive_input' in s else None
    require(p.get('archive_inputs')==expected_archive,'pilot/producer archive input pair differs')
''')
edit(n,"    require(roles <= set(ad.inputs), 'real population/config/graph inputs not registered')",'''    if 'archive_inputs' in p:roles.update(p['archive_inputs'].values())
    require(roles <= set(ad.inputs), 'real population/config/graph inputs not registered')''')
edit(n,"    journal = owner = None; targets = []; events = []; began = time.monotonic()", "    journal = owner = archive_context = None; targets = []; events = []; began = time.monotonic()")
edit(n,"    try:\n        journal,bound = resource_binding.open_first",'''    try:
        if 'archive_inputs' in p:
            from . import archive_dispatch
            archive_plan=archive_dispatch.preflight(run,payload,{name:True})
            require(archive_plan is not None,'selected real-pilot archive preflight absent')
            archive_context=archive_dispatch.Context(archive_plan)
        journal,bound = resource_binding.open_first''')
edit(n,"        owner,stage = original_import_stage.attach(prepared,policy_input=s['compact_policy_input'],stage_policy_input=s['original_dictionary_stage_input'])",'''        if archive_context is None:
            owner,stage = original_import_stage.attach(prepared,policy_input=s['compact_policy_input'],stage_policy_input=s['original_dictionary_stage_input'])
        else:
            owner,stage = original_import_stage.attach(prepared,policy_input=s['compact_policy_input'],stage_policy_input=s['original_dictionary_stage_input'],archive_transport=archive_context.view(name))''')
edit(n,'    throughput = None\n', '''    if archive_context is not None:
        try:archive_context.close(primary)
        except BaseException as later:primary=resource_fixture._preserve_terminal(primary,later)
    throughput = None
''')
records={}
for name,base in bases.items():
 old=base.read_text();s=old
 for e in edits[name]:
  assert s.count(e['old'])==1,(name,e['old']);s=s.replace(e['old'],e['new'])
 ast.parse(s);target=D/'candidate'/P/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(s)
 inverse=s
 for e in reversed(edits[name]):assert inverse.count(e['new'])==1;inverse=inverse.replace(e['new'],e['old'])
 assert inverse==old
 records[name]={'baseline':str(base),'baseline_sha256':hashlib.sha256(old.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(s.encode()).hexdigest(),'edits':edits[name]}
 (D/(name+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='baseline/'+name,tofile='candidate/'+name)))
(D/'SOURCE_DELTA01.json').write_text(json.dumps(records,indent=2)+'\n')
print({name:r['candidate_sha256'] for name,r in records.items()})
