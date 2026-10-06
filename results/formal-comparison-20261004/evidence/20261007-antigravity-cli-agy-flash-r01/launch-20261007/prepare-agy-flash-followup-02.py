"""Resume own reviewed Flash source; clean generated outputs in the new copy only."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys, time
BASE=Path('C:/meter-operator-20261004')
PREV=Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02')
ROOT=Path('C:/meter-followups-20261007')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence,KST
from comparison_manager import prepare_followup
from operator_baseline import verify
def extended(path): return Path('\\\\?\\'+str(path.resolve()))
tick=time.monotonic()
audit=read(Path('C:/meter-run-restores-20261005/agy-flash-r02-final/frozen-validator-audit.json'))
assert audit['rm_review_completed'] and audit['inventory_bytes_verified'] and audit['board_slot_released']
previous=read(PREV/'run-manifest.json'); ledger_path=Path(previous['operator']['comparison']['ledger'])
ledger_before=read(ledger_path)
assert len(ledger_before['runs'])==2 and all(x['reviewed'] for x in ledger_before['runs'])
remaining=7200-sum(x['elapsed_seconds'] for x in ledger_before['runs'][1:])
assert abs(remaining-5710.781)<0.00001 and audit['implementation_commit']=='94018f1785a590e1514ef1b5145c40f0c03ffca3'
old_hashes={name:digest((PREV/name).read_bytes()) for name in ('run-manifest.json','reference-review.json','comparison-source.bundle','operator-source-freeze.json')}
paths=['operator-observation/common-stimulus-check.json','operator-observation/reference-capture-r1/capture.json',
       'operator-observation/reference-capture-r1/device-serial.bin','operator-observation/reference-capture-r1/sent-frames.jsonl',
       'operator-observation/user-video-01/video-review.json','operator-observation/user-video-01/capture-identity-confirmation.json',
       'operator-policy-decision.json']
feedback={'previous_run_id':PREV.name,'previous_commit':audit['implementation_commit'],'target_ids':['RM2','RM3','RM4','RM5'],
 'observed':'Own followup1 completed after1489.219seconds. RM1 pass/RM2 partial/RM3 fail/RM4 partial/RM5 partial. Encoder matches unchanged common seq0/1 wires. Default and legacy collectors differ from common payload/provenance/stale semantics. Each host write completed1543bytes, but real serial capture contains two LoadProhibited panics/reboots and no frame acceptance. Confirmed46.3-second video shows WAITING FOR USB DATA, Sequence NONE/cache0, no58%/82%, global NO RECENT RESET RECORD/default FRESH and empty diagnostics. Three view categories appear and dashboard/global/diagnostic/dashboard cycles are visible, but separate BOOT versus IMU trigger/count unknown. Mixed header/body, blank or occluded intervals prevent certifying30-second readable populated continuity; uptime restart cause unknown. Prior policy invalid_for_comparison because inherited generated CTest cache ran own prior-run executables and host build touched prior checkout; the harness contribution and all original results/cost remain preserved. The new copy starts with generated build/cache/config removed; retained product source unchanged.',
 'expected':'Meet unchanged product/RM requirements using own source and fixed inputs: correct collector common fixture semantics, accept normal seq0/1, visibly show legible five-hour remaining58% and weekly remaining82% with stale/provenance meaning, populated usage/global-reset/diagnostic information and BOOT navigation returning to the first view. Preserve common task restrictions and honestly report unmeasured hardware/timing. Diagnose from own source and fixed board/vendor references. No other implementation, prior checkout access, account/network, serial/flash, global settings change or another model/session. One shell command per tool call; no composed commands/pipelines. Remaining followup budget5710.781seconds, at most2 calls including this round2, timeout floor5710seconds. No operator repair method or extra board facts supplied.',
 'evidence':[{'path':str(PREV/name),'sha256':digest((PREV/name).read_bytes())} for name in paths]}
ROOT.mkdir(exist_ok=True);save(ROOT/'operator-feedback-agy-flash-followup-02.json',feedback)
RUN=prepare_followup(ledger_path,ROOT,feedback);CO=RUN/'checkout'
m=read(RUN/'run-manifest.json');before=benchmark.git('rev-parse','HEAD',cwd=CO)
assert RUN.name=='20261007-antigravity-cli-agy-flash-r01' and m['operator']['comparison']['round']==2
assert m['execution']['timeout_seconds']==5710 and m['operator']['local_base_commit']==before
generated={}
for name in ('build','build-host','build-idf','sdkconfig','sdkconfig.old'):
 target=(CO/name).resolve();assert target.parent==CO.resolve() and target.is_relative_to(ROOT.resolve())
 xp=extended(target)
 if xp.is_dir():
  for p in xp.rglob('*'):
   if p.is_file():generated[p.relative_to(extended(CO)).as_posix()]={'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())}
  shutil.rmtree(xp)
 elif xp.is_file():generated[name]={'bytes':xp.stat().st_size,'sha256':digest(xp.read_bytes())};xp.unlink()
delta=benchmark.git('diff','--name-only',cwd=CO).splitlines()
assert delta and all(s.startswith(('build/','build-host/','build-idf/')) or s in ('sdkconfig','sdkconfig.old') for s in delta)
freeze=read(PREV/'operator-source-freeze.json');verified={};omitted={}
for name,item in freeze['sources'].items():
 if name.startswith(('docs/agent-runs/'+PREV.name+'/', 'results/'+PREV.name+'/')) or name in ('sdkconfig','sdkconfig.old'):
  omitted[name]='Prior submission or generated config only';continue
 raw=extended(PREV/item['operator_raw_copy']).read_bytes();actual=extended(CO/name).read_bytes()
 assert raw.replace(b'\r\n',b'\n')==actual.replace(b'\r\n',b'\n'),name
 assert benchmark.git('rev-parse',before+':'+name,cwd=CO)==benchmark.git('rev-parse',freeze['commit']+':'+name,cwd=CO),name
 verified[name]={'original_raw_sha256':digest(raw),'new_working_copy_sha256':digest(actual),'git_blob_unchanged':True}
info=CO/'.git/info/exclude';info.write_bytes(info.read_bytes()+b'\n/build/\n/build-host/\n/build-idf/\n/sdkconfig\n/sdkconfig.old\n')
benchmark.git('add','--all',cwd=CO)
benchmark.git('-c','user.name=Benchmark','-c','user.email=benchmark@localhost','commit','-m','Remove inherited generated outputs from followup source',cwd=CO)
after=benchmark.git('rev-parse','HEAD',cwd=CO);m['operator']['local_base_commit']=after
assert not benchmark.git('status','--porcelain',cwd=CO) and all(not extended(CO/name).exists() for name in ('build','build-host','build-idf','sdkconfig','sdkconfig.old'))
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
assert all(digest((PREV/name).read_bytes())==value for name,value in old_hashes.items())
assert benchmark.git('rev-parse','HEAD',cwd=PREV/'checkout')==freeze['commit']
note={'run_id':RUN.name,'date':datetime.now(KST).date().isoformat(),'recorded_at':datetime.now(timezone.utc).isoformat(),
 'previous_run_id':PREV.name,'previous_frozen_commit':freeze['commit'],'prepared_commit_before_cleanup':before,'prepared_commit_after_cleanup':after,
 'deleted_generated_outputs':generated,'deleted_files':len(generated),'product_source_verified':verified,'omitted_prior_outputs':omitted,
 'immutable_input_files_verified':57,'previous_frozen_files_unchanged':old_hashes,'original_candidate_commit_unchanged':True,
 'scope':'Only new-copy generated output deletion and local Git excludes; retained product source and original evidence unchanged.',
 'preparation_seconds':time.monotonic()-tick,'model_calls_during_preparation':0,'round':2,'reserved_seconds':5710,
 'remaining_exact_seconds':remaining,'remaining_rounds_including_this':2}
save(RUN/'operator-source-preparation.json',note)
m['operator']['evidence']['operator-source-preparation.json']=digest((RUN/'operator-source-preparation.json').read_bytes());save(RUN/'run-manifest.json',m)
save(ROOT/'prepared-agy-flash-followup-02.json',{'directory':str(RUN),'run_id':RUN.name,'round':2,'local_base_commit':after,'source_preparation_sha256':digest((RUN/'operator-source-preparation.json').read_bytes())})
print(json.dumps({'run_id':RUN.name,'round':2,'source_files_verified':len(verified),'deleted_generated_files':len(generated),'timeout_seconds':5710,'model_calls':0}))
