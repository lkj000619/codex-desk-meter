"""Publish a dated observation checkpoint; keep all earlier results intact."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, sys

ROOT = Path.cwd()
FORMAL = ROOT / 'results/formal-comparison-20261004'
BASE = Path('C:/meter-operator-20261004')
RUN = Path('C:/meter-followups-20261007/20261007-codex-cli-gpt-6-luna-r01')
OUT = RUN / 'operator-observation'
PACK = Path('C:/meter-run-packages-20261007/codex-luna-followup03-pre-observation')
REST = Path('C:/meter-run-restores-20261007/codex-luna-followup03-pre-observation')
sys.path.insert(0, str(BASE / 'scripts'))
from benchmark_support import read, save, digest, verify_evidence
from policy_review import validate_review

p = read(FORMAL / 'progress.json')
assert p['state'] == 'codex_luna_followup_03_running'
protected_keys = ['previous_series', 'closed_agy_pro_series', 'deferred_agy_flash_series', 'closed_codex_sol_series', 'codex_sol_result_at_transition', 'current_series_first_result', 'current_series_previous_result']
protected = {k: p[k] for k in protected_keys}
m = read(RUN / 'run-manifest.json')
f = read(RUN / 'operator-source-freeze.json')
audit = read(REST / 'frozen-validator-audit.json')
slot = read(OUT / 'hardware-slot.json')
runtime = read(OUT / 'hardware-post-upload-reset/runtime-source-binding.json')
ledger = read(Path(p['ledger']))
assert len(ledger['runs']) == 4 and not ledger['runs'][-1]['reviewed']
assert m['operator']['status'] == 'completed' and audit['host_checks_completed']
assert audit['files_verified'] == 462 and not audit['reference_review_applied']
assert slot['upload_completed'] and runtime['boot_elf_sha_prefix_matches']
assert validate_review(m, RUN / 'run-manifest.json')['decision']['status'] == 'eligible'
verify_evidence(m, RUN)
remaining = ledger['limits']['remediation_seconds'] - sum(x['elapsed_seconds'] for x in ledger['runs'][1:])
assert abs(remaining - 1773.142) < 0.00001

inputs = []
for path in [
    Path('C:/meter-runs-20261004/ledgers/20261004-opencode-cli-opencode-muse-r01.json'),
    Path('C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-flash-r01.json'),
    Path('C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-pro-r01.json'),
    Path('C:/meter-runs-20261005/ledgers/20261005-codex-cli-gpt-6-sol-r01.json'),
    Path(p['ledger']),
]:
    for run in read(path)['runs']:
        assert run['status'] in {'completed', 'timeout', 'aborted', 'environment_failed'}
        source = Path(run['directory']) / 'run-manifest.json'
        if run['run_id'] == '20261005-codex-cli-gpt-6-sol-r01':
            source = Path('C:/meter-policy-corrections-20261006/codex-sol-initial/run-manifest.json')
        inputs.append(source)
assert len(inputs) == len({read(x)['run_id'] for x in inputs}) == 15
known = [read(x)['measurement']['tokens']['total'] for x in inputs if read(x)['measurement']['tokens']['total'] is not None]
assert len(known) == 14 and sum(known) == 61608453
checkpoint = FORMAL / 'comparison-checkpoint-15.md'
assert not checkpoint.exists()
subprocess.run([sys.executable, '-B', '-X', 'utf8', BASE / 'scripts/summarize-benchmark.py', *inputs, '--output', checkpoint], check=True, capture_output=True)
header = '2026-10-07 checkpoint15: 마지막 Luna 후속3는 정상 completed 종료했다. 실제1,192.593초·정규화4,090,978 token, 원본 source37/artifact20·462파일 독립 복원과 Python22/C3/provider17·공통 host 경로를 확인했다. COM3에02:57 KST 원본 업로드,02:58 KST 같은 app 리셋·재전송을 완료했으며 matching ELF boot·PSRAM·USB 첫64byte 수신을 확인했다. 완전한 frame 수락과 LCD/BOOT/30초는 관측 대기다. 전체15회 token coverage14/15, 알려진 정규화 합계61,608,453 token·전체 합계 미상(null)이다. 후속2 사용량 한도 실패·token null을0으로 바꾸지 않았다. Luna series coverage3/4·알려진34,918,496 token·실제 시간8,521.280초다. 후속3회 누적5,426.858초·잔여1,773.142초가 있으나 회차0으로 추가 호출은 불가하다. 이번 정책 eligible·과거 series invalid를 유지하며 기준 도달/RM은 실물 관측 뒤 평가한다. 전체 비교는 미완료이고 Sol/Pro 종료·Flash 보류·과거 판정은 보존한다.\n\n'
body = checkpoint.read_text(encoding='utf-8')
assert body.startswith('# Benchmark results\n\n')
checkpoint.write_text(body.replace('# Benchmark results\n\n', '# Benchmark results\n\n' + header, 1), encoding='utf-8')

now = datetime.now(timezone.utc).isoformat()
public = FORMAL / 'evidence' / RUN.name / 'observation-awaiting-20261007'
public.mkdir(parents=True, exist_ok=False)
def extended(path):
    return Path('\\\\?\\' + str(path.resolve()))
def copy(source, name):
    dest = extended(public / name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(extended(source), dest)

names = ['run-manifest.json', 'policy-review.json', 'operator-policy-decision.json', 'operator-source-freeze.json']
names += [x.relative_to(RUN).as_posix() for x in OUT.rglob('*') if x.is_file() and 'artifact-snapshot' not in x.relative_to(RUN).parts]
for name in sorted(set(names)):
    copy(RUN / name, name)
for source, name in [
    (Path(p['ledger']), 'ledger-before-reference-review.json'),
    (PACK / 'package-manifest.json', 'package-manifest.json'),
    (PACK.parent / 'codex-luna-followup03-pre-observation-create.json', 'package-create.json'),
    (REST / 'frozen-validator-audit.json', 'restore-audit.json'),
    (REST / 'restore-report.json', 'restore-report.json'),
    (Path(__file__), 'operator-helpers/' + Path(__file__).name),
]:
    copy(source, name)
cost_inputs = []
for index, source in enumerate(inputs, 1):
    name = 'cost-inputs/' + str(index).zfill(2) + '-' + read(source)['run_id'] + '.json'
    copy(source, name)
    cost_inputs.append({'original_path': str(source), 'snapshot_path': name, 'run_id': read(source)['run_id'], 'sha256': digest(source.read_bytes())})
save(public / 'cost-checkpoint-inputs.json', {
    'unique_attempts': 15, 'token_measurement_coverage': '14/15', 'total_normalized_tokens': None,
    'known_normalized_tokens': 61608453, 'input_manifests': cost_inputs,
    'checkpoint': checkpoint.relative_to(ROOT).as_posix(), 'checkpoint_sha256': digest(checkpoint.read_bytes()),
    'original_cost_definitions_unchanged': True,
})
save(public / 'snapshot-inventory.json', {
    'run_id': RUN.name, 'round': 2, 'captured_at': now,
    'files': {x.relative_to(public).as_posix(): {'sha256': digest(extended(x).read_bytes()), 'bytes': x.stat().st_size} for x in public.rglob('*') if x.is_file()},
    'scope': 'Immutable final followup3 terminal/host/COM3 upload checkpoint before user optical observation and RM review. Normal completed exit and measured cost preserved; prior followup2 quota failure/null costs unchanged. Same archived firmware, exact host frames and ELF boot verified. Complete device frames/LCD/BOOT/stability unconfirmed; last authorized call ended; no further round allowed.',
})
p.update(
    checked_at=now, state='codex_luna_followup_03_uploaded_awaiting_optical_observation', product_executions_completed=15,
    started_at=m['execution']['started_at'], ended_at=m['execution']['ended_at'], timeout_seconds=m['execution']['timeout_seconds'],
    elapsed_seconds=m['measurement']['wall_clock_seconds'], tokens=m['measurement']['tokens'], tool_calls=m['measurement']['tool_calls'], failed_commands=m['measurement']['failed_commands'],
    candidate_terminal_status_observed='completed', candidate_exit_code=0, ongoing_usage_not_terminal=False,
    candidate_current_phase='Own implementation and result JSON preserved after normal completed exit. Source frozen, independent host checks complete, COM3 artifact uploaded, matching boot observed; current physical LCD/BOOT/stability and bounded RM review pending.',
    process_ids_are_historical=True, candidate_processes_remaining=[],
    policy_status='eligible', policy_confirmed_pipeline_calls=0, rm_review='awaiting_current_user_optical_observation',
    reference_status='not_run', rm_items=None, product_pass=None,
    source_freeze_complete=True, independent_host_evaluation_complete=True, implementation_commit=f['commit'],
    local_candidate_branch_at_freeze=f['candidate_branch'], candidate_result_submission_present=True,
    candidate_selection_document_present=True, candidate_submitted_product_pass=False, firmware_artifact_present=True,
    firmware_build_directory='build', source_files_frozen=37, artifacts_frozen=20,
    pre_observation_package_manifest_sha256=audit['package_manifest_sha256'], pre_observation_package_files_verified=462,
    pre_observation_package=str(PACK), pre_observation_restore=str(REST), current_observation_snapshot=public.relative_to(ROOT).as_posix(),
    cost_checkpoint=checkpoint.relative_to(ROOT).as_posix(), cost_checkpoint_covers_completed_executions=15,
    cost_checkpoint_covers_completed_invocations=15, current_invocation_terminal_cost_available=True,
    current_invocation_terminal_time_available=True, total_normalized_tokens_all_attempts=None,
    known_normalized_tokens_all_attempts=61608453, token_measurement_coverage='14/15',
    current_series_normalized_tokens=None, current_series_known_normalized_tokens=34918496,
    current_series_token_measurement_coverage='3/4', current_series_measured_seconds=sum(x['elapsed_seconds'] for x in ledger['runs']),
    current_series_followup_measured_seconds=sum(x['elapsed_seconds'] for x in ledger['runs'][1:]),
    remaining_current_series_followup_seconds=remaining, remaining_seconds_is_pre_terminal_budget=False,
    remaining_current_series_followup_rounds=0, additional_candidate_round_ready_now=False,
    board_state='Frozen final Luna followup3 original artifact uploaded onCOM3 2026-10-07 02:57KST; same app reset/common frames sent02:58KST. Matching ELF boot, PSRAM and first USB chunk observed. Complete frame acceptance and optical behavior unconfirmed.',
    board_artifact_run_id=RUN.name, luna_hardware_upload_performed=True, hardware_artifact_sha256=slot['artifact_sha256'],
    upload_completed_at=slot['upload_completed_at'], hardware_slot='COM3', boot_observed=True,
    psram_memory_test_ok_observed=True, usb_receiver_ready_observed=True, receiver_acceptance='unconfirmed',
    serial_capture_bytes=runtime['serial_capture_bytes'], serial_closed=True, current_optical_evidence_received=False,
    current_optical_evidence_kind=None, continuous_30s_verified=False,
    restart_instruction='Final followup3 completed, source88b2bbc frozen and462-file package independently checked. Same firmware uploadedCOM3 02:57KST/reset02:58KST. Await current user optical evidence, then one bounded RM review/final package and close Luna series. Remaining1773.142seconds but zero rounds: no more candidate call, retry, new initial or other model. Current4090978tokens known; previous followup2 null and total coverage14/15 retained. Preserve prior verdicts and closed/deferred series.',
)
assert all(p[k] == protected[k] for k in protected_keys)
save(FORMAL / 'progress.json', p)

link = public.relative_to(ROOT).as_posix()
summary = '2026-10-07 마지막 Luna 후속3 `20261007-codex-cli-gpt-6-luna-r01`는02:53:25.503 KST 정상 completed 종료했다. Ledger round3이며 새 최초가 아니다. 원본 source commit `88b2bbc61047242afb22f272c419b3a57d30bb49`와37source/20artifact를 동결하고462파일 독립 복원·Python22/C3/provider17·공통 host 경로를 확인했다. COM3에02:57 KST 원본 업로드,02:58 KST 같은 app 리셋·공통 frame0/1 재전송을 완료했고 ELF 일치 boot·PSRAM·USB 첫64byte 수신을 확인했다. 완전한 frame 수락과 LCD/BOOT/30초는 미확인으로 사용자 실물 관측과 RM을 기다린다. 실제1,192.593초·정규화4,090,978 token, 전체15회 coverage14/15·알려진61,608,453 token·전체 합계 미상(null), Luna series coverage3/4·알려진34,918,496 token이다. 잔여1,773.142초(29분33.142초)는 있으나 후속3회 한도를 사용해 추가 호출은 불가하다. 이번 정책 eligible·과거 series invalid를 유지한다. Sol/Pro 종료·Flash 보류·과거 판정/비용은 보존한다. 독립 series 종료3/15로 전체 비교는 미완료다.'
readiness = ROOT / 'docs/experiments/next-comparison-readiness.md'
text = readiness.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)
assert lines[2].startswith('확인일:')
lines[2] = '확인일: 2026-10-07. 상태: **' + summary + '**\n'
readiness.write_text(''.join(lines) + '\n## 2026-10-07 Luna 마지막 후속3 종료·업로드·관측 대기\n\n' + summary + '\n\n[종료/관측 원본](../../' + link + '/snapshot-inventory.json) · [독립 검증](../../' + link + '/restore-audit.json) · [비용15](../../results/formal-comparison-20261004/comparison-checkpoint-15.md). 종료 원본·독립 host 검증·업로드와 원시 비용을 보존하며 후보 source 수정이나 재빌드는 없다. 후속2의 날짜 있는 정정과 실패 원본은 이전 범위에 그대로 남긴다.\n', encoding='utf-8')
report = FORMAL / 'report.md'
text = report.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)
assert lines[2].startswith('상태:') and lines[3].startswith('후보 실행 시작')
lines[2] = '상태: ' + summary + '\n'
lines[3] = '독립 series 종료3/15이며 전체 비교는 미완료다. 아래 기록은 각 당시 관측이며 최신 상태는 위 상태와 마지막 갱신을 따른다.\n'
report.write_text(''.join(lines) + '\n## 2026-10-07 Luna 마지막 후속3 종료·원본 업로드\n\n' + summary + '\n\n[동결 원본과 관측](evidence/' + RUN.name + '/observation-awaiting-20261007/snapshot-inventory.json) · [원본 native 종료 사유](evidence/' + RUN.name + '/observation-awaiting-20261007/operator-observation/native-terminal-failure-review.json) · [비용15](comparison-checkpoint-15.md).\n', encoding='utf-8')
plan = ROOT / 'docs/plans/2026-10-06-codex-luna-remaining-followups.md'
text = plan.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)
index = next(i for i, line in enumerate(lines) if line.startswith('상태:'))
lines[index] = '상태: 2026-10-07 마지막 후속3 종료·동결·독립 검증·COM3 원본 업로드 완료, 사용자 실물 관측/RM 대기. 실제1,192.593초·정규화4,090,978 token, 잔여1,773.142초이나 남은 회차0으로 추가 실행 불가.\n'
text = ''.join(lines).replace('- [ ] 종료 뒤 후보 source/artifact', '- [x] 종료 뒤 후보 source/artifact')
text += '\n## 2026-10-07 마지막 후속3 검증·관측 대기\n\n- [x] 정상 종료·원시 비용·source37/artifact20 동결,462파일 독립 복원·Python22 skip0/C3/provider17·공통 host 경로 확인.\n- [x] 같은 COM3/MAC·원본 artifact 확인 후02:57 KST 업로드,02:58 KST 같은 app 리셋·고정 frame0/1 재전송. Matching ELF boot·PSRAM·USB 첫64byte 확인, 완전한 수락 미확인.\n- [x] 종료15회 비용 집계: token coverage14/15·알려진61,608,453 token, 후속2 null과 원본 판정 보존.\n- [ ] 현재 사용자 LCD/BOOT/30초 관측을 연결하고 마지막 RM review·최종 독립 package 확정·series 종료.\n\n남은 시간1,773.142초와 관계없이 후속 회차는0으로 추가 호출하지 않는다.\n'
plan.write_text(text, encoding='utf-8')
docmap = ROOT / 'docs/DOCUMENTATION_MAP.md'
text = docmap.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)
index = next(i for i, line in enumerate(lines) if line.startswith('| Luna 남은 후속2/3'))
lines[index] = lines[index].rstrip('\n').rstrip()[:-1] + ' · [마지막 후속3 종료·업로드·관측 대기](../' + link + '/snapshot-inventory.json) · [비용15](../results/formal-comparison-20261004/comparison-checkpoint-15.md) |\n'
docmap.write_text(''.join(lines), encoding='utf-8')
assert all(read(FORMAL / 'progress.json')[k] == protected[k] for k in protected_keys)
print(json.dumps({'snapshot_files': len(read(public / 'snapshot-inventory.json')['files']), 'state': p['state'], 'remaining_seconds': remaining, 'token_coverage': '14/15', 'history_preserved': True}))
