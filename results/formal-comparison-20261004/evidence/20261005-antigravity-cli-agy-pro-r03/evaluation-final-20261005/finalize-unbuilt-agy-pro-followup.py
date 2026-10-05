"""Preserve one inspected Pro followup that stopped on denial before firmware build."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import subprocess
import sys
import zipfile

ROOT = Path.cwd()
RUN = Path(sys.argv[1])
CO = RUN / 'checkout'
BASE = Path('C:/meter-operator-20261004')
sys.path.insert(0, str(BASE / 'scripts'))
import benchmark
from benchmark_support import read, save, digest, verify_evidence
from operator_baseline import verify
from agy_pilot_environment import paths_for
from policy_review import create_review, validate_review
from comparison_manager import review_run
from evidence_package import create_package, restore_package

m = read(RUN / 'run-manifest.json')
ledger_path = Path(m['operator']['comparison']['ledger'])
ledger = read(ledger_path)
entry = ledger['runs'][-1]
round_number = entry['round']
assert entry['run_id'] == RUN.name and not entry['reviewed']
assert m['agent']['model'] == 'gemini-3.1-pro-high'
assert m['operator']['status'] == 'environment_failed' and m['execution']['ended_at']
terminal_hash = digest((RUN / 'run-manifest.json').read_bytes())
assert terminal_hash == entry['terminal_manifest_sha256']
benchmark.verify_agent_inputs(RUN, m)
verify_evidence(m, RUN)
verify(m, RUN)
assert not (CO / m['outputs']['structured_result']).exists()
assert not (CO / m['outputs']['selection_document']).exists()
assert not list(CO.rglob('*.bin')) and not list(CO.rglob('*.elf'))
events = [json.loads(line) for line in (RUN / 'stdout.jsonl').read_bytes().splitlines()]
init = events[0]['init']
assert init['model'] == 'gemini-3.1-pro-high' and init['permission_mode'] == 'request-review'
assert Path(init['cwd']).resolve() == CO.resolve()
denied = events[-2]['step_update']
assert denied['step_type'] == 'tool' and denied['state'] == 'ERROR'
assert 'user denied permission' in denied['tool_info']['error']['message']
assert events[-1]['event'] == 'result' and events[-1]['result']['denied_actions']
scope = read(RUN / 'operator-launch-preflight/scope-exit.json')
gemini = Path.home() / '.gemini'
assert {k: digest(p.read_bytes()) if p.is_file() else None for k, p in paths_for(gemini).items()} == scope['before_sha256'] == scope['after_sha256']
assert not (gemini / '.agy-pilot-owner.json').exists()
assert subprocess.check_output(['powershell', '-NoProfile', '-Command',
    '@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match "^agy(\\.exe)?$|^opencode(\\.exe)?$" }).Count'], text=True).strip() == '0'
OUT = RUN / 'operator-observation'
OUT.mkdir(exist_ok=False)
originals = OUT / 'terminal-originals'
originals.mkdir()
for p in (RUN / 'run-manifest.json', ledger_path, RUN / 'stdout.jsonl', RUN / 'stderr.txt', RUN / 'command-audit.json'):
    shutil.copy2(p, originals / p.name)
fixed = set(read(RUN / 'candidate-inputs.json')['files'])
sources = {}
for p in CO.rglob('*'):
    rel = p.relative_to(CO)
    if not p.is_file() or any(part in {'.git', '.benchmark-inputs', '__pycache__', 'build', 'build-host'} for part in rel.parts):
        continue
    if rel.as_posix() in fixed:
        continue
    dest = OUT / 'source-snapshot' / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
    sources[rel.as_posix()] = {'bytes': p.stat().st_size, 'sha256': digest(p.read_bytes()), 'operator_raw_copy': dest.relative_to(RUN).as_posix()}
benchmark.git('add', '--all', cwd=CO)
if benchmark.git('diff', '--cached', '--name-only', cwd=CO):
    benchmark.git('-c', 'user.name=Benchmark', '-c', 'user.email=benchmark@localhost', 'commit', '-m', 'Freeze ' + RUN.name, cwd=CO)
commit = benchmark.git('rev-parse', 'HEAD', cwd=CO)
assert not benchmark.git('status', '--porcelain', cwd=CO)
verification = {
    'run_id': RUN.name, 'round': round_number, 'checked_at': datetime.now(timezone.utc).isoformat(),
    'terminal_status': m['operator']['status'], 'execution': m['execution'], 'measurement': m['measurement'],
    'native_model': init['model'], 'native_permission_mode': init['permission_mode'], 'native_cwd': init['cwd'],
    'native_conversation_id': events[0]['conversation_id'], 'native_events': len(events),
    'denial_raw_line': len(events) - 1, 'denied_tool': denied['tool_name'],
    'denied_parameters': denied['tool_info']['parameters'], 'subsequent_tool_calls': 0,
    'original_terminal_manifest_sha256': terminal_hash, 'immutable_input_files_verified': 57,
    'candidate_source_files': len(sources), 'candidate_firmware_artifacts': 0,
    'candidate_result_submission': 'missing', 'candidate_selection_document_submission': 'missing',
    'global_native_files_restored': True, 'owner_journal_present': False,
    'operator_audited_user_interventions': 0, 'operator_product_source_changes': False,
    'board_slot_released': True, 'serial_opened': False, 'product_pass': False
}
save(OUT / 'terminal-verification.json', verification)
freeze = {'run_id': RUN.name, 'commit': commit, 'frozen_at': datetime.now(timezone.utc).isoformat(),
    'original_terminal_manifest_sha256': terminal_hash, 'sources': sources, 'artifacts': {},
    'operator_product_source_modifications': False, 'operator_firmware_rebuild': False}
save(RUN / 'operator-source-freeze.json', freeze)
actions = [s['step_update'] for s in events if s.get('step_update', {}).get('step_type') == 'tool' and s['step_update'].get('state') == 'ACTIVE']
save(OUT / 'policy-notes.json', {'run_id': RUN.name, 'reviewed_at': datetime.now(timezone.utc).isoformat(),
    'actions': [{'index': s['step_index'], 'name': s['tool_name'], 'parameters': s['tool_info'].get('parameters')} for s in actions],
    'denial_raw_line': len(events) - 1, 'later_tool_or_assistant_events': 0,
    'finding': 'Operator inspected all native events. Accesses were own declared checkout inputs/feedback and declared SDK/manufacturer source; built-in task status used its own conversation. No other candidate source, serial/flash, online access, permission change or operator implementation feedback. The last tool denial ended the attempt; ordinary missing-argument errors are separate.'})
decision = {'status': 'eligible', 'reviewer': 'Codex operator',
    'reason': 'Reviewed all native events: only own checkout inputs/feedback and declared SDK/manufacturer source, plus own built-in task management. The final native tool was denied and no later tool or assistant action followed. Stop-on-denial respected. Preserve environment_failed, partial files, absent firmware/submissions and all cost separately.',
    'user_interventions': 0, 'intervention_review': 'No source repair, permissions changes, serial/flash or execution-time implementation feedback. Global files restored and native process/owner absent.',
    'evidence': [{'path': p.relative_to(RUN).as_posix(), 'sha256': digest(p.read_bytes())} for p in (OUT / 'policy-notes.json', OUT / 'terminal-verification.json')]}
save(RUN / 'operator-policy-decision.json', decision)
create_review(RUN / 'run-manifest.json', decision)
names = ['operator-source-freeze.json', 'operator-policy-decision.json']
names += [p.relative_to(RUN).as_posix() for p in OUT.rglob('*') if p.is_file()]
names += [p.relative_to(RUN).as_posix() for p in (RUN / 'operator-launch-preflight').rglob('*') if p.is_file()]
names += [name for name in ('experiment-launch.json', 'native-start-observation.json', 'native-start-observation-prefix.jsonl') if (RUN / name).is_file()]
evidence = [{'path': name, 'sha256': digest((RUN / name).read_bytes())} for name in names]
report = {'run_id': RUN.name, 'reference_inputs_sha256': m['operator']['comparison']['reference_inputs_sha256'],
    'reviewed_at': datetime.now(timezone.utc).isoformat(), 'reviewer': 'Codex operator', 'product_pass': False,
    'items': {key: {'status': 'fail' if key == 'RM1' else 'not_run', 'evidence': evidence,
                    'reason': 'No completed firmware build or submitted implementation result.' if key == 'RM1' else 'No firmware to upload; hardware behavior untested.'} for key in ('RM1', 'RM2', 'RM3', 'RM4', 'RM5')}}
save(RUN / 'operator-reference-review-input.json', report)
review_run(RUN, report)
reviewed = read(RUN / 'run-manifest.json')
assert reviewed['execution'] == m['execution'] and reviewed['measurement'] == m['measurement']
assert reviewed['outputs']['implementation_commit'] == commit
validate_review(reviewed, RUN / 'run-manifest.json')
PACK = Path('C:/meter-run-packages-20261005') / ('agy-pro-r%02d-final' % (round_number + 1))
REST = Path('C:/meter-run-restores-20261005') / PACK.name
created = create_package(RUN, PACK)
save(PACK.parent / (PACK.name + '-create.json'), created)
restored = restore_package(PACK, REST, created['package_manifest_sha256'])
# Launch a separate fresh interpreter with the packaged frozen validators.
audit_program = r'''
from pathlib import Path
import json,subprocess,sys,zipfile
pack=Path(sys.argv[1]);rest=Path(sys.argv[2]);expected=sys.argv[3];frozen=rest.parent/(rest.name+'-frozen-operator');frozen.mkdir(exist_ok=False)
with zipfile.ZipFile(rest/'operator/operator-baseline.zip') as z:
    for info in z.infolist():
        p=frozen/info.filename;assert p.resolve().is_relative_to(frozen.resolve()) and not info.is_dir();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(info))
sys.path.insert(0,str(frozen/'scripts'))
from benchmark_support import read,save,digest,validate_schema,validate_operator,verify_evidence
from benchmark import verify_agent_inputs,validate_preflight_receipt
from policy_review import review_eligibility
from evidence_package import verify_report_dependencies
assert digest((pack/'package-manifest.json').read_bytes())==expected
inv=read(pack/'package-manifest.json')
for name,meta in inv['files'].items():
    data=(pack/name).read_bytes();assert len(data)==meta['bytes'] and digest(data)==meta['sha256']
op=rest/'operator';co=rest/'checkout';m=read(op/'run-manifest.json');orig=read(op/'operator-observation/terminal-originals/run-manifest.json')
validate_schema(m,'run-manifest.schema.json');validate_operator(m);verify_evidence(m,op);verify_agent_inputs(op,m);verify_report_dependencies(m,op)
validate_preflight_receipt(read(op/'execution-preflight.json'),m,read(op/'profile.json'),op/'preflight-evidence')
eligible,status,reason=review_eligibility(m,op/'run-manifest.json');assert eligible and status=='eligible'
assert orig['measurement']==m['measurement']
assert {k:v for k,v in orig['execution'].items() if k!='worktree'}=={k:v for k,v in m['execution'].items() if k!='worktree'}
ledger=read(op/'comparison-ledger.json');entry=next(e for e in ledger['runs'] if e['run_id']==m['run_id']);assert entry['reviewed'] and entry['reference_status']=='fail'
assert digest((op/'operator-observation/terminal-originals/run-manifest.json').read_bytes())==entry['terminal_manifest_sha256']
freeze=read(op/'operator-source-freeze.json');assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=co,text=True).strip()==freeze['commit']==m['outputs']['implementation_commit']
for name,meta in freeze['sources'].items():
    raw=(op/meta['operator_raw_copy']).read_bytes();assert len(raw)==meta['bytes'] and digest(raw)==meta['sha256'];restored=(co/name).read_bytes();assert restored.replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n');blob=subprocess.check_output(['git','hash-object','--path='+name,'--stdin'],cwd=co,input=raw).decode().strip();assert blob==subprocess.check_output(['git','rev-parse','HEAD:'+name],cwd=co,text=True).strip()
assert not (co/m['outputs']['structured_result']).exists() and not (co/m['outputs']['selection_document']).exists()
rm={k:v['status'] for k,v in read(op/'reference-review.json')['items'].items()};assert rm=={'RM1':'fail','RM2':'not_run','RM3':'not_run','RM4':'not_run','RM5':'not_run'}
spent=sum(e['elapsed_seconds'] or 0 for e in ledger['runs'] if e['round']>0);used=sum(e['round']>0 for e in ledger['runs'])
audit=dict(read(rest/'restore-report.json'),frozen_operator_validators_used=True,original_run_or_checkout_path_used=False,inventory_bytes_verified=True,immutable_input_files_verified=57,original_terminal_and_cost_preserved=True,rm_review_completed=True,rm_items=rm,reference_status='fail',product_pass=False,candidate_source_files_verified=len(freeze['sources']),candidate_firmware_artifacts=0,remaining_followup_seconds=max(0,7200-spent),remaining_followup_rounds=3-used,board_slot_released=True)
assert audit['result_valid'] is False
save(rest/'frozen-validator-audit.json',audit);print(json.dumps(audit))
'''
audit_path = PACK.parent / (PACK.name + '-audit.py')
assert not audit_path.exists()
audit_path.write_text(audit_program, encoding='utf-8')
subprocess.run([sys.executable, '-B', '-X', 'utf8', str(audit_path), str(PACK), str(REST), created['package_manifest_sha256']], check=True)
audit = read(REST / 'frozen-validator-audit.json')
PUBLIC = ROOT / 'results/formal-comparison-20261004/evidence' / RUN.name / 'evaluation-final-20261005'
PUBLIC.mkdir(parents=True, exist_ok=False)
files = set(names) | {'run-manifest.json', 'stdout.jsonl', 'stderr.txt', 'command-audit.json', 'prompt.txt', 'profile.json',
                      'policy-review.json', 'reference-review.json', 'operator-reference-review-input.json',
                      'feedback.json', 'candidate-feedback.json', 'candidate-inputs.json', 'execution-preflight.json'}
for name in files:
    dest = PUBLIC / name; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(RUN / name, dest)
for src, name in [(ledger_path, 'ledger-reviewed.json'), (PACK / 'package-manifest.json', 'package-manifest.json'),
                  (REST / 'frozen-validator-audit.json', 'restore-audit.json'), (REST / 'restore-report.json', 'restore-report.json'),
                  (PACK.parent / (PACK.name + '-create.json'), 'package-create.json'), (audit_path, audit_path.name), (Path(__file__), Path(__file__).name)]:
    shutil.copy2(src, PUBLIC / name)
now = datetime.now(timezone.utc).isoformat()
save(PUBLIC / 'snapshot-inventory.json', {'run_id': RUN.name, 'captured_at': now,
    'files': {p.relative_to(PUBLIC).as_posix(): {'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size} for p in PUBLIC.rglob('*') if p.is_file()},
    'scope': 'Final review and independent restore of one unbuilt Pro followup. Original terminal/cost and source bytes retained. No Pro firmware upload.'})
p = read(ROOT / 'results/formal-comparison-20261004/progress.json')
assert p['current_run'] == RUN.name
p.update(checked_at=now, state='agy_pro_followup_%d_review_complete' % round_number,
    product_executions_completed=p['product_executions_started'], started_at=m['execution']['started_at'], ended_at=m['execution']['ended_at'],
    launcher_pid=None, candidate_terminal_status_observed='environment_failed', ongoing_usage_not_terminal=False,
    policy_status='eligible', rm_review='complete', rm_items=audit['rm_items'], reference_status='fail', product_pass=False,
    elapsed_seconds=m['measurement']['wall_clock_seconds'], tokens=m['measurement']['tokens'],
    candidate_current_phase='Followup ended on denial without firmware or final submissions; policy/RM and independent archive complete.',
    remaining_current_series_followup_seconds=audit['remaining_followup_seconds'], remaining_current_series_followup_rounds=audit['remaining_followup_rounds'],
    current_native_scope='Global native settings/instructions/hooks restored byte-for-byte; owner absent.',
    implementation_commit=commit, independent_restore='verified_with_packaged_frozen_validators',
    final_package_manifest_sha256=created['package_manifest_sha256'], final_package_files_verified=created['files'],
    candidate_result_submission='missing', candidate_selection_document_submission='missing',
    terminal_snapshot=PUBLIC.relative_to(ROOT).as_posix(), additional_candidate_round_start_authorized_now=audit['remaining_followup_rounds']>0)
save(ROOT / 'results/formal-comparison-20261004/progress.json', p)
print(json.dumps({'run_id': RUN.name, 'seconds': m['measurement']['wall_clock_seconds'], 'tokens': m['measurement']['tokens']['total'],
                  'freeze': commit, 'package_files': created['files'], 'public_files': len(read(PUBLIC / 'snapshot-inventory.json')['files']),
                  'remaining_seconds': audit['remaining_followup_seconds'], 'remaining_rounds': audit['remaining_followup_rounds']}))
