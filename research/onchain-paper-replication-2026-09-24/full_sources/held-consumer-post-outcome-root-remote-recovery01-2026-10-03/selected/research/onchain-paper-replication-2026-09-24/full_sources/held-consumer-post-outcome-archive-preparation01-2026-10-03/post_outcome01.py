"""One-use append-only byte capture. Root proves quiescence; no research authority."""
import argparse
import json
import os
import shutil
from pathlib import Path
import recovery04 as R

BASELINE_SHA256 = '660a715bc4da9bfd93e4076cee4d82730301024b9fa95668c8182a48d9ac2061'
PARENT = '/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-root-launch-20261003-01'
IDENTITY = 'original-import-held-success-20261003-01'
ROLES = ('capsule', 'external')
EVIDENCE = ('terminal', 'cleanup', 'closed_tree_review')
HELPER_SHA256 = 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'

def subset(original, current):
    """Pure manifest predicate; all original directories and files remain exact."""
    R.validate(original)
    R.validate(current)
    R.require(original['root_mode'] == current['root_mode'], 'baseline root mode changed')
    old = {r['path']: r for r in original['members']}
    now = {r['path']: r for r in current['members']}
    R.require(all(now.get(p) == row for p, row in old.items()), 'original baseline member changed or absent')
    return {'original_members': len(old), 'current_members': len(now),
            'added_members': len(now)-len(old),
            'added_regular_files': sum(row['kind']=='file' for p,row in now.items() if p not in old)}

def pin(value):
    R.require(type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value), 'SHA256 required')

def canonical_path(value):
    R.require(type(value) is str, 'path string')
    p = Path(value)
    R.path_name(str(p).lstrip('/'))
    R.require(p.is_absolute() and p.resolve()==p, 'canonical path')
    return p

def load_ref(ref):
    R.require(type(ref) is dict and set(ref)=={'path','sha256'}, 'exact body reference')
    pin(ref['sha256'])
    p = canonical_path(ref['path'])
    raw = R.read(p.parent,p.name)
    R.require(R.digest(raw)==ref['sha256'], 'referenced body hash differs')
    return raw

def request(q):
    fields={'schema_version','identity','baseline','baseline_sha256','current_manifests',
            'current_manifest_sha256','evidence','support_bodies','output_root'}
    R.require(type(q) is dict and set(q)==fields and type(q['schema_version']) is int and q['schema_version']==1, 'request schema')
    R.require(q['identity']==IDENTITY and q['baseline_sha256']==BASELINE_SHA256, 'fixed identity/baseline')
    R.require(R.digest(R.encode(q['baseline']))==BASELINE_SHA256, 'original final950 baseline pin')
    b=q['baseline']
    # request() only validates the supplied original metadata; it does not scan roots.
    R.request(b)
    R.require(b['external_root']==PARENT, 'fixed Parent03 root')
    R.require(set(q['current_manifests'])==set(ROLES)==set(q['current_manifest_sha256']), 'two complete inventories')
    changes={}
    for role in ROLES:
        m=q['current_manifests'][role]
        pin(q['current_manifest_sha256'][role])
        R.require(R.digest(R.encode(m))==q['current_manifest_sha256'][role], 'current manifest pin')
        changes[role]=subset(b[role+'_manifest'],m)
    R.require(sum(row.get('bytes',0) for m in q['current_manifests'].values() for row in m['members'])<=R.BASE, 'combined current logical128MiB')
    R.require(type(q['evidence']) is dict and set(q['evidence'])==set(EVIDENCE), 'terminal/cleanup/review references required')
    roots=[canonical_path(b['capsule_root']),canonical_path(PARENT),canonical_path(q['output_root'])]
    R.require(all(not a.is_relative_to(c) for i,a in enumerate(roots) for j,c in enumerate(roots) if i!=j), 'nonrecursive roots')
    R.require(type(q['support_bodies']) is dict and len(q['support_bodies'])<=256, 'finite extra Root stream bodies')
    for name in q['support_bodies']:
        R.require(type(name) is str and name and len(name)<=80 and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in name), 'support role name')
    for ref in list(q['evidence'].values())+list(q['support_bodies'].values()):
        R.require(type(ref) is dict and set(ref)=={'path','sha256'}, 'evidence reference shape')
        pin(ref['sha256']);p=canonical_path(ref['path'])
        R.require(not p.is_relative_to(roots[2]), 'evidence cannot depend on new archive')
    return roots,changes

def evidence(q, bodies):
    """Authenticate genuine supplied evidence bytes. Never invent missing evidence.

    This is a Root/reviewer evidence contract, not a live process enumerator. The
    independent review states the actual terminal and whole-tree cleanup joins.
    Outcome values do not authorize dependent execution or imply model success.
    """
    R.require(set(bodies)==set(EVIDENCE), 'evidence bodies')
    for name,raw in bodies.items():
        R.require(len(raw)<=R.FILE and R.digest(raw)==q['evidence'][name]['sha256'], 'evidence body pin')
    review=json.loads(bodies['closed_tree_review'])
    fields={'schema_version','decision','identity','source','baseline_sha256',
            'current_manifest_sha256','terminal_sha256','cleanup_sha256',
            'processes_absent','cgroup_absent','writer_quiescence_verified','support_sha256','outcome'}
    R.require(type(review) is dict and set(review)==fields and type(review['schema_version']) is int and review['schema_version']==1, 'closed-tree review schema')
    R.require(review['decision']=='accepted-closed-tree-byte-preservation' and review['identity']==IDENTITY and review['source']==R.SOURCE, 'closed-tree decision identity')
    R.require(review['baseline_sha256']==BASELINE_SHA256 and review['current_manifest_sha256']==q['current_manifest_sha256'], 'review inventory joins')
    R.require(review['terminal_sha256']==q['evidence']['terminal']['sha256'] and review['cleanup_sha256']==q['evidence']['cleanup']['sha256'], 'review actual evidence joins')
    R.require(all(review[k] is True for k in ('processes_absent','cgroup_absent','writer_quiescence_verified')), 'closed tree required; absent/unknown processes refuse')
    R.require(review['support_sha256']=={n:r['sha256'] for n,r in q['support_bodies'].items()}, 'review complete support joins')
    R.require(review['outcome'] in ('COMPLETE','FAILED','UNAVAILABLE','UNKNOWN'), 'explicit noncoerced outcome')
    return review

def capture(q):
    roots,changes=request(q)
    cap,parent,out=roots
    R.require(not os.path.lexists(out),'capture identity already reserved')
    R.require(shutil.disk_usage(out.parent).free>=R.FLOOR,'10GiB floor')
    bodies={name:load_ref(q['evidence'][name]) for name in EVIDENCE}
    decision=evidence(q,bodies)
    support={name:load_ref(ref) for name,ref in q['support_bodies'].items()}
    R.require(sum(row.get('bytes',0) for m in q['current_manifests'].values() for row in m['members'])+sum(map(len,bodies.values()))+sum(map(len,support.values()))<=R.BASE, 'whole logical128MiB including outside evidence')
    R.require(R.digest(R.read(Path(__file__).resolve().parent,'recovery04.py'))==HELPER_SHA256,'accepted primitive source differs')
    for role,root in zip(ROLES,(cap,parent)):R.same(root,q['current_manifests'][role])
    # The unchanged ORIGINAL baseline retains288 as a baseline statement only.
    # All current source/Git/input bytes are authenticated by the original code.
    source_join=R.authenticate_source(cap,q['baseline'])
    allocated=sum(root.lstat().st_blocks*512+sum((root/r['path']).lstat().st_blocks*512 for r in q['current_manifests'][role]['members']) for role,root in zip(ROLES,(cap,parent)))
    allocated+=sum(Path(ref['path']).lstat().st_blocks*512 for ref in list(q['evidence'].values())+list(q['support_bodies'].values()))
    R.require(allocated<=R.BASE,'combined current allocated128MiB including outside evidence')
    out.mkdir(mode=0o700)
    archives={}
    for role,root in zip(ROLES,(cap,parent)):
        archives[role]=R.pack(root,q['current_manifests'][role],out/(role+'.tar.gz'))
        R.put(out/(role+'-manifest.json'),q['current_manifests'][role])
        R.require(shutil.disk_usage(out).free>=R.FLOOR,'capture floor')
    for name in EVIDENCE:
        # Exact raw receipt bodies are retained; arbitrary terminal formats allowed.
        R.require(load_ref(q['evidence'][name])==bodies[name], 'evidence changed during capture')
        with R.new_file(out/(name+'.body')) as fd:
            sink=R.Sink(fd);sink.write(bodies[name]);os.fsync(fd)
    for name,body in support.items():
        R.require(load_ref(q['support_bodies'][name])==body, 'support changed during capture')
        with R.new_file(out/('support-'+name+'.body')) as fd:
            sink=R.Sink(fd);sink.write(body);os.fsync(fd)
    for role,root in zip(ROLES,(cap,parent)):R.same(root,q['current_manifests'][role])
    receipt={'schema_version':1,'identity':IDENTITY,'source':R.SOURCE,
             'request_sha256':R.digest(R.encode(q)),'archives':archives,'subset':changes,
             'original_source_join':source_join,'evidence_sha256':{n:q['evidence'][n]['sha256'] for n in EVIDENCE},
             'support_sha256':{n:q['support_bodies'][n]['sha256'] for n in support},
             'reported_outcome':decision['outcome'],'scope':'complete closed supplied trees and evidence bytes; no scientific or recovery authority'}
    R.put(out/'capture.json',receipt)
    R.require(shutil.disk_usage(out).free>=R.FLOOR,'final capture floor')
    return receipt

def recover(bundle,capture_sha256,q,request_sha256,destination):
    roots,changes=request(q);pin(capture_sha256);pin(request_sha256)
    R.require(R.digest(R.encode(q))==request_sha256,'request pin')
    bundle=canonical_path(str(bundle));destination=canonical_path(str(destination))
    R.require(all(not destination.is_relative_to(p) and not p.is_relative_to(destination) for p in [bundle]+roots),'separate flat namespace')
    raw=R.read(bundle,'capture.json');R.require(R.digest(raw)==capture_sha256,'actual capture pin');receipt=json.loads(raw)
    fields={'schema_version','identity','source','request_sha256','archives','subset','original_source_join','evidence_sha256','support_sha256','reported_outcome','scope'}
    R.require(set(receipt)==fields and R.encode(receipt)==raw and type(receipt['schema_version']) is int and receipt['schema_version']==1 and receipt['identity']==IDENTITY and receipt['source']==R.SOURCE and receipt['request_sha256']==request_sha256 and set(receipt['archives'])==set(ROLES) and receipt['subset']==changes,'actual capture contract')
    R.require(receipt['original_source_join']=={'source':R.SOURCE,'committed_source_registration_bodies':205,'registered_inputs':33,'tracked_files':246,'nonGit_files':288},'original source join shape')
    bodies={name:R.read(bundle,name+'.body') for name in EVIDENCE}
    decision=evidence(q,bodies)
    support={name:R.read(bundle,'support-'+name+'.body') for name in q['support_bodies']}
    R.require(receipt['support_sha256']=={n:R.digest(body) for n,body in support.items()}=={n:ref['sha256'] for n,ref in q['support_bodies'].items()}, 'recovered support bytes')
    R.require(sum(row.get('bytes',0) for m in q['current_manifests'].values() for row in m['members'])+sum(map(len,bodies.values()))+sum(map(len,support.values()))<=R.BASE, 'whole recovered logical128MiB')
    R.require(receipt['evidence_sha256']=={n:q['evidence'][n]['sha256'] for n in EVIDENCE} and receipt['reported_outcome']==decision['outcome'],'capture evidence joins')
    R.require(shutil.disk_usage(destination).free>=R.FLOOR,'recovery floor')
    output=R.FlatOutput(destination);results={}
    try:
        output.begin()
        for role in ROLES:
            raw=R.read(bundle,role+'-manifest.json')
            R.require(raw==R.encode(q['current_manifests'][role]),'full current manifest exact bytes')
            results[role]=R.restore(bundle/(role+'.tar.gz'),receipt['archives'][role],q['current_manifests'][role],output,prefix=role)
            R.require(shutil.disk_usage(destination).free>=R.FLOOR,'recovery floor')
        for name in EVIDENCE:output.create(name+'.body',bodies[name])
        for name,body in support.items():output.create('support-'+name+'.body',body)
        result={'schema_version':1,'status':'fresh-flat-post-outcome-archival-recovery-not-origin-proof',
                'capture_sha256':capture_sha256,'request_sha256':request_sha256,'results':results,
                'subset':changes,'reported_outcome':decision['outcome'],'support_sha256':receipt['support_sha256'],
                'instantiated_posix_tree':False,'recovered_tree_git_join':False,
                'runtime_package_bodies_recovered':False,'outside_stores_recovered':False,
                'research_authority':False,'scientific_representation_complete':False}
        output.create('recovery.json',R.encode(result));output.finish()
        R.require(shutil.disk_usage(destination).free>=R.FLOOR,'final recovery floor')
        return result
    finally:R._cleanup((output.close,))

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',required=True,choices=('capture','recover'))
    p.add_argument('--request',type=Path,required=True);p.add_argument('--request-sha256',required=True)
    p.add_argument('--bundle',type=Path);p.add_argument('--capture-sha256');p.add_argument('--destination',type=Path)
    a=p.parse_args();raw=R.read(a.request.parent.resolve(),a.request.name)
    R.require(R.digest(raw)==a.request_sha256,'explicit request pin');q=json.loads(raw);R.require(raw==R.encode(q),'canonical request')
    if a.mode=='capture':capture(q)
    else:
        R.require(a.bundle is not None and a.capture_sha256 is not None and a.destination is not None,'explicit recovery pins')
        recover(a.bundle,a.capture_sha256,q,a.request_sha256,a.destination)

if __name__=='__main__':main()
