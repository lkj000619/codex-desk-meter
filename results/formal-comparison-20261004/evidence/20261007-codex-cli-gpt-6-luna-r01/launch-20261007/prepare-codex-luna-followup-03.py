"""Prepare the one remaining authorized round using own reviewed source and observations."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, sys, time
BASE=Path('C:/meter-operator-20261004')
PREV=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r03')
ROOT=Path('C:/meter-followups-20261007')
REST=Path('C:/meter-run-restores-20261007/codex-luna-followup02-evaluation')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence,KST
from comparison_manager import prepare_followup
from operator_baseline import verify
tick=time.monotonic();audit=read(REST/'frozen-validator-audit.json')
assert audit['reference_review_applied'] and audit['inventory_bytes_verified'] and audit['reference_status']=='fail'
assert not audit['normal_readable_screen_observed'] and audit['remaining_followup_rounds']==1
previous=read(PREV/'run-manifest.json');ledger_path=Path(previous['operator']['comparison']['ledger'])
ledger_before=read(ledger_path);assert len(ledger_before['runs'])==3 and all(x['reviewed'] for x in ledger_before['runs'])
remaining=7200-sum(x['elapsed_seconds'] for x in ledger_before['runs'][1:]);assert abs(remaining-2965.735)<0.00001
old_hashes={name:digest((PREV/name).read_bytes()) for name in ('run-manifest.json','reference-review.json','comparison-source.bundle','operator-source-freeze.json')}
paths=[PREV/'operator-observation'/name for name in (
    'user-observation-confirmation.json','user-video-01/video-review.json','host-semantic-review.json',
    'independent-host-checks/common-stimulus-check.json','hardware-post-upload-reset/runtime-source-binding.json',
    'hardware-post-upload-reset/reset-and-frames-capture/device-serial.bin',
    'hardware-post-upload-reset/reset-and-frames-capture/capture.json','hardware-post-upload-reset/reset-and-frames-capture/sent-frames.jsonl',
    'user-video-01/frames/frame-001.png','user-video-01/frames/frame-009.png','user-video-01/frames/frame-016.png','user-video-01/frames/frame-037.png')]
paths.append(PREV/'operator-policy-decision.json')
feedback={'previous_run_id':PREV.name,'previous_commit':audit['implementation_commit'],'target_ids':['RM1','RM2','RM3','RM4','RM5'],
    'observed':'Followup2 ended environment_failed after1247.265seconds: native usage-limit error during remote compact, with firmware build and valid result JSON preserved. Native token usage unavailable/null. Own original firmware uploaded to same COM3 ESP32-S3 with three hashes verified, matching ELF217445082 prefix boot, SPI SRAM memory test OK, boot-screen submitted and USB Serial/JTAG ready. First64-byte USB receive chunk observed. Both common seq0/1 host writes completed1543bytes at unchanged5-second intervals, but no complete accepted/rejected frame markers; actual device acceptance unconfirmed. User supplied38.55-second current video: LCD now emits colored glyphs/bars. Around0.5-1.5 and8.5-9.5seconds a rotated/clipped ER WINDOWS heading fragment appears twice with SOURCE STALE fragments. Other samples show isolated rotated/clipped edge glyphs;12.5-13.5seconds have almost no text. Physical rotation near34.5-36.5seconds still shows duplicated fragmented text. No legible58%/82% or three complete information views. User confirms both BOOT and RESET pressed; exact times/order/count unknown, so changes are not attributed to BOOT alone or automatic restart. Review RM1 pass/RM2 partial/RM3 fail/RM4 fail/RM5 not_run. Independent restored Python22 with no skips, three original C checks and17provider validity cases passed. Common declared collector/encoder exactly match fixed reference and archived production C CLI accepts0/1. Own wire/schema tests differ from frozen operator29, which remains not_run. Current policy eligible: no confirmed forbidden shell composition among129 commands; previous invalid policy remains separate.',
    'expected':'Meet the unchanged product/RM requirements from your own current implementation and fixed inputs. Display complete legible five-hour remaining58% and weekly remaining82% with stale/provenance semantics; accept normal common seq0/1; expose usage/global-reset/diagnostic information through BOOT navigation and return. Preserve confirmed host collector/encoder/provider correctness. Diagnose and implement from own source and fixed board/vendor references. Do not access operator or other candidate directories, accounts/network, serial/flash, global settings or launch another model/session. One command per shell call; no pipelines or composed statements. This is the final authorized followup round3: remaining2965.735seconds, runner timeout floor2965seconds, at most this one invocation. No operator repair method, new board facts or replacement reference supplied. Report actual unmeasured hardware and token fields honestly.',
    'evidence':[{'path':str(path),'sha256':digest(path.read_bytes())} for path in paths]}
ROOT.mkdir(exist_ok=True)
save(ROOT/'operator-feedback-luna-followup-03.json',feedback)
RUN=prepare_followup(ledger_path,ROOT,feedback);CO=RUN/'checkout'
m=read(RUN/'run-manifest.json');head=benchmark.git('rev-parse','HEAD',cwd=CO)
assert RUN.name=='20261007-codex-cli-gpt-6-luna-r01'
assert m['operator']['local_base_commit']==head and m['operator']['comparison']['round']==3 and m['execution']['timeout_seconds']==2965
assert not benchmark.git('status','--porcelain',cwd=CO)
assert all(not (CO/name).exists() for name in ('build','build-idf','build-host','sdkconfig'))
freeze=read(PREV/'operator-source-freeze.json');verified={};omitted={}
for name,item in freeze['sources'].items():
    if name.startswith(('docs/agent-runs/'+PREV.name+'/', 'results/'+PREV.name+'/')):
        omitted[name]='Previous submission removed by frozen followup manager';continue
    probe=subprocess.run(['git','-c','core.longpaths=true','rev-parse',freeze['commit']+':'+name],cwd=CO,capture_output=True,text=True)
    if probe.returncode:
        assert name=='sdkconfig' and not (CO/name).exists();omitted[name]='Generated ignored sdkconfig not inherited';continue
    raw=(PREV/item['operator_raw_copy']).read_bytes();actual=(CO/name).read_bytes()
    assert raw.replace(b'\r\n',b'\n')==actual.replace(b'\r\n',b'\n'),name
    assert benchmark.git('rev-parse',head+':'+name,cwd=CO)==probe.stdout.strip(),name
    verified[name]={'original_raw_sha256':digest(raw),'new_working_copy_sha256':digest(actual),'git_blob_unchanged':True,'line_ending_normalized_content_unchanged':True}
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
assert len(verified)==33 and all(digest((PREV/name).read_bytes())==value for name,value in old_hashes.items())
assert benchmark.git('rev-parse','HEAD',cwd=PREV/'checkout')==freeze['commit']
note={'run_id':RUN.name,'date':datetime.now(KST).date().isoformat(),'recorded_at':datetime.now(timezone.utc).isoformat(),
    'previous_run_id':PREV.name,'previous_frozen_commit':freeze['commit'],'prepared_commit':head,
    'product_source_verified':verified,'omitted_prior_outputs':omitted,'inherited_generated_files':0,
    'immutable_input_files_verified':57,'previous_frozen_files_unchanged':old_hashes,'original_candidate_commit_unchanged':True,
    'scope':'Own tracked source equivalence, no inherited build outputs; observational feedback only.',
    'preparation_seconds':time.monotonic()-tick,'model_calls_during_preparation':0,'round':3,'reserved_seconds':2965,
    'remaining_exact_seconds':remaining,'remaining_rounds_including_this':1}
save(RUN/'operator-source-preparation.json',note)
m['operator']['evidence']['operator-source-preparation.json']=digest((RUN/'operator-source-preparation.json').read_bytes());save(RUN/'run-manifest.json',m)
save(ROOT/'prepared-luna-followup-03.json',{'directory':str(RUN),'run_id':RUN.name,'round':3,'local_base_commit':head,'source_preparation_sha256':digest((RUN/'operator-source-preparation.json').read_bytes())})
print(json.dumps({'run_id':RUN.name,'round':3,'source_files_verified':len(verified),'generated_files_inherited':0,'timeout_seconds':2965,'model_calls':0}))
