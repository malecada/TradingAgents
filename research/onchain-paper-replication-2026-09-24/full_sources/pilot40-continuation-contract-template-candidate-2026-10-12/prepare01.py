from pathlib import Path
P=Path(__file__).resolve().parent;prior=P.parent/'pilot40-continuation-target-poll-candidate-2026-10-12'
s=(prior/'batched_continuation.py').read_text();(P/'BASELINE_batched_continuation.py').write_text(s)
helper='''
def _bind_contract_template(run,target,m,expected_contract):
    """Bind only operational identities after genuine Target creation."""
    from . import compact_mcm_batched
    require(m['contract_mode']=='genuine-target-contract-template-v1' and target is not None,
        'explicit genuine target contract template required')
    pin=_target_identity(run,target)
    template=m['contract']
    fields={'source_sha256','config_sha256','dictionary_sha256','graph_hash','node_order_hash',
        'descriptor_sha256','workflow_identity','cells','batch_cells','numerical_contract_sha256'}
    require(type(template) is dict and set(template)==fields and set(expected_contract)==fields
        and template['workflow_identity'] is None and template['descriptor_sha256'] is None,
        'exact two-slot contract template required')
    role=m['runtime_policy_input']
    require(type(role) is str and role in run.admission.inputs,'registered runtime MCM policy required')
    raw=_bounded_input(run,role,max_bytes=2*1024**2,target=target)
    policy=_json(raw)
    _poll_target(run,target)
    scope=type(target).derive_scope(target)
    require(scope==target.scope and scope['graph']==target.key
        and scope['dictionary']==target.dictionary.identity, 'genuine target scope differs')
    rows=len(target.graph.node_ids);cells=rows*32
    descriptor={'rows':rows,'cells':cells,'motifs':32,'graph_hash':target.key,
        'node_order_hash':scope['node_order'],'workload_sha256':scope['workflow'],'purpose_schema_version':2}
    start={'rows':rows,'cells':cells,'graph_hash':target.key,'scope':scope}
    compact_mcm_batched.validate(policy,cells)
    current=compact_mcm_batched._continuation_contract(target,start,policy,descriptor)
    frozen={**current,'workflow_identity':None,'descriptor_sha256':None}
    require(body(frozen)==body(template) and body(current)==body(expected_contract),
        'template scientific/source/config or runtime contract differs')
    require(all(a is b for a,b in zip(pin,_target_identity(run,target),strict=True)),
        'template target authority changed')
    return descriptor

'''
s=s.replace('\ndef _authority(',helper+'\ndef _authority(',1)
needle="    recovered={}\n";assert s.count(needle)==1
s=s.replace(needle,"    if 'contract_mode' in m:\n        require(m['contract_mode']=='genuine-target-contract-template-v1'\n            and review['contract_mode']==m['contract_mode']\n            and review['contract_template_sha256']==digest(body(m['contract']))\n            and review['runtime_policy_input']==m['runtime_policy_input'], 'reviewed contract template differs')\n"+needle)
needle="    require(m['policy']==POLICY and m.get('provenance_mode','durable-commit') in ('durable-commit','legacy-recovered-prefix-v1') and m['contract']==expected_contract, 'prefix exact contract differs')"
assert s.count(needle)==1
s=s.replace(needle,"    runtime_descriptor=None\n    if 'contract_mode' in m:\n        runtime_descriptor=_bind_contract_template(run,target,m,expected_contract)\n        require(m['policy']==POLICY and m.get('provenance_mode','durable-commit') in ('durable-commit','legacy-recovered-prefix-v1'), 'prefix exact contract differs')\n    else:\n    "+needle)
s=s.replace("    require((m['contract']['workflow_identity'],m['contract']['graph_hash']) not in _USED.get(run,set()),'continuation already consumed by successor')", "    if runtime_descriptor is None:\n        require((m['contract']['workflow_identity'],m['contract']['graph_hash']) not in _USED.get(run,set()),'continuation already consumed by successor')\n    else:\n        require((expected_contract['workflow_identity'],expected_contract['graph_hash']) not in _USED.get(run,set()),'continuation already consumed by successor')")
s=s.replace("    descriptors=_descriptors(m.get('descriptors',{}),expected_contract)", "    descriptors=_descriptors(m.get('descriptors',{}),expected_contract)\n    if runtime_descriptor is not None:\n        runtime_key=digest(body(runtime_descriptor))\n        require(runtime_key==expected_contract['descriptor_sha256'],'runtime descriptor digest differs')\n        require(runtime_key not in descriptors or descriptors[runtime_key]==body(runtime_descriptor),'runtime descriptor conflicts with parent')\n        descriptors[runtime_key]=body(runtime_descriptor)")
needle="    _authority(run,m,**({'target':target} if target is not None else {}))\n    expected="
assert s.count(needle)==1
s=s.replace(needle,"    _authority(run,m,**({'target':target} if target is not None else {}))\n    if runtime_descriptor is not None:\n        require(_bind_contract_template(run,target,m,expected_contract)==runtime_descriptor,'runtime template binding changed during verification')\n    expected=")
needle="            _authority(run,_json(manifest),**({'target':target} if target is not None else {}))"
s=s.replace(needle,needle+"\n            if 'contract_mode' in _json(manifest):\n                runtime_descriptor=_bind_contract_template(run,target,_json(manifest),_json(reader[1]))\n                require(dict(prefix.descriptors).get(digest(body(runtime_descriptor)))==body(runtime_descriptor)\n                    and runtime_descriptor['workload_sha256']==prefix.workflow_identity,'restored runtime template binding differs')")
(P/'batched_continuation.py').write_text(s)
