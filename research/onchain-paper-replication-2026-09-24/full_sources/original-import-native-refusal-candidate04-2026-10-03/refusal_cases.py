"""Finite source-only denominator. Importing this file creates no authority."""
GROUPS=(
 ('wrong-kind',('kind',)),('wrong-job-input-hash',('job-input','job-hash')),
 ('bool-unknown-policy',('policy-bool','policy-unknown')),('matching-swap',('matching-swap',)),
 ('source-kernel-helper',('source','kernel','helper')),('motif-order-identity',('motif-order','motif-identity')),
 ('target-mapping-order-array',('target-mapping','node-order','target-array')),('copied-import',('receipt-copy','capability-copy')),
 ('owner-lease-death',('owner-death','lease-terminal')),('post-lease-mutation',('post-lease-mutation',)),
 ('purpose-ack',('wrong-purpose','wrong-ack')),('matrix-count',('wrong-matrix','wrong-count')),
 ('reservation',('reservation',)),('legacy-backend',('legacy-backend',)),
 ('journal-scientific',('journal-scientific',)),('financial-closure',('financial-closure',)),
)
NAMES=tuple(name for _,values in GROUPS for name in values)
PRECLAIM=('kind','source','kernel','helper')
NO_JOURNAL=PRECLAIM+('policy-bool','policy-unknown','reservation','target-mapping')
NO_OWNER=PRECLAIM+('policy-bool','policy-unknown','reservation','job-input','job-hash','target-mapping')
FRAGMENTS={'kind':'native-only file limits require compact_resource','job-input':'import job input differs','job-hash':'import job hash differs','policy-bool':'import numeric limit','policy-unknown':'import policy fields','matching-swap':'original numeric evidence changed','source':'registered source hash differs','kernel':'registered source hash differs','helper':'registered source hash differs','motif-order':'original object replaced','motif-identity':'original Dictionary identity changed','target-mapping':'complete distinct target mapping required','node-order':'import target objects changed','target-array':'import target objects changed','receipt-copy':'import stage membership changed','capability-copy':'import execution authority replaced','owner-death':'representation terminal marker exists','lease-terminal':'representation terminal marker exists','post-lease-mutation':'import target objects changed','wrong-purpose':'exact MCM purpose differs','wrong-ack':'matcher returned another purpose','wrong-matrix':'MCM matrix','wrong-count':'MCM completed denominator differs','reservation':'both target pair reservations required','legacy-backend':'dictionary/backend/matching identity differs','journal-scientific':'resource journal numerical component publication not admitted','financial-closure':'actual compact dictionary and denominator required'}
def identity(name):
    if name not in NAMES:raise ValueError('unknown refusal case')
    return 'original-import-refusal-'+str(NAMES.index(name)+1).zfill(2)+'-20261003-01'
def policy(name):
    if name not in NAMES:raise ValueError('unknown refusal case')
    return {'schema_version':1,'case':name,'identity':identity(name),'claim_cardinality_max':0 if name in PRECLAIM else 1,'owner_cardinality_max':0 if name in NO_OWNER else 1,'expected_stage':'admission-before-claim' if name in PRECLAIM else 'registered-worker-after-claim-before-publication','expected_exception':'ValueError','message_fragment':FRAGMENTS[name],'before_any_target_publication':True}
def selected(job):
    jobs=job['payload']['representation_jobs']
    if len(jobs)!=1:raise ValueError('one refusal representation required')
    item=next(iter(jobs.values()));case=item['descriptor']['resource_fixture']['case']
    if not case.startswith('refusal-') or case[8:] not in NAMES:raise ValueError('unknown finite refusal case')
    return case[8:]
