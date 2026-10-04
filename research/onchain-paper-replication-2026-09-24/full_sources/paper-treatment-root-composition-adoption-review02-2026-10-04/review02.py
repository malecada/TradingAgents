import copy,importlib.util,json,os,sys
from pathlib import Path
O=Path(__file__).resolve().parent;S=O.parent/'paper-treatment-root-composition-adoption-preparation02-2026-10-04';sys.path.insert(0,str(S));sp=importlib.util.spec_from_file_location('reviewed02',S/'recipe02.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M);pins=json.loads((S/'BASELINE01.json').read_bytes())['sources'];root=O/'owned-source-controls';results=[]
def refuse(name,f):
 try:f()
 except (ValueError,OSError) as e:results.append({'name':name,'reason':str(e)})
 else:raise AssertionError(name)
for rel in pins:
 q=copy.deepcopy(pins);q[rel+'/changed']=q.pop(rel);refuse('exact declared path '+rel,lambda:M.verify_source(root,q))
for field,v in [('sha256','0'*64),('bytes',0),('git_blob_oid','0'*40),('git_mode','120000')]:
 for rel in pins:
  q=copy.deepcopy(pins);q[rel][field]=v;refuse('exact '+field+' '+rel,lambda:M.verify_source(root,q))
p=root/'tradingagents/research/onchain_replication/job.py';hold=O/'retained-original-job';p.rename(hold);refuse('actual missing file',lambda:M.verify_source(root,pins));p.mkdir();refuse('actual directory replacing source',lambda:M.verify_source(root,pins));p.rename(O/'retained-directory-witness');p.symlink_to(hold);refuse('actual symlink replacing source',lambda:M.verify_source(root,pins));p.rename(O/'retained-symlink-witness');hold.rename(p)
parent=p.parent;held=O/'held-source-directory';parent.rename(held);parent.symlink_to(held);refuse('actual ancestor redirect',lambda:M.verify_source(root,pins));parent.rename(O/'retained-ancestor-symlink');held.rename(parent)
guards=json.loads((S/'SCIENTIFIC_GUARDS01.json').read_bytes())
for rel,pin in guards.items():
 actual=M.MAIN/rel;raw=M.bounded(actual);assert M.sha(raw)==pin['sha256'];results.append({'name':'unchanged actual scientific guard '+rel,'sha256':pin['sha256']})
M.verify_source(root,pins);(O/'CHECKS02.json').write_text(json.dumps({'count':len(results),'checks':results,'scope':'path/OID/size/hash/Git type and genuine owned filesystem refusal metadata only'},sort_keys=True,indent=2)+'\n');print(len(results))
