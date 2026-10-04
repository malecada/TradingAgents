"""Pure metadata contract; no array/model imports and no research authority."""
import hashlib,json,re
from datetime import datetime,timedelta,timezone

def require(v,m):
 if not v:raise ValueError(m)
def stamp(value):
 require(type(value)is str and value.endswith('Z'),'UTC timestamp required');v=datetime.fromisoformat(value.replace('Z','+00:00'));require(v.tzinfo==timezone.utc,'UTC required');return v
def hashed(v):require(type(v)is str and re.fullmatch('[0-9a-f]{64}',v) is not None,'SHA256 required')
def name(v):require(type(v)is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,127}',v) is not None,'registered input role required')
def schema(p):
 require(type(p)is dict and set(p)=={'schema_version','kind','asset','variant','coverage','expected_weeks','parents','cohort_input','cohort_review_input'},'treatment plan fields differ')
 require(type(p['schema_version'])is int and p['schema_version']==1 and p['kind']=='paper-graph-treatment-v1' and p['asset'] in ('ETH','BTC') and p['variant'] in ('whale','fund'),'treatment kind differs')
 require(p['variant']!='fund' or p['asset']=='ETH','paper fund scope is ETH only')
 require(type(p['coverage'])is list and 0<len(p['coverage'])<=64,'finite complete coverage required');weeks=[]
 for pair in p['coverage']:
  require(type(pair)is list and len(pair)==2,'coverage pair required');a,b=map(stamp,pair)
  require(a<b and all(v.weekday()==0 and v.hour==v.minute==v.second==v.microsecond==0 for v in (a,b)),'complete Monday weeks required')
  while a<b:
   weeks.append(a.isoformat().replace('+00:00','Z'));require(len(weeks)<=1024,'finite week limit');a+=timedelta(days=7)
 require(weeks==sorted(set(weeks))==p['expected_weeks'] and set(p['parents'])==set(weeks),'exact full week denominator required')
 for ref in p['parents'].values():
  require(type(ref)is dict and set(ref)=={'manifest_input','coverage_input','claim_input','terminal_input','ledger_input','components'},'parent provenance fields differ')
  for k,v in ref.items():
   if k!='components':name(v)
  require(type(ref['components'])is dict and 0<len(ref['components'])<=10,'bounded exact parent component roles required')
  for path,role in ref['components'].items():
   require(path in ('graph/manifest.json','node_features.npy','node_ids.npy','edge_index.npy','edge_features.npy','edge_aggregates.npy','graph/node_features.npy','graph/node_ids.npy','graph/edge_index.npy','graph/edge_features.npy','graph/edge_aggregates.npy','edge_satoshis.hex','incident_satoshis.hex'),'unknown parent component path');name(role)
 if p['variant']=='whale':require(p['cohort_input'] is None and p['cohort_review_input'] is None,'whale must not select a cohort')
 else:
  require((p['cohort_input'] is None)==(p['cohort_review_input'] is None),'cohort evidence/review paired')
  if p['cohort_input'] is not None:name(p['cohort_input']);name(p['cohort_review_input'])
 return ['treatment-'+p['asset'].lower()+'-'+p['variant']+'-'+w[:10] for w in weeks]

def cohort(document,review,raw_hash,week,end):
 require(set(document)=={'schema_version','kind','entities','known_at','valid_from','valid_to','evidence_inputs'},'historical cohort fields differ')
 require(type(document['schema_version'])is int and document['schema_version']==1 and document['kind']=='original-paper-historical-fund-address-cohort','contemporary substitute forbidden')
 require(type(document['entities'])is dict and len(document['entities'])==65,'original65 entities must be mapped explicitly')
 addresses=[]
 for entity,values in document['entities'].items():
  require(type(entity)is str and entity and type(values)is list and values,'entity requires explicit addresses')
  for address in values:require(type(address)is str and re.fullmatch('0x[0-9a-f]{40}',address) is not None,'canonical ETH address required')
  addresses.extend(values)
 require(len(addresses)==len(set(addresses)) and len(addresses)<=100000,'ambiguous/repeated address membership refused')
 require(stamp(document['valid_from'])<=stamp(week)<stamp(end)<=stamp(document['valid_to']),'historical membership interval does not cover graph')
 stamp(document['known_at']);require(type(document['evidence_inputs'])is dict and document['evidence_inputs'],'authentic historical source evidence required')
 for role,pin in document['evidence_inputs'].items():name(role);hashed(pin)
 require(set(review)=={'schema_version','decision','cohort_sha256','evidence_inputs','known_at','valid_from','valid_to'},'independent cohort review fields')
 require(type(review['schema_version'])is int and review['schema_version']==1 and review['decision']=='accepted-exact-original-historical-cohort' and review['cohort_sha256']==raw_hash and review['evidence_inputs']==document['evidence_inputs'] and all(review[k]==document[k] for k in ('known_at','valid_from','valid_to')),'exact independent historical cohort review required')
 return tuple(sorted(addresses))

def parent_receipts(claim,terminal,ledger,claim_hash,manifest_hash,week,asset):
 hashed(claim_hash);hashed(manifest_hash);hashed(claim.get('registration_sha256'));require(type(claim.get('source'))is str and re.fullmatch('[0-9a-f]{40}',claim['source']) is not None,'parent committed source required')
 require(terminal.get('claim_sha256')==claim_hash and terminal.get('status')=='complete','parent must be genuinely complete')
 require(claim.get('experiment_id')==terminal.get('experiment_id'),'parent claim/terminal identity differs')
 rows=[r for r in ledger if r.get('id')=='graph-'+week[:10]]
 require(len(rows)==1 and rows[0].get('status')=='complete' and rows[0].get('manifest_sha256')==manifest_hash,'parent graph output is not completed in ledger')
 return rows[0]
