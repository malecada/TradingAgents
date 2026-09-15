"""Invented source tests; no public transport or financial outcomes."""
import base64
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'research/defi-depth-2026-09-15'
loader=importlib.util.spec_from_file_location('q3_test',HERE/'q3_source.py')
q=importlib.util.module_from_spec(loader);loader.loader.exec_module(q)

class Q3Tests(unittest.TestCase):
    def setUp(self):
        self.design=json.loads((HERE/'q3-design-v2.json').read_text())
        self.days=json.loads((HERE/'q2-spec.json').read_text())['days']
        self.clock=0.;self.calls=[];self.outputs={}
    def publish(self,name,value):
        self.assertNotIn(name,self.outputs);self.outputs[name]=value
    def sleep(self,t):self.clock+=t
    def fetch(self,url,payload):
        self.assertIsInstance(payload,dict);self.calls.append((self.clock,url,payload))
        self.clock+=2
        body=json.dumps({'jsonrpc':'2.0','id':payload['id'],'result':'0x1'}).encode()
        return dict(body=body,http_status=200,headers={},error=None,body_complete=True)
    def source(self,fetch=None):
        return q.p.PacedSource(self.design,self.publish,fetch or self.fetch,monotonic=lambda:self.clock,sleep=self.sleep,
                              utc=lambda:datetime(2026,9,15,tzinfo=timezone.utc))
    def test_response_pacing_and_endpoint_independence(self):
        source=self.source()
        for chain,rid in [('ethereum','a'),('ethereum','b'),('base','c'),('ethereum','d')]:
            source.request(chain,q.member(rid,'eth_chainId',[]),lambda v,t:v)
        self.assertEqual([r[0] for r in self.calls],[0,7,9,14])
        self.assertEqual(len(self.outputs),8)
    def test_rpc_throttle_http200_stops_without_retry(self):
        def fetch(url,payload):
            response=self.fetch(url,payload)
            response['body']=json.dumps({'jsonrpc':'2.0','id':payload['id'],'error':{'code':-32016,'message':'over rate limit'}}).encode()
            return response
        source=self.source(fetch)
        a=source.request('base',q.member('a','eth_chainId',[]),lambda v,t:v)
        b=source.request('base',q.member('b','eth_chainId',[]),lambda v,t:v)
        self.assertEqual((a['status'],b['status']),('unavailable','unavailable'))
        self.assertEqual(len(self.calls),1);self.assertFalse(self.outputs['b-receipt.json']['attempted'])
        raw=base64.b64decode(self.outputs['a-receipt.json']['body_base64'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),self.outputs['a-receipt.json']['body_sha256'])
    def test_http_denial_stops_but_execution_revert_does_not(self):
        for code in [403,418,429,451]:
            self.outputs={};self.calls=[]
            def fetch(url,payload):
                r=self.fetch(url,payload);r['http_status']=code;r['error']='denied';return r
            source=self.source(fetch)
            for rid in ['a','b']:source.request('base',q.member(rid,'eth_chainId',[]),lambda v,t:v)
            self.assertEqual(len(self.calls),1)
        self.outputs={}
        def revert(url,payload):
            r=self.fetch(url,payload);r['body']=json.dumps({'jsonrpc':'2.0','id':payload['id'],'error':{'code':3,'message':'execution reverted'}}).encode();return r
        source=self.source(revert);source.request('base',q.member('x','eth_chainId',[]),lambda v,t:v)
        self.assertFalse(source.stopped)
    def test_excluded_failed_header_and_new_plan(self):
        first=self.days[0]
        receipt={'attempted':True,'request':[q.member('old','eth_getBlockByNumber',[hex(first['candidate_block']),False])],'error':'timeout'}
        keys=q.p.prior_header_keys([receipt]);self.assertEqual(len(keys),1)
        plan=q.p.new_header_plan(self.design,self.days,keys);self.assertEqual(len(plan),1008)
        key=q.p.request_key(plan['2023-11-29'][0]['method'],plan['2023-11-29'][0]['params'])
        with self.assertRaises(ValueError):q.p.new_header_plan(self.design,self.days,keys|{key})
    def boundary(self,price=1):
        cells={k:{'status':'complete'} for k in ('canonical-bracket','wrapper-decimals','wrapper-code','oracle-unit','oracle-base','oracle-wsteth-price','oracle-wsteth-source','oracle-source-code')}
        for k,value in [('wrapper-decimals',18),('oracle-unit',10**8),('oracle-base','0x'+'0'*40),('oracle-wsteth-price',price),('oracle-wsteth-source','0x'+'1'*40)]:cells[k]['value']={'words':[value]}
        for k in ('wrapper-code','oracle-source-code'):cells[k]['value']={'bytecode_bytes':1}
        return cells
    def test_boundary_source_only_not_price_level_selection(self):
        for value in [1,10**8,10**30]:self.assertEqual(q.p.boundary_eligibility(self.boundary(value))['status'],'complete')
        for value in [0,-1]:self.assertEqual(q.p.boundary_eligibility(self.boundary(value))['status'],'unavailable')
        x=self.boundary();x['oracle-unit']['value']['words']=[10**18]
        self.assertEqual(q.p.boundary_eligibility(x)['status'],'unavailable')
    def test_whole_denominator_preserved_when_endpoint_denies(self):
        # Invented context contains no real header/price values.
        context={'prior_header_keys':['invented']*176,'new_headers':q.p.new_header_plan(self.design,self.days,set()),
                 'headers':{d['date']:{'request':[],'body_base64':'','body_bytes':0,'body_sha256':hashlib.sha256(b'').hexdigest(),'http_status':500,'error':'invented unavailable','body_complete':False} for d in self.days[:88]},
                 'ethereum_anchor':{'hash':'0x'+'1'*64,'number':1,'timestamp':1},'first_boundary':{k:q.unavailable('invented missing') for k in ('oracle-unit','oracle-base')}}
        def deny(url,payload):
            r=self.fetch(url,payload);r['http_status']=429;r['error']='denied';return r
        with contextlib.redirect_stdout(io.StringIO()):
            result=q.capture(self.design,self.days,context,self.publish,deny,monotonic=lambda:self.clock,sleep=self.sleep)
        self.publish('summary.json',result)
        cells,outputs=q.manifests(self.design,self.days)
        self.assertEqual(set(self.outputs),set(outputs));self.assertEqual([c['id'] for c in result['cells']],cells)
        self.assertEqual(result['http_requests'],2);self.assertEqual(len(self.calls),2)
        self.assertEqual(len([c for c in result['cells'] if c['id'].endswith('canonical-bracket')]),1096)
        self.assertFalse(result['financial_outcomes_computed'])
    def test_retained_bracket_raw_integrity_and_clock(self):
        day=self.days[0];h=day['candidate_block'];t=day['timestamp']
        req=[q.member(day['date']+'-header-'+side,'eth_getBlockByNumber',[hex(h+i),False]) for i,side in enumerate(('left','right'))]
        values=[{'number':hex(h+i),'timestamp':hex(t+i*2),'baseFeePerGas':'0x1','hash':'0x'+str(i+1)*64,'parentHash':'0x'+str(i)*64} for i in (0,1)]
        body=json.dumps([{'jsonrpc':'2.0','id':r['id'],'result':v} for r,v in zip(req,values)]).encode()
        receipt=dict(request=req,body_base64=base64.b64encode(body).decode(),body_bytes=len(body),body_sha256=hashlib.sha256(body).hexdigest(),http_status=200,error=None,body_complete=True,retrieval_utc='2026-09-15T00:00:00+00:00')
        self.assertEqual(q.p.qualify_retained_bracket(day,receipt)['status'],'complete')
        receipt['body_sha256']='0'*64
        self.assertEqual(q.p.qualify_retained_bracket(day,receipt)['status'],'unavailable')

if __name__=='__main__':unittest.main()
