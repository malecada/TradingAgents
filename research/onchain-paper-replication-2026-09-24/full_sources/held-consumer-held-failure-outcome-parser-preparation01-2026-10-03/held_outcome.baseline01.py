"""Read-only LOCAL6 held-output semantic supplement; never grants authority.

No package imports, array decoding, fitting, claims or file writes. Original
current capsule only: recovery verification must not rebase native inode proof.
"""
import ast,hashlib,json,os,selectors,stat,subprocess,sys,time
from pathlib import Path
MAX=4*1024**2
META=8192
SOURCE='d443208795f59292c156c5b81b687594efacea4d'
IDENTITY='original-import-held-success-20261003-01'
ORIGINAL='48832eeb9774ef6ca13915364c17d1ac89f5c67165636de5811ebf82ad6ad726'
RAW='fixture_tools/raw_receipts01.py'
RAW_SHA='47e025bb5e6c1a442ab8c03d9d19d95d6f9f5541377f8c7e753584dbfa2077b4'
TARGETS={'e5abfa02758c751c6f0ec2eca2bf358be3c1e7615f5a024c268834882069802d':2,'f674b9d99a40c621d90a5b37cc35b53a82faa746388ec7d61185f593fcf95f49':3}
class CleanupFailure(BaseException):pass
def require(v,m):
    if not v:raise ValueError(m)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def equal(a,b):return canonical(a)==canonical(b)
def fatal(e):return isinstance(e,MemoryError) or (not isinstance(e,Exception) and not isinstance(e,CleanupFailure))
def cleanup(actions,primary=None):
    failures=[]
    for action in actions:
        try:action()
        except BaseException as error:failures.append(error)
    errors=([primary] if primary is not None else [])+failures
    chosen=next((e for e in errors if fatal(e)),None)
    if chosen is not None:raise chosen
    if failures:raise CleanupFailure('owned read/process cleanup uncertain') from (primary or failures[0])
    if primary is not None:raise primary
def signature(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def parse(raw):
    def pairs(items):
        out={}
        for k,v in items:require(k not in out,'duplicate JSON key');out[k]=v
        return out
    def constant(value):raise ValueError('nonfinite JSON constant')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)

class Reader:
    def __init__(self,root):
        self.root=Path(root);require(self.root.is_absolute() and self.root.resolve()==self.root,'canonical original root required')
        self.total=0;self.files={};self.deadline=time.monotonic()+120
    def body(self,relative,limit=MAX):
        require(time.monotonic()<self.deadline,'bounded semantic read deadline')
        require(type(relative) is str and relative and not Path(relative).is_absolute() and all(p not in ('','.','..') for p in relative.split('/')) and '\\' not in relative,'finite relative original member')
        require(not any(p.lower() in ('keys','apis','.env','.ssh') or p.lower().endswith(('.pem','.key')) or p.lower()=='hf_token.txt' for p in relative.split('/')),'protected path refused before IO')
        require(type(limit) is int and 0<limit<=MAX,'finite per-file bound')
        path=self.root/relative;fds=[];parents=[];primary=None;result=None
        try:
            fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(fd);parent=self.root
            parents.append((parent,fd,signature(os.fstat(fd))))
            for part in Path(relative).parts[:-1]:
                fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);fds.append(fd);parent=parent/part;parents.append((parent,fd,signature(os.fstat(fd))))
            name=Path(relative).name;before=os.stat(name,dir_fd=fd,follow_symlinks=False);pin=signature(before)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<=before.st_size<=limit,'original file type/link/extent')
            child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=fd);fds.append(child)
            require(signature(os.fstat(child))==pin,'original member changed before read')
            chunks=[];count=0
            while True:
                part=os.read(child,min(65536,before.st_size-count+1))
                if not part:break
                count+=len(part);require(count<=before.st_size and count<=limit,'original member grew during read');chunks.append(part)
            require(count==before.st_size and signature(os.fstat(child))==pin and signature(os.stat(name,dir_fd=fd,follow_symlinks=False))==pin and signature(path.lstat())==pin and path.resolve()==path,'original member changed during read')
            for parent,parentfd,expected in parents:require(parent.resolve()==parent and signature(parent.lstat())==expected==signature(os.fstat(parentfd)),'original parent redirected/replaced')
            result=b''.join(chunks);self.total+=len(result);require(self.total<=64*1024**2 and len(self.files)<4096,'aggregate semantic read ceiling')
            row=(pin,sha(result));require(relative not in self.files or self.files[relative]==row,'retained member changed between checks');self.files[relative]=row
        except BaseException as error:primary=error
        cleanup([lambda fd=fd:os.close(fd) for fd in reversed(fds)],primary)
        return result
    def json(self,name,limit=MAX):return parse(self.body(name,limit))
    def exact_members(self,relative,names):
        root=self.root/relative;require(root.resolve()==root,'member directory redirected');fd=None;it=None;primary=None
        try:
            fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);pin=signature(os.fstat(fd));it=os.scandir(fd);seen=set()
            for row in it:
                require(row.name not in seen and row.name in names,'unexpected original member');s=row.stat(follow_symlinks=False);require(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'nonregular original member');seen.add(row.name)
            require(seen==set(names) and root.resolve()==root and signature(root.lstat())==pin==signature(os.fstat(fd)),'missing/replaced original member directory')
        except BaseException as error:primary=error
        cleanup(([] if it is None else [it.close])+([] if fd is None else [lambda:os.close(fd)]),primary)
    def recheck(self):
        saved=dict(self.files)
        for name in sorted(saved):self.body(name)
        require(self.files==saved,'evidence changed during final readback')

def git(root,args,request=b'',cap=8*1024**2):
    """Fresh offline Git process; bounded pipes/cleanup, no fetch or mutation."""
    env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'}
    require(len(request)<=65536,'Git request bound');child=None;poll=None;primary=None;out=bytearray();err=bytearray();offset=0
    try:
        child=subprocess.Popen(['git','-c','protocol.allow=never',*args],cwd=root,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        poll=selectors.DefaultSelector()
        for stream,event in ((child.stdin,selectors.EVENT_WRITE),(child.stdout,selectors.EVENT_READ),(child.stderr,selectors.EVENT_READ)):os.set_blocking(stream.fileno(),False);poll.register(stream,event)
        deadline=time.monotonic()+10
        while poll.get_map():
            require(time.monotonic()<deadline,'Git bounded deadline')
            for key,event in poll.select(.1):
                if key.fileobj is child.stdin:
                    if offset<len(request):offset+=os.write(child.stdin.fileno(),request[offset:offset+16384])
                    else:poll.unregister(child.stdin);child.stdin.close()
                else:
                    data=os.read(key.fileobj.fileno(),65536)
                    if not data:poll.unregister(key.fileobj)
                    else:
                        buf=out if key.fileobj is child.stdout else err;buf.extend(data);require(len(buf)<=(cap if buf is out else 65536),'Git response bound')
        require(child.wait(timeout=1)==0,'Git source lookup failed')
    except BaseException as error:primary=error
    actions=[]
    if child is not None:
        if child.poll() is None:actions.extend([child.kill,lambda:child.wait(timeout=5)])
        actions.extend(stream.close for stream in (child.stdin,child.stdout,child.stderr) if not stream.closed)
    if poll is not None:actions.append(poll.close)
    cleanup(actions,primary);return bytes(out)

def sources(reader,release):
    root=reader.root;require(release['capsule_commit']==SOURCE and release['capsule_root']==str(root),'fixed original source/root differs')
    require(not os.path.lexists(root/'.git/objects/info/alternates') and not os.path.lexists(root/'.git/info/grafts') and not os.path.lexists(root/'.git/refs/replace'),'external/replaced Git authority refused')
    require(git(root,['rev-parse','HEAD'],cap=128).decode().strip()==SOURCE,'actual current HEAD differs')
    expected=release['source_files'];require(type(expected) is dict and len(expected)==204,'exact199code plus5auxiliary sources required')
    refs=dict(expected);refs[release['registration']]=release['registration_sha256']
    names=sorted(refs);require(all(type(n) is str and '\n' not in n and '\r' not in n and '\0' not in n for n in names),'Git source path characters')
    current={n:reader.body(n) for n in names}
    require(all(sha(current[n])==refs[n] for n in names),'current source/registration body hash differs')
    response=git(root,['cat-file','--batch'],''.join(SOURCE+':'+n+'\n' for n in names).encode());offset=0
    for name in names:
        end=response.index(b'\n',offset);head=response[offset:end].split();require(len(head)==3 and head[1]==b'blob' and head[2].isdigit(),'genuine committed blob missing/type')
        size=int(head[2]);require(size<=MAX,'Git blob bound');start=end+1;raw=response[start:start+size];require(raw==current[name] and response[start+size:start+size+1]==b'\n','committed/current source bytes differ');offset=start+size+1
    require(offset==len(response),'Git trailing response')
    require(expected.get(RAW)==RAW_SHA,'original raw parser pin differs')
    return parse(current[release['registration']])

def input_body(reader,experiment,name):
    ref=experiment['inputs'][name];raw=reader.body(ref['path']);require(sha(raw)==ref['sha256'],'registered input hash differs: '+name);return raw

def held_target(reader,stage_root,scope,owner,nodes,policy_name,policy_raw,policy,output_raw):
    cells=nodes*32;chunk=64;chunks=(cells+chunk-1)//chunk
    require(type(nodes) is int and nodes in (2,3) and 8*cells<=policy['max_read_bytes'] and chunks<=policy['max_members'],'exact original held denominator/policy')
    start_raw=reader.body(stage_root+'/stream/start.json',META);start=parse(start_raw)
    batch_root=stage_root+'/stream/batches';batch_raw=reader.body(batch_root+'/start.json',META)
    expected_start={'schema_version':1,'scope':scope,'owner':owner,'rows':nodes,'motifs':32,'chunk_cells':64,'dtype':'<f8','order':'row-major'}
    require(equal(parse(batch_raw),expected_start),'held original batch header differs')
    require(equal(start,{'schema_version':1,'kind':'mcm-score-stream','scope':scope,'owner':owner,'rows':nodes,'motifs':32,'batch_start_sha256':sha(batch_raw),'chunk_cells':64}),'held original stream header differs')
    terminal_raw=reader.body(batch_root+'/terminal.json',META);terminal=parse(terminal_raw);stream_raw=reader.body(stage_root+'/stream/complete.json',META);stream=parse(stream_raw)
    require(set(terminal)=={'schema_version','start_sha256','head','status','cells','chunks','reason','pending'} and equal({k:terminal[k] for k in ('schema_version','start_sha256','status','cells','chunks','pending')},{'schema_version':1,'start_sha256':sha(batch_raw),'status':'complete','cells':cells,'chunks':chunks,'pending':[]}) and type(terminal['reason']) is str and len(terminal['reason'].encode())<=1024,'original batch terminal differs')
    batch_head=sha(batch_raw);stream_head=sha(start_raw);digest=hashlib.sha256();parts=0;names={'start.json','terminal.json'}
    for index in range(chunks):
        stem='chunk-%012d'%index;count=min(64,cells-index*64)
        payload=reader.body(batch_root+'/'+stem+'.bin',count*8);require(len(payload)==count*8,'held complete payload byte denominator')
        header_raw=reader.body(batch_root+'/'+stem+'.json',META);header=parse(header_raw)
        require(equal(header,{'schema_version':1,'start_sha256':sha(batch_raw),'previous':batch_head,'index':index,'start_cell':index*64,'cells':count,'payload_sha256':sha(payload)}),'held chunk index/order/body chain differs');batch_head=sha(header_raw)
        seal_raw=reader.body(stage_root+'/stream/seal-%012d.json'%index,META);seal=parse(seal_raw)
        require(set(seal)=={'schema_version','start_sha256','previous','index','start_cell','cells','tail_terminal_sha256','batch_header_sha256'} and equal({k:seal[k] for k in seal if k!='tail_terminal_sha256'},{'schema_version':1,'start_sha256':sha(start_raw),'previous':stream_head,'index':index,'start_cell':index*64,'cells':count,'batch_header_sha256':batch_head}),'original stream seal/order differs')
        tail=reader.body(stage_root+'/stream/tails/tail-%012d/terminal.json'%index,META);require(sha(tail)==seal['tail_terminal_sha256'],'original stream tail reference differs');stream_head=sha(seal_raw)
        digest.update(payload);parts+=(len(payload)+policy['part_bytes']-1)//policy['part_bytes'];names.update({stem+'.bin',stem+'.json'})
    reader.exact_members(batch_root,names)
    require(batch_head==terminal['head'] and equal(stream,{'schema_version':1,'start_sha256':sha(start_raw),'head':stream_head,'cells':cells,'chunks':chunks,'batch_terminal_sha256':sha(terminal_raw)}),'complete original stream/batch chain differs')
    observation={'schema_version':1,'kind':'original-import-held-score-readback-v1','status':'local-byte-readback','target':scope['graph'],'owner':owner,'stage':'mcm-'+scope['graph'],'policy_input':policy_name,'policy_sha256':sha(policy_raw),'readback':{'members':chunks,'parts':parts,'bytes':8*cells,'sha256':digest.hexdigest()},'scientific_publication':False,'transport_authority':False,'local_bytes_retired':0}
    require(len(output_raw)<=META and equal(parse(output_raw),observation),'held output semantics/body hash differs')
    return {'target':scope['graph'],'output_sha256':sha(output_raw),'stream_complete_sha256':sha(stream_raw),'batch_terminal_sha256':sha(terminal_raw),'readback':observation['readback']}

def authenticate(root,release_path,release_sha256):
    """Observed success semantics only; exact original claim and six outputs.

    Caller must retain independent release/recovery/final exit evidence. This
    function does not issue an approval, token, claim, or source exemption.
    """
    reader=Reader(root);release_path=Path(release_path)
    require(release_path.is_absolute(),'exact external release path required')
    external=Reader(release_path.parent);release_raw=external.body(release_path.name)
    require(sha(release_raw)==release_sha256,'selected original release body differs');release=parse(release_raw)
    require(release['status']=='released-native-engineering' and release['remaining']==[],'unreleased source preparation')
    for field in ('release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256'):
        value=release[field];require(type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value),'original release evidence reference absent')
    registration=sources(reader,release);entry=release['cases']['success'];exp=entry['experiment']
    require(entry['identity']==IDENTITY and release['registration']=='held-fixture-registration01.json' and equal(exp,registration['experiments'][IDENTITY]) and release['program_id']==registration['program_id'] and equal(release['family'],registration['families'][exp['family']]),'actual original registered experiment differs')
    require(exp['outputs']==['resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json','held-target-01.json','held-target-02.json'],'exact original LOCAL6 output contract')
    require(len(exp['inputs'])==33,'exact current LOCAL33 input roles required')
    for input_name in sorted(exp['inputs']):input_body(reader,exp,input_name) # Opaque bytes only; no array/sample JSON decoding.
    job=parse(input_body(reader,exp,'execution_job'));require(job['kind']=='compact_resource' and len(job['payload']['representation_jobs'])==1 and equal(job['resources'],entry['job_resources']),'actual selected resource job differs')
    selected=next(iter(job['payload']['representation_jobs'].values()));plan=parse(input_body(reader,exp,selected['plan_input']));item=plan['producers'][selected['producer']]
    require(set(item)==set(selected)|{'binding_output','journal_output'} and all(equal(item[k],v) for k,v in selected.items()),'whole original job/producer differs')
    require(selected['descriptor']['required_graphs']==sorted(TARGETS) and equal(selected['descriptor']['resource_fixture']['target_nodes'],TARGETS) and entry['targets']==[{'graph_hash':h,'nodes':n} for h,n in TARGETS.items()],'fixed original target population differs')
    name=selected['held_score_consumer_input'];require(name==item['held_score_consumer_input']=='held_score_policy','original selected held input differs')
    policy_raw=input_body(reader,exp,name);policy=parse(policy_raw)
    expected={'schema_version':1,'kind':'original-import-held-score-readback-v1','targets':{h:{'output':'held-target-%02d.json'%(i+1)} for i,h in enumerate(TARGETS)},'part_bytes':1048576,'max_read_bytes':768,'max_members':32767}
    require(equal(policy,expected),'actual original held policy/configuration differs')
    compact_policy=parse(input_body(reader,exp,selected['compact_policy_input']));require(type(compact_policy['stage_policy']['score_chunk_cells']) is int and compact_policy['stage_policy']['score_chunk_cells']==64,'original physical chunk policy differs')
    original=parse(input_body(reader,exp,selected['original_dictionary_input']));require(original['dictionary_identity']==ORIGINAL and type(original['motif_count']) is int and original['motif_count']==32 and type(original['sample_count']) is int and original['sample_count']==512,'original imported32/512 evidence differs')
    # Invoke the exact original stdlib parser's semantic functions; only its
    # unsafe generic byte reader is replaced with this bounded read-only reader.
    # No caller-provided result dictionary is accepted as prior proof.
    raw_source=reader.body(RAW);require(sha(raw_source)==RAW_SHA,'actual retained raw parser differs')
    tree=ast.parse(raw_source);allowed={'require','digest','target_artifact','positive_native_observations','authenticate'}
    ns={'Path':Path,'hashlib':hashlib,'json':json,'os':os,'stat':stat,'GIB':1024**3,'MAX':MAX,'body':lambda r,n,limit=MAX:reader.body(str(n),limit),'metadata':lambda r,n:reader.json(str(n))}
    exec(compile(ast.Module([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in allowed],type_ignores=[]),str(reader.root/RAW),'exec'),ns)
    base=ns['authenticate'](reader.root,'success',release)
    run='research_runs/'+IDENTITY;claim_raw=reader.body(run+'/claim.json');terminal=reader.json(run+'/complete.json')
    require(base['claim_sha256']==sha(claim_raw) and base['lifecycle_status']=='complete','original complete claim required')
    journal=reader.json(run+'/outputs/resource-journal.json');root_journal='research_artifacts/onchain_representations/'+journal['owner']['workflow_identity']+'/'+IDENTITY
    owner_root=root_journal+'/compact';owner_raw=reader.body(owner_root+'/owner.json');owner_doc=parse(owner_raw);owner=sha(canonical(owner_doc))
    pair=parse(input_body(reader,exp,selected['pair_checkpoint_input']))
    binding={'experiment':IDENTITY,'source_commit':SOURCE,'claim_sha256':sha(claim_raw),'registration_sha256':release['registration_sha256'],'representation':next(iter(job['payload']['representation_jobs'])),'producer':selected['producer'],'workflow_identity':journal['owner']['workflow_identity'],'policy_sha256':exp['inputs'][selected['pair_checkpoint_input']]['sha256'],'journal_directory':str(reader.root/root_journal),'numerical_source':pair['numerical_source'],'job_input':'execution_job','job_sha256':exp['inputs']['execution_job']['sha256'],'resource_only':True}
    require(equal(owner_doc['binding'],binding) and all(binding.get(k)==v for k,v in journal['owner'].items()) and owner_doc['required_stages']==['dictionary-import']+['mcm-'+h for h in TARGETS],'original Owner/Binding/required stage population differs')
    compact=reader.json(owner_root+'/complete.json');require(compact['owner']==owner,'compact original Owner identity differs')
    environment=parse(input_body(reader,exp,job['environment_input']));require(owner_doc['context']['runtime_hash']==sha(canonical(environment)) and owner_doc['context']['source_commit']==pair['numerical_source']['commit'],'original runtime/package anchor context differs')
    imported_raw=reader.body(owner_root+'/dictionary-import/import-complete.json');imported=parse(imported_raw);intent_raw=reader.body(owner_root+'/dictionary-import/intent.json')
    require(imported['kind']=='dictionary-import-complete' and imported['owner']==owner and imported['intent_sha256']==sha(intent_raw) and imported['numeric']['original_dictionary']==imported['execution']['original_dictionary']==ORIGINAL and type(imported['current_matching_pairs']) is int and imported['current_matching_pairs']==0 and imported['historical_work_recomputed'] is False,'original import completion authority differs')
    motifs=imported['numeric']['ordered_motifs']
    require(type(motifs) is list and len(motifs)==32 and all(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h) for h in motifs) and imported['numeric']['original_matching']==imported['execution']['original_matching'],'original imported motif order/matching evidence differs')
    stage_digest=hashlib.sha256();stage_digest.update(canonical({'stage':'dictionary-import','receipt_sha256':sha(imported_raw)}));results=[]
    cells=reader.json(run+'/outputs/cell-ledger.json')
    for index,(graph,nodes) in enumerate(TARGETS.items()):
        row=cells[index];target=row['target'];scope=target['scope'];stage='mcm-'+graph;prefix=owner_root+'/'+stage
        require(scope['graph']==graph and scope['dictionary']==ORIGINAL and scope['ordered_motifs']==sha(canonical(motifs)) and row['status']=='complete','original Target/scope differs')
        seal_raw=reader.body(prefix+'/stage-complete.json',META);seal=parse(seal_raw);intent=reader.json(prefix+'/intent.json',META)
        producer_path='research_artifacts/onchain_compact_mcm/'+journal['owner']['workflow_identity']+'/'+IDENTITY+'/'+stage
        producer_raw=reader.body(producer_path+'/complete.json',META);producer=parse(producer_raw)
        require(sha(producer_raw)==target['producer_receipt_sha256'] and producer['stage_sha256']==sha(seal_raw) and equal(producer['scope'],scope) and equal(producer['output'],target['output']) and producer['graph_hash']==graph and producer['rows']==nodes and producer['motifs']==32,'original producer completion/stage/output joins differ')
        require(seal['owner']==owner and seal['kind']=='mcm' and seal['completed_pairs']==32*nodes and seal['execution_admitted'] is False and intent['owner']==owner and intent['stage']==stage and intent['pairs']==32*nodes and intent['scope']['workflow']==scope['workflow'] and equal(intent['scope'],seal['scope']),'closed original stage identity/denominator differs')
        require(seal['stream_terminal_sha256']==sha(reader.body(prefix+'/stream/complete.json',META)) and seal['stream_start_sha256']==sha(reader.body(prefix+'/stream/start.json',META)),'stage/stream terminal source differs')
        output=policy['targets'][graph]['output'];out_raw=reader.body(run+'/outputs/'+output,META);require(terminal['output_sha256'][output]==sha(out_raw),'original held output terminal hash differs')
        results.append(held_target(reader,prefix,scope,owner,nodes,name,policy_raw,policy,out_raw));stage_digest.update(canonical({'stage':stage,'receipt_sha256':sha(seal_raw)}))
    require(stage_digest.hexdigest()==compact['stage_receipts_sha256'],'original complete stage receipt order/hash differs')
    reader.exact_members(run+'/outputs',set(exp['outputs']));reader.recheck();external.recheck()
    return {'schema_version':1,'kind':'observed-local6-held-output-semantics','status':'verified-original-success-only','source':SOURCE,'identity':IDENTITY,'claim_sha256':sha(claim_raw),'release_sha256':release_sha256,'targets':results,'original_base_parser_sha256':RAW_SHA,'original_native_observations':base['native_observations'],'authority_granted':False,'scientific_publication':False,'transport_authority':False,'local_bytes_retired':0,'qualification':'Original retained file/native/output observations; not a recreated live Target/token or recovery, release approval, financial/capacity proof. External caller final exit/late-failure checks remain required.'}
