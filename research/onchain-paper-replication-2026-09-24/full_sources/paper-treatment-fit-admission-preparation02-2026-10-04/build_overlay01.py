from pathlib import Path
import hashlib,json,ast
D=Path(__file__).resolve().parent
ROOT=D.parents[3]
changes={}
def change(name,old,new):
    p=D/'overlay/tradingagents/research/onchain_replication'/name
    if not p.exists():
        raw=(ROOT/'tradingagents/research/onchain_replication'/name).read_bytes()
        (D/'origins'/name).write_bytes(raw);p.write_bytes(raw)
    body=p.read_text();assert body.count(old)==1,(name,old)
    p.write_text(body.replace(old,new));changes.setdefault(name,[]).append({'old':old,'new':new})
change('run.py',"        mask_key = (cell['asset'], cell['fold'])", "        from .treatment_admission import preflight_treatment\n        preflight_treatment(run, reference, cell, examples)\n        mask_key = (cell['asset'], cell['fold'])")
change('population_assembly.py','expected_weeks, source_admission):','expected_weeks, source_admission, *, treatment_configs=None):')
change('population_assembly.py',"    hashes = c['graph_manifest_hashes']", "    if treatment_configs is not None:\n        complete_weeks = {w for w,r in graph_references.items() if r['status'] == 'complete'}\n        if set(treatment_configs) != complete_weeks or c['graph_config_hash'] != digest(canonical_bytes(treatment_configs)):\n            raise ValueError('exact per-week treatment configuration commitment differs')\n        for value in treatment_configs.values(): require_hash(value)\n    hashes = c['graph_manifest_hashes']")
change('population_assembly.py',"m['graph_config_hash'] != c['graph_config_hash']", "m['graph_config_hash'] != (c['graph_config_hash'] if treatment_configs is None else treatment_configs[week])")
change('population_assembly.py',"    projection = type(plan.get('schema_version'))", "    treatment = 'treatment_input' in plan\n    projection = type(plan.get('schema_version'))")
change('population_assembly.py',"'expected_weeks','admission_input','outputs'} | ({'projection_input'} if projection else set()))", "'expected_weeks','admission_input','outputs'} | ({'projection_input'} if projection else set()) | ({'treatment_input'} if treatment else set()))")
change('population_assembly.py',"    price_record = json.loads(run.read_input(plan['price_input']))", "    treatment_configs = None\n    if treatment:\n        from .treatment_admission import admit_treatment, _reader\n        declared, _, _ = _reader(run, plan['treatment_input'])\n        admitted = admit_treatment(run, plan['treatment_input'], asset=declared['asset'], variant=declared['variant'], weeks=plan['expected_weeks'])\n        for week, ref in refs.items():\n            value = admitted[week]\n            if ref['status'] != value['status']:\n                raise ValueError('population treatment disposition differs')\n            if value['status'] == 'complete':\n                if ref['sha256'] != value['population_manifest_sha256']:\n                    raise ValueError('population graph is not the admitted treatment graph')\n            elif ref != value:\n                raise ValueError('population unavailable treatment evidence differs')\n        treatment_configs = {w:r['graph_config_hash'] for w,r in admitted.items() if r['status'] == 'complete'}\n    price_record = json.loads(run.read_input(plan['price_input']))")
change('population_assembly.py',"                json.loads(run.read_input(plan['admission_input'])))", "                json.loads(run.read_input(plan['admission_input'])), treatment_configs=treatment_configs)")
change('population_assembly.py',"    run.write_json(outputs['population'], result['population'])", "    if treatment:\n        result['provenance']['treatment_input_sha256'] = digest(run.read_input(plan['treatment_input']))\n        result['provenance']['treatment_weeks'] = admitted\n    run.write_json(outputs['population'], result['population'])")
records=[]
for name, pairs in changes.items():
    raw=(D/'overlay/tradingagents/research/onchain_replication'/name).read_bytes();old=(D/'origins'/name).read_bytes();inv=raw.decode()
    for pair in reversed(pairs):assert inv.count(pair['new'])==1;inv=inv.replace(pair['new'],pair['old'])
    assert inv.encode()==old
    ast.parse(raw)
    records.append({'path':'tradingagents/research/onchain_replication/'+name,'original_sha256':hashlib.sha256(old).hexdigest(),'candidate_sha256':hashlib.sha256(raw).hexdigest(),'exact_inverse':True,'edits':pairs})
(D/'DELTA_INVERSE01.json').write_text(json.dumps(records,indent=2)+'\n')
