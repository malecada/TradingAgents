"""One-use, topology-only seven-graph preparation; no research lifecycle/model.

Before/after hashes and stat checks are sampled observations, not writer exclusion.
Only edge endpoints are decoded. Node IDs are header/stat corroboration only;
features, labels and historical sample bodies are never opened.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import stat
import sys
import time
import types
import numpy as np

HELPER='tradingagents/research/onchain_replication/weak_one_hop_census.py'
WORK=256*1024**2
QUALIFICATION='Sampled before/after identity and byte checks do not exclude concurrent writers or changes restored between observations. Node IDs are not decoded or body-hash-verified. Helper work envelope excludes input mmap, interpreter, allocator and kernel cache; native monitor owns RSS/cgroup evidence.'

def require(ok,why):
    if not ok:raise ValueError(why)

def identity(s):return dict(device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,nlink=s.st_nlink)

def path(root,name):
    q=Path(name);require(not q.is_absolute() and '..' not in q.parts,'input path must be repository relative')
    p=root/q;require(p.resolve(strict=True)==p,'input symlink or noncanonical path')
    return p

def snapshot(p,expected=None,*,body=True):
    before=p.lstat();require(stat.S_ISREG(before.st_mode) and before.st_nlink==1,'single regular input required')
    with p.open('rb') as f:
        require(identity(os.fstat(f.fileno()))==identity(before),'input identity changed on open')
        digest=hashlib.sha256()
        if body:
            while block:=f.read(1024**2):digest.update(block)
        after=os.fstat(f.fileno())
    require(identity(before)==identity(after)==identity(p.lstat()),'input changed during observation')
    record={'stat':identity(after)}
    if body:record['sha256']=digest.hexdigest()
    if expected is not None:
        require(after.st_size==expected['bytes'],'input byte length differs')
        if body:require(record['sha256']==expected['sha256'],'input hash differs')
    return record

def metadata(root,ref):
    p=path(root,ref['path']);require(p.stat().st_size<=1024**2,'metadata exceeds1MiB')
    observed=snapshot(p,ref);b=p.read_bytes()
    require(hashlib.sha256(b).hexdigest()==ref['sha256'] and identity(p.lstat())==observed['stat'],'metadata changed during decode')
    return json.loads(b),observed

def header(p,ref):
    observed=snapshot(p,ref,body=False)
    with p.open('rb') as f:
        version=np.lib.format.read_magic(f)
        require(version in [(1,0),(2,0)],'unsupported NPY header version')
        reader=np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0
        shape,order,dtype=reader(f,max_header_size=4096);end=f.tell();f.seek(0);head=f.read(end)
        require(identity(os.fstat(f.fileno()))==observed['stat'],'header input changed')
    require(not dtype.hasobject and dtype.str==ref['dtype'] and list(shape)==ref['shape'] and order is ref['fortran_order'],'NPY metadata differs')
    elements=1
    for n in shape:elements*=n
    require(end+elements*dtype.itemsize==ref['bytes'],'NPY size or trailing data differs')
    require(identity(p.lstat())==observed['stat'],'header identity changed')
    return observed|{'header_bytes':end,'header_sha256':hashlib.sha256(head).hexdigest()}

def load_helper(root,digest):
    p=path(root,HELPER);b=p.read_bytes();require(hashlib.sha256(b).hexdigest()==digest,'helper source hash differs')
    # Execute the exact adopted, pinned module body without importing ResearchRun.
    module=types.ModuleType('pinned_weak_one_hop_census');exec(compile(b,str(p),'exec'),module.__dict__);return module

def write(p,value):
    b=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode();require(len(b)<4*1024**2,'JSON output exceeds4MiB')
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())

def timing(start,cpu):
    return dict(elapsed_seconds=time.monotonic()-start,process_cpu_seconds=time.process_time()-cpu,ru_maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,rss_qualification='Linux process lifetime high-water RSS, not graph-only or cgroup charged peak; no subtraction of high-water values.')

def independent_counts(edge,counts,maximum,chunk):
    checks=[]
    for center in sorted({0,maximum}):
        neighbors={center}
        for lo in range(0,edge.shape[1],chunk):
            u,v=edge[:,lo:lo+chunk]
            neighbors.update(v[u==center].tolist());neighbors.update(u[v==center].tolist())
            require(len(neighbors)<=len(counts),'independent neighbor set exceeds node universe')
        expected=len(neighbors);require(expected==int(counts[center]),'independent per-center cardinality differs')
        checks.append(dict(center_index=center,independent_cardinality=expected,returned_cardinality=int(counts[center])))
        del neighbors
    return checks

def graph(root,row,output,helper,settings):
    start=time.monotonic();cpu=time.process_time();observations={};chunks=[];mm=view=None
    try:
        manifest,observations['manifest']=metadata(root,row['manifest'])
        count,observations['node_count']=metadata(root,row['node_count_reference'])
        require(manifest['graph_hash']==row['graph_hash'],'graph hash label differs')
        require(count['schema_version']==1 and count['kind']=='graph-node-count-metadata-v1' and count['rows']==row['node_count'],'node count differs')
        require(count['graph_manifest_sha256']==row['manifest']['sha256'] and count['node_features_sha256']==manifest['arrays']['node_features']['sha256'],'count manifest/feature pin differs')
        mp=path(root,row['manifest']['path'])
        for name in ['edge_index','node_ids']:
            pin=manifest['arrays'][name];ref=row[name];p=path(root,ref['path'])
            require(p==mp.parent/pin['path'] and pin['sha256']==ref['sha256'] and pin['bytes']==ref['bytes'],'manifest companion differs')
            observations[name+'_header']=header(p,ref)
        require(row['node_ids']['shape']==[row['node_count']],'node header/count differs')
        edge=path(root,row['edge_index']['path']);observations['edge_index']=snapshot(edge,row['edge_index'])
        with edge.open('rb') as fd:
            require(identity(os.fstat(fd.fileno()))==observations['edge_index']['stat'],'edge descriptor identity differs')
            # /proc pins the existing descriptor; np.load cannot follow a replaced pathname.
            mm=np.load('/proc/self/fd/'+str(fd.fileno()),mmap_mode='r',allow_pickle=False,max_header_size=4096)
            view=mm.view(np.ndarray);view.flags.writeable=False
            require(type(view) is np.ndarray and not view.flags.writeable and view.shape==tuple(row['edge_index']['shape']) and view.dtype.str==row['edge_index']['dtype'],'mapped edge metadata differs')
            census_start=time.monotonic();census_cpu=time.process_time()
            result=helper.census(view,row['node_count'],max_work_bytes=settings['max_work_bytes'],chunk_edges=settings['chunk_edges'])
            result['helper_elapsed_seconds']=time.monotonic()-census_start;result['helper_process_cpu_seconds']=time.process_time()-census_cpu
            result['independent_center_checks']=independent_counts(view,result['cardinalities'],result['maximum_center_index'],settings['chunk_edges'])
            result['independent_check_memory_qualification']='Sequential Python incident-neighbor set bounded by node_count; Python object memory is outside helper numeric-array envelope and contained by Root native controls.'
            require(identity(os.fstat(fd.fileno()))==observations['edge_index']['stat'],'edge descriptor changed during census')
        counts=result.pop('cardinalities');require(counts.dtype==np.dtype('int64') and counts.shape==(row['node_count'],),'census count output differs')
        after={}
        for name,ref in [('manifest',row['manifest']),('node_count',row['node_count_reference']),('edge_index',row['edge_index'])]:
            after[name]=snapshot(path(root,ref['path']),ref);require(after[name]==observations[name],'input changed across census')
        for name in ['edge_index','node_ids']:
            after[name+'_header']=header(path(root,row[name]['path']),row[name]);require(after[name+'_header']==observations[name+'_header'],'header changed across census')
        # Publish counts only after all rechecks. Partial files survive any later failure.
        for lo in range(0,len(counts),settings['chunk_centers']):
            hi=min(lo+settings['chunk_centers'],len(counts));p=output/f'cardinalities-{lo:012d}-{hi:012d}.npy'
            with p.open('xb') as f:np.save(f,counts[lo:hi],allow_pickle=False);f.flush();os.fsync(f.fileno())
            require(p.stat().st_size<=4*1024**2,'cardinality chunk exceeds4MiB')
            pin=snapshot(p);chunks.append(dict(path=str(p.relative_to(output.parent)),start_center=lo,stop_center=hi,bytes=p.stat().st_size,sha256=pin['sha256']))
        record=dict(status='completed',**result,chunks=chunks,inputs_before=observations,inputs_after=after,**timing(start,cpu))
    except BaseException as exc:
        rechecks={}
        for name,ref in [('manifest',row['manifest']),('node_count',row['node_count_reference']),('edge_index',row['edge_index'])]:
            try:
                observed=snapshot(path(root,ref['path']));observed['matches_declared']=observed['sha256']==ref['sha256'] and observed['stat']['bytes']==ref['bytes'];rechecks[name]=observed
            except BaseException as error:rechecks[name]={'error':type(error).__name__+': '+str(error)}
        record=dict(status='failed',reason=type(exc).__name__+': '+str(exc),chunks=chunks,inputs_before=observations,failure_rechecks=rechecks,partial_output_names=sorted(p.name for p in output.iterdir()),**timing(start,cpu))
    finally:
        view=None
        if mm is not None:
            try:mm._mmap.close()
            except BaseException as error:
                record['cleanup_error']=type(error).__name__+': '+str(error)
                if record['status']=='completed':record['status']='failed';record['reason']='mmap cleanup failed; completed calculation not admitted'
    return record

def run(root,settings_path,settings_sha256,output):
    root=Path(root).resolve(strict=True);settings_path=Path(settings_path).resolve(strict=True);output=Path(output).absolute()
    require(output.parent.resolve(strict=True)==output.parent,'output parent must already exist without symlinks')
    source=Path(__file__).resolve();settings_bytes=settings_path.read_bytes()
    require(hashlib.sha256(settings_bytes).hexdigest()==settings_sha256,'settings hash differs')
    settings=json.loads(settings_bytes)
    require(settings['schema_version']==1 and settings['kind']=='topology-only-seven-graph-census-v1','settings schema differs')
    require(settings['max_work_bytes']==WORK and settings['chunk_edges']==65536 and settings['chunk_centers']==262144,'fixed caller work/chunk settings differ')
    require(hashlib.sha256(source.read_bytes()).hexdigest()==settings['caller_sha256'],'caller source differs')
    rows,input_observation=metadata(root,settings['inputs'])
    require(type(rows) is list and len(rows)==7,'exactly seven graph rows required')
    require(len({r['graph_hash'] for r in rows})==len({r['manifest']['path'] for r in rows})==7,'seven distinct graphs required')
    for r in rows:
        require(type(r['node_count']) is int and 0<r['node_count']<=2**32,'node count invalid')
        shape=r['edge_index']['shape'];require(len(shape)==2 and shape[0]==2 and type(shape[1]) is int and shape[1]>=0,'edge shape invalid')
        dtype=np.dtype(r['edge_index']['dtype']);require(dtype.kind in 'iu' and dtype.itemsize<=8,'integer edge dtype required')
        envelope=8*r['node_count']+8*shape[1]+48*min(max(r['node_count'],shape[1]),settings['chunk_edges'])
        require(envelope<=WORK,'declared work envelope exceeds256MiB')
    require(sum(r['node_count']*8 for r in rows)<240*1024**2,'cardinality output payload exceeds reserved240MiB')
    sys.path.insert(0,str(root));helper=load_helper(root,settings['helper_sha256'])
    output.mkdir() # Exclusive one-use directory; existing output is always refused.
    start=time.monotonic();cpu=time.process_time()
    result=dict(schema_version=1,kind=settings['kind'],settings_sha256=settings_sha256,inputs_sha256=settings['inputs']['sha256'],caller_sha256=settings['caller_sha256'],helper_sha256=settings['helper_sha256'],qualification=QUALIFICATION,graphs=[dict(graph_hash=r['graph_hash'],week=r['week'],status='unattempted',reason='not_attempted_after_failure_or_interruption') for r in rows])
    write(output/'START01.json',result)
    for i,row in enumerate(rows):
        d=output/f'graph-{i:02d}';d.mkdir();write(d/'ATTEMPT01.json',dict(graph_hash=row['graph_hash'],week=row['week'],status='attempted',monotonic_seconds=time.monotonic()))
        record=result['graphs'][i];record.pop('reason');record.update(graph(root,row,d,helper,settings));write(d/'RESULT01.json',record)
        if record['status']=='failed':break
    try:
        result['input_list_after']=snapshot(path(root,settings['inputs']['path']),settings['inputs'])
        require(result['input_list_after']==input_observation,'input declaration changed')
        require(settings_path.read_bytes()==settings_bytes and hashlib.sha256(source.read_bytes()).hexdigest()==settings['caller_sha256'] and hashlib.sha256(path(root,HELPER).read_bytes()).hexdigest()==settings['helper_sha256'],'settings/source changed during census')
    except BaseException as error:result['integrity_failure']=type(error).__name__+': '+str(error)
    result.update(timing(start,cpu));result['status']='completed' if all(r['status']=='completed' for r in result['graphs']) and 'integrity_failure' not in result else 'failed'
    write(output/'SUMMARY01.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--settings',required=True);p.add_argument('--settings-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=run(Path(a.root),Path(a.settings),a.settings_sha256,Path(a.output));print(json.dumps({'status':result['status'],'graphs':[x['status'] for x in result['graphs']]}));sys.exit(0 if result['status']=='completed' else 1)
