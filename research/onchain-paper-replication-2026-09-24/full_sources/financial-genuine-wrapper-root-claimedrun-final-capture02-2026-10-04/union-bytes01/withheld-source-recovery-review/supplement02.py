import hashlib,json,sys,zlib
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'financial-genuine-wrapper-claimedrun-source-recovery-preparation01-2026-10-04';sys.path.insert(0,str(P));import restore01 as S
from git_objects01 import tree_join
checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
C=H.parent/'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04';bodies={n:S.R.read(C,n) for n in S.EXPECTED}
for n,pin in S.EXPECTED.items():check(S.R.digest(bodies[n])==pin['sha256'] and len(bodies[n])==pin['bytes'],'actual fixed capture body '+n)
m,_,t=S.joins(bodies);check(len(m['members'])==1029 and sum(r['kind']=='file' for r in m['members'])==747,'actual fixed complete source metadata');check(t['current_equals_design']==S.SOURCE and t['new_claim_started'] is False and t['parent_or_final_review_captured'] is False,'actual source-only qualifications')
# Executable Git tree mode vs ordinary preserved file mode, independently owned.
d={}
def obj(kind,value):
 b=kind.encode()+b' '+str(len(value)).encode()+b'\0'+value;oid=hashlib.sha1(b).hexdigest();d['.git/objects/'+oid[:2]+'/'+oid[2:]]=zlib.compress(b);return oid
payload=b'opaque executable-mode witness';blob=obj('blob',payload);tree=obj('tree',b'100755 body\0'+bytes.fromhex(blob));commit=obj('commit',b'tree '+tree.encode()+b'\n\nmode witness\n');d['body']=payload;root=H/'mode-source';root.mkdir()
for n,b in d.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
(root/'body').chmod(0o600);manifest=S.R.scan(root);archive=S.R.pack(root,manifest,H/'mode.tar.gz');flat=H/'mode-flat';S.reserve(flat);res=S.R.restore(H/'mode.tar.gz',archive,manifest,flat);meta=json.loads(S.R.read(flat,res['metadata_file']));mapping=meta['flat_members'];joined=tree_join(lambda n:S.R.read(flat,mapping[n]),set(mapping),commit,1);row=next(r for r in manifest['members'] if r['path']=='body');check(joined['body'][0]=='100755' and row['mode']==0o600,'Git executable/literal mode mismatch accepted');check(not(row['mode']&0o111),'preserved ordinary mode actually non-executable')
out={'checks':len(checks),'check_names':checks,'witness':{'id':'SR3','commit':commit,'tree_mode':joined['body'][0],'actual_preserved_original_file_mode':row['mode'],'parser_accepted':True,'qualification':'The new parser authenticates Git mode syntax but does not compare Git executable class to the archived original mode. flat_source_joins discards returned mode tuples. Fixed actual archive remains independently pinned; this is omitted semantic validation, not proof of actual bad modes.'},'actual_capture_restored':False};(H/'SUPPLEMENT02.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out))
