"""Publish final evidence and close Luna without changing earlier snapshots."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys

ROOT = Path.cwd()
FORMAL = ROOT / 'results/formal-comparison-20261004'
RUN = Path('C:/meter-followups-20261007/20261007-codex-cli-gpt-6-luna-r01')
OUT = RUN / 'operator-observation'
PACK = Path('C:/meter-run-packages-20261007/codex-luna-followup03-evaluation')
REST = Path('C:/meter-run-restores-20261007/codex-luna-followup03-evaluation')
sys.path.insert(0, 'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest

progress = read(FORMAL / 'progress.json')
assert progress['state'] == 'codex_luna_followup_03_uploaded_awaiting_optical_observation'
audit = read(REST / 'frozen-validator-audit.json')
manifest = read(RUN / 'run-manifest.json')
closure = read(OUT / 'operator-series-completion.json')
assert audit['files_verified'] == 584 and audit['reference_review_applied'] and audit['series_closed']
assert not audit['normal_readable_screen_observed'] and audit['remaining_followup_rounds'] == 0
assert digest((PACK / 'package-manifest.json').read_bytes()) == audit['package_manifest_sha256']
protected = {key: progress[key] for key in ('previous_series', 'closed_agy_pro_series', 'deferred_agy_flash_series', 'closed_codex_sol_series', 'codex_sol_result_at_transition', 'current_series_first_result', 'current_series_previous_result')}
now = datetime.now(timezone.utc).isoformat()
public = FORMAL / 'evidence' / RUN.name / 'evaluation-20261007'
public.mkdir(exist_ok=False)
def extended(path):
    return Path('\\\\?\\' + str(path.resolve()))
def copy(source, name):
    destination = extended(public / name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(extended(source), destination)

names = ['run-manifest.json', 'policy-review.json', 'operator-policy-decision.json', 'operator-source-freeze.json', 'reference-review.json', 'operator-reference-review-input.json']
names += [path.relative_to(RUN).as_posix() for path in OUT.rglob('*') if extended(path).is_file() and 'artifact-snapshot' not in path.relative_to(RUN).parts]
for name in sorted(set(names)):
    copy(RUN / name, name)
for source, name in [
    (Path(progress['ledger']), 'ledger-at-review.json'),
    (REST / 'frozen-validator-audit.json', 'restore-audit.json'),
    (REST / 'restore-report.json', 'restore-report.json'),
    (REST / 'operator-audit-procedure-correction.json', 'operator-audit-procedure-correction.json'),
    (PACK / 'package-manifest.json', 'package-manifest.json'),
    (PACK.parent / 'codex-luna-followup03-evaluation-create.json', 'package-create.json'),
    (PACK.parent / 'verify-codex-luna-followup03-evaluation-v2.py', 'operator-helpers/verify-codex-luna-followup03-evaluation-v2.py'),
    (PACK.parent / 'prepare-luna-followup03-audit-correction.py', 'operator-helpers/prepare-luna-followup03-audit-correction.py'),
    (Path(__file__), 'operator-helpers/' + Path(__file__).name),
]:
    copy(source, name)
prior = FORMAL / 'evidence' / RUN.name / 'observation-awaiting-20261007'
save(public / 'cost-checkpoint-origin.json', {
    'scope': 'Checkpoint15 preserves the15 terminal attempts before this final optical review. No new candidate invocation or cost change; latest RM verdict is in this final snapshot.',
    'checkpoint': progress['cost_checkpoint'],
    'checkpoint_sha256': digest((ROOT / progress['cost_checkpoint']).read_bytes()),
    'input_snapshot_directory': prior.relative_to(ROOT).as_posix(),
    'input_inventory': (prior / 'cost-checkpoint-inputs.json').relative_to(ROOT).as_posix(),
    'input_inventory_sha256': digest((prior / 'cost-checkpoint-inputs.json').read_bytes()),
    'token_measurement_coverage': '14/15', 'known_normalized_tokens': 61608453, 'total_normalized_tokens': None,
})
save(public / 'snapshot-inventory.json', {
    'run_id': RUN.name, 'round': 3, 'captured_at': now,
    'files': {path.relative_to(public).as_posix(): {'sha256': digest(extended(path).read_bytes()), 'bytes': extended(path).stat().st_size} for path in public.rglob('*') if extended(path).is_file()},
    'scope': 'Final followup3 video/RM/series closure and584-file independent restoration. Original package, cost and prior verdicts preserved. Normal readable display/reference unmet; unused time remains but round allowance is exhausted. Independent auditor9-character boot-prefix correction is dated and separate from candidate evidence.',
})
progress.update(
    checked_at=now, state='codex_luna_series_closed_round_limit', independent_series_completed=4,
    rm_review='followup03_final_reference_review_complete_with_unmeasured_items',
    rm_items=audit['rm_items'], reference_status='fail', product_pass=False,
    final_package_manifest_sha256=audit['package_manifest_sha256'], final_package_files_verified=584,
    final_package=str(PACK), final_restore=str(REST), final_snapshot=public.relative_to(ROOT).as_posix(),
    current_optical_evidence_received=True, current_optical_evidence_kind='user_video',
    video_sha256=audit['video_sha256'], video_duration_seconds=48.17,
    user_initiated_reset_confirmed=True, boot_press_count=None, boot_navigation_observed=None,
    continuous_30s_verified=False, lcd_output_present=True, normal_readable_screen_observed=False,
    additional_candidate_round_ready_now=False, additional_candidate_round_start_authorized_now=False,
    next_model_start_authorized_now=False, next_model_execution_started=False,
    candidate_current_phase='Final followup3 reviewed and independently archived. LCD emits duplicated/rotated/clipped text, required58/82 and three views absent. Both BOOT/RESET confirmed; isolated BOOT cycle and30-second readable persistence unverified. Luna series closed by followup round limit; no additional candidate call.',
    board_state='Final frozen Luna followup3 app remains onCOM3. Current48.17s video confirms duplicated/rotated/clipped output and both BOOT/RESET; complete frame acceptance remains unconfirmed. Serial closed; no upload or reset repeated during final review.',
    host_python_unit_tests_passed=22, host_c_executables_passed=3, host_provider_fixture_validity_checks_passed=17,
    collector_matches_common_reference_payload=True, common_wire_encoder_exact_match=True, frozen_operator29_pipeline_completed=False,
    closed_codex_luna_series=dict(closure, final_package_manifest_sha256=audit['package_manifest_sha256'], final_package_files_verified=584, final_snapshot=public.relative_to(ROOT).as_posix()),
    restart_instruction='Luna initial+three followups have ended and been reviewed. Final584-file package independently verified; normal readable LCD/reference unmet and product_pass false. Derived closure remediation_round_limit_reached, unused1773.142sec but zero rounds. No further Luna call/retry/new initial/other model is authorized. Preserve cost15 coverage14/15, known61608453/null total, prior failures, raw sources/verdicts and closed/deferred series. Overall comparison remains incomplete at4/15 independent series.',
)
assert all(progress[key] == value for key, value in protected.items())
save(FORMAL / 'progress.json', progress)

summary = '2026-10-07 Luna 마지막 후속3 평가·series 종료 완료. 48.17초 영상에서 글자/블록이 회전·중복·잘림 상태이며 일부 문구는 읽히지만58%/82%와 세 정보 화면은 보이지 않아 정상 가독 화면에 도달하지 못했다. 사용자는 이번 영상에서도 BOOT와 RESET 모두 눌렀다고 확인했고 정확한 순서/횟수/시점이 없어 자동 재부팅과 분리된 BOOT 순환은 확인되지 않았다. RM1 pass·RM2 partial·RM3/RM4 fail·RM5 not_run, reference fail·product_pass false다. 최종584파일 package 독립 복원·원본 hash/source/artifact/비용/정책/영상/RM 연결 검증을 완료했다. 이번 정책 eligible·과거 series invalid를 유지한다. 최초1회+후속3회로 한도 종료, 잔여1,773.142초(29분33.142초)와 관계없이 추가 호출은 없다. 전체15회 비용 coverage14/15·알려진61,608,453 token·전체 합계 미상, Luna coverage3/4·알려진34,918,496 token·8,521.280초를 보존한다. 독립 series 종료4/15로 전체 비교는 미완료이며 Sol/Pro 종료·Flash 보류와 과거 원본 판정을 유지한다.'
link = public.relative_to(ROOT).as_posix()
links = '[후속3 최종 RM](../../' + link + '/reference-review.json) · [최종 독립 복원](../../' + link + '/restore-audit.json) · [회차 한도 종료](../../' + link + '/operator-observation/operator-series-completion.json)'
readiness = ROOT / 'docs/experiments/next-comparison-readiness.md'
lines = readiness.read_text(encoding='utf-8').splitlines(keepends=True)
assert lines[2].startswith('확인일:')
lines[2] = '확인일: 2026-10-07. 상태: **' + summary + '**\n'
readiness.write_text(''.join(lines) + '\n## 2026-10-07 Luna 마지막 영상 평가·회차 한도 종료\n\n' + summary + '\n\n' + links + '\n', encoding='utf-8')
report = FORMAL / 'report.md'
lines = report.read_text(encoding='utf-8').splitlines(keepends=True)
assert lines[2].startswith('상태:') and lines[3].startswith('독립 series 종료')
lines[2] = '상태: ' + summary + '\n'
lines[3] = '독립 series 종료4/15이며 전체 비교는 미완료다. 아래 기록은 각 당시 관측이며 최신 상태는 위 상태와 마지막 갱신을 따른다.\n'
report.write_text(''.join(lines) + '\n## 2026-10-07 Luna 마지막 후속3 최종 평가·종료\n\n' + summary + '\n\n[최종 RM](evidence/' + RUN.name + '/evaluation-20261007/reference-review.json) · [독립 복원](evidence/' + RUN.name + '/evaluation-20261007/restore-audit.json) · [series 종료](evidence/' + RUN.name + '/evaluation-20261007/operator-observation/operator-series-completion.json). 비용15는15회 종료·광학 대기 당시 원본으로 보존하며 비용 변화는 없다.\n\n2026-10-07 독립 감사의 [boot hash 검사 정정](evidence/' + RUN.name + '/evaluation-20261007/operator-audit-procedure-correction.json): 원본 로그는9자리 ELF hash prefix를 출력하므로10자리 고정 문자열 검사를 실제 prefix/full ELF hash 대조로 바꿨다. 원본584파일 package·실패한 감사 절차를 보존하고 v2로 같은 package를 검증했다. 후보 재호출·source 수정·재빌드·추가 업로드·host 재시험은 없다.\n', encoding='utf-8')
plan = ROOT / 'docs/plans/2026-10-06-codex-luna-remaining-followups.md'
lines = plan.read_text(encoding='utf-8').splitlines(keepends=True)
index = next(i for i, line in enumerate(lines) if line.startswith('상태:'))
lines[index] = '상태: 2026-10-07 마지막 후속3 영상/RM·최종584파일 독립 검증 완료. 정상 가독 화면 미도달·후속3회 한도 종료, 잔여1,773.142초·남은 회차0·추가 실행 없음.\n'
text = ''.join(lines)
for prefix in ('LCD 출력이 미도달이고', '가시 출력·reference 도달', 'LCD 출력이 없으면', '유효 build가 있으면', '정상 가독 화면 도달 여부', '현재 사용자 LCD/BOOT/30초 관측'):
    text = text.replace('- [ ] ' + prefix, '- [x] ' + prefix)
plan.write_text(text + '\n## 2026-10-07 마지막 후속3 완료·종료 사유\n\n' + summary + '\n\n' + links + '\n', encoding='utf-8')
docmap = ROOT / 'docs/DOCUMENTATION_MAP.md'
lines = docmap.read_text(encoding='utf-8').splitlines(keepends=True)
index = next(i for i, line in enumerate(lines) if line.startswith('| Luna 남은 후속2/3'))
lines[index] = lines[index].replace('Luna 남은 후속2/3·LCD 출력 확인·잔여 예산', 'Luna 후속2/3 평가 완료·회차 한도 종료').rstrip('\n').rstrip()[:-1] + ' · [후속3 최종 RM](../' + link + '/reference-review.json) · [후속3 최종 복원](../' + link + '/restore-audit.json) · [Luna 종료](../' + link + '/operator-observation/operator-series-completion.json) |\n'
docmap.write_text(''.join(lines), encoding='utf-8')
print(json.dumps({'state': progress['state'], 'snapshot_files': len(read(public / 'snapshot-inventory.json')['files']), 'package_verified': 584, 'independent_series_closed': 4, 'remaining_rounds': 0}))
