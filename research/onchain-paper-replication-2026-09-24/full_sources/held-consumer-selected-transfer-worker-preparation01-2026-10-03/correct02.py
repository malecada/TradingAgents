from pathlib import Path
p=Path(__file__).parent;f=p/'held_score_consumer.py';s=f.read_text()
needle='def _transfer_budget(p,pop,tx,nodes,chunk,resources):'
helper='''def _transfer_auxiliary(run,closure):
    # Original admission owns effective-budget authority. This checks the exact
    # auxiliary/source partition, not a new review or an allowance exemption.
    exp=run.admission.experiment;aux=closure['auxiliary_source_files']
    extension=exp['cumulative_budget_extension'];refs={'budget_extension':extension['extension'],'budget_review':extension['review'],'charter':exp['charter']}
    body=json.loads(_body(run.admission.root/refs['budget_extension']['path']))
    refs['budget_allocation']=body['allocation']
    paths=set()
    for ref in refs.values():
        require(type(ref) is dict and set(ref)=={'path','sha256'} and aux.get(ref['path'])==ref['sha256'] and ref['path'] not in paths,'original auxiliary registered references differ')
        raw=_body(run.admission.root/ref['path']);require(hashlib.sha256(raw).hexdigest()==ref['sha256'],'original auxiliary body differs')
        paths.add(ref['path'])
    remaining=set(aux)-paths;require(len(remaining)==1,'exact separate auxiliary declaration required')
    name=next(iter(remaining));raw=_body(run.admission.root/name)
    require(len(raw)<=8192 and hashlib.sha256(raw).hexdigest()==aux[name],'bounded registered auxiliary declaration differs')
    declaration=json.loads(raw)
    expected={'schema_version':1,'kind':'selected-held-auxiliary-source-metadata-v1','program_id':run.admission.spec['program_id'],'experiment_id':run.admission.experiment_id,'implementation_source_count':201,'package_count':150,'implementation_map_sha256':hashlib.sha256(json.dumps(closure['source_files'],sort_keys=True,separators=(',',':')).encode()+b'\\n').hexdigest(),'entries':[{'role':role,'reference':refs[role]} for role in sorted(refs)]}
    require(declaration==expected and json.dumps(expected,sort_keys=True,separators=(',',':')).encode()+b'\\n'==raw,'complete selected auxiliary/code/case declaration differs')

'''
s=s.replace(needle,helper+needle).replace("    _sources(run)\n    fixed=", "    _transfer_auxiliary(run,closure)\n    _sources(run)\n    fixed=")
f.write_text(s)
