from pathlib import Path
import ast,difflib
H=Path(__file__).resolve().parent;F=H.parent;old=F/'real-data-pilot-final23-2026-10-09';s=(old/'preflight02.py').read_text();original=s
s=s.replace('20261009-23','20261009-24').replace("HERE/'gate03.json'","HERE/'gate01.json'").replace("HERE/'BINDING02.json'","HERE/'BINDING01.json'").replace("HERE/'RELEASE_REVIEW02.json'","HERE/'RELEASE_REVIEW01.json'").replace('!=94','!=95').replace("'effective_attempt_budget':94","'effective_attempt_budget':95")
# Remove historical builders/inverse and projected preparation inventory, retain exact read/auth helpers.
t=ast.parse(s)
for name in ('inverse_binding','prepared_inputs','projected'):
 n=next(x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef) and x.name==name);lines=s.splitlines(True);s=''.join(lines[:n.lineno-1]+lines[n.end_lineno:])
s='\n'.join(line for line in s.split('\n') if not line.startswith(('SUCCESSOR=','BINDER=','GRAPH_METADATA_SHA=')))
s=s.replace("for role in ('gate','draft','preparation','baseline','transport','binding_review','transport_binding'):reference(binding[role])","for role in ('gate','core_manifest','public_manifest','public_refs','capacity_observation','transport','binding_review','transport_binding','budget_review'):reference(binding[role])")
s=s.replace("    prepared=prepared_inputs(binding,release,admission,job)","    capacity=prepared_inputs(binding,release,admission,job)")
s=s.replace("    scopes=projected(prepared['inventory'],storage,budget['limits'])","    scopes=projected(capacity,storage,budget['limits'])")
insert='''def _encoded(value):
    if type(value) is dict:
        for key,child in value.items():
            need(type(key) is str,'plain metadata key required');_encoded(child)
    elif type(value) in (list,tuple):
        for child in value:_encoded(child)
    elif type(value) is int:need(-(2**63)<value<2**63,'encoded integer bound differs')
    elif value is None or type(value) in (str,float,bool):pass
    else:raise ValueError('plain registered metadata required')

def _path_envelope(path):
    import re
    need(type(path) is str and len(path.encode('ascii'))<=512 and re.fullmatch(r'[A-Za-z0-9_./-]+',path) and '..' not in Path(path).parts,'actual path encoding envelope differs')

def prepared_inputs(binding,release,admission,job):
    """Exact independently reviewed current inputs; no obsolete builder replay."""
    review=read(binding['binding_review']);core=read(binding['core_manifest']);public=read(binding['public_manifest']);prior=read(binding['public_refs'])
    need(review['decision']=='accepted' and review['identity']==NAME,'actual final input binding review required')
    actual={role:{key:info[key] for key in ('path','sha256')} for role,info in admission.inputs.items()}
    need(len(actual)==64 and review['input_refs']==actual and binding['input_refs']==actual,'exact genuine64-role input closure differs')
    need(public['experiment']==NAME and public['all_input_roles']==64,'accepted public04 identity/roster differs')
    for role,ref in binding.items():
        if type(ref) is dict and {'path','sha256'}<=set(ref):
            need(release['evidence'].get(ref['path'])==ref['sha256'],'binding evidence absent from release')
            if role!='binding_review':need(review['evidence'].get(ref['path'])==ref['sha256'],'current binding evidence not independently joined')
    for role,info in actual.items():
        need(len(role.encode('ascii'))<=128,'actual input role encoding differs');_path_envelope(str(ROOT/info['path']))
        if role!=OPAQUE_ROLE:_encoded(read(info))
    # Immutable four core documents must be literal core03 bodies.
    for role,ref in core['inputs'].items():need(read(actual[role])==read(ref),'accepted core03 body changed: '+role)
    selected=next(iter(job['payload']['representation_jobs'].values()))
    pilot=read(actual[selected['real_pilot_input']]);mcm=read(actual[selected['compact_mcm_input']]);output=read(actual[selected['compact_mcm_output_input']]);compact=read(actual[selected['compact_policy_input']])
    need(mcm['schema_version']==6 and mcm['batched']['group_batches']==16 and mcm['batched']['batch_cells']==4096 and mcm['batched']['max_body_bytes']==1024 and mcm['batched']['max_checkpoint_bytes']==269114368,'exact grouped/single fatal snapshot policy differs')
    need(output['schema_version']==1 and 'partial_progress' not in pilot and 'scoring_diagnostic' not in pilot and 'diagnostic' not in pilot['outputs'],'full route cannot select diagnostic stop')
    schedule=compact['stage_policy']['schedule']
    need(schedule['max_total_checkpoints']==160 and schedule['max_total_checkpoint_bytes']==43058298880 and schedule['max_checkpoints']==1,'original cumulative checkpoint schedule differs')
    capacity=read(binding['capacity_observation'])
    need(capacity['identity']==NAME and capacity['decision']=='accepted' and capacity['source']==admission.source,'authenticated Root current capacity observation required')
    for field in ('new_logical_growth_bytes','new_allocated_growth_bytes','new_entries','directory_allocated_bound_bytes','other_writer_reserved_bytes','max_age_seconds'):
        need(type(capacity.get(field)) is int and capacity[field]>=0,'missing explicit capacity term: '+field)
    need(capacity['max_age_seconds']>0 and capacity['max_age_seconds']<=300,'finite current capacity observation required')
    observed=datetime.datetime.fromisoformat(capacity['at']);now=datetime.datetime.now(datetime.timezone.utc)
    need(observed.tzinfo is not None and 0<=(now-observed).total_seconds()<=capacity['max_age_seconds'],'Root capacity observation stale/future')
    need(capacity['directory_and_other_writers_included'] is True and capacity['runtime_residuals_included'] is True,'complete physical closure unjoined')
    return capacity

def projected(capacity,observation,limits):
    logical=capacity['new_logical_growth_bytes'];allocated=capacity['new_allocated_growth_bytes'];entries=capacity['new_entries']
    need(logical>0 and allocated>=logical and entries>0,'actual reviewed growth required')
    for key,growth,limit in (('logical_file_bytes',logical,'max_logical_bytes'),('allocated_bytes',allocated,'max_allocated_bytes'),('entries',entries,'max_entries')):
        need(observation[key]+growth<=limits[limit],'current union plus complete growth exceeds '+limit)
    return {'new_logical_growth_bytes':logical,'new_allocated_growth_bytes':allocated,'new_entries':entries,'projected_logical_bytes':observation['logical_file_bytes']+logical,'projected_allocated_bytes':observation['allocated_bytes']+allocated,'projected_entries':observation['entries']+entries,'qualification':'Authenticated Root growth includes directory/other-writer reservation; current union is sampled, not a hard quota.'}


'''
s=s.replace('def check():',insert+'def check():')
(H/'preflight24.py').write_text(s)
r=(old/'root_io02.py').read_text();r=r.replace('from preflight02 import check','from preflight24 import check');(H/'root_io24.py').write_text(r)
(H/'inverse.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),original.splitlines(True),fromfile='candidate/preflight24.py',tofile='baseline/preflight02.py')))
