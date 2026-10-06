"""Emit only reviewable metadata candidates in this owned directory; no authority."""
import json,hashlib
from pathlib import Path
from check01 import run,HERE,FINAL,b,read,selected

def main():
    result,job,plan=run()
    out=HERE/'metadata_candidate01'
    out.mkdir(exist_ok=False)
    refs=read(FINAL/'INPUT_REFS02.json');changes=[]
    for role,value in [('execution_job',job),('producer_plan',plan)]:
        before=b.metadata(HERE.parents[3],refs[role]);body=b.raw(value)
        (out/(role+'.json')).write_bytes(body)
        old=selected(before)['descriptor'] if role=='execution_job' else before['producers'][selected(job)['producer']]['descriptor']
        new=selected(value)['descriptor'] if role=='execution_job' else value['producers'][selected(job)['producer']]['descriptor']
        pointer=('/payload/representation_jobs/'+next(iter(job['payload']['representation_jobs'])) if role=='execution_job' else '/producers/'+selected(job)['producer'])+'/descriptor/compact_execution/policy_sha256'
        changes.append({'role':role,'historical_reference':refs[role],'candidate_sha256':hashlib.sha256(body).hexdigest(),'candidate_bytes':len(body),'patch':[{'op':'test','path':pointer,'value':old['compact_execution']['policy_sha256']},{'op':'replace','path':pointer,'value':new['compact_execution']['policy_sha256']}],'inverse':[{'op':'test','path':pointer,'value':new['compact_execution']['policy_sha256']},{'op':'replace','path':pointer,'value':old['compact_execution']['policy_sha256']}]})
    (out/'CHANGES01.json').write_text(json.dumps({'status':'CANDIDATE_ONLY_NOT_REGISTERED_NOT_ADMITTED','historical_identity':'eth-paper-real-data-end-to-end-resource-20261005-01','historical_state':'FAILED_SPENT_NEVER_REOPEN','changes':changes,'qualification':'These are concrete two-field repair examples, not a runnable successor identity, registration or release.'},indent=2)+'\n')
    (HERE/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
