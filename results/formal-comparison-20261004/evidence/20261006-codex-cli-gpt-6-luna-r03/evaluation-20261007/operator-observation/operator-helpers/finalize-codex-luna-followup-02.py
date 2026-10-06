"""Review the current user video once against the frozen reference contract."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys

RUN = Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r03')
OUT = RUN / 'operator-observation'
VIDEO = OUT / 'user-video-01'
sys.path.insert(0, 'C:/meter-operator-20261004/scripts')
import benchmark
from benchmark_support import read, save, digest, verify_evidence
from comparison_manager import review_run
from policy_review import validate_review

before = read(RUN / 'run-manifest.json')
f = read(RUN / 'operator-source-freeze.json')
ledger_path = Path(before['operator']['comparison']['ledger'])
ledger = read(ledger_path)
original_path = OUT / 'terminal-originals/run-manifest.json'
original = read(original_path)
assert len(ledger['runs']) == 3 and all(x['reviewed'] for x in ledger['runs'][:2]) and not ledger['runs'][-1]['reviewed']
assert not (RUN / 'reference-review.json').exists()
assert digest(original_path.read_bytes()) == f['original_terminal_manifest_sha256'] == ledger['runs'][-1]['terminal_manifest_sha256']
assert before['execution'] == original['execution'] and before['measurement'] == original['measurement']
assert original['operator']['status'] == 'environment_failed' and original['measurement']['tokens']['total'] is None
assert benchmark.git('rev-parse', 'HEAD', cwd=RUN / 'checkout') == f['commit']
assert not benchmark.git('status', '--porcelain', cwd=RUN / 'checkout')
verify_evidence(before, RUN)
assert validate_review(before, RUN / 'run-manifest.json')['decision']['status'] == 'eligible'
now = datetime.now(timezone.utc).isoformat()
slot = read(OUT / 'hardware-slot.json')
runtime = read(OUT / 'hardware-post-upload-reset/runtime-source-binding.json')
meta = read(VIDEO / 'video-metadata.json')
assert digest((VIDEO / 'source.mp4').read_bytes()) == meta['source_sha256']
assert meta['duration_seconds'] == 38.55 and len(meta['sample_frames']) == 39
save(OUT / 'user-observation-confirmation.json', {
    'run_id': RUN.name, 'recorded_at': now,
    'video_question_item_id': '["request_user_input_async","call_Lt397WK2GF33hbL222lt8aXM",0]',
    'video_answer_original': '"' + meta['source_path'] + '"',
    'button_question_item_id': '["request_user_input_async","call_3kDkL4Mz9wfCvybm5aQSieI7",0]',
    'button_answer_original': 'BOOT와 RESET 모두 누름',
    'user_manual_reset': True, 'boot_manipulation_reported': True,
    'exact_button_press_times_or_count': None, 'automatic_reboot_observed': None,
    'implementation_commit': f['commit'], 'artifact_sha256': slot['artifact_sha256'],
    'current_upload_at': slot['upload_completed_at'], 'supplemental_reset_at': runtime['reset_requested_at'],
    'video_sha256': meta['source_sha256'],
    'scope': 'Current artifact video and user confirms both BOOT and RESET. Exact allocation of visual changes to each button, spontaneous restart and timing are not inferred.',
})
save(VIDEO / 'video-review.json', {
    'run_id': RUN.name, 'round': 2, 'reviewed_at': now, 'reviewer': 'Codex operator',
    'video_sha256': meta['source_sha256'], 'duration_seconds': 38.55,
    'contact_sheets_reviewed': 4, 'one_second_sample_frames_reviewed': 39,
    'individual_readable_frames_reviewed': [1, 9, 16, 37],
    'observed': 'LCD now emits colored glyphs and bars. Around0.5-1.5 and8.5-9.5s, rotated clipped heading fragment ER WINDOWS appears twice with SOURCE STALE fragments. Other samples contain isolated rotated/clipped glyphs at edges;12.5-13.5s have almost no text. Rotating the physical board near34.5-36.5s still shows duplicated fragmented text. Required58%/82% usage and three complete information views are not legible.',
    'lcd_output_present': True, 'normal_readable_screen_observed': False,
    'required_usage_values_observed': False, 'three_information_views_observed': False,
    'manual_reset_user_confirmed': True, 'exact_button_times_or_count': None,
    'boot_only_cycle_or_return_verified': False, 'continuous_30_seconds_verified': False,
    'automatic_restart_conclusion': 'unconfirmed; user also pressed RESET',
    'precise_input_display_latency': 'not_measured',
    'scope': 'Visual observations only. Fragmented output is progress from black but does not satisfy readable LCD objective, reference matching or product pass. No implementation repair method inferred.',
})
for helper in [Path(__file__), RUN.parent / 'inspect-codex-luna-followup02-user-video.py', RUN.parent / 'prepare-luna-followup02-video-inspection.py']:
    shutil.copy2(helper, OUT / 'operator-helpers' / helper.name)

binding = OUT / 'reference-review-binding'
binding.mkdir(exist_ok=False)
shutil.copy2(RUN / 'run-manifest.json', binding / 'pre-review-operator-metadata.json')
save(binding / 'binding-note.json', {
    'run_id': RUN.name, 'original_terminal_manifest_sha256': digest(original_path.read_bytes()),
    'pre_review_operator_metadata_sha256': digest((binding / 'pre-review-operator-metadata.json').read_bytes()),
    'scope': 'Use preserved exact terminal bytes for frozen review guard once, then reattach operator records. Candidate source, execution, raw null cost and original terminal ledger hash stay unchanged.',
})
hw = 'operator-observation/'
visual = [hw + 'user-observation-confirmation.json', hw + 'user-video-01/video-review.json', hw + 'user-video-01/video-metadata.json', hw + 'user-video-01/source.mp4']
def evidence(names):
    return [{'path': name, 'sha256': digest((RUN / name).read_bytes())} for name in names]
report = {'run_id': RUN.name, 'reference_inputs_sha256': ledger['reference_inputs_sha256'], 'reviewer': 'Codex operator', 'reviewed_at': now,
    'items': {
        'RM1': {'status': 'pass', 'reason': 'Original ESP-IDF5.3.2 build and same archived ESP32-S3 artifact verified. COM3 three image hashes verified, matching ELF SHA217445082 prefix and normal app/PSRAM/USB boot observed. Native usage-limit exit is preserved separately.', 'evidence': evidence(['operator-source-freeze.json', hw + 'hardware-slot.json', hw + 'frozen-artifact-upload-stdout.txt', hw + 'hardware-post-upload-reset/runtime-source-binding.json'])},
        'RM2': {'status': 'partial', 'reason': 'Declared common collector/encoder exactly match fixed frames and archived production C CLI accepts0/1. Physical host writes1543 bytes each and first64-byte USB chunk observed, but no complete accepted/rejected markers. Actual device frame acceptance remains unconfirmed.', 'evidence': evidence([hw + 'host-semantic-review.json', hw + 'independent-host-checks/common-stimulus-check.json', hw + 'reference-capture-r1/capture.json', hw + 'hardware-post-upload-reset/runtime-source-binding.json'])},
        'RM3': {'status': 'fail', 'reason': 'Current38.55-second video shows duplicated, rotated and clipped title/glyph fragments. Required58% five-hour and82% weekly remaining values are not legibly displayed. LCD emits output but normal readable usage screen is not reached.', 'evidence': evidence(visual)},
        'RM4': {'status': 'fail', 'reason': 'Current video and reported button trials do not show three legible usage/global-reset/diagnostic information views. Fragmented edge glyphs and partial heading are not functional information screens.', 'evidence': evidence(visual)},
        'RM5': {'status': 'not_run', 'reason': 'User confirms both BOOT and RESET, exact order/times/count unspecified. Visual changes cannot establish separated BOOT navigation to the three information views and return. RST changes are not counted as BOOT navigation; button hardware failure is not inferred.', 'evidence': evidence(visual)},
    }, 'product_pass': False, 'policy_status': 'eligible',
    'note': 'Current bounded review. Host22/C3/17 and own wire coverage differ from frozen operator29 and device/GUI proof. Prior original/round1 invalid policy and costs preserved; current eligible does not make series quality/reference cost eligible. Native environment_failed and all token null preserved. Readable LCD objective unmet, one authorized last followup remains.',
}
save(RUN / 'operator-reference-review-input.json', report)
(RUN / 'run-manifest.json').write_bytes(original_path.read_bytes())
try:
    review_run(RUN, report)
except Exception:
    if not read(ledger_path)['runs'][-1]['reviewed']:
        (RUN / 'run-manifest.json').write_bytes((binding / 'pre-review-operator-metadata.json').read_bytes())
    raise
after = read(RUN / 'run-manifest.json')
after['operator']['evidence'].update(before['operator']['evidence'])
after['outputs']['build_status'] = 'pass'
remaining = ledger['limits']['remediation_seconds'] - sum(x['elapsed_seconds'] for x in ledger['runs'][1:])
assert abs(remaining - 2965.735) < 0.00001
save(OUT / 'observation-finalization.json', {
    'run_id': RUN.name, 'recorded_at': now, 'status': 'followup02_reference_review_complete_with_unmeasured_items',
    'source_and_raw_cost_unchanged': True, 'serial_closed': True, 'current_upload_at': slot['upload_completed_at'],
    'board_state': 'Same Luna followup2 app onCOM3; video shows duplicated/clipped/rotated text, required values absent. User BOOT+RESET confirmed; actual complete frame receipt unconfirmed.',
    'rm_items': {k: v['status'] for k, v in report['items'].items()}, 'reference_status': 'fail', 'policy_status': 'eligible',
    'series_policy_status': 'invalid_for_comparison', 'product_pass': False, 'followups_run': 2,
    'remaining_followup_seconds': remaining, 'remaining_followup_rounds': 1, 'additional_candidate_call_started': False,
    'lcd_output_present': True, 'normal_readable_screen_observed': False,
})
after['operator']['evidence']['operator-reference-review-input.json'] = digest((RUN / 'operator-reference-review-input.json').read_bytes())
for path in OUT.rglob('*'):
    if path.is_file(): after['operator']['evidence'][path.relative_to(RUN).as_posix()] = digest(path.read_bytes())
assert after['measurement'] == original['measurement'] and after['execution'] == original['execution']
assert after['outputs']['implementation_commit'] == f['commit']
save(RUN / 'run-manifest.json', after)
verify_evidence(after, RUN)
benchmark.verify_agent_inputs(RUN, after)
assert validate_review(after, RUN / 'run-manifest.json')['decision']['status'] == 'eligible'
reviewed = read(ledger_path)
assert reviewed['runs'][:2] == ledger['runs'][:2] and reviewed['runs'][-1]['reviewed']
assert digest((RUN / 'comparison-source.bundle').read_bytes()) == digest((RUN / 'operator-terminal-source.bundle').read_bytes())
print(json.dumps({'rm_items': {k: v['status'] for k, v in report['items'].items()}, 'remaining_seconds': remaining, 'remaining_rounds': 1, 'policy': 'eligible', 'readable_lcd': False}))
