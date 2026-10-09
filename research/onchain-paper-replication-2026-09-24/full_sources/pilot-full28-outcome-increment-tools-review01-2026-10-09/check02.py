import ast,hashlib,json,os
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).resolve().parent;P=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';N=P/'outcome13';O=P/'outcome11'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as s:
  for b in iter(lambda:s.read(65536),b''):h.update(b)
 return h.hexdigest()
manifest=json.loads((N/'HELPERS_MANIFEST01.json').read_text())
for name,h in manifest['helpers'].items():assert sha(N/name)==h;ast.parse((N/name).read_text())
for name in ('capture','recover'):assert (O/(name+'11.py')).read_text().replace('11','13').replace('full27','full28')==(N/(name+'13.py')).read_text()
a=(O/'select11.py').read_text();b=(N/'select13.py').read_text()
# Strip exactly changing assignments/literal descriptions, leaving security and selection logic literal.
def normalized(s):
 lines=s.splitlines(True)
 return ''.join(x for x in lines if not x.startswith(('prior =','owned =','N=','scopes=','prior_selection=','assert sha(prior.parent/','    \'selection_rule\':','with (HERE/'))).replace('capture11.py','capture13.py').replace('recover11.py','recover13.py').replace('select11.py','select13.py')
assert normalized(a)==normalized(b)
t=ast.parse(b);assign={x.targets[0].id:x.value for x in t.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name)};owned=ast.literal_eval(assign['owned']);assert owned==manifest['owned_directories'] and len(owned)==len(set(owned))==36
assert all((F/name).is_dir() for name in owned)
namespace=ast.literal_eval(assign['N']);scopes=eval(compile(ast.Expression(assign['scopes']),'scope_literals','eval'),{'ROOT':R,'N':namespace,'__builtins__':{}});assert len(scopes)==7 and all(p.is_dir() and not p.is_symlink() for p in scopes)
prior=R/manifest['baseline_return'];v=json.loads(prior.read_text());cap_path=R/v['capture']['path'];assert sha(cap_path)==v['capture']['sha256'];cap=json.loads(cap_path.read_text());selection=prior.parent/'SELECTION12.json';assert sha(selection)==cap['selection']['sha256'];old=json.loads(selection.read_text());assert len({x['path'] for x in old['rows']})==len(old['rows']);assert v['source']==v['actual_fetch_head']==v['actual_remote_head'] and v['no_alternates'] is True and all(x['exit_code']==0 for x in v['operations'])
excluded=[R/cap['archive']['path'],R/v['returned_archive']['path'],prior.parent/'actual_external_archive_blob_return.stdout'];assert all(sha(p)==v['returned_archive']['sha256'] for p in excluded)
returned=F/'real-data-pilot-full28-group-fresh-return01-2026-10-09';group=json.loads((returned/'RETURN01.json').read_text());gp=Path(group['returned_path']);gp=gp if gp.is_absolute() else R/gp;assert sha(gp)==group['returned_sha256'];assert returned.name in owned and gp not in excluded
outcome=F/'real-data-pilot-full28-outcome-review01-2026-10-09/OUTCOME_REVIEW01.json';evidence=json.loads(outcome.read_text())['evidence']
# Actual opaque source-name lineage present in reviewed outcome metadata; no scientific bytes read.
assert all(any(str(p.relative_to(R)) in name for name in evidence) for p in [scopes[i] for i in (0,1,3,5)])
absent=[N/n for n in ('SELECTION13.json','CAPTURE13.json','FRESH_GIT_RECOVERY13.json','GIT_OPERATIONS13.json','failed-outcome-increment13.tar','fresh-git-recovered-outcome13.tar')]+[R.parent/'onchain-pilot-recovery/real-pilot-full28-outcome-20261009-13.git'];assert all(not os.path.lexists(p) for p in absent)
result={'capture_recover_literal_inverse':True,'selector_security_and_logic_literal_inverse':True,'owned_directories':36,'scope_states':[{'path':str(p.relative_to(R)),'exists':True} for p in scopes],'baseline_return':{'path':str(prior.relative_to(R)),'sha256':sha(prior)},'baseline_capture_sha256':sha(cap_path),'baseline_selection_sha256':sha(selection),'three_duplicate_hashes_joined':True,'original_group_return_included':True,'fresh_namespaces_absent':[str(p) for p in absent],'outcome_review_sha256':sha(outcome),'helpers':manifest['helpers']};(D/'RESULT02.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS')
