"""Finalize post-upload observations and publish a separate terminal snapshot."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT=Path.cwd();BASE=Path('C:/meter-operator-20261004')
RUN=Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-flash-r01');CO=RUN/'checkout';OUT=RUN/'operator-observation'
LEDGER=RUN.parent/'ledgers'/f'{RUN.name}.json'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from policy_review import validate_review
from operator_baseline import verify

m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');slot=read(OUT/'hardware-slot.json')
capture=read(OUT/'reference-capture-r1/capture.json');now=datetime.now(timezone.utc).isoformat()
assert slot['commands'][1]['exit_code']==0 and slot['commands'][2]['exit_code']==1
assert capture['status']=='failed' and capture['error']=='Write timeout'
assert capture['frames'][0]['bytes_written'] is None
assert (OUT/'reference-capture-r1/device-serial.bin').stat().st_size==0
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
shutil.copy2(OUT/'hardware-slot.json',OUT/'hardware-slot-before-capture-finalization.json')
slot.update(status='awaiting_user_optical_observation_after_capture_failure',upload_completed=True,
    reference_capture_status='failed',reference_capture_error='Write timeout',receiver_acceptance_observed=False,
    complete_common_stimulus_transmission_confirmed=False,serial_closed_after_capture=True,
    upload_and_capture_ended_at='2026-10-04T19:14:18.942251+00:00',observation_recorded_at=now,
    board_state='Frozen AGY Flash r01 app installed; seq 0 write timed out, seq 1 not attempted; manual LCD/BOOT observation pending.',
    capture_finalization_note='Hardware slot was still allocated when operator helper raised after capture exit 1. Existing raw files are preserved; this records their actual terminal outcome without re-upload, resend or candidate call.')
save(OUT/'hardware-slot.json',slot)
save(OUT/'receiver-source-review.json',{'run_id':RUN.name,'reviewer':'Codex operator','reviewed_at':now,
    'source_commit':f['commit'],'source':'main/main.c','source_sha256':digest((CO/'main/main.c').read_bytes()),
    'serial_source':'components/bsp/src/bsp_serial.c','serial_source_sha256':digest((CO/'components/bsp/src/bsp_serial.c').read_bytes()),
    'sdkconfig_sha256':digest((CO/'sdkconfig').read_bytes()),'artifact_sha256':slot['artifact_sha256'],
    'raw_log':'operator-observation/reference-capture-r1/device-serial.bin','raw_log_sha256':digest(b''),'raw_bytes':0,
    'receipt_status':'not_observed','transport_status':'seq_0_write_timeout_seq_1_not_attempted',
    'source_transport_observation':'Candidate bsp_serial reads UART_NUM_0; sdkconfig enables UART_DEFAULT console and disables USB_SERIAL_JTAG console. COM3 is USB VID303A/PID1001.',
    'inference':'USB transport mismatch is a plausible cause of capture failure, not proven by the empty log alone. No operator source repair, hardware transport substitution or firmware rebuild.',
    'source_acceptance_branch':'Frame accepted: seq is emitted only after parsing and successful meter_state_process_frame; no such line captured.',
    'transmitted_file_limit':'RecordingWriter saves attempted bytes before serial.write. sent-frames.jsonl is one attempted 1543-byte seq 0 frame; write completion/bytes_written unknown. It is not proof of delivery.'})
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='eligible'
assert not benchmark.git('status','--porcelain',cwd=CO)
assert digest(LEDGER.read_bytes())==read(OUT/'terminal-verification.json')['original_ledger_sha256']
PUBLIC=ROOT/'results/formal-comparison-20261004/evidence'/RUN.name/'terminal-20261005'
PUBLIC.mkdir(parents=True,exist_ok=False)
files=[RUN/n for n in ('run-manifest.json','stdout.jsonl','stderr.txt','command-audit.json','prompt.txt','profile.json','candidate-inputs.json','agent-context.json','policy-review.json','operator-policy-decision.json','operator-source-freeze.json')]
files.extend(p for p in OUT.rglob('*') if p.is_file() and p.suffix.lower() not in {'.elf','.map'})
for name in ('scope-exit.json','current-checks.json'):files.append(RUN/'operator-launch-preflight-r2'/name)
for p in files:
    dest=PUBLIC/p.relative_to(RUN);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
shutil.copy2(LEDGER,PUBLIC/'ledger-original.json')
helpers=PUBLIC/'operator-helpers';helpers.mkdir()
for name in ('preserve-agy-flash-r01.py','check-agy-flash-r01.py','observe-agy-flash-r01.py','record-agy-flash-r01-terminal.py'):
    shutil.copy2(RUN.parent/name,helpers/name)
inventory={'run_id':RUN.name,'captured_at':now,'scope':'Separate post-terminal snapshot. Original launch snapshot, terminal manifest, ledger and candidate result absence preserved. Optical/reference review and final package remain pending.',
    'files':{p.relative_to(PUBLIC).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in PUBLIC.rglob('*') if p.is_file()},
    'external_source_bundle':{'path':str(RUN/'operator-terminal-source.bundle'),'sha256':f['source_bundle_sha256']},
    'large_elf_map_files':'Raw copies outside repo; each path/hash/size bound in operator-source-freeze.json.'}
save(PUBLIC/'snapshot-inventory.json',inventory)
progress_path=ROOT/'results/formal-comparison-20261004/progress.json';progress=read(progress_path)
progress.update(checked_at=now,product_executions_completed=3,state='agy_flash_initial_awaiting_optical_observation',
    started_at=m['execution']['started_at'],ended_at=m['execution']['ended_at'],launcher_pid=None,
    policy_review_required=True,policy_status='eligible',rm_review='awaiting_user_optical_observation',
    elapsed_seconds=m['measurement']['wall_clock_seconds'],tokens=m['measurement']['tokens'],
    user_interventions_reported=m['measurement']['user_interventions'],operator_audited_user_interventions=0,
    board_state=slot['board_state'],current_native_scope='AGY global settings/instructions/hooks restored byte-for-byte; owner journal absent.',
    candidate_terminal_status_observed=m['operator']['status'],candidate_current_phase='Initial run terminal; source/policy/host/upload checks complete; optical/reference review pending.',
    last_event_count=383,last_step_type='tool',last_step_state='ERROR',native_tool_events_observed=123,
    ongoing_usage_not_terminal=False,implementation_commit=f['commit'],hardware_artifact_sha256=slot['artifact_sha256'],
    hardware_upload='pass',hardware_reference_capture='failed',hardware_reference_capture_error='Write timeout',
    receiver_acceptance_observed=False,candidate_result_submission='missing',candidate_selection_document_submission='present',
    candidate_host_tests={'python_passed':5,'host_executables_passed':4},
    candidate_collector_common_payload_match=False,candidate_encoder_common_wire_match=True,
    terminal_snapshot=str(PUBLIC.relative_to(ROOT).as_posix()),
    followups_started_for_current_series=0,remaining_current_series_followup_seconds=7200,
    restart_instruction='Current initial run is terminal, reviewed=false. Read frozen source/terminal/policy/capture and obtain user LCD/BOOT observation; do not repeat initial invocation or fabricate final result. Apply reference review once, archive/restore, then prepare allowed followup from own prior source.')
save(progress_path,progress)
print(json.dumps({'public_snapshot_files':len(inventory['files']),'inventory_sha256':digest((PUBLIC/'snapshot-inventory.json').read_bytes()),
    'terminal_status':m['operator']['status'],'policy_status':'eligible','upload_status':'pass','capture_status':'failed',
    'original_manifest_and_ledger_unchanged':True,'candidate_source_clean':True,'optical_review':'pending'}))
