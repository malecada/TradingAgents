from pathlib import Path
import sys,json,subprocess,os
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import recover01 as R
p=D/'local02_owned';p.mkdir();R.HERE=p;origin=p/'origin.git';dest=p/'received.git'
R.git(['init','--bare',str(origin)])
blob=os.urandom(262144)
q=subprocess.run(['git','--git-dir',str(origin),'hash-object','-w','--stdin'],input=blob,capture_output=True,check=True);oid=q.stdout.decode().strip()
R.git(['init','--bare',str(dest)]);R.git(['fetch','--no-tags',str(origin),oid],dest);assert R.git(['cat-file','blob',oid],dest)==blob
assert len(R.CALLS)==4 and all(r['exit']==0 and r['cleanup_failures']==[] and r['actual_child_limits']['fsize']==[4194304,4194304] and not Path('/proc',str(r['pid'])).exists() for r in R.CALLS)
(D/'LOCAL02.json').write_text(json.dumps({'calls':R.CALLS,'samples':R.WATCHES,'initial':R.BASELINE,'local_blob_bytes':len(blob),'local_only':True,'external_release':False},sort_keys=True,indent=2)+'\n');print('PASS4')
