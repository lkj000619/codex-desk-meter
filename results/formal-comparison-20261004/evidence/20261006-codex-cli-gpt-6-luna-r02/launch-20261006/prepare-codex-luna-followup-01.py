"""Prepare one own-source Luna followup with observational feedback only."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, sys, time
BASE=Path('C:/meter-operator-20261004')
PREV=Path('C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01')
ROOT=Path('C:/meter-followups-20261006')
DIAG=Path('C:/meter-operator-diagnostics-20261006/codex-luna-r01-black-screen')
REST=Path('C:/meter-run-restores-20261006/codex-luna-r01-evaluation')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest, read, save, verify_evidence
from comparison_manager import prepare_followup
from operator_baseline import verify

tick=time.monotonic();audit=read(REST/'frozen-validator-audit.json')
assert audit['reference_review_applied'] and audit['inventory_bytes_verified'] and audit['reference_status']=='fail'
previous=read(PREV/'run-manifest.json');ledger_path=Path(previous['operator']['comparison']['ledger'])
ledger_before=read(ledger_path);assert len(ledger_before['runs'])==1 and ledger_before['runs'][0]['reviewed']
old_hashes={n:digest((PREV/n).read_bytes()) for n in ('run-manifest.json','reference-review.json','comparison-source.bundle','operator-source-freeze.json')}
copies=PREV/'operator-followup-observations-20261006';copies.mkdir(exist_ok=False)
selected=['user-after-diagnostic-reset.json','hard-reset-capture.json','hard-reset-serial.bin',
          'post-reset-reference-capture/capture.json','post-reset-reference-capture/device-serial.bin','post-reset-reference-capture/sent-frames.jsonl',
          'reset-and-frames-session.json','reset-and-frames-capture/capture.json','reset-and-frames-capture/device-serial.bin','reset-and-frames-capture/sent-frames.jsonl']
for name in selected:
    target=copies/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(DIAG/name,target)
save(copies/'observation-origin.json',{'date':'2026-10-06','previous_run_id':PREV.name,
    'app_sha256':'3af7fd933b743ea7b16ba02627617e3adb3be0d5273eb9deb184f1be9c9d51d6',
    'scope':'Own original firmware runtime observations after operator native resets, plus user continued-black report. Separate dated addition; original evaluation unchanged.',
    'files':{n:digest((copies/n).read_bytes()) for n in selected},'source_modifications':0,'firmware_rebuilds':0,'flash_writes_during_diagnosis':0})
paths=[PREV/'operator-observation/hardware-attempt-02/user-black-screen-report.json',
       PREV/'operator-observation/host-semantic-limitations.json',
       PREV/'operator-observation/independent-host-checks/common-stimulus-check.json',
       *[copies/n for n in selected],copies/'observation-origin.json']
feedback={'previous_run_id':PREV.name,'previous_commit':audit['implementation_commit'],'target_ids':['RM1','RM2','RM3','RM4','RM5'],
    'observed':'Initial completed; original review RM1/RM2 partial, RM3 fail, RM4/RM5 not_run. Frozen original app was reuploaded on COM3 with verified image hashes; user reports LCD remains black. Separate dated observations after operator native hard reset: normal boot, PSRAM memory test OK, LCD initialization returned, USB receiver ready. One later common-data capture contains actual accepted cdm/1 sequence=0; frame1 host write timed out. A second reset/capture completed both host writes but contains no accepted/rejected frame logs; latest receipt remains unconfirmed. User continued-black report applies to first diagnostic reset. No BOOT-count or 30-second optical observation was supplied. Common wire encoder exactly matches; production collector payload has eight reported differences in identity/reset-status/error fields and 16/17 provider validity cases match (available-over-stale-threshold accepted after coercion). Full 29-case production C pipeline oracle was not completed. Initial command audit also found eight piped calls and one three-statement semicolon call contrary to unchanged shell restrictions.',
    'expected':'Meet the unchanged fixed product and RM contract using the same fixture/reference UTC and production collector/encoder/receiver. Correctly collect/encode and accept normal common seq0/1; visibly display five-hour remaining58% and weekly remaining82% retaining stale/provenance meaning, and make usage/global-reset/diagnostic information reachable with BOOT navigation and return. Preserve fixed provider semantics and schema validation. Keep 30-second continuity as a separate product requirement and honestly mark unobserved hardware/timing. All common task restrictions remain: one command per shell call, no pipelines or composed statements, no real accounts/network, serial/flash, other implementation or operator directories. Diagnose and implement using your own source and already fixed inputs; no operator repair method is supplied.',
    'evidence':[{'path':str(p),'sha256':digest(p.read_bytes())} for p in paths]}
save(ROOT/'operator-feedback-luna-followup-01.json',feedback)
RUN=prepare_followup(ledger_path,ROOT,feedback);CO=RUN/'checkout'
m=read(RUN/'run-manifest.json');head=benchmark.git('rev-parse','HEAD',cwd=CO)
assert m['operator']['local_base_commit']==head and m['operator']['comparison']['round']==1
assert not benchmark.git('status','--porcelain',cwd=CO)
assert all(not (CO/n).exists() for n in ('build','build-idf','build-host','sdkconfig'))
freeze=read(PREV/'operator-source-freeze.json');verified={};omitted={}
for name,item in freeze['sources'].items():
    if name.startswith(('docs/agent-runs/'+PREV.name+'/', 'results/'+PREV.name+'/')):
        omitted[name]='Previous submission intentionally removed by frozen followup manager';continue
    probe=subprocess.run(['git','-c','core.longpaths=true','rev-parse',freeze['commit']+':'+name],cwd=CO,capture_output=True,text=True)
    if probe.returncode:
        assert name=='sdkconfig' and not (CO/name).exists();omitted[name]='Ignored generated sdkconfig not inherited; fixed defaults preserved';continue
    raw=(PREV/item['operator_raw_copy']).read_bytes();actual=(CO/name).read_bytes()
    assert raw.replace(b'\r\n',b'\n')==actual.replace(b'\r\n',b'\n'),name
    assert benchmark.git('rev-parse',head+':'+name,cwd=CO)==probe.stdout.strip(),name
    verified[name]={'original_raw_sha256':digest(raw),'new_working_copy_sha256':digest(actual),'git_blob_unchanged':True,'line_ending_normalized_content_unchanged':True}
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
assert all(digest((PREV/n).read_bytes())==v for n,v in old_hashes.items())
assert benchmark.git('rev-parse','HEAD',cwd=PREV/'checkout')==freeze['commit']
note={'run_id':RUN.name,'date':'2026-10-06','recorded_at':datetime.now(timezone.utc).isoformat(),
    'previous_run_id':PREV.name,'previous_frozen_commit':freeze['commit'],'prepared_commit':head,
    'product_source_verified':verified,'omitted_prior_outputs':omitted,'inherited_generated_files':0,
    'immutable_input_files_verified':57,'previous_frozen_files_unchanged':old_hashes,'original_candidate_commit_unchanged':True,
    'scope':'Own tracked source equivalence and no inherited generated output; no product source or frozen input modification. Observations only, no diagnostic implementation methods.',
    'preparation_seconds':time.monotonic()-tick,'model_calls_during_preparation':0,'round':1,'reserved_seconds':7200,'remaining_rounds_including_this':3}
save(RUN/'operator-source-preparation.json',note)
m['operator']['evidence']['operator-source-preparation.json']=digest((RUN/'operator-source-preparation.json').read_bytes());save(RUN/'run-manifest.json',m)
save(ROOT/'prepared-luna-followup-01.json',{'directory':str(RUN),'run_id':RUN.name,'round':1,'local_base_commit':head,'source_preparation_sha256':digest((RUN/'operator-source-preparation.json').read_bytes())})
print(json.dumps({'run_id':RUN.name,'round':1,'source_files_verified':len(verified),'generated_files_inherited':0,'remaining_seconds':7200,'model_calls':0}))
