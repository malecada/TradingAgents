"""Bounded immutable source journal; no admission, transport, or scheduling."""
import copy
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid


class JournalError(RuntimeError):
    """Conservative refusal; no retry or replacement of existing evidence."""


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(path):
    path = Path(os.path.abspath(path))
    for parent in reversed((path, *path.parents)):
        if parent.is_symlink(): raise JournalError('symlink component forbidden')
    return path


class Journal:
    """One context holds the same persistent lock inode for a short invocation.

    The lock coordinates cooperating writers, not hostile filesystem mutation.
    Full validation occurs on entry/recovery/explicit validate/seal. Locked appends
    update an invocation-local inventory only after durable publication; failed
    publication invalidates it. External file changes are detected at full
    validation boundaries, not promised instantaneously during cached appends.
    Outer admission owns claim creation and cheap check_source, and must enforce its
    policy window. begin's durable return is a request permission prerequisite,
    not a network action. Caller records receipts before parsing or next request.
    """
    def __init__(self, path, *, claim_path, claim_sha256, slots, total_cap,
                 terminal_reserve, check_source, readonly=False):
        self.path = safe(path); self.claim = safe(claim_path)
        if not re.fullmatch('[0-9a-f]{64}', claim_sha256): raise JournalError('invalid claim hash')
        self.claim_hash = claim_sha256; self.callback = check_source; self.readonly=readonly
        if not callable(check_source): raise JournalError('explicit source callback required')
        if type(total_cap) is not int or type(terminal_reserve) is not int or not 2048 <= terminal_reserve < total_cap:
            raise JournalError('invalid total/reserved byte caps')
        self.total_cap=total_cap;self.reserve=terminal_reserve
        if not isinstance(slots,list) or not 1 <= len(slots) <= 20000: raise JournalError('finite slot list required')
        self.slots={}
        for slot in slots:
            if set(slot)!={'id','scheduled_ms','deadline_ms','request','body_cap'}: raise JournalError('slot schema')
            name=slot['id']
            if not isinstance(name,str) or not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',name) or name in self.slots: raise JournalError('slot identity')
            if type(slot['scheduled_ms']) is not int or slot['scheduled_ms']<0 or type(slot['body_cap']) is not int or not 0<=slot['body_cap']<=5*1024**2:
                raise JournalError('slot bounds')
            if type(slot['deadline_ms']) is not int or slot['deadline_ms'] < slot['scheduled_ms']:raise JournalError('slot deadline')
            encode(slot['request'])
            self.slots[name]=json.loads(encode(slot))
        groups={}
        for slot in self.slots.values():
            window=(slot['scheduled_ms'],slot['deadline_ms'])
            groups[window]=groups.get(window,0)+1
        if any(count>16 for count in groups.values()):raise JournalError('intent group exceeds 16 slots')
        self.spec={'claim_sha256':claim_sha256,'slots':list(self.slots.values()),'total_cap':total_cap,'terminal_reserve':terminal_reserve}
        self.fd=None;self._cache=None

    def __enter__(self):
        self._cache=None
        if self.readonly:
            if not self.path.is_dir() or not (self.path/'lock').exists() or not (self.path/'spec.json').exists():
                raise JournalError('read-only requires existing directory, lock and specification')
        else:
            self.path.mkdir(exist_ok=True)
            parent_fd=os.open(self.path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            try:os.fsync(parent_fd)
            finally:os.close(parent_fd)
        safe(self.path)
        self.fd=os.open(self.path/'lock',os.O_RDWR|os.O_NOFOLLOW|(0 if self.readonly else os.O_CREAT),0o600)
        if not self.readonly:os.fsync(self.fd);self._sync()
        try:
            fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            self.lock_identity=(os.fstat(self.fd).st_dev,os.fstat(self.fd).st_ino)
            self._boundary(active=not self.readonly)
            if (self.path/'spec.json').exists():
                if self._read('spec.json') != encode(self.spec): raise JournalError('frozen journal specification changed')
            elif self.readonly:raise JournalError('read-only journal has no specification')
            else:self._publish('spec.json',encode(self.spec))
            self.validate()
            return self
        except BaseException:
            os.close(self.fd);self.fd=None;raise

    def __exit__(self,*unused):
        os.close(self.fd);self.fd=None

    def _read(self,name):
        fd=os.open(self.path/name,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode): raise JournalError('nonregular member')
            with os.fdopen(fd,'rb',closefd=False) as stream:return stream.read(self.total_cap+1)
        finally:os.close(fd)

    def _boundary(self, active=True):
        if self.fd is None:raise JournalError('journal lock required')
        safe(self.path);safe(self.claim)
        lock=(self.path/'lock').stat(follow_symlinks=False)
        if (lock.st_dev,lock.st_ino)!=self.lock_identity or not stat.S_ISREG(lock.st_mode):raise JournalError('persistent lock replaced')
        fd=os.open(self.claim,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            with os.fdopen(fd,'rb',closefd=False) as stream:
                if digest(stream.read())!=self.claim_hash:raise JournalError('active claim changed')
        finally:os.close(fd)
        self.callback()
        if active and (self.readonly or (self.path/'seal.json').exists()):raise JournalError('sealed or read-only journal cannot resume')
        if active and any((self.claim.parent/name).exists() for name in ('complete.json','failed.json')):raise JournalError('outer terminal claim cannot resume')

    def _inventory(self):
        members={};total=0
        paths=list(self.path.iterdir())
        if len(paths)>70*len(self.slots)+10:raise JournalError('journal member count exceeded')
        for path in sorted(paths):
            if path.is_symlink() or not path.is_file():raise JournalError('unsafe journal member')
            name=path.name
            if not (name in ('lock','spec.json','seal.json') or re.fullmatch(r'(intent|receipt)-[a-z0-9-]+\.json|partial-[a-z0-9-]+-[0-9]{6}\.bin|recovery-[0-9]{6}\.json|pending-[0-9a-f]{32}',name)):
                raise JournalError('unregistered journal member')
            raw=self._read(name);total+=len(raw)
            members[name]={'sha256':digest(raw),'bytes':len(raw)}
        if total>self.total_cap:raise JournalError('journal total byte cap exceeded')
        return members,total

    def _publish(self,name,raw,terminal=False):
        if (self.path/name).exists():raise JournalError('immutable publication already exists')
        if self._cache is not None:member_count=len(self._cache['members']);used=self._cache['bytes']
        else:
            members,used=self._inventory();member_count=len(members)
        count_ceiling=70*len(self.slots)+10-(0 if terminal else 2)
        if member_count+2>count_ceiling:raise JournalError('journal staging member reservation exceeded')
        ceiling=self.total_cap if terminal else self.total_cap-self.reserve
        if used+2*len(raw)>ceiling or terminal and 2*len(raw)>self.reserve:
            raise JournalError('journal byte reservation exceeded')
        temporary=self.path/('pending-'+uuid.uuid4().hex)
        try:
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            try:
                with os.fdopen(fd,'wb',closefd=False) as stream:stream.write(raw);stream.flush();os.fsync(fd)
            finally:os.close(fd)
            os.link(temporary,self.path/name,follow_symlinks=False)
            self._sync();temporary.unlink();self._sync()
        except BaseException:
            self._cache=None
            raise
        if self._cache is not None:
            self._cache['members'][name]={'sha256':digest(raw),'bytes':len(raw)}
            self._cache['bytes']+=len(raw)
            if name.startswith(('intent-','receipt-')):
                value=json.loads(raw);slot=value['slot']
                state='intent_without_receipt' if value['kind']=='intent' else value['status']
                self._states[slot]['status']=state
                if state=='intent_without_receipt':self._pending.add(slot)
                else:self._pending.discard(slot)
            if name.startswith('partial-'):
                slot=name[len('partial-'):].rsplit('-',1)[0]
                self._partials.setdefault(slot,[]).append(name)

    def _current(self):
        if self._cache is None:self.validate()
        return self._cache

    def _sync(self):
        fd=os.open(self.path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)

    def _slot(self,name):
        if name not in self.slots:raise JournalError('unregistered slot')
        return self.slots[name]

    def validate(self):
        self._boundary(active=False)
        self._cache=None
        members,total=self._inventory();states=[];partials_by_slot={}
        for filename in members:
            if filename.startswith('partial-'):
                slot=filename[len('partial-'):].rsplit('-',1)[0]
                partials_by_slot.setdefault(slot,[]).append(filename)
        if self._read('spec.json')!=encode(self.spec):raise JournalError('frozen specification changed')
        for name,slot in self.slots.items():
            intent='intent-'+name+'.json';receipt='receipt-'+name+'.json'
            state='future_or_unattempted'
            for filename,kind in ((intent,'intent'),(receipt,'receipt')):
                if filename not in members:continue
                try:value=json.loads(self._read(filename))
                except (ValueError,RecursionError) as exc:raise JournalError('corrupt record') from exc
                if value.get('claim_sha256')!=self.claim_hash or value.get('slot')!=name or value.get('request')!=slot['request'] or value.get('kind')!=kind:
                    raise JournalError('record identity mismatch')
                if kind=='intent':
                    if type(value.get('now_ms')) is not int or not slot['scheduled_ms']<=value['now_ms']<=slot['deadline_ms']:raise JournalError('intent clock outside frozen window')
                    state='intent_without_receipt'
                else:
                    if not {'status','body_base64','body_sha256','body_bytes','metadata'}<=set(value):raise JournalError('receipt schema')
                    state=value['status']
                    try:body=base64.b64decode(value['body_base64'],validate=True)
                    except (ValueError,TypeError) as exc:raise JournalError('invalid raw encoding') from exc
                    if len(body)>slot['body_cap'] or digest(body)!=value['body_sha256'] or len(body)!=value['body_bytes']:raise JournalError('raw body binding differs')
                    if state not in ('received','unavailable','missed'):raise JournalError('receipt status')
                    if state=='received' and intent not in members:raise JournalError('receipt lacks intent')
                    if state in ('missed','unavailable'):
                        now=value.get('metadata',{}).get('recovered_at_ms')
                        if type(now) is not int:raise JournalError('recovery clock required')
                        if state=='missed' and (intent in members or now<=slot['deadline_ms']):raise JournalError('invalid missed slot chronology')
                        if state=='unavailable' and (intent not in members or now<json.loads(self._read(intent))['now_ms']):raise JournalError('invalid interrupted chronology')
                    if state=='received':
                        partials=partials_by_slot.get(name,[])
                        prefix=b''.join(self._read(k) for k in sorted(partials))
                        if not body.startswith(prefix):raise JournalError('receipt contradicts retained partial prefix')
            parts=[members[k]['bytes'] for k in partials_by_slot.get(name,[])]
            if sum(parts)>slot['body_cap']:raise JournalError('partial body cap exceeded')
            states.append({'id':name,'status':state})
        recognized={s['id'] for s in states}
        for name in members:
            if name.startswith(('intent-','receipt-')) and name.split('-',1)[1][:-5] not in recognized:raise JournalError('foreign slot record')
            if name.startswith('partial-') and name[len('partial-'):].rsplit('-',1)[0] not in recognized:raise JournalError('foreign partial slot')
        for filename in members:
            if filename.startswith('recovery-'):
                event=json.loads(self._read(filename))
                if set(event)!={'claim_sha256','now_ms','closed_slots'} or event['claim_sha256']!=self.claim_hash or type(event['now_ms']) is not int or not isinstance(event['closed_slots'],list) or len(set(event['closed_slots']))!=len(event['closed_slots']):raise JournalError('recovery event schema')
                for slot in event['closed_slots']:
                    if slot not in self.slots or 'receipt-'+slot+'.json' not in members:raise JournalError('recovery event slot')
                    receipt=json.loads(self._read('receipt-'+slot+'.json'))
                    if receipt['status'] not in ('missed','unavailable') or receipt['metadata']['recovered_at_ms']!=event['now_ms']:raise JournalError('recovery event differs from receipt')
        result={'claim_sha256':self.claim_hash,'slots':states,'members':members,'bytes':total}
        if 'seal.json' in members:
            seal=json.loads(self._read('seal.json'))
            prior=dict(result, members={k:v for k,v in members.items() if k!='seal.json'}, bytes=total-members['seal.json']['bytes'])
            if seal.get('claim_sha256')!=self.claim_hash or seal.get('inventory_sha256')!=digest(encode(prior)):
                raise JournalError('sealed inventory changed')
            expected_fields={'claim_sha256','status','inventory_sha256','slot_count','prior_bytes','scope'}
            if seal.get('status')=='failed':expected_fields|={'suppressed_count','suppressed_slots_sha256'}
            if set(seal)!=expected_fields or seal.get('status') not in ('complete','failed') or type(seal.get('slot_count')) is not int or seal['slot_count']!=len(self.slots) or type(seal.get('prior_bytes')) is not int or seal['prior_bytes']!=prior['bytes'] or seal.get('scope')!='source journal seal only; no outer claim completion or financial authorization':raise JournalError('source seal schema/accounting')
            if seal['status']=='complete' and any(c['status'] in ('future_or_unattempted','intent_without_receipt') for c in states):raise JournalError('complete seal has unfinished slots')
            if seal['status']=='failed':
                suppressed=[c['id'] for c in states if c['status']=='future_or_unattempted']
                if type(seal['suppressed_count']) is not int or seal['suppressed_count']!=len(suppressed) or seal['suppressed_slots_sha256']!=digest(encode(suppressed)):raise JournalError('suppressed denominator changed')
            if seal['status']=='failed':
                for cell in result['slots']:
                    if cell['status']=='future_or_unattempted':cell['status']='suppressed'
        self._cache=result
        self._states={c['id']:c for c in states}
        self._pending={c['id'] for c in states if c['status']=='intent_without_receipt'}
        self._partials=partials_by_slot
        return copy.deepcopy(result)

    def begin(self,name,*,now_ms):
        self._boundary();manifest=self._current();slot=self._slot(name)
        pending=[self.slots[name] for name in self._pending]
        window=(slot['scheduled_ms'],slot['deadline_ms'])
        if any((p['scheduled_ms'],p['deadline_ms'])!=window for p in pending):
            raise JournalError('prior group receipt or controlled recovery required before next group')
        if len(pending)>=16:raise JournalError('inflight intent group bound')
        if type(now_ms) is not int or not slot['scheduled_ms']<=now_ms<=slot['deadline_ms']:raise JournalError('begin outside fixed slot window')
        if (self.path/('receipt-'+name+'.json')).exists():raise JournalError('slot already closed')
        value={'kind':'intent','claim_sha256':self.claim_hash,'slot':name,'request':slot['request'],'now_ms':now_ms}
        raw=encode(value);self._publish('intent-'+name+'.json',raw)
        return {'intent_sha256':digest(raw),'slot':name}

    def begin_group(self,names,*,now_ms):
        """Return only after every intent is durable; caller may then acquire in parallel.

        Failure returns no group permission; preserved intents require recovery.
        No transport is invoked here. All slot IDs must comprise one full window.
        """
        if not isinstance(names,list) or not names or len(names)!=len(set(names)):
            raise JournalError('unique finite intent group required')
        slots=[self._slot(name) for name in names]
        window=(slots[0]['scheduled_ms'],slots[0]['deadline_ms'])
        expected={s['id'] for s in self.slots.values() if (s['scheduled_ms'],s['deadline_ms'])==window}
        if set(names)!=expected:raise JournalError('complete frozen window group required')
        return [self.begin(name,now_ms=now_ms) for name in names]

    def partial(self,name,body):
        self._boundary();manifest=self._current();slot=self._slot(name)
        if not (self.path/('intent-'+name+'.json')).exists() or (self.path/('receipt-'+name+'.json')).exists():raise JournalError('partial requires open intent')
        parts=[manifest['members'][k] for k in self._partials.get(name,[])]
        if not isinstance(body,bytes) or sum(v['bytes'] for v in parts)+len(body)>slot['body_cap'] or len(parts)>=64:raise JournalError('partial bound')
        self._publish(f'partial-{name}-{len(parts):06d}.bin',body)

    def _receipt(self,name,body,status,metadata):
        slot=self._slot(name)
        if not isinstance(body,bytes) or len(body)>slot['body_cap']:raise JournalError('body cap exceeded')
        if status=='received':
            self._current()
            prefix=b''.join(self._read(k) for k in sorted(self._partials.get(name,[])))
            if not body.startswith(prefix):raise JournalError('receipt contradicts retained partial prefix')
        value={'kind':'receipt','claim_sha256':self.claim_hash,'slot':name,'request':slot['request'],
               'status':status,'body_base64':base64.b64encode(body).decode(),'body_sha256':digest(body),'body_bytes':len(body),'metadata':metadata}
        self._publish('receipt-'+name+'.json',encode(value))

    def record(self,name,body,*,metadata):
        self._boundary();self._current();self._slot(name)
        if not (self.path/('intent-'+name+'.json')).exists():raise JournalError('durable intent required')
        self._receipt(name,body,'received',metadata)

    def recover(self,*,now_ms):
        self._boundary();manifest=self.validate();changed=[]
        if type(now_ms) is not int:raise JournalError('integer recovery clock required')
        for cell in manifest['slots']:
            name=cell['id']
            if cell['status']=='intent_without_receipt':
                if now_ms<json.loads(self._read('intent-'+name+'.json'))['now_ms']:raise JournalError('recovery predates intent')
                status='unavailable';reason='interrupted request; no retry'
            elif cell['status']=='future_or_unattempted' and self.slots[name]['deadline_ms']<now_ms:status='missed';reason='past slot; no backfill'
            else:continue
            self._receipt(name,b'',status,{'reason':reason,'recovered_at_ms':now_ms});changed.append(name)
        if changed:
            count=sum(k.startswith('recovery-') for k in self._current()['members'])
            self._publish(f'recovery-{count:06d}.json',encode({'claim_sha256':self.claim_hash,'now_ms':now_ms,'closed_slots':changed}))
        return self.validate()

    def seal(self,status):
        self._boundary();manifest=self.validate()
        if status not in ('complete','failed'):raise JournalError('terminal status')
        if status=='complete' and any(c['status'] in ('future_or_unattempted','intent_without_receipt') for c in manifest['slots']):raise JournalError('unfinished denominator')
        value={'claim_sha256':self.claim_hash,'status':status,'inventory_sha256':digest(encode(manifest)),
               'slot_count':len(self.slots),'prior_bytes':manifest['bytes'],
               'scope':'source journal seal only; no outer claim completion or financial authorization'}
        if status=='failed':
            suppressed=[c['id'] for c in manifest['slots'] if c['status']=='future_or_unattempted']
            value['suppressed_count']=len(suppressed);value['suppressed_slots_sha256']=digest(encode(suppressed))
        self._publish('seal.json',encode(value),terminal=True)
        return value
