"""Reuse the frozen followup manager and prior source-equivalence procedure."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, sys, time
BASE=Path('C:/meter-operator-20261004')
PREV=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r02')
ROOT=Path('C:/meter-followups-20261006')
REST=Path('C:/meter-run-restores-20261006/codex-luna-followup01-evaluation')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest, read, save, verify_evidence, KST
from comparison_manager import prepare_followup
from operator_baseline import verify

tick=time.monotonic();audit=read(REST/'frozen-validator-audit.json')
assert audit['reference_review_applied'] and audit['inventory_bytes_verified'] and audit['reference_status']=='fail'
previous=read(PREV/'run-manifest.json');ledger_path=Path(previous['operator']['comparison']['ledger'])
ledger_before=read(ledger_path);assert len(ledger_before['runs'])==2 and all(r['reviewed'] for r in ledger_before['runs'])
assert 7200-sum(r['elapsed_seconds'] for r in ledger_before['runs'][1:])==4213
old_hashes={n:digest((PREV/n).read_bytes()) for n in ('run-manifest.json','reference-review.json','comparison-source.bundle','operator-source-freeze.json')}
paths=[PREV/'operator-observation'/name for name in (
    'user-black-screen-report.json','host-semantic-review.json','independent-host-checks/common-stimulus-check.json',
    'hardware-post-upload-reset/runtime-source-binding.json','hardware-post-upload-reset/runtime-observation-correction.json',
    'hardware-post-upload-reset/reset-and-frames-capture/device-serial.bin',
    'hardware-post-upload-reset/reset-and-frames-capture/capture.json',
    'hardware-post-upload-reset/reset-and-frames-capture/sent-frames.jsonl')]
paths.append(PREV/'operator-policy-decision.json')
feedback={'previous_run_id':PREV.name,'previous_commit':audit['implementation_commit'],'target_ids':['RM1','RM2','RM3','RM4','RM5'],
    'observed':'Followup1 completed after2987 seconds. Original review RM1 pass, RM2 partial, RM3 fail, RM4/RM5 not_run. Original archived firmware was uploaded to the same COM3 ESP32-S3 with three image hashes verified. Supplemental native reset captured matching ELF SHA prefix81c1bd1d2, normal boot, SPI SRAM memory test OK, LCD initialization returned, boot-screen-submitted log and USB Serial/JTAG receiver ready. The boot-screen-submitted log is not evidence of readable LCD. Current user reply after this upload/reset: continued black screen. Both common seq0/1 host writes completed1543 bytes each at fixed5-second intervals, but device accepted/rejected frame markers were absent; actual receipt remains unconfirmed. BOOT manipulation/count/return and30-second optical continuity were not reported. Independent restored host tests22 Python/3 original C executables passed; candidate final response reported21, preserved separately. Declared common collector payload and wire encoder now exactly match common reference; archived production C CLI accepts both frames, and17/17 provider validity cases match. Candidate29 wire/schema cases passed but frozen operator29 pipeline remains not_run. Own command review found two forbidden pipeline calls at raw39 and288; no in-run operator feedback or source repair.',
    'expected':'Meet unchanged product and RM contract using your own current implementation and fixed inputs. Visibly display the common five-hour remaining58% and weekly remaining82% with stale/provenance semantics, accept normal common seq0/1, and expose usage/global-reset/diagnostics with BOOT navigation and return. Preserve confirmed host collector/encoder/provider correctness and honest unobserved hardware/timing reporting. Keep one command per shell call, no pipelines or composed statements, no account/network or serial/flash access, no other candidate or operator directories. Diagnose and implement from your own source and fixed board/vendor inputs; no operator repair method or new board facts supplied. Remaining4213seconds and2rounds include this invocation; do not launch another session yourself.',
    'evidence':[{'path':str(p),'sha256':digest(p.read_bytes())} for p in paths]}
save(ROOT/'operator-feedback-luna-followup-02.json',feedback)
RUN=prepare_followup(ledger_path,ROOT,feedback);CO=RUN/'checkout'
m=read(RUN/'run-manifest.json');head=benchmark.git('rev-parse','HEAD',cwd=CO)
assert m['operator']['local_base_commit']==head and m['operator']['comparison']['round']==2 and m['execution']['timeout_seconds']==4213
assert not benchmark.git('status','--porcelain',cwd=CO)
assert all(not (CO/n).exists() for n in ('build','build-idf','build-host','sdkconfig'))
freeze=read(PREV/'operator-source-freeze.json');verified={};omitted={}
for name,item in freeze['sources'].items():
    if name.startswith(('docs/agent-runs/'+PREV.name+'/', 'results/'+PREV.name+'/')):
        omitted[name]='Previous submission removed by frozen followup manager';continue
    probe=subprocess.run(['git','-c','core.longpaths=true','rev-parse',freeze['commit']+':'+name],cwd=CO,capture_output=True,text=True)
    if probe.returncode:
        assert name=='sdkconfig' and not (CO/name).exists();omitted[name]='Ignored generated sdkconfig not inherited';continue
    raw=(PREV/item['operator_raw_copy']).read_bytes();actual=(CO/name).read_bytes()
    assert raw.replace(b'\r\n',b'\n')==actual.replace(b'\r\n',b'\n'),name
    assert benchmark.git('rev-parse',head+':'+name,cwd=CO)==probe.stdout.strip(),name
    verified[name]={'original_raw_sha256':digest(raw),'new_working_copy_sha256':digest(actual),'git_blob_unchanged':True,'line_ending_normalized_content_unchanged':True}
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
assert all(digest((PREV/n).read_bytes())==v for n,v in old_hashes.items())
assert benchmark.git('rev-parse','HEAD',cwd=PREV/'checkout')==freeze['commit']
note={'run_id':RUN.name,'date':datetime.now(KST).date().isoformat(),'recorded_at':datetime.now(timezone.utc).isoformat(),
    'previous_run_id':PREV.name,'previous_frozen_commit':freeze['commit'],'prepared_commit':head,
    'product_source_verified':verified,'omitted_prior_outputs':omitted,'inherited_generated_files':0,
    'immutable_input_files_verified':57,'previous_frozen_files_unchanged':old_hashes,'original_candidate_commit_unchanged':True,
    'scope':'Own tracked source equivalence, no inherited build outputs; observational feedback only.',
    'preparation_seconds':time.monotonic()-tick,'model_calls_during_preparation':0,'round':2,'reserved_seconds':4213,'remaining_rounds_including_this':2}
save(RUN/'operator-source-preparation.json',note)
m['operator']['evidence']['operator-source-preparation.json']=digest((RUN/'operator-source-preparation.json').read_bytes());save(RUN/'run-manifest.json',m)
save(ROOT/'prepared-luna-followup-02.json',{'directory':str(RUN),'run_id':RUN.name,'round':2,'local_base_commit':head,'source_preparation_sha256':digest((RUN/'operator-source-preparation.json').read_bytes())})
print(json.dumps({'run_id':RUN.name,'round':2,'source_files_verified':len(verified),'generated_files_inherited':0,'remaining_seconds':4213,'model_calls':0}))
