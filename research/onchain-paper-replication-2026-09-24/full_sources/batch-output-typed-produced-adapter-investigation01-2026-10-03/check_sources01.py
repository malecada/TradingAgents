"""Read-only source authentication/AST indexing; no selected module imports."""
import ast, hashlib, json, os, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[3]
FULL=HERE.parent
SOURCE=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-03/source')
HEAD='903488c49ad25e8026ec849a1c8b30ca5f90bcff'
ENV=os.environ|{'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0'}
def git(*args):
 return subprocess.run(['git','-c','protocol.allow=never','-C',str(SOURCE),*args],env=ENV,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15).stdout
def digest(b):return hashlib.sha256(b).hexdigest()
assert git('rev-parse','HEAD').decode().strip()==HEAD
names=['compact_owner','compact_mcm','compact_mcm_output','compact_mcm_publication','compact_features','compact_graph_artifacts','compact_publication','compact_terminal','compact_cold_features','compact_native_features','held_score_consumer','imported_mcm_identity','mcm_score_stream','owned_io']
rows=[]
def add(path,origin):
 body=path.read_bytes();tree=ast.parse(body)
 definitions=[]
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
   definitions.append({'name':node.name,'line':node.lineno,'end_line':node.end_lineno})
   if isinstance(node,ast.ClassDef):
    definitions.extend({'name':node.name+'.'+v.name,'line':v.lineno,'end_line':v.end_lineno} for v in node.body if isinstance(v,(ast.FunctionDef,ast.AsyncFunctionDef)))
 rows.append({'path':str(path),'bytes':len(body),'sha256':digest(body),'origin':origin,'definitions':definitions})
for name in names:
 rel=f'tradingagents/research/onchain_replication/{name}.py';path=SOURCE/rel
 assert path.read_bytes()==git('show',HEAD+':'+rel)
 add(path,{'git_commit':HEAD,'git_path':rel,'current_equals_committed':True})
rel='research/onchain-paper-replication-2026-09-24/full_sources/neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03/held_score_reader.py'
assert (SOURCE/rel).read_bytes()==git('show',HEAD+':'+rel)
add(SOURCE/rel,{'git_commit':HEAD,'git_path':rel,'current_equals_committed':True})
manifests=[]
for directory,manifest,expected,selected in [
 ('batch-output-durable-context-preparation03-2026-10-03','MANIFEST03.json','390d282f8d5a4737afc55d16d85b8221a54bd2bef3918883f0233238e2dcaff3',['archive_non_tail.py']),
 ('financial-streamed-execution-candidate02-2026-10-02','manifest02.json','dfb5ff9f6de051cf163436139190c360eca09d45c3b1102778431c1d87f86000',['financial_execution.py','training.py','checkpoints.py','run.py'])]:
 base=FULL/directory;raw=(base/manifest).read_bytes();assert digest(raw)==expected
 values=json.loads(raw)['files'];items=values if isinstance(values,list) else [dict(v,path=k) for k,v in values.items()]
 for item in items:
  b=(base/item['path']).read_bytes();assert len(b)==item['bytes'] and digest(b)==item['sha256'],item['path']
 manifests.append({'path':str(base/manifest),'sha256':expected,'verified_bodies':len(items)})
 for name in selected:add(base/name,{'frozen_manifest':str(base/manifest),'manifest_sha256':expected,'installed_in_source03':False})
result={'scope':'Source bytes/AST only; no numeric or authority execution','source03':str(SOURCE),'head':HEAD,'sources':rows,'manifests':manifests,'numeric_imports':False,'array_reads':False,'jobs':0}
(HERE/'SOURCE_REFERENCES01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'verified_source_bodies':len(rows),'manifests':manifests,'source03_head':HEAD,'numeric_imports':False,'jobs':0},indent=2))
