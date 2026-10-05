"""Prepare own-source followup, removing only new-copy generated outputs."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,sys,time
BASE=Path('C:/meter-operator-20261004');PREV=Path('C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01')
ROOT=Path('C:/meter-followups-20261006');REST=Path('C:/meter-run-restores-20261006/codex-sol-r01-final')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from comparison_manager import prepare_followup
from operator_baseline import verify
tick=time.monotonic();audit=read(REST/'frozen-validator-audit.json');previous=read(PREV/'run-manifest.json')
assert audit['rm_review_completed'] and audit['inventory_bytes_verified'] and audit['reference_status']=='fail'
ledger_path=Path(previous['operator']['comparison']['ledger']);assert len(read(ledger_path)['runs'])==1
paths=['operator-observation/independent-host-checks/common-stimulus-check.json','operator-observation/receiver-source-review.json',
    'operator-observation/reference-capture-r1/sent-frames.jsonl','operator-observation/reference-capture-r1/device-serial.bin',
    'operator-observation/user-video-01/video-review.json','operator-observation/user-video-01/capture-identity-confirmation.json']
feedback={'previous_run_id':PREV.name,'previous_commit':audit['implementation_commit'],'target_ids':['RM2','RM3','RM4','RM5'],
    'observed':'Initial completed, RM1 pass. Encoder matches common wires, but production C host and real device reject both common seq 0/1 frames with SCHEMA_INVALID. Legacy personal-usage collector returns SCHEMA_INVALID with no usage entries and different common payload. Uploaded frozen artifact displays no legible title/numbers/information, only blue/dark panel and horizontal color bands in confirmed 12.9s video. User confirms short BOOT x3 and long press have no response. 30s continuity/precise latency/physical selected feature remain unmeasured.',
    'expected':'Under the unchanged product/reference contract and fixed fixture/reference UTC, collect and encode correct data and accept normal seq0/1 on production receiver/device; visibly show five-hour remaining58% and weekly remaining82% with stale/provenance meaning retained; show usage/global-reset/diagnostic information; BOOT navigation reaches the information and returns. Preserve all common task restrictions and honestly mark unobserved hardware/timing. No real account access, serial/flash or other implementation input.',
    'evidence':[{'path':str(PREV/name),'sha256':digest((PREV/name).read_bytes())} for name in paths]}
save(ROOT/'operator-feedback-followup-01.json',feedback)
RUN=prepare_followup(ledger_path,ROOT,feedback);CO=RUN/'checkout'
m=read(RUN/'run-manifest.json');before=benchmark.git('rev-parse','HEAD',cwd=CO)
assert m['operator']['local_base_commit']==before and m['operator']['comparison']['round']==1
generated={}
for name in ('build','build-host'):
    target=(CO/name).resolve();assert target.parent==CO.resolve() and target.is_relative_to(ROOT.resolve())
    if target.is_dir():
        for p in target.rglob('*'):
            if p.is_file():generated[p.relative_to(CO).as_posix()]={'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())}
        shutil.rmtree(target)
assert len(generated)==1413,len(generated)
delta=benchmark.git('diff','--name-only',cwd=CO).splitlines()
assert len(delta)==1413 and all(s.startswith(('build/','build-host/')) for s in delta)
freeze=read(PREV/'operator-source-freeze.json');source_verified={}
for name,item in freeze['sources'].items():
    if name.startswith(('docs/agent-runs/'+PREV.name+'/', 'results/'+PREV.name+'/')):continue
    raw=(PREV/item['operator_raw_copy']).read_bytes();actual=(CO/name).read_bytes()
    assert raw.replace(b'\r\n',b'\n')==actual.replace(b'\r\n',b'\n'),name
    assert benchmark.git('rev-parse',before+':'+name,cwd=CO)==benchmark.git('rev-parse',freeze['commit']+':'+name,cwd=CO),name
    source_verified[name]={'original_raw_sha256':digest(raw),'new_working_copy_sha256':digest(actual),'git_blob_unchanged':True,'line_ending_normalized_content_unchanged':True}
info=CO/'.git/info/exclude';old=info.read_bytes();info.write_bytes(old+b'\n/build/\n/build-host/\n')
benchmark.git('add','--all',cwd=CO)
benchmark.git('-c','user.name=Benchmark','-c','user.email=benchmark@localhost','commit','-m','Exclude inherited generated build output from followup source',cwd=CO)
after=benchmark.git('rev-parse','HEAD',cwd=CO);m['operator']['local_base_commit']=after
assert not benchmark.git('status','--porcelain',cwd=CO) and not (CO/'build').exists() and not (CO/'build-host').exists()
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
note={'run_id':RUN.name,'date':'2026-10-06','recorded_at':datetime.now(timezone.utc).isoformat(),
    'scope':'Only new followup generated outputs/local Git exclude; no product source, fixed inputs, profile, global files, prior freeze/package/review/cost changed.',
    'previous_run_id':PREV.name,'previous_frozen_commit':freeze['commit'],'prepared_commit_before_cleanup':before,'prepared_commit_after_cleanup':after,
    'deleted_generated_outputs':generated,'deleted_files':len(generated),'product_source_verified':source_verified,
    'immutable_input_files_verified':57,'local_git_exclude_generated_outputs_only':True,'starting_source_reference_unchanged':m['operator']['comparison']['starting_commit']==freeze['commit'],
    'original_candidate_commit_unchanged':benchmark.git('rev-parse','HEAD',cwd=PREV/'checkout')==freeze['commit'],
    'preparation_seconds':time.monotonic()-tick,'model_calls_during_preparation':0,'round':1,'reserved_seconds':7200,'remaining_rounds_including_this':3}
save(RUN/'operator-generated-output-cleanup.json',note)
m['operator']['evidence']['operator-generated-output-cleanup.json']=digest((RUN/'operator-generated-output-cleanup.json').read_bytes())
save(RUN/'run-manifest.json',m);save(ROOT/'prepared-followup-01.json',{'directory':str(RUN),'run_id':RUN.name,'round':1,'local_base_commit':after,'cleanup_note_sha256':digest((RUN/'operator-generated-output-cleanup.json').read_bytes())})
print(json.dumps({'run_id':RUN.name,'round':1,'deleted_generated_files':len(generated),'source_files_verified':len(source_verified),'local_base_commit':after,'remaining_seconds':7200,'model_calls':0}))
