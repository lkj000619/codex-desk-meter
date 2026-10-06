"""Publish a dated observation checkpoint; keep all earlier results intact."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, sys

ROOT = Path.cwd()
FORMAL = ROOT / 'results/formal-comparison-20261004'
BASE = Path('C:/meter-operator-20261004')
RUN = Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r03')
OUT = RUN / 'operator-observation'
PACK = Path('C:/meter-run-packages-20261007/codex-luna-followup02-pre-observation')
REST = Path('C:/meter-run-restores-20261007/codex-luna-followup02-pre-observation')
sys.path.insert(0, str(BASE / 'scripts'))
from benchmark_support import read, save, digest, verify_evidence
from policy_review import validate_review

p = read(FORMAL / 'progress.json')
assert p['state'] == 'codex_luna_followup_02_running'
protected_keys = ['previous_series', 'closed_agy_pro_series', 'deferred_agy_flash_series', 'closed_codex_sol_series', 'codex_sol_result_at_transition', 'current_series_first_result', 'current_series_previous_result']
protected = {k: p[k] for k in protected_keys}
m = read(RUN / 'run-manifest.json')
f = read(RUN / 'operator-source-freeze.json')
audit = read(REST / 'frozen-validator-audit.json')
slot = read(OUT / 'hardware-slot.json')
runtime = read(OUT / 'hardware-post-upload-reset/runtime-source-binding.json')
ledger = read(Path(p['ledger']))
assert len(ledger['runs']) == 3 and not ledger['runs'][-1]['reviewed']
assert m['operator']['status'] == 'environment_failed' and audit['host_checks_completed']
assert audit['files_verified'] == 455 and not audit['reference_review_applied']
assert slot['upload_completed'] and runtime['boot_elf_sha_prefix_matches']
assert validate_review(m, RUN / 'run-manifest.json')['decision']['status'] == 'eligible'
verify_evidence(m, RUN)
remaining = ledger['limits']['remediation_seconds'] - sum(x['elapsed_seconds'] for x in ledger['runs'][1:])
assert abs(remaining - 2965.735) < 0.00001

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
assert len(inputs) == len({read(x)['run_id'] for x in inputs}) == 14
known = [read(x)['measurement']['tokens']['total'] for x in inputs if read(x)['measurement']['tokens']['total'] is not None]
assert len(known) == 13 and sum(known) == 57517475
checkpoint = FORMAL / 'comparison-checkpoint-14.md'
assert not checkpoint.exists()
subprocess.run([sys.executable, '-B', '-X', 'utf8', BASE / 'scripts/summarize-benchmark.py', *inputs, '--output', checkpoint], check=True, capture_output=True)
header = '2026-10-07 checkpoint14: Luna 후속2는 원본 펌웨어 build·결과 JSON을 생성한 뒤 native usage limit으로 environment_failed 종료했다. 실제 후보 시간1,247.265초를 차감해 잔여2,965.735초·최대1회다. 토큰 계측은 null이며 0으로 합산하지 않는다. 전체14회 시간은 계측됐고 token coverage는13/14, 알려진 정규화 합계57,517,475 token이며 전체 합계는 미상이다. Luna series token coverage2/3·알려진 합계30,827,518 token, 전체 시간7,328.687초다. 이번 정책은 eligible, 이전 두 회차 invalid 판정으로 series 품질·reference-cost 부적격은 유지한다. 455파일 독립 복원, Python22/C3·공통 host 경로 검증, COM3 원본 업로드·ELF 일치 boot를 확인했다. 장치의 완전한 frame0/1 수락과 LCD/BOOT/30초는 아직 미확인으로 RM은 대기다. 전체 비교는 미완료이며 Sol/Pro 종료·Flash 보류·과거 판정과 비용을 보존한다.\n\n'
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
    (PACK.parent / 'codex-luna-followup02-pre-observation-create.json', 'package-create.json'),
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
    'unique_attempts': 14, 'token_measurement_coverage': '13/14', 'total_normalized_tokens': None,
    'known_normalized_tokens': 57517475, 'input_manifests': cost_inputs,
    'checkpoint': checkpoint.relative_to(ROOT).as_posix(), 'checkpoint_sha256': digest(checkpoint.read_bytes()),
    'original_cost_definitions_unchanged': True,
})
save(public / 'snapshot-inventory.json', {
    'run_id': RUN.name, 'round': 2, 'captured_at': now,
    'files': {x.relative_to(public).as_posix(): {'sha256': digest(extended(x).read_bytes()), 'bytes': x.stat().st_size} for x in public.rglob('*') if x.is_file()},
    'scope': 'Immutable followup2 terminal/host/COM3 upload checkpoint before user optical observation and RM review. Native environment failure and token null preserved. Same archived firmware, exact host frames and ELF boot verified. Complete device frames/LCD/BOOT/stability unconfirmed; no last call started.',
})
p.update(
    checked_at=now, state='codex_luna_followup_02_uploaded_awaiting_optical_observation', product_executions_completed=14,
    started_at=m['execution']['started_at'], ended_at=m['execution']['ended_at'], timeout_seconds=m['execution']['timeout_seconds'],
    elapsed_seconds=m['measurement']['wall_clock_seconds'], tokens=m['measurement']['tokens'], tool_calls=m['measurement']['tool_calls'], failed_commands=m['measurement']['failed_commands'],
    candidate_terminal_status_observed='environment_failed', candidate_exit_code=1, ongoing_usage_not_terminal=False,
    candidate_current_phase='Own build and result JSON preserved after native usage-limit failure. Source frozen, independent host checks complete, COM3 artifact uploaded, matching boot observed; current physical LCD/BOOT/stability and bounded RM review pending.',
    process_ids_are_historical=True, candidate_processes_remaining=[],
    policy_status='eligible', policy_confirmed_pipeline_calls=0, rm_review='awaiting_current_user_optical_observation',
    reference_status='not_run', rm_items=None, product_pass=None,
    source_freeze_complete=True, independent_host_evaluation_complete=True, implementation_commit=f['commit'],
    local_candidate_branch_at_freeze=f['candidate_branch'], candidate_result_submission_present=True,
    candidate_selection_document_present=True, candidate_submitted_product_pass=False, firmware_artifact_present=True,
    firmware_build_directory='build', source_files_frozen=38, artifacts_frozen=20,
    pre_observation_package_manifest_sha256=audit['package_manifest_sha256'], pre_observation_package_files_verified=455,
    pre_observation_package=str(PACK), pre_observation_restore=str(REST), current_observation_snapshot=public.relative_to(ROOT).as_posix(),
    cost_checkpoint=checkpoint.relative_to(ROOT).as_posix(), cost_checkpoint_covers_completed_executions=14,
    cost_checkpoint_covers_completed_invocations=14, current_invocation_terminal_cost_available=False,
    current_invocation_terminal_time_available=True, total_normalized_tokens_all_attempts=None,
    known_normalized_tokens_all_attempts=57517475, token_measurement_coverage='13/14',
    current_series_normalized_tokens=None, current_series_known_normalized_tokens=30827518,
    current_series_token_measurement_coverage='2/3', current_series_measured_seconds=sum(x['elapsed_seconds'] for x in ledger['runs']),
    current_series_followup_measured_seconds=sum(x['elapsed_seconds'] for x in ledger['runs'][1:]),
    remaining_current_series_followup_seconds=remaining, remaining_seconds_is_pre_terminal_budget=False,
    remaining_current_series_followup_rounds=1, additional_candidate_round_ready_now=False,
    board_state='Frozen Luna followup2 original artifact uploaded onCOM3 2026-10-07 02:19KST; same app reset/common frames sent02:20KST. Matching ELF boot, PSRAM and first USB chunk observed. Complete frame acceptance and optical behavior unconfirmed.',
    board_artifact_run_id=RUN.name, luna_hardware_upload_performed=True, hardware_artifact_sha256=slot['artifact_sha256'],
    upload_completed_at=slot['upload_completed_at'], hardware_slot='COM3', boot_observed=True,
    psram_memory_test_ok_observed=True, usb_receiver_ready_observed=True, receiver_acceptance='unconfirmed',
    serial_capture_bytes=runtime['serial_capture_bytes'], serial_closed=True, current_optical_evidence_received=False,
    current_optical_evidence_kind=None, continuous_30s_verified=False,
    restart_instruction='Current followup2 is terminal, not running. Same original firmware uploaded; await current user optical observation, then one bounded RM review and final package. If LCD remains unreadable and budget positive, last followup3 already authorized from own frozen91f7de6 with timeout floor2965seconds. No extra entitlement probe, replacement initial or other model. Current tokens unknown, all failure time counted; prior verdicts and closed/deferred series preserved.',
)
assert all(p[k] == protected[k] for k in protected_keys)
save(FORMAL / 'progress.json', p)

link = public.relative_to(ROOT).as_posix()
summary = '2026-10-07: Luna 후속2 `20261006-codex-cli-gpt-6-luna-r03`는00:11:33.017 KST native 사용량 한도로 environment_failed 종료했다. 제출 JSON·빌드가 남아 source commit `91f7de60328b7db9a9d04acef60ac45eafb3685a`를 동결하고455파일 독립 복원·Python22/C3·공통 host 경로를 확인했다. COM3에02:19 KST 원본 업로드,02:20 KST 같은 app 리셋·재전송을 완료했고 ELF 일치 boot·PSRAM·USB 첫64byte 수신을 확인했다. 완전한 frame0/1 수락·LCD/BOOT/30초는 미확인으로 사용자 실물 관측과 RM 평가를 기다린다. 실제1,247.265초 차감 후 잔여2,965.735초(49분25.735초)·최대1회, 다음 호출은 관측 후 LCD 출력 미도달일 때만 가능하다. 이번 정책은 eligible이나 series는 과거 invalid 판정 때문에 품질·reference-cost 부적격이다. 후보 시작/종료14회·token coverage13/14, 알려진 합계57,517,475 token·전체 합계 미상(null), Luna series coverage2/3·알려진30,827,518 token이다. Sol/Pro 종료·Flash 보류·과거 판정/비용을 보존한다.'
readiness = ROOT / 'docs/experiments/next-comparison-readiness.md'
text = readiness.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)
assert lines[2].startswith('확인일:')
lines[2] = '확인일: 2026-10-07. 상태: **' + summary + '**\n'
readiness.write_text(''.join(lines) + '\n## 2026-10-07 Luna 후속2 종료·업로드·관측 대기\n\n' + summary + '\n\n[종료/관측 원본](../../' + link + '/snapshot-inventory.json) · [독립 검증](../../' + link + '/restore-audit.json) · [비용14](../../results/formal-comparison-20261004/comparison-checkpoint-14.md). 정책 helper 출력의 이전 숫자 잔존과 독립 복원의 CLI 배치 누락은 날짜 있는 정정으로 남겼다. 원본 실패/skip 로그·도구를 보존하며 후보 source 수정이나 재빌드는 없다.\n', encoding='utf-8')
report = FORMAL / 'report.md'
text = report.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)
assert lines[2].startswith('상태:') and lines[3].startswith('후보 실행 시작')
lines[2] = '상태: ' + summary + '\n'
lines[3] = '독립 series 종료3/15이며 전체 비교는 미완료다. 아래 기록은 각 당시 관측이며 최신 상태는 위 상태와 마지막 갱신을 따른다.\n'
report.write_text(''.join(lines) + '\n## 2026-10-07 Luna 후속2 종료·원본 업로드\n\n' + summary + '\n\n[동결 원본과 관측](evidence/' + RUN.name + '/observation-awaiting-20261007/snapshot-inventory.json) · [원본 native 종료 사유](evidence/' + RUN.name + '/observation-awaiting-20261007/operator-observation/native-terminal-failure-review.json) · [비용14](comparison-checkpoint-14.md).\n', encoding='utf-8')
plan = ROOT / 'docs/plans/2026-10-06-codex-luna-remaining-followups.md'
text = plan.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)
index = next(i for i, line in enumerate(lines) if line.startswith('상태:'))
lines[index] = '상태: 2026-10-07 후속2 종료·동결·독립 검증·COM3 원본 업로드 완료, 사용자 실물 관측/RM 대기. 사용량 한도로 environment_failed 종료했으나 제출 JSON·build는 보존했다. 실제1,247.265초 차감 후 잔여2,965.735초·최대1회다. Native PID는 역사적 기록이며 현재 실행 중이 아니다.\n'
text = ''.join(lines).replace('- [ ] 종료 뒤 후보 source/artifact', '- [x] 종료 뒤 후보 source/artifact')
text += '\n## 2026-10-07 후속2 검증·관측 대기\n\n- [x] 원본 source38/artifact20·비용 null·native usage-limit 실패 동결,455파일 독립 복원. CLI 배치 정정 뒤 Python22 skip0, 기존 통과 C3 재사용, 공통 collector/encoder/receiver와 provider17 확인. 원본 skip32·실패 guard 로그 보존.\n- [x] 같은 COM3/MAC·원본 artifact 확인 후02:19 KST 업로드;02:20 KST 같은 app 단일 리셋·고정 frame0/1 재전송. ELF/PSRAM/USB 첫64byte 수신 확인, 완전한 수락은 미확인.\n- [x] 종료14회 비용 집계: token coverage13/14·전체 합계 미상, 알려진57,517,475 token. 이번 실제 시간 차감·정책 eligible과 과거 series invalid 분리.\n- [ ] 현재 LCD/BOOT/30초 사용자 관측을 원본에 연결하고 한번만 RM review·최종 독립 package 확정.\n- [ ] LCD 출력이 없으면 기존 승인 범위의 마지막 후속3: 현재 잔여floor2,965초·최대1회, 자기 동결 source에서 준비. 출력 관측 없이는 실패를 추정해 새 호출하지 않음.\n\n[현재 원본](../../' + link + '/snapshot-inventory.json) · [비용14](../../results/formal-comparison-20261004/comparison-checkpoint-14.md).\n'
plan.write_text(text, encoding='utf-8')
docmap = ROOT / 'docs/DOCUMENTATION_MAP.md'
text = docmap.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)
index = next(i for i, line in enumerate(lines) if line.startswith('| Luna 남은 후속2/3'))
lines[index] = lines[index].rstrip('\n').rstrip()[:-1] + ' · [후속2 종료·업로드·관측 대기](../' + link + '/snapshot-inventory.json) · [비용14](../results/formal-comparison-20261004/comparison-checkpoint-14.md) |\n'
docmap.write_text(''.join(lines), encoding='utf-8')
assert all(read(FORMAL / 'progress.json')[k] == protected[k] for k in protected_keys)
print(json.dumps({'snapshot_files': len(read(public / 'snapshot-inventory.json')['files']), 'state': p['state'], 'remaining_seconds': remaining, 'token_coverage': '13/14', 'history_preserved': True}))
