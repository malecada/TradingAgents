"""One exact July25 GET retirement after accepted backup and Data relocation."""
from pathlib import Path
import fcntl, hashlib, json, os, stat, sys, types

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ID = 'real-pilot-july25-recovered-duplicate-retirement-20261006-01'
RELOCATION = 'real-pilot-july25-ledger-relocation-20261006-01'
TARGET = Path('/home/malecada/Data/onchain-pilot-retained-ledgers/eth-paper-resource-pilot-20260924-02/2022-07-25/events.sqlite')
SIZE = 3755212800
SHA = 'ef3dd69023de071cdaec0780b2fbd35463f2832c816ad204aa07cf2c88594235'
PINS_SHA = '07d8553f8567ec3db2f5e922f09f54e0d981e9bc4c8fc33a7d1c2f9896ee16c9'


def need(ok, message):
    if not ok: raise ValueError(message)


def sig(s):
    return [s.st_dev, s.st_ino, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns, stat.S_IMODE(s.st_mode)]


def sources():
    raw = (HERE/'SOURCE_PINS01.json').read_bytes()
    need(hashlib.sha256(raw).hexdigest() == PINS_SHA, 'source pin table differs')
    pins = json.loads(raw)
    modules = {}
    for name, ref in pins.items():
        path = ROOT/ref['path']; body = path.read_bytes()
        need(hashlib.sha256(body).hexdigest() == ref['sha256'], 'source pin differs')
        module = types.ModuleType(name); module.__file__ = str(path)
        exec(compile(body, str(path), 'exec'), module.__dict__)
        modules[name] = module
    return modules['recovery'], modules['cold']


def bound(m, c, ref):
    need(type(ref) is dict and set(ref) == {'path','sha256'} and c['evidence'].get(ref['path']) == ref['sha256'], 'actual pinned outcome required')
    return json.loads(m.metadata(ROOT, ref['path'], ref['sha256']))


def retained(target):
    need(target['path'] == str(TARGET) and target['device'] == 66307 and target['bytes'] == SIZE and target['sha256'] == SHA, 'fixed retained Data descriptor differs')
    need(type(target['stat_identity']) is list and len(target['stat_identity']) == 7
         and target['stat_identity'][0] == 66307 and target['stat_identity'][2] == 1
         and target['stat_identity'][3] == SIZE, 'retained Data identity/device differs')
    need(TARGET.resolve(strict=True) == TARGET and stat.S_ISREG(TARGET.lstat().st_mode)
         and TARGET.lstat().st_nlink == 1 and sig(TARGET.lstat()) == target['stat_identity'], 'retained Data stat differs')
    need(set(p.name for p in TARGET.parent.iterdir()) == {'events.sqlite'}, 'retained Data namespace differs')


def validate(m, c):
    need(c['identity'] == ID and c['schema_version'] == 1 and c['status'] == 'FROZEN_FOR_REVIEW'
         and c['retire_bytes'] == SIZE, 'fixed frozen duplicate selection required')
    m.recovery(ROOT, c['recovery_selection'])
    row = c['recovery_selection']['rows'][0]
    refs = c['relocation']
    need(set(refs) == {'copy_receipt','copy_review','retire_receipt','relocation_receipt','outcome_review',
                      'copy_native','copy_outer','copy_root','retire_outer','retire_root'}, 'exact relocation evidence required')
    records = {k: bound(m,c,v) for k,v in refs.items()}
    cp, cr, rt, bridge, outcome = [records[k] for k in ('copy_receipt','copy_review','retire_receipt','relocation_receipt','outcome_review')]
    need(cr['decision'] == 'accepted' and cr['identity'] == RELOCATION and cr['copy_receipt_sha256'] == refs['copy_receipt']['sha256']
         and cr['full_destination_readback_verified'] is True, 'actual Data COPY acceptance required')
    need(cp['identity'] == RELOCATION and cp['original'] == row['original'] and cp['copy_readback_verified'] is True
         and cp['external_byte_recovery_verified'] is True and cp['typed_name_mode_verified'] is True
         and cp['original_retired'] is False and cp['source_retired'] is False
         and cp['original_claim_sha256'] == m.CLAIM_SHA and cp['original_source'] == m.SOURCE
         and cp['recovery_review'] == c['recovery_selection']['recovery_basis']['outcome_review'], 'copy ancestry differs')
    target = cp['target']
    need(target['stat_identity'][6] == row['original']['mode'], 'retained original mode differs')
    need(rt['identity'] == RELOCATION and rt['original'] == row['original'] and rt['target'] == target
         and rt['source_retired'] is True and rt['original_retired'] is True and rt['original_parent_status'] == 'failed'
         and rt['copy_receipt'] == refs['copy_receipt'] and rt['copy_review'] == refs['copy_review'], 'successful original retirement required')
    need(bridge['identity'] == RELOCATION and bridge['kind'] == 'closed-ledger-cross-volume-relocation' and bridge['predecessor'] == m.GRAPH
         and bridge['original'] == {k:row['original'][k] for k in ('path','bytes','sha256')}
         and bridge['target'] == target and bridge['retirement_evidence'] == refs['retire_receipt']
         and bridge['copy_readback_verified'] is True and bridge['external_byte_recovery_verified'] is True
         and bridge['original_retired'] is True and bridge['original_claim_sha256'] == m.CLAIM_SHA
         and bridge['original_source'] == m.SOURCE, 'retained authority mapping differs')
    need(outcome['decision'] == 'accepted' and outcome['identity'] == RELOCATION
         and outcome['copy_success_accepted'] is True and outcome['original_retirement_success_accepted'] is True
         and outcome['cleanup_verified'] is True,
         'actual complete relocation outcome acceptance required')
    native=records['copy_native'];copy_outer=records['copy_outer'];retire_outer=records['retire_outer']
    need(native['phase']=='complete' and native['child_exit_code']==0 and native['cleanup_verified'] is True
         and not Path(native['cgroup']).exists() and not Path('/proc',str(native['monitor_pid'])).exists()
         and copy_outer['identity']==RELOCATION and copy_outer['phase']=='copy' and copy_outer['entry_selected_exit_code']==0
         and records['copy_root']['actual_root_tool_exit_code']==0, 'actual copy native/outer/Root required')
    need(retire_outer['identity']==RELOCATION and retire_outer['phase']=='retire' and retire_outer['entry_selected_exit_code']==0
         and retire_outer['guard_phase'] is None and retire_outer['guard_child_exit_code'] is None and retire_outer['cleanup_verified'] is None
         and records['retire_root']['actual_root_tool_exit_code']==0, 'actual ordinary retirement outer/Root required')
    for key in set(refs)-{'outcome_review'}:
        ref=refs[key];need(outcome['evidence'].get(ref['path']) == ref['sha256'], 'relocation acceptance scope join differs')
    for path,pin in outcome['evidence'].items():
        need(c['evidence'].get(path) == pin, 'relocation actual source/outcome evidence unbound')
        m.metadata(ROOT,path,pin)
    retained(target)
    need(not os.path.lexists(ROOT/m.ORIGINAL), 'original Root ledger reappeared')
    m.current(ROOT,row['recovered'])
    return row, target


def inactive(m):
    m.inactive()
    for claim in (ROOT/'research_runs').glob('*/claim.json'):
        if claim.with_name('complete.json').exists() or claim.with_name('failed.json').exists(): continue
        record=json.loads(m.metadata(ROOT,str(claim.relative_to(ROOT))))
        for ref in record.get('experiment',{}).get('inputs',{}).values():
            need(not (ROOT/ref['path']).resolve().is_relative_to(TARGET.parent), 'active registered Data consumer')


def retire(m, cold, row, target, c):
    """Finite inherited hold/flock/unlink/disposition pattern, one GET only."""
    for name in ('attempt01.json','complete01.json','failed01.json'):
        need(not os.path.lexists(HERE/name), 'one-use retirement identity spent')
    inactive(m);retained(target);get=m.current(ROOT,row['recovered'])
    need(not os.path.lexists(ROOT/m.ORIGINAL), 'original Root ledger reappeared')
    cold.publish(HERE/'attempt01.json', {'identity':ID,'selection_sha256':c['selection_sha256'],'no_retry':True})
    held=[];attempted=[];removed=[];error=None;stage='open-held-descriptors'
    try:
        for path in (TARGET,get):
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW);held.append(fd)
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        need(sig(os.fstat(held[0])) == target['stat_identity'] and m.identity(os.fstat(held[1])) == row['recovered']['stat_identity'], 'held descriptor differs')
        inactive(m);retained(target);m.current(ROOT,row['recovered'])
        need(not os.path.lexists(ROOT/m.ORIGINAL), 'original Root ledger reappeared')
        stage='unlink-exact-get';attempted.append(row['recovered']['path'])
        get.unlink();removed.append(row['recovered']['path'])
        stage='sync-get-parent';cold.sync_directory(get.parent)
        stage='post-unlink-disposition';retained(target)
        need(not os.path.lexists(get) and not os.path.lexists(ROOT/m.ORIGINAL), 'post-retirement namespace differs')
    except BaseException as caught:error=caught
    finally:
        for fd in reversed(held):
            try:os.close(fd)
            except BaseException as caught:
                if error is None:error=caught;stage='close-held-descriptors'
                else:error.add_note('Additional descriptor close failure: '+repr(caught))
    disposition={'identity':ID,'unlink_attempted':attempted,'removed':removed,
                 'ambiguous_attempts':[p for p in attempted if p not in removed],
                 'get_retired':True if removed else (None if attempted else False),
                 'retained_target':target,'original_parent_status':'failed','no_retry':True}
    if error is not None:
        try:cold.publish(HERE/'failed01.json',disposition|{'stage':stage,'error_type':type(error).__name__})
        except BaseException as secondary:error.add_note('Retirement failure evidence unavailable: '+repr(secondary))
        raise error
    try:cold.publish(HERE/'complete01.json',disposition|{'payload_bytes_retired':SIZE,'all_other_recoveries_retained':True,'data_retained':True})
    except BaseException as error:
        try:cold.publish(HERE/'failed01.json',disposition|{'stage':'publish-complete','error_type':type(error).__name__})
        except BaseException as secondary:error.add_note('Retirement failure evidence unavailable: '+repr(secondary))
        raise


def execute(review_path, review_sha):
    m,cold=sources()
    review=json.loads(m.metadata(ROOT,review_path,review_sha))
    need(review['decision']=='accepted' and review['retirement_identity']==ID
         and review['entry_sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
         and review['retire_only_exact_backup02_get'] is True, 'exact independent release required')
    ref=review['selection'];c=json.loads(m.metadata(ROOT,ref['path'],ref['sha256']))
    for path,pin in c['evidence'].items():m.metadata(ROOT,path,pin)
    for path,pin in review['evidence'].items():m.metadata(ROOT,path,pin)
    row,target=validate(m,c);c=dict(c,selection_sha256=ref['sha256'])
    retire(m,cold,row,target,c)


if __name__=='__main__':
    need(len(sys.argv)==3, 'exact independent release relative path and hash required')
    execute(sys.argv[1],sys.argv[2])
