"""Reviewed offline synthetic targets only; no empirical entry point imports."""
import hashlib,json,pathlib,re,subprocess,sys
p=pathlib.Path(__file__).parent
label=sys.argv[1] if len(sys.argv)>1 else 'independent'
assert re.fullmatch(r'[a-z0-9_-]{1,32}',label)
results=[]
for name in ['test_selection01.py','test_transport01.py','test_controls01.py','test_roundtrip01.py']:
 r=subprocess.run([sys.executable,'-B',str(p/name)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20)
 raw=r.stdout;log=p/(name+'.'+label+'.log')
 with log.open('xb') as stream:stream.write(raw)
 results.append({'test':name,'exit_code':r.returncode,'log':log.name,'sha256':hashlib.sha256(raw).hexdigest()})
print(json.dumps({'source_only':True,'actual_network':False,'checks':results},sort_keys=True))
assert all(r['exit_code']==0 for r in results)
