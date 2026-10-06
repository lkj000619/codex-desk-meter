"""Prepare the last authorized Flash call from its own reviewed, unchanged source."""
from datetime import datetime,timezone
from pathlib import Path
import json,sys,time
BASE=Path('C:/meter-operator-20261004');PREV=Path('C:/meter-followups-20261007/20261007-antigravity-cli-agy-flash-r01');ROOT=PREV.parent
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence,KST
from comparison_manager import prepare_followup
from operator_baseline import verify
tick=time.monotonic();audit=read(Path('C:/meter-run-restores-20261007/agy-flash-followup02-final/frozen-validator-audit.json'))
assert audit['rm_review_completed'] and audit['inventory_bytes_verified'] and audit['board_slot_released'] and audit['remaining_followup_rounds']==1
previous=read(PREV/'run-manifest.json');ledger_path=Path(previous['operator']['comparison']['ledger']);ledger_before=read(ledger_path)
assert len(ledger_before['runs'])==3 and all(x['reviewed'] for x in ledger_before['runs'])
remaining=7200-sum(x['elapsed_seconds'] for x in ledger_before['runs'][1:]);assert abs(remaining-5445.281)<0.00001
old_hashes={name:digest((PREV/name).read_bytes()) for name in ('run-manifest.json','reference-review.json','comparison-source.bundle','operator-source-freeze.json')}
paths=['operator-observation/terminal-verification.json','operator-observation/policy-notes.json','reference-review.json','stdout.jsonl',
 'feedback-evidence/000-common-stimulus-check.json','feedback-evidence/001-capture.json','feedback-evidence/002-device-serial.bin',
 'feedback-evidence/003-sent-frames.jsonl','feedback-evidence/004-video-review.json']
feedback={'previous_run_id':PREV.name,'previous_commit':audit['implementation_commit'],'target_ids':['RM1','RM2','RM3','RM4','RM5'],
 'observed':'Own followup2 ended environment_failed after265.500seconds, normalized213498tokens. Last native tool git log -n5 --oneline was denied by unchanged permission policy. Stop-on-denial respected: no subsequent tool/assistant action. All36 tool calls reviewed: own supplied inputs/feedback/product source and git status/ls-files; no product modification, host test/build, new firmware or final result/selection submission. RM1 fail/RM2-RM5 not_run for this attempt. Frozen own product source is unchanged from earlier implementation after generated-output cleanup. Prior observed defects therefore remain unresolved, not newly retested: prior encoder exact common0/1; default/legacy collector common semantics mismatch; two LoadProhibited device panics with no accepted frames; prior video WAITING, no58%/82%, empty/default global/diagnostic views and mixed/blank screen intervals. Current policy eligible, earlier series invalid remains. Current board still contains unrelated last Luna firmware; no physical observation is attributed to this attempt.',
 'expected':'Complete unchanged product/reference implementation and submission from own current source and immutable inputs. Correct common collector semantics and frame0/1 reception; legible five-hour58% and weekly82% with stale/provenance; populated usage/global-reset/diagnostic views and BOOT cycle returning to first view. Preserve the same native permission/task restrictions and stop on denial; access only own current checkout and declared inputs/SDK/vendor sources. No prior checkout/operator/other candidate source, account/network, hardware/serial/flash/global change, new model or extra session. One shell command per tool call, no composition/pipelines. This is FINAL followup3: remaining5445.281seconds, runner floor5445seconds, one invocation only. No replacement initial attempt or extra retry; report unmeasured hardware honestly. No operator implementation repair or new board facts supplied.',
 'evidence':[{'path':str(PREV/name),'sha256':digest((PREV/name).read_bytes())} for name in paths]}
save(ROOT/'operator-feedback-agy-flash-followup-03.json',feedback)
RUN=prepare_followup(ledger_path,ROOT,feedback);CO=RUN/'checkout';m=read(RUN/'run-manifest.json');head=benchmark.git('rev-parse','HEAD',cwd=CO)
assert RUN.name=='20261007-antigravity-cli-agy-flash-r02' and m['operator']['comparison']['round']==3 and m['execution']['timeout_seconds']==5445
assert m['operator']['local_base_commit']==head and not benchmark.git('status','--porcelain',cwd=CO)
assert all(not (CO/name).exists() for name in ('build','build-idf','build-host','sdkconfig','sdkconfig.old'))
freeze=read(PREV/'operator-source-freeze.json');verified={}
for name,item in freeze['sources'].items():
 raw=(PREV/item['operator_raw_copy']).read_bytes();actual=(CO/name).read_bytes()
 assert raw.replace(b'\r\n',b'\n')==actual.replace(b'\r\n',b'\n'),name
 assert benchmark.git('rev-parse',head+':'+name,cwd=CO)==benchmark.git('rev-parse',freeze['commit']+':'+name,cwd=CO),name
 verified[name]={'original_raw_sha256':digest(raw),'new_working_copy_sha256':digest(actual),'git_blob_unchanged':True}
assert len(verified)==36 and all(digest((PREV/name).read_bytes())==value for name,value in old_hashes.items())
info=CO/'.git/info/exclude';info.write_bytes(info.read_bytes()+b'\n/build/\n/build-host/\n/build-idf/\n/sdkconfig\n/sdkconfig.old\n')
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
assert benchmark.git('rev-parse','HEAD',cwd=PREV/'checkout')==freeze['commit']
note={'run_id':RUN.name,'date':datetime.now(KST).date().isoformat(),'recorded_at':datetime.now(timezone.utc).isoformat(),
 'previous_run_id':PREV.name,'previous_frozen_commit':freeze['commit'],'prepared_commit':head,'product_source_verified':verified,
 'inherited_generated_outputs':0,'immutable_input_files_verified':57,'previous_frozen_files_unchanged':old_hashes,'original_candidate_commit_unchanged':True,
 'scope':'Own source equivalence; observation/terminal failure feedback only. Generated outputs absent; local excludes retained.',
 'preparation_seconds':time.monotonic()-tick,'model_calls_during_preparation':0,'round':3,'reserved_seconds':5445,
 'remaining_exact_seconds':remaining,'remaining_rounds_including_this':1}
save(RUN/'operator-source-preparation.json',note);m['operator']['evidence']['operator-source-preparation.json']=digest((RUN/'operator-source-preparation.json').read_bytes());save(RUN/'run-manifest.json',m)
save(ROOT/'prepared-agy-flash-followup-03.json',{'directory':str(RUN),'run_id':RUN.name,'round':3,'local_base_commit':head,'source_preparation_sha256':digest((RUN/'operator-source-preparation.json').read_bytes())})
print(json.dumps({'run_id':RUN.name,'round':3,'source_files_verified':36,'generated_files_inherited':0,'timeout_seconds':5445,'model_calls':0}))
