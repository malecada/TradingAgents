import ast,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;P=B.parent/'paper-treatment-root-composition-preparation01-2026-10-04';D=P/'origin-evidence';C=P/'candidate/tradingagents/research/onchain_replication';checks=[]
def h(s):return hashlib.sha256(s.encode()).hexdigest()
def ok(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def inverse(source,edits):
 for e in reversed(edits):
  ok(source.count(e['new'])==1,'unique inherited inverse');source=source.replace(e['new'],e['old'])
 return source
def exact(source,path,label):ok(source==path.read_text() and ast.dump(ast.parse(source))==ast.dump(ast.parse(path.read_text())),label)
# Producer corrected observer + original four job substitutions restore exact Main.
s=(C/'job.py').read_text();correction=json.loads((D/'producer/CORRECTION_INVERSE02.json').read_text());s=inverse(s,correction['job']);j=json.loads((D/'producer/JOB_INVERSE01.json').read_text());s=inverse(s,j['changes']);ok(h(s)==j['baseline_sha256'],'full job original Main hash');exact(s,P/'baseline/tradingagents/research/onchain_replication/job.py','full job byte/AST inverse to Main')
# Producer TP3 and T1/T2 chain, retaining original producer01 module.
s=(C/'treatment_production.py').read_text();tp=json.loads((D/'producer/TP3_INVERSE01.json').read_text());s=inverse(s,[tp['exact_change']]);ok(h(s)==tp['old_sha256'],'TP3 predecessor hash');s=inverse(s,correction['producer']);exact(s,B.parent/'paper-treatment-production-preparation01-2026-10-04/overlay/tradingagents/research/onchain_replication/treatment_production.py','full producer correction chain byte/AST inverse')
# Admission composition + DA4 + DA1-3 all invert to original withheld module.
s=(C/'treatment_admission.py').read_text();composition=json.loads((P/'COMPOSITION_INVERSE01.json').read_text());s=inverse(s,composition['edits']);da4=json.loads((D/'consumer/DA4_INVERSE01.json').read_text());s=inverse(s,[da4]);ok(h(s)==da4['old_sha256'],'DA4 predecessor hash');da123=json.loads((D/'consumer/CORRECTION_INVERSE01.json').read_text());s=inverse(s,da123['edits']);ok(h(s)==da123['baseline_sha256'],'DA1-3 predecessor hash');exact(s,B.parent/'paper-treatment-fit-admission-preparation01-2026-10-04/overlay/tradingagents/research/onchain_replication/treatment_admission.py','full admission chain byte/AST inverse')
# Three existing scientific call sites reverse to exactly current135 baseline.
for row in json.loads((D/'consumer/DELTA_INVERSE01.json').read_text()):
 s=(P/'candidate'/row['path']).read_text();s=inverse(s,row['edits']);ok(h(s)==row['original_sha256'],'original caller hash');exact(s,P/'baseline'/row['path'],'full caller byte/AST inverse '+row['path'])
(B/'INVERSE_CHECKS02.json').write_text(json.dumps({'status':'passed','checks':len(checks),'labels':checks,'scope':'full exact source inverse chains only; no implementation imported or executed'},sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks)}))
