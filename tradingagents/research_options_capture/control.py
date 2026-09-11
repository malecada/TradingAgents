"""Local-only controller for one explicitly granted prospective options episode.

No transport, scheduler, credentials, or financial evaluation is provided.
Grant schema is checked by _admit; episode_protocol contains exactly version1,
observation_window(start,end), worker_lease(not_before,expires_at), and
analysis_inputs. All clocks are explicit UTC ISO strings. Initial inputs
are existing design bytes; future observed bytes are phase products, not inputs.
Control callbacks/records grant no authority to a remote financial process.
"""
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import uuid

from tradingagents.research.verify import _blob, verify_claim
from tradingagents.research_spread.verify import verify_run as historical_verify

TARGET='options-episode-20260911'
FAMILY='options-volatility'
MECHANISM='binance-option-delta-hedged-volatility-premium'


class ControlError(ValueError):
    pass


def encoded(value):
    return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def sha(raw):return hashlib.sha256(raw).hexdigest()


def utc(value):
    try:d=datetime.fromisoformat(value.replace('Z','+00:00'))
    except (ValueError,AttributeError) as exc:raise ControlError('explicit UTC clock required') from exc
    if d.tzinfo is None or d.utcoffset()!=timedelta(0):raise ControlError('UTC required')
    return d


def local(root,name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts or not p.parts or any(x in {'keys','apis','.env','hf_token.txt'} or x.startswith('.env.') for x in p.parts):raise ControlError('unsafe path')
    path=root/p
    if any(x.is_symlink() for x in (path,*path.parents)):raise ControlError('symlink forbidden')
    return path


def file_sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def reference(root,ref,source=None):
    if not isinstance(ref,dict) or set(ref)!={'path','sha256'} or not re.fullmatch('[0-9a-f]{64}',ref['sha256']):raise ControlError('exact artifact reference required')
    path=local(root,ref['path'])
    if file_sha(path)!=ref['sha256']:raise ControlError('retained artifact hash changed')
    if source is not None and sha(_blob(root,source,ref['path']))!=ref['sha256']:raise ControlError('committed artifact changed')
    return path.read_bytes()


def syncdir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)


def immutable(path,value):
    raw=value if isinstance(value,bytes) else encoded(value)
    temp=path.parent/('.pending-'+uuid.uuid4().hex)
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'wb',closefd=False) as f:f.write(raw);f.flush();os.fsync(fd)
    finally:os.close(fd)
    os.link(temp,path,follow_symlinks=False);syncdir(path.parent);temp.unlink();syncdir(path.parent)


@contextmanager
def lock(root):
    directory=root/'research_runs';directory.mkdir(exist_ok=True);syncdir(root)
    fd=os.open(directory/'.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX)
        yield
    finally:os.close(fd)


def runtime_hashes():
    base=Path(__file__).parent.parent
    return {package+'/'+p.name:file_sha(p) for package in ('research','research_amended','research_extended','research_spread','research_options_capture') for p in sorted((base/package).glob('*.py'))}


def inventory(root,own=None,allow_active=False):
    items={};claims={}
    for directory in sorted((root/'research_runs').iterdir()):
        if directory.name.startswith('.') or directory.name==own:continue
        claim=verify_claim(directory);claims[directory.name]=claim
        terminals=[name for name in ('complete.json','failed.json') if (directory/name).exists()]
        if not terminals and allow_active:
            items[directory.name]={'claim_sha256':file_sha(directory/'claim.json'),'terminal':None,'terminal_sha256':None,'output_sha256':{}}
            continue
        if len(terminals)!=1:raise ControlError('historical claim not terminal')
        historical_verify(directory)
        terminal=json.loads((directory/terminals[0]).read_bytes())
        items[directory.name]={'claim_sha256':file_sha(directory/'claim.json'),'terminal':terminals[0],
                              'terminal_sha256':file_sha(directory/terminals[0]),'output_sha256':terminal['output_sha256']}
    return items,claims


def _admit(root,registration,source,design_source,now,own=None):
    now=utc(now);root=Path(root).resolve()
    raw=_blob(root,source,registration)
    if local(root,registration).read_bytes()!=raw or _blob(root,design_source,registration)!=raw:raise ControlError('registration execution/design/current mismatch')
    spec=json.loads(raw);exp=spec['experiments'][TARGET];family=spec['families'][exp['family']]
    if exp['family']!=FAMILY or family['mechanism_id']!=MECHANISM or type(family['attempt_budget']) is not int or family['attempt_budget']!=4 or type(family['prior_attempts']) is not int or family['prior_attempts']!=1:raise ControlError('original options family changed')
    if exp['stage'] not in ('development','exploratory') or len(exp['cells'])!=8 or len(set(exp['cells']))!=8:raise ControlError('fixed eight development cases required')
    protocol=exp['episode_protocol']
    if set(protocol)!={'schema_version','observation_window','worker_lease','analysis_inputs'} or type(protocol['schema_version']) is not int or protocol['schema_version']!=1:raise ControlError('episode protocol schema')
    if set(protocol['observation_window'])!={'start','end'} or set(protocol['worker_lease'])!={'not_before','expires_at'}:raise ControlError('clock schema')
    start,end=map(utc,(protocol['observation_window']['start'],protocol['observation_window']['end']))
    lease_start,lease_end=map(utc,(protocol['worker_lease']['not_before'],protocol['worker_lease']['expires_at']))
    if not lease_start<=start<end<=lease_end or not timedelta(0)<lease_end-lease_start<=timedelta(days=46):raise ControlError('frozen lease/window bound')
    committed_at=max(datetime.fromisoformat(subprocess.check_output(['git','show','-s','--format=%cI',commit],cwd=root,text=True).strip()).astimezone(timezone.utc) for commit in {source,design_source})
    if committed_at>=lease_start or own is None and (now>=lease_start or now<committed_at):raise ControlError('design and exclusive claim must precede collection')
    if not isinstance(protocol['analysis_inputs'],dict) or not protocol['analysis_inputs']:raise ControlError('fixed analysis input denominator')
    for name,item in protocol['analysis_inputs'].items():
        if not re.fullmatch('[a-z][a-z0-9_-]{0,63}',name) or set(item)!={'path'}:raise ControlError('fixed analysis path schema')
        local(root,item['path'])
    for name in exp['outputs']:
        if Path(name).name!=name or not name.endswith('.json'):raise ControlError('output basename required')
    if len(set(exp['outputs']))!=len(exp['outputs']):raise ControlError('duplicate outputs')
    if exp['runtime_hashes']!=runtime_hashes():raise ControlError('runtime source changed')
    pins=dict(exp['source_files'])
    for key in ('charter','selection'):
        if not exp.get(key):raise ControlError('charter and policy pins required')
        pins[exp[key]['path']]=exp[key]['sha256']
    for package_name,digest in exp['runtime_hashes'].items():pins['tradingagents/'+package_name]=digest
    for name,digest in pins.items():
        for commit in {source,design_source}:reference(root,{'path':name,'sha256':digest},commit)
    inputs=exp['inputs']
    if not inputs:raise ControlError('existing design inputs required')
    for item in inputs.values():
        if item['sha256'] is None:raise ControlError('future source bytes are not initial inputs')
        reference(root,{'path':item['path'],'sha256':item['sha256']})
    if not any(w['start']==protocol['observation_window']['start'] and w['end']==protocol['observation_window']['end'] and w['availability']=='prospective' for w in exp['windows']):raise ControlError('honest future observation window required')
    grant=json.loads(reference(root,exp['episode_book_grant'],source))
    if _blob(root,design_source,exp['episode_book_grant']['path'])!=_blob(root,source,exp['episode_book_grant']['path']):raise ControlError('grant design binding')
    fields={'schema_version','target_experiment','program_id','family_id','mechanism_id','original_budget','prior_attempts','increment','effective_budget','target_contract_sha256','history_source','prior_claims','options_prior_ids','review','preflight'}
    if set(grant)!=fields:raise ControlError('target-only grant schema')
    for key,value in [('schema_version',1),('original_budget',4),('prior_attempts',1),('increment',1),('effective_budget',5)]:
        if type(grant[key]) is not int or grant[key]!=value:raise ControlError('grant accounting')
    target={k:v for k,v in exp.items() if k!='episode_book_grant'}
    target_hash=sha(canonical(target))
    if grant['target_experiment']!=TARGET or grant['program_id']!=spec['program_id'] or grant['family_id']!=FAMILY or grant['mechanism_id']!=MECHANISM or grant['target_contract_sha256']!=target_hash:raise ControlError('grant identity')
    actual,claims=inventory(root,own,allow_active=own is not None)
    prior=grant['prior_claims']
    if not isinstance(prior,dict) or len(prior)!=19 or any(actual.get(k)!=v for k,v in prior.items()):raise ControlError('complete nineteen-claim history changed')
    extra=set(actual)-set(prior)
    if own is None and extra:raise ControlError('unregistered initial history')
    if own:
        current=verify_claim(root/'research_runs'/own)
        if not committed_at<=utc(current['started_at'])<lease_start:raise ControlError('claim was not reserved before collection')
        if any(claims[k]['family']['mechanism_id']==MECHANISM or utc(claims[k]['started_at'])<=utc(current['started_at']) for k in extra):raise ControlError('unbound historical/same-family descendant')
    options=sorted(k for k in prior if claims[k]['family']['mechanism_id']==MECHANISM)
    if len(options)!=3 or grant['options_prior_ids']!=options:raise ControlError('three spent options claims required')
    subprocess.run(['git','merge-base','--is-ancestor',grant['history_source'],design_source],cwd=root,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    for name in prior:
        old=claims[name]
        oldspec=json.loads(_blob(root,old['source'],old['registration']))
        for collection in ('experiments','families','datasets'):
            if any(spec[collection].get(k)!=v for k,v in oldspec[collection].items()):raise ControlError('historical gate object changed')
        baseline=_blob(root,grant['history_source'],old['registration'])
        if local(root,old['registration']).read_bytes()!=baseline or _blob(root,source,old['registration'])!=baseline:raise ControlError('physical historical registration changed')
        oldpins=dict(old['experiment']['source_files'])
        for key in ('charter','selection'):
            if old['experiment'].get(key):oldpins[old['experiment'][key]['path']]=old['experiment'][key]['sha256']
        for path,digest in oldpins.items():reference(root,{'path':path,'sha256':digest},source)
    for name,old in claims.items():
        if name not in prior:continue
        package='research_spread' if 'budget_book_grant' in old['experiment'] else 'research_extended' if 'budget_extension' in old['experiment'] else 'research_amended' if 'budget_amendment' in old['experiment'] else 'research'
        for key,digest in old['experiment'].get('runtime_hashes',{}).items():
            prefixes={'original':'research','amended':'research_amended','extended':'research_extended'}
            if '/' in key:
                prefix,filename=key.split('/',1);runtime_path=prefixes.get(prefix,prefix)+'/'+filename
            else:runtime_path=package+'/'+key
            if exp['runtime_hashes'].get(runtime_path)!=digest:raise ControlError('ancestor runtime changed')
    for name in options:
        if claims[name]['family']!=family:raise ControlError('options historical family reset')
    approval=json.loads(reference(root,grant['review'],source));preflight=json.loads(reference(root,grant['preflight'],source))
    common={'target_experiment':TARGET,'target_contract_sha256':target_hash,'prior_claims_sha256':sha(canonical(prior))}
    if set(approval)!={*common,'decision','independent_review'} or approval['decision']!='approve-single-prospective-options-book-episode' or any(approval[k]!=v for k,v in common.items()):raise ControlError('explicit book approval missing')
    reference(root,approval['independent_review'],source)
    if set(preflight)!={*common,'status','reports'} or preflight['status']!='pass' or any(preflight[k]!=v for k,v in common.items()) or not preflight['reports']:raise ControlError('bound preflight missing')
    for ref in preflight['reports']:reference(root,ref,source)
    for ref in [grant['review'],grant['preflight'],approval['independent_review'],*preflight['reports']]:reference(root,ref,design_source)
    return root,spec,exp,protocol,grant


class Episode:
    def __init__(self,root,claim):
        self.root=root;self.claim=claim;self.directory=root/'research_runs'/TARGET
        self.claim_hash=file_sha(self.directory/'claim.json')

    @classmethod
    def start(cls,*,root,registration,source,now_utc,design_source=None):
        root=Path(root).resolve();design_source=design_source or source
        with lock(root):
            if (root/'research_runs'/TARGET).exists():raise ControlError('episode attempt already consumed')
            root,spec,exp,protocol,grant=_admit(root,registration,source,design_source,now_utc)
            directory=root/'research_runs'/TARGET;directory.mkdir();(directory/'outputs').mkdir();(directory/'control').mkdir();syncdir(directory.parent)
            claim={'schema_version':1,'program_id':spec['program_id'],'experiment_id':TARGET,'started_at':utc(now_utc).isoformat(),'source':source,'design_source':design_source,
                   'registration':registration,'registration_sha256':sha(_blob(root,source,registration)),'bindings':None,'bindings_sha256':None,'inputs':exp['inputs'],'experiment':exp,'family':spec['families'][FAMILY],
                   'windows':[{**w,'identity':spec['datasets'][w['dataset']]['identity'],'state':'exposed'} for w in exp['windows']],
                   'prior_exposures':[{**e,'identity':d['identity']} for d in spec['datasets'].values() for e in d['exposures']],
                   'episode_protocol':protocol,'episode_book_grant':exp['episode_book_grant'],'authority':'local-master-only'}
            immutable(directory/'claim.json',claim)
            return cls(root,claim)

    @classmethod
    def resume(cls,*,root,now_utc):
        root=Path(root).resolve()
        with lock(root):
            claim=verify_claim(root/'research_runs'/TARGET);obj=cls(root,claim);obj._active(now_utc);return obj

    def _active(self,now,allow_analysis_failure=False):
        if file_sha(self.directory/'claim.json')!=self.claim_hash or any((self.directory/n).exists() for n in ('complete.json','failed.json')):raise ControlError('changed or terminal claim')
        if utc(now)<utc(self.claim['started_at']):raise ControlError('control clock predates claim')
        _admit(self.root,self.claim['registration'],self.claim['source'],self.claim['design_source'],now,TARGET)
        if self.claim.get('episode_protocol')!=self.claim['experiment']['episode_protocol'] or self.claim.get('episode_book_grant')!=self.claim['experiment']['episode_book_grant'] or self.claim.get('authority')!='local-master-only':raise ControlError('unbound episode fields')

        self._check_controls(now,check_analysis=not allow_analysis_failure)

    def _source_binding(self,now):
        path=self.directory/'control/source-binding.json'
        if not path.exists():return None
        bound=json.loads(path.read_bytes())
        if set(bound)!={'claim_sha256','seal','manifest'} or bound['claim_sha256']!=self.claim_hash:raise ControlError('source binding schema')
        value=json.loads(reference(self.root,bound['seal']));reference(self.root,bound['manifest'])
        if set(value)!={'claim_sha256','worker_lease_sha256','manifest_sha256','worker_stopped','sealed_at'} or value['claim_sha256']!=self.claim_hash or value['worker_lease_sha256']!=sha(canonical(self.claim['episode_protocol']['worker_lease'])) or value['manifest_sha256']!=bound['manifest']['sha256'] or value['worker_stopped'] is not True or not utc(self.claim['started_at'])<=utc(value['sealed_at'])<=utc(now):raise ControlError('retained source seal invalid')
        return bound

    def _stop_ack(self,now):
        path=self.directory/'control/stop-ack.json'
        if not path.exists():return False
        bound=json.loads(path.read_bytes())
        if set(bound)!={'claim_sha256','ack'} or bound['claim_sha256']!=self.claim_hash:raise ControlError('stop binding schema')
        value=json.loads(reference(self.root,bound['ack']))
        if set(value)!={'claim_sha256','worker_lease_sha256','stopped_at','status'} or value['claim_sha256']!=self.claim_hash or value['worker_lease_sha256']!=sha(canonical(self.claim['episode_protocol']['worker_lease'])) or value['status']!='stopped' or not utc(self.claim['started_at'])<=utc(value['stopped_at'])<=utc(now):raise ControlError('retained stop acknowledgement invalid')
        return True

    def _analysis_binding(self,binding,commit,now):
        if utc(now)<utc(self.claim['episode_protocol']['observation_window']['end']):raise ControlError('analysis before frozen observation end')
        source=self._source_binding(now)
        if source is None:raise ControlError('returned sealed source required')
        bound=json.loads(reference(self.root,binding,commit))
        expected={'claim_sha256','target_contract_sha256','source_manifest','inputs','independent_review'}
        target={k:v for k,v in self.claim['experiment'].items() if k!='episode_book_grant'}
        if set(bound)!=expected or bound['claim_sha256']!=self.claim_hash or bound['target_contract_sha256']!=sha(canonical(target)) or bound['source_manifest']!=source['manifest']:raise ControlError('analysis binding cannot change contract')
        if set(bound['inputs'])!=set(self.claim['episode_protocol']['analysis_inputs']):raise ControlError('analysis input denominator')
        for name,item in bound['inputs'].items():
            if set(item)!={'path','sha256','availability'} or item['path']!=self.claim['episode_protocol']['analysis_inputs'][name]['path'] or item['availability'] not in ('complete','unavailable'):raise ControlError('analysis input binding')
            reference(self.root,{k:item[k] for k in ('path','sha256')})
        review=json.loads(reference(self.root,bound['independent_review'],commit))
        if review!={'decision':'admit-frozen-options-source','claim_sha256':self.claim_hash,'source_manifest_sha256':source['manifest']['sha256'],'inputs_sha256':sha(canonical(bound['inputs']))}:raise ControlError('independent source review binding')
        subprocess.run(['git','merge-base','--is-ancestor',self.claim['source'],commit],cwd=self.root,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        return bound

    def _check_controls(self,now,check_analysis=True):
        self._source_binding(now);self._stop_ack(now)
        allowed={'source-binding.json','stop-ack.json','analysis-intent.json','stop-pending.json'}
        for path in (self.directory/'control').iterdir():
            if path.is_symlink() or not path.is_file() or (path.name not in allowed and not re.fullmatch(r'\.pending-[0-9a-f]{32}',path.name)):raise ControlError('unsafe control member')
        path=self.directory/'control/analysis-intent.json'
        if path.exists() and check_analysis:
            intent=json.loads(path.read_bytes())
            if set(intent)!={'claim_sha256','binding','commit','started_at'} or intent['claim_sha256']!=self.claim_hash or not utc(self.claim['started_at'])<=utc(intent['started_at'])<=utc(now):raise ControlError('analysis intent invalid')
            self._analysis_binding(intent['binding'],intent['commit'],intent['started_at'])
        path=self.directory/'control/stop-pending.json'
        if path.exists():
            value=json.loads(path.read_bytes())
            if set(value)!={'claim_sha256','requested_at','reason'} or value['claim_sha256']!=self.claim_hash or not utc(self.claim['started_at'])<=utc(value['requested_at'])<=utc(now):raise ControlError('stop-pending identity')

    def _write(self,name,value):immutable(self.directory/'control'/name,value)

    def bind_source(self,*,seal,manifest,now_utc):
        with lock(self.root):
            self._active(now_utc)
            value=json.loads(reference(self.root,seal));reference(self.root,manifest)
            expected={'claim_sha256','worker_lease_sha256','manifest_sha256','worker_stopped','sealed_at'}
            if set(value)!=expected or value['claim_sha256']!=self.claim_hash or value['worker_lease_sha256']!=sha(canonical(self.claim['episode_protocol']['worker_lease'])) or value['manifest_sha256']!=manifest['sha256'] or value['worker_stopped'] is not True or not utc(self.claim['started_at'])<=utc(value['sealed_at'])<=utc(now_utc):raise ControlError('source seal quiescence binding')
            self._write('source-binding.json',{'claim_sha256':self.claim_hash,'seal':seal,'manifest':manifest})

    def acknowledge_stop(self,*,ack,now_utc):
        with lock(self.root):
            self._active(now_utc);value=json.loads(reference(self.root,ack))
            if set(value)!={'claim_sha256','worker_lease_sha256','stopped_at','status'} or value['claim_sha256']!=self.claim_hash or value['worker_lease_sha256']!=sha(canonical(self.claim['episode_protocol']['worker_lease'])) or value['status']!='stopped' or not utc(self.claim['started_at'])<=utc(value['stopped_at'])<=utc(now_utc):raise ControlError('stop acknowledgement binding')
            self._write('stop-ack.json',{'claim_sha256':self.claim_hash,'ack':ack})

    def _quiescent(self,now):
        return self._source_binding(now) is not None or self._stop_ack(now) or utc(now)>=utc(self.claim['episode_protocol']['worker_lease']['expires_at'])

    def analysis_intent(self,*,binding,commit,now_utc):
        with lock(self.root):
            self._active(now_utc)
            if not self._quiescent(now_utc):raise ControlError('worker not quiescent')
            self._analysis_binding(binding,commit,now_utc)
            self._write('analysis-intent.json',{'claim_sha256':self.claim_hash,'binding':binding,'commit':commit,'started_at':utc(now_utc).isoformat()})

    def write_output(self,name,body,*,now_utc):
        with lock(self.root):
            self._active(now_utc)
            if not (self.directory/'control/analysis-intent.json').exists() or name not in self.claim['experiment']['outputs'] or not isinstance(body,bytes):raise ControlError('authorized analysis output required')
            immutable(self.directory/'outputs'/name,body)

    def finish(self,*,status,cells,reason,now_utc):
        if status not in ('complete','failed'):raise ControlError('terminal status')
        with lock(self.root):
            self._active(now_utc,allow_analysis_failure=status=='failed')
            if not self._quiescent(now_utc):
                path=self.directory/'control/stop-pending.json'
                if not path.exists():self._write('stop-pending.json',{'claim_sha256':self.claim_hash,'requested_at':utc(now_utc).isoformat(),'reason':reason})
                return {'status':'stop-pending','terminal':False}
            if status not in ('complete','failed'):raise ControlError('terminal status')
            output_paths=list((self.directory/'outputs').iterdir())
            # Reject every unsafe/unregistered member before reading any output.
            # Pending crash files remain in place for separate forensic closure.
            for path in output_paths:
                if not stat.S_ISREG(path.lstat().st_mode) or path.name not in self.claim['experiment']['outputs']:
                    raise ControlError('unsafe, pending, or unregistered output retained; terminal publication refused')
            outputs={p.name:file_sha(p) for p in output_paths}
            if status=='complete':
                if not (self.directory/'control/analysis-intent.json').exists() or set(outputs)!=set(self.claim['experiment']['outputs']) or {c['id'] for c in cells}!=set(self.claim['experiment']['cells']) or len(cells)!=8 or any(c['status'] not in ('complete','unavailable') or c['status']=='unavailable' and not c.get('reason') for c in cells):raise ControlError('analysis/output/cell denominator incomplete')
            control={p.name:file_sha(p) for p in (self.directory/'control').iterdir()}
            receipt={'schema_version':1,'experiment_id':TARGET,'status':status,'ended_at':utc(now_utc).isoformat(),'source':self.claim['source'],'registration_sha256':self.claim['registration_sha256'],'claim_sha256':self.claim_hash,'output_sha256':outputs,'control_sha256':control,'cells':cells,'cell_count':len(cells),'unavailable_count':sum(c['status']=='unavailable' for c in cells),'reason':reason}
            immutable(self.directory/(status+'.json'),receipt)
            return {'status':status,'terminal':True}


def verify_episode(*,root,now_utc):
    """Read-only current protocol/retained-hash check; not independent science."""
    root=Path(root).resolve()
    with lock(root):
        claim=verify_claim(root/'research_runs'/TARGET);episode=Episode(root,claim)
        _admit(root,claim['registration'],claim['source'],claim['design_source'],now_utc,TARGET)
        if claim.get('episode_protocol')!=claim['experiment']['episode_protocol'] or claim.get('episode_book_grant')!=claim['experiment']['episode_book_grant'] or claim.get('authority')!='local-master-only':raise ControlError('episode claim semantics changed')
        terminals=[name for name in ('complete.json','failed.json') if (episode.directory/name).exists()]
        if len(terminals)>1:raise ControlError('duplicate terminal')
        if not terminals:
            episode._check_controls(now_utc)
            return {'status':'active','claim_sha256':episode.claim_hash,'authority':'local-master-only'}
        receipt=json.loads((episode.directory/terminals[0]).read_bytes())
        episode._check_controls(now_utc,check_analysis=receipt['status']!='failed')
        if utc(receipt['ended_at'])>utc(now_utc) or not episode._quiescent(receipt['ended_at']):raise ControlError('terminal preceded worker quiescence')
        controls={p.name:file_sha(p) for p in (episode.directory/'control').iterdir()}
        if controls!=receipt['control_sha256']:raise ControlError('terminal control inventory changed')
        result=historical_verify(episode.directory)
        if receipt['status']=='complete' and not (episode.directory/'control/analysis-intent.json').exists():raise ControlError('completion lacks analysis intent')
        return {**result,'authority':'local-master-only','new_protocol':'grant/future/source/control bindings checked; no scientific validation'}
