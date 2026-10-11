"""Root-only post-install/commit public joins; never binder/admission/launch."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
def raw(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
def updated_documents(docs,mcm,files,commit):
    # Caller supplies fresh parsed copies of authenticated public baselines.
    old=hashlib.sha256(raw(docs['pair_policy'])).hexdigest()
    docs['pair_policy']['numerical_source']={'commit':commit,'files':files}
    new=hashlib.sha256(raw(docs['pair_policy'])).hexdigest()
    count=0
    def join(value):
        nonlocal count
        if isinstance(value,dict):
            if 'pair_execution' in value:
                entry=value['pair_execution'];assert entry['policy_sha256']==old
                entry['policy_sha256']=new;count+=1
            for child in value.values():join(child)
        elif isinstance(value,list):
            for child in value:join(child)
    join(docs['producer_plan']);join(docs['execution_job']);assert count==2
    docs['mcm_policy']=mcm
    return docs

def main(commit):
    assert re.fullmatch('[0-9a-f]{40}',commit),'actual committed source anchor required'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==commit
    files=json.loads((P/'PROSPECTIVE_NUMERICAL_FILES01.json').read_bytes())
    # Exact committed blob joins, same bounded batch transport as existing public builder.
    request=''.join(commit+':'+name+'\n' for name in files).encode()
    body=subprocess.check_output(['git','-c','core.packedGitWindowSize=16m','-c','core.packedGitLimit=64m','cat-file','--batch'],input=request,cwd=ROOT,timeout=30)
    offset=0
    for name,digest in files.items():
        end=body.index(b'\n',offset);header=body[offset:end].split();assert len(header)==3 and header[1]==b'blob'
        size=int(header[2]);assert 0<size<=4*1024**2;offset=end+1;blob=body[offset:offset+size];offset+=size
        assert body[offset:offset+1]==b'\n';offset+=1
        assert hashlib.sha256(blob).hexdigest()==digest and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    assert offset==len(body)
    plan=json.loads((P/'INSTALLATION_PLAN01.json').read_bytes());docs={}
    for name,reference in plan['public_metadata_baselines'].items():
        path=ROOT/reference['path'];content=path.read_bytes();assert len(content)==reference['bytes'] and hashlib.sha256(content).hexdigest()==reference['sha256'];docs[Path(name).stem]=json.loads(content)
    mcm=json.loads((P/'MCM_POLICY_TEMPLATE01.json').read_bytes())
    docs=updated_documents(docs,mcm,files,commit)
    out=P/'committed-public-joins01';out.mkdir(mode=0o700,exist_ok=False)
    for name,value in docs.items():
        with (out/(name+'.json')).open('xb') as stream:stream.write(raw(value))
    refs={name:{'path':str((out/(name+'.json')).relative_to(ROOT)),'sha256':hashlib.sha256(raw(value)).hexdigest()} for name,value in docs.items()}
    with (out/'PUBLIC_REFS01.json').open('x') as stream:json.dump(refs,stream,indent=2,sort_keys=True);stream.write('\n')
    print('PUBLIC_SOURCE_JOINS_ONLY: inherited spent34 identities are NOT a new launch; Root must use the fresh public binder/preparation route.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-commit',required=True);main(parser.parse_args().source_commit)
