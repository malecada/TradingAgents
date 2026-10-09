import copy,hashlib,json,subprocess
from pathlib import Path
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
anchor='1d23956e7057f11f1e57bf6c767a3a768981846f'
load=lambda name:json.loads((HERE/name).read_bytes())
raw=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def save(name,v):
 p=HERE/name
 with p.open('xb') as f:f.write(raw(v))
 return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
source=load('SOURCE_MANIFEST01.json');pins=source['current_source_pins'];assert subprocess.check_output(['git','rev-parse',anchor+'^{commit}'],text=True).strip()==anchor
names=sorted(pins);out=subprocess.check_output(['git','cat-file','--batch'],input=''.join(anchor+':'+n+'\n' for n in names).encode());pos=0
for n in names:
 end=out.index(b'\n',pos);fields=out[pos:end].split();assert len(fields)==3 and fields[1]==b'blob';size=int(fields[2]);pos=end+1;body=out[pos:pos+size];pos+=size;assert out[pos:pos+1]==b'\n';pos+=1
 assert hashlib.sha256(body).hexdigest()==pins[n]==hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),n
assert pos==len(out)
source['source_anchor']=anchor;save('SOURCE_MANIFEST02.json',source)
prepared=load('PREPARATION01.json');docs=prepared['builder03_result']['inputs'];docs['pair_policy']['numerical_source']['commit']=anchor
for v in [docs['execution_job']['payload']['representation_jobs']['original32'],docs['producer_plan']['producers']['original32']]:v['descriptor']['pair_execution']['policy_sha256']=hashlib.sha256(raw(docs['pair_policy'])).hexdigest()
(HERE/'public02').mkdir();refs=load('PUBLIC_INPUT_REFS01.json');pub={}
for role,value in docs.items():
 pub[role]=save('public02/'+role+'.json',value);refs[role]={**pub[role],'dataset':refs[role]['dataset']}
save('PUBLIC_INPUT_REFS02.json',refs)
public=load('PUBLIC_MANIFEST01.json');public.update(source_anchor=anchor,public_inputs=pub,builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());save('PUBLIC_MANIFEST02.json',public)
prepared['unresolved'].pop('numerical_source_commit');prepared['source_anchor']=anchor;prepared['remaining_root_work'][0]='Exact current committed source anchor authenticated; Root registration/review must bind these source bodies and metadata.';save('PREPARATION02.json',prepared)
save('ANCHOR_CHECK02.json',{'status':'PASS_SOURCE_BODY_JOIN_ONLY','anchor':anchor,'admitted_source_files':len(pins),'numerical_source_files':len(source['numerical_sources']),'all_anchor_and_current_bodies_equal':True,'authority_or_recovery_claim':False})
print('PASS actual Git blob and current body joins',len(pins),anchor)
