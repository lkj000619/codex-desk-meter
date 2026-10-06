"""Publish reviewed Sol round2 and close its series without another invocation."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, sys

ROOT = Path.cwd(); FORMAL = ROOT/'results/formal-comparison-20261004'
RUN = Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r02')
PACK = Path('C:/meter-run-packages-20261006/codex-sol-followup02-final')
REST = Path('C:/meter-run-restores-20261006/codex-sol-followup02-final')
BASE = Path('C:/meter-operator-20261004')
sys.path.insert(0, str(BASE/'scripts'))
from benchmark_support import read, save, digest

m = read(RUN/'run-manifest.json'); f = read(RUN/'operator-source-freeze.json')
audit = read(REST/'frozen-validator-audit.json')
ledger = read(Path(m['operator']['comparison']['ledger']))
assert audit['files_verified'] == 483 and audit['inventory_bytes_verified']
assert audit['rm_items'] == {f'RM{i}': 'pass' for i in range(1, 6)}
assert audit['reference_status'] == 'pass' and audit['policy_status'] == 'invalid_for_comparison'
assert not audit['product_pass'] and not audit['additional_followup_allowed']
assert ledger['state'] == 'reached' and len(ledger['runs']) == 3
assert digest((PACK/'package-manifest.json').read_bytes()) == audit['package_manifest_sha256']
p = read(FORMAL/'progress.json')
assert p['state'] == 'codex_sol_followup_02_awaiting_user_optical_observation'
assert p['product_executions_started'] == p['product_executions_completed'] == 11
assert p['implementation_commit'] == f['commit'] == audit['implementation_commit']
now = datetime.now(timezone.utc).isoformat()

# Use actual unique terminal invocations and preserve the dated initial policy correction.
inputs = []
for path in [Path('C:/meter-runs-20261004/ledgers/20261004-opencode-cli-opencode-muse-r01.json'),
             Path('C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-flash-r01.json'),
             Path('C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-pro-r01.json'),
             Path(p['ledger'])]:
    for run in read(path)['runs']:
        assert run['status'] in {'completed', 'timeout', 'aborted', 'environment_failed'}
        source = Path(run['directory'])/'run-manifest.json'
        if run['run_id'] == '20261005-codex-cli-gpt-6-sol-r01':
            source = Path('C:/meter-policy-corrections-20261006/codex-sol-initial/run-manifest.json')
        inputs.append(source)
assert len(inputs) == len({read(path)['run_id'] for path in inputs}) == 11
total = sum(read(path)['measurement']['tokens']['total'] for path in inputs)
assert total == 26689957
checkpoint = FORMAL/'comparison-checkpoint-11.md'; assert not checkpoint.exists()
subprocess.run([sys.executable, '-B', '-X', 'utf8', str(BASE/'scripts/summarize-benchmark.py'),
                *map(str, inputs), '--output', str(checkpoint)], check=True)
body = checkpoint.read_text(encoding='utf-8'); assert body.startswith('# Benchmark results\n\n')
header = ('2026-10-06 checkpoint11: Sol 후속2의 관측·RM·최종 독립 감사를 마친 후보11회 비용 집계다. '
          'RM1~RM5는 관측상 pass이며 ledger reached로 Sol series를 종료했다. '
          '정책 invalid_for_comparison으로 품질·적격 reference-cost 집계에서는 제외하고 product_pass false를 유지한다. '
          '이 series의 관측 도달 비용은 최초+후속2회 3,532.405초·정규화22,413,413 token이며 적격 도달 비용은 아니다. '
          '전체11회 정규화26,689,957 token에 모든 실패·부적격 호출을 포함한다. '
          '[날짜 있는 최초 정책 정정](evidence/20261005-codex-cli-gpt-6-sol-r01/policy-correction-20261006/correction-note.json)을 반영하며 '
          '기존 review·package·비용과 checkpoint08~10은 보존한다. 전체 비교는 종료3/15 series로 미완료다.\n\n')
checkpoint.write_text(body.replace('# Benchmark results\n\n', '# Benchmark results\n\n'+header, 1), encoding='utf-8')

public = FORMAL/'evidence'/RUN.name/'evaluation-final-20261006'
public.mkdir(parents=True, exist_ok=False)
def extended(path): return Path('\\\\?\\'+str(path.resolve()))
def copy(source, name):
    dest = extended(public/name); dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(extended(source), dest)

names = ['run-manifest.json', 'policy-review.json', 'operator-policy-decision.json',
         'operator-source-freeze.json', 'reference-review.json', 'operator-reference-review-input.json']
names += [name for name in m['operator']['evidence']
          if name.startswith('operator-observation/') and 'artifact-snapshot' not in Path(name).parts]
for name in sorted(set(names)): copy(RUN/name, name)
for source, name in [(Path(p['ledger']), 'ledger-at-review.json'),
                     (REST/'frozen-validator-audit.json', 'restore-audit.json'),
                     (REST/'restore-report.json', 'restore-report.json'),
                     (PACK/'package-manifest.json', 'package-manifest.json'),
                     (PACK.parent/'codex-sol-followup02-final-create.json', 'package-create.json'),
                     (PACK.parent/'verify-codex-sol-followup02-final.py', 'verify-final.py'),
                     (Path(__file__), Path(__file__).name)]: copy(source, name)
save(public/'cost-checkpoint-inputs.json', {
    'unique_attempts': 11, 'total_normalized_tokens': total,
    'input_manifests': [{'path': str(path), 'run_id': read(path)['run_id'], 'sha256': digest(path.read_bytes())} for path in inputs],
    'checkpoint': checkpoint.relative_to(ROOT).as_posix(), 'checkpoint_sha256': digest(checkpoint.read_bytes()),
    'rm_review_completed': True, 'observed_reference_pass': True, 'quality_reference_cost_eligible': False,
    'original_snapshots_and_cost_definitions_unchanged': True})
closed = {
    'comparison_id': ledger['comparison_id'], 'recorded_at': now, 'derived_state': 'observed_reference_reached',
    'ledger_state': 'reached', 'initial_attempts': 1, 'followup_rounds': 2, 'candidate_invocations': 3,
    'reference_reached_at_round': 2, 'reference_status': 'pass', 'rm_items': audit['rm_items'],
    'effective_policy_status': 'invalid_for_comparison', 'quality_reference_cost_eligible': False, 'product_pass': False,
    'series_measured_seconds': p['series_measured_seconds'], 'series_normalized_tokens': p['series_measured_normalized_tokens'],
    'followup_measured_seconds': sum(v['elapsed_seconds'] for v in ledger['runs'] if v['round']),
    'remaining_unused_followup_seconds': audit['remaining_followup_seconds'], 'remaining_unused_followup_rounds': 1,
    'additional_followup_allowed': False, 'reason_no_more_calls': 'Frozen ledger reached; unused budget does not authorize another invocation.',
    'final_run_id': RUN.name, 'final_implementation_commit': f['commit'],
    'final_package_manifest_sha256': audit['package_manifest_sha256'], 'final_package_files_verified': 483,
    'video_sha256': audit['video_sha256'], 'user_initiated_reset_confirmed': True,
    'continuous_30s_readable_valid_data_certified': False, 'next_model': 'codex-luna', 'next_model_started': False,
    'original_source_execution_cost_and_prior_results_preserved': True}
save(public/'operator-series-completion.json', closed)
files = {path.relative_to(extended(public)).as_posix(): {'sha256': digest(path.read_bytes()), 'bytes': path.stat().st_size}
         for path in extended(public).rglob('*') if path.is_file()}
save(public/'snapshot-inventory.json', {'run_id': RUN.name, 'captured_at': now, 'files': files,
    'scope': 'Immutable final RM/video/cost/policy review and series closure. Full483-file package independently restored. Prior pending snapshots, source and raw cost unchanged.'})
p.update(checked_at=now, state='codex_sol_series_closed_reference_reached_quality_ineligible',
    independent_series_completed=3, rm_review='complete', reference_status='pass', product_pass=False, rm_items=audit['rm_items'],
    candidate_current_phase='Round2 implementation/submission and evaluation complete; observed RM1-RM5 pass. Sol series closed at reached; quality invalid and full product false. No further call.',
    final_package_manifest_sha256=audit['package_manifest_sha256'], final_package_files_verified=483,
    final_package=str(PACK), final_restore=str(REST), final_snapshot=public.relative_to(ROOT).as_posix(),
    cost_checkpoint=checkpoint.relative_to(ROOT).as_posix(), closed_codex_sol_series=closed,
    current_optical_evidence_received=True, user_initiated_reset_confirmed=True,
    video_sha256=audit['video_sha256'], video_duration_seconds=63.3, additional_followup_allowed=False,
    quality_reference_cost_eligible=False,
    board_state='Sol followup2 original artifact remains. Video before manual RESET shows58/82 and three information pages. User confirmed RST near18sec clears data to WAITING; post-reset text-free samples20.5-30.5sec preserved, cause unverified. No new stimulus or reupload; serial closed. Current board not reobserved after video.',
    restart_instruction='Sol series is terminal, evaluated, independently preserved and closed at observed RM reference reach round2. No followup3, replay or rebuild. Unused6127.751sec/one round is not authorization. Policy invalid, eligible reference-cost false and full product false remain. Preserve initial/followup1/pending snapshots, Pro closure and Flash deferral. Luna unstarted and no next-model start authorized now.')
save(FORMAL/'progress.json', p)
print(json.dumps({'public_snapshot_files': len(files), 'package_files': 483, 'state': p['state'],
                  'series_completed': 3, 'unique_attempts': 11, 'total_normalized_tokens': total}))
