"""Prepare own-source round2, stripping only new-copy generated caches."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,sys,time,math
BASE=Path('C:/meter-operator-20261004');PREV=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r01')
ROOT=Path('C:/meter-followups-20261006');REST=Path('C:/meter-run-restores-20261006/codex-sol-followup01-final')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from comparison_manager import prepare_followup
from operator_baseline import verify
tick=time.monotonic();audit=read(REST/'frozen-validator-audit.json');previous=read(PREV/'run-manifest.json')
assert audit['rm_review_completed'] and audit['inventory_bytes_verified'] and audit['reference_status']=='fail'
ledger_path=Path(previous['operator']['comparison']['ledger']);ledger=read(ledger_path)
assert len(ledger['runs'])==2 and all(v['reviewed'] for v in ledger['runs'])
remaining=7200-sum(v['elapsed_seconds'] for v in ledger['runs'] if v['round'])
paths=['operator-observation/independent-host-checks/common-stimulus-check.json',
    'operator-observation/independent-host-checks/legacy-collector-payload-differences.json',
    'operator-observation/receiver-source-review.json','operator-observation/reference-capture-r1/sent-frames.jsonl',
    'operator-observation/reference-capture-r1/device-serial.bin','operator-observation/user-photo-01/photo-review.json',
    'operator-observation/user-photo-01/capture-identity-confirmation.json','operator-observation/shell-command-policy-audit.json']
feedback={'previous_run_id':PREV.name,'previous_commit':audit['implementation_commit'],'target_ids':['RM2','RM3','RM4','RM5'],
    'observed':'Own followup1 completed. RM1 pass; RM2 partial: encoder exactly matches fixed frames and production C host plus actual device accept seq0/1. Legacy collector payload differs only in global reset error_code at two locations (SOURCE_STALE instead of reference null); all other values, including remaining58/82, match. Device stimulus used common operator replay; full own collector-to-device path unproven. User photograph has dark panel and horizontal color bands with no legible title/numbers/text. User reports no information change with any button; manual RESET reboots to same image. This is deliberate reset, not evidence of spontaneous reboot.30s continuity, exact navigation count and timing unmeasured. Four explicit shell pipelines in own prior commands violate existing common-task restriction; final Git permission denial was respected with no later tool action.',
    'expected':'Under unchanged product/reference contract and common task restrictions, collect/encode correct fixed fixture data and visibly display remaining58%/82% with stale/provenance meaning, usage/global-reset/diagnostic information and working BOOT information navigation/return. Preserve already achieved normal seq0/1 acceptance. Mark unobserved physical/timing behavior honestly. All predeclared shell/access/permission restrictions remain in force; no real account access, serial/flash, other implementation inputs or permission bypass.',
    'evidence':[{'path':str(PREV/name),'sha256':digest((PREV/name).read_bytes())} for name in paths]}
save(ROOT/'operator-feedback-followup-02.json',feedback)
RUN=prepare_followup(ledger_path,ROOT,feedback);CO=RUN/'checkout';m=read(RUN/'run-manifest.json')
before=benchmark.git('rev-parse','HEAD',cwd=CO)
assert m['operator']['local_base_commit']==before and m['operator']['comparison']['round']==2
generated={}
targets=[CO/name for name in ('build','build-host') if (CO/name).exists()]
targets.extend(p for p in CO.rglob('__pycache__') if '.git' not in p.relative_to(CO).parts)
for target in targets:
    target=target.resolve()
    assert target.is_relative_to(CO.resolve()) and target.is_relative_to(ROOT.resolve()) and target!=CO.resolve()
    assert target.name in ('build','build-host','__pycache__')
    if target.is_dir():
        for p in target.rglob('*'):
            if p.is_file():generated[p.relative_to(CO).as_posix()]={'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())}
        shutil.rmtree(target)
for p in list(CO.rglob('*.pyc')):
    if '.git' in p.relative_to(CO).parts:continue
    resolved=p.resolve();assert resolved.is_relative_to(CO.resolve()) and resolved.suffix=='.pyc'
    generated[p.relative_to(CO).as_posix()]={'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())};p.unlink()
assert len(generated)==3 and all(n.endswith('.pyc') for n in generated),generated
delta=benchmark.git('diff','--name-only',cwd=CO).splitlines()
assert set(delta)==set(generated),delta
freeze=read(PREV/'operator-source-freeze.json');source_verified={}
for name,item in freeze['sources'].items():
    if name.startswith(('docs/agent-runs/'+PREV.name+'/', 'results/'+PREV.name+'/')):continue
    raw=(PREV/item['operator_raw_copy']).read_bytes();actual=(CO/name).read_bytes()
    assert raw.replace(b'\r\n',b'\n')==actual.replace(b'\r\n',b'\n'),name
    assert benchmark.git('rev-parse',before+':'+name,cwd=CO)==benchmark.git('rev-parse',freeze['commit']+':'+name,cwd=CO),name
    source_verified[name]={'original_raw_sha256':digest(raw),'new_working_copy_sha256':digest(actual),'git_blob_unchanged':True,'line_ending_normalized_content_unchanged':True}
info=CO/'.git/info/exclude';info.write_bytes(info.read_bytes()+b'\n/build/\n/build-host/\n__pycache__/\n*.pyc\n')
benchmark.git('add','--all',cwd=CO)
benchmark.git('-c','user.name=Benchmark','-c','user.email=benchmark@localhost','commit','-m','Exclude inherited generated Python bytecode from new followup copy',cwd=CO)
after=benchmark.git('rev-parse','HEAD',cwd=CO);m['operator']['local_base_commit']=after
assert not benchmark.git('status','--porcelain',cwd=CO) and not (CO/'build').exists() and not (CO/'build-host').exists()
assert not list(CO.rglob('*.pyc')) and len(source_verified)==18
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
note={'run_id':RUN.name,'date':'2026-10-06','recorded_at':datetime.now(timezone.utc).isoformat(),
    'scope':'New-copy generated bytecode removal/local Git excludes only; no product source, fixed inputs, profile/global permissions or previous frozen evidence/cost changed.',
    'previous_run_id':PREV.name,'previous_frozen_commit':freeze['commit'],'prepared_commit_before_cleanup':before,'prepared_commit_after_cleanup':after,
    'deleted_generated_outputs':generated,'deleted_files':len(generated),'product_source_verified':source_verified,
    'immutable_input_files_verified':57,'local_git_exclude_generated_outputs_only':True,
    'starting_source_reference_unchanged':m['operator']['comparison']['starting_commit']==freeze['commit'],
    'original_candidate_commit_unchanged':benchmark.git('rev-parse','HEAD',cwd=PREV/'checkout')==freeze['commit'],
    'preparation_seconds':time.monotonic()-tick,'model_calls_during_preparation':0,'round':2,
    'reserved_seconds':math.floor(remaining),'remaining_seconds_including_this':remaining,'remaining_rounds_including_this':2}
save(RUN/'operator-generated-output-cleanup.json',note)
m['operator']['evidence']['operator-generated-output-cleanup.json']=digest((RUN/'operator-generated-output-cleanup.json').read_bytes())
save(RUN/'run-manifest.json',m)
save(ROOT/'prepared-followup-02.json',{'directory':str(RUN),'run_id':RUN.name,'round':2,'local_base_commit':after,
    'cleanup_note_sha256':digest((RUN/'operator-generated-output-cleanup.json').read_bytes())})
print(json.dumps({'run_id':RUN.name,'round':2,'deleted_generated_files':len(generated),'source_files_verified':len(source_verified),
    'local_base_commit':after,'remaining_seconds':remaining,'reserved_seconds':math.floor(remaining),'model_calls':0}))
