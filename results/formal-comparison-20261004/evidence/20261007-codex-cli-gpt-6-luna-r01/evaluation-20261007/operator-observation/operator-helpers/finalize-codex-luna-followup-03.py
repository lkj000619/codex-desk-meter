"""Apply one final frozen RM review and record the exhausted round allowance."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys

RUN = Path('C:/meter-followups-20261007/20261007-codex-cli-gpt-6-luna-r01')
OUT = RUN / 'operator-observation'
VIDEO = OUT / 'user-video-01'
sys.path.insert(0, 'C:/meter-operator-20261004/scripts')
import benchmark
from benchmark_support import read, save, digest, verify_evidence
from comparison_manager import review_run
from policy_review import validate_review

before = read(RUN / 'run-manifest.json')
freeze = read(RUN / 'operator-source-freeze.json')
ledger_path = Path(before['operator']['comparison']['ledger'])
ledger_before = read(ledger_path)
original_path = OUT / 'terminal-originals/run-manifest.json'
original = read(original_path)
assert len(ledger_before['runs']) == 4 and all(x['reviewed'] for x in ledger_before['runs'][:3]) and not ledger_before['runs'][-1]['reviewed']
assert not (RUN / 'reference-review.json').exists()
assert digest(original_path.read_bytes()) == freeze['original_terminal_manifest_sha256'] == ledger_before['runs'][-1]['terminal_manifest_sha256']
assert before['execution'] == original['execution'] and before['measurement'] == original['measurement']
assert original['operator']['status'] == 'completed' and original['measurement']['tokens']['total'] == 4090978
assert benchmark.git('rev-parse', 'HEAD', cwd=RUN / 'checkout') == freeze['commit']
assert not benchmark.git('status', '--porcelain', cwd=RUN / 'checkout')
verify_evidence(before, RUN)
assert validate_review(before, RUN / 'run-manifest.json')['decision']['status'] == 'eligible'

now = datetime.now(timezone.utc).isoformat()
slot = read(OUT / 'hardware-slot.json')
runtime = read(OUT / 'hardware-post-upload-reset/runtime-source-binding.json')
metadata = read(VIDEO / 'video-metadata.json')
assert digest((VIDEO / 'source.mp4').read_bytes()) == metadata['source_sha256'] == 'c21d3386a3772b7f38bf4ae7eb2a740df3043220691e222c3aba6b6e9f051343'
assert metadata['duration_seconds'] == 48.17 and len(metadata['sample_frames']) == 48
save(OUT / 'user-observation-confirmation.json', {
    'run_id': RUN.name, 'recorded_at': now,
    'video_answer_original': '"C:\\Users\\이광진\\Documents\\카카오톡 받은 파일\\KakaoTalk_20261007_031533792.mp4"',
    'button_question_item_id': '["request_user_input_async","call_DTK3R3fX9yO5ihIe8wMUChXE",0]',
    'button_answer_original': 'BOOT와 RESET 모두',
    'user_manual_reset': True, 'boot_manipulation_reported': True,
    'exact_button_press_times_or_count': None, 'automatic_reboot_observed': None,
    'implementation_commit': freeze['commit'], 'artifact_sha256': slot['artifact_sha256'],
    'current_upload_at': slot['upload_completed_at'], 'supplemental_reset_at': runtime['reset_requested_at'],
    'video_sha256': metadata['source_sha256'],
    'scope': 'User supplied this video in response to current final followup3 observation request and confirms both BOOT and RESET in this video. Exact button sequence, counts and times remain unknown; prior followup2 response is not reused.',
})
save(VIDEO / 'video-review.json', {
    'run_id': RUN.name, 'round': 3, 'reviewed_at': now, 'reviewer': 'Codex operator',
    'video_sha256': metadata['source_sha256'], 'duration_seconds': 48.17,
    'contact_sheets_reviewed': 4, 'one_second_sample_frames_reviewed': 48,
    'individual_readable_frames_reviewed': [1, 11, 15, 22, 48],
    'observed': 'Colored text and blue blocks appear twice with rotation and clipping. Early samples alternate these duplicated blocks and almost-empty edge fragments. With the board held vertically around10.5/14.5s, WINDOW and SOURCE STALE fragments and clipped RECEIVE AGE counters are visible twice, but58%/82% are absent. From about19.5s onward most content is clipped to the edges, including the final47.5s sample. Physical board rotation does not produce a complete correct information view.',
    'lcd_output_present': True, 'normal_readable_screen_observed': False,
    'required_usage_values_observed': False, 'three_information_views_observed': False,
    'manual_reset_user_confirmed': True, 'exact_button_times_or_count': None,
    'boot_only_cycle_or_return_verified': False, 'continuous_30_seconds_verified': False,
    'automatic_restart_conclusion': 'unconfirmed; user also pressed RESET and exact timing is unspecified',
    'precise_input_display_latency': 'not_measured',
    'scope': 'A48.17-second recording does not prove30 seconds of continuous readable valid data. Some text fragments are legible; duplicated/clipped fragments do not meet the normal readable-screen objective or the three required information views.',
})
for helper in [Path(__file__), RUN.parent / 'inspect-codex-luna-followup03-user-video.py', RUN.parent / 'supplement-luna-followup03-publication-inventory.py', RUN.parent / 'verify-luna-followup03-awaiting-staged.py']:
    shutil.copy2(helper, OUT / 'operator-helpers' / helper.name)

binding = OUT / 'reference-review-binding'
binding.mkdir(exist_ok=False)
shutil.copy2(RUN / 'run-manifest.json', binding / 'pre-review-operator-metadata.json')
save(binding / 'binding-note.json', {
    'run_id': RUN.name, 'original_terminal_manifest_sha256': digest(original_path.read_bytes()),
    'pre_review_operator_metadata_sha256': digest((binding / 'pre-review-operator-metadata.json').read_bytes()),
    'scope': 'Apply frozen review once using exact preserved terminal bytes, then reattach operator evidence. Source, execution, normalized4090978 token cost and original terminal ledger hash are preserved.',
})
hardware_prefix = 'operator-observation/'
visual = [hardware_prefix + 'user-observation-confirmation.json', hardware_prefix + 'user-video-01/video-review.json', hardware_prefix + 'user-video-01/video-metadata.json', hardware_prefix + 'user-video-01/source.mp4']
def evidence(names):
    return [{'path': name, 'sha256': digest((RUN / name).read_bytes())} for name in names]
report = {
    'run_id': RUN.name, 'reference_inputs_sha256': ledger_before['reference_inputs_sha256'],
    'reviewer': 'Codex operator', 'reviewed_at': now,
    'items': {
        'RM1': {'status': 'pass', 'reason': 'Original ESP-IDF5.3.2 build and same archived ESP32-S3 artifact verified. Three COM3 image hashes, matching d404366963 ELF prefix and normal boot/PSRAM/USB are observed. The candidate completed normally.', 'evidence': evidence(['operator-source-freeze.json', hardware_prefix + 'hardware-slot.json', hardware_prefix + 'frozen-artifact-upload-stdout.txt', hardware_prefix + 'hardware-post-upload-reset/runtime-source-binding.json'])},
        'RM2': {'status': 'partial', 'reason': 'Declared collector/encoder match exact fixed common frames and archived production C receiver accepts0/1 on host. Physical host writes1543 bytes each and first64-byte USB chunk are observed; complete device accepted/rejected markers remain absent and actual frame acceptance is unconfirmed.', 'evidence': evidence([hardware_prefix + 'host-semantic-review.json', hardware_prefix + 'independent-host-checks/common-stimulus-check.json', hardware_prefix + 'reference-capture-r1/capture.json', hardware_prefix + 'hardware-post-upload-reset/runtime-source-binding.json'])},
        'RM3': {'status': 'fail', 'reason': 'Current48.17-second video has duplicated, rotated and clipped text/blue blocks. Some WINDOW/SOURCE STALE/receive-age fragments can be read when physically rotated; the required58% five-hour and82% weekly remaining values are absent. Normal readable usage display is not reached.', 'evidence': evidence(visual)},
        'RM4': {'status': 'fail', 'reason': 'The current recording does not show three complete visible usage/global-reset/diagnostic information views. Duplicated fragments and near-empty edge glyphs do not provide the required three kinds of information.', 'evidence': evidence(visual)},
        'RM5': {'status': 'not_run', 'reason': 'User confirms both BOOT and RESET in this current video without exact sequence, counts or timing. Separate BOOT navigation to the three information views and return cannot be verified. RST changes are not counted as navigation; button hardware failure is not inferred.', 'evidence': evidence(visual)},
    },
    'product_pass': False, 'policy_status': 'eligible',
    'note': 'Final authorized followup3. Current eligible policy is separate from earlier invalid series; quality/reference cost remains ineligible. Host22/C3/provider17 and own wire checks differ from full frozen operator29/device/GUI validation. Exact timing, full acceptance and30-second readable stability remain unmeasured. Round allowance exhausted; no additional invocation.',
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
ledger_after = read(ledger_path)
assert ledger_after['runs'][:3] == ledger_before['runs'][:3] and all(x['reviewed'] for x in ledger_after['runs'])
remaining = ledger_after['limits']['remediation_seconds'] - sum(x['elapsed_seconds'] for x in ledger_after['runs'][1:])
assert abs(remaining - 1773.142) < 0.00001
finalization = {
    'run_id': RUN.name, 'recorded_at': now, 'status': 'followup03_final_reference_review_complete_with_unmeasured_items',
    'source_and_raw_cost_unchanged': True, 'serial_closed': True, 'current_upload_at': slot['upload_completed_at'],
    'board_state': 'Same final Luna followup3 app onCOM3; current video has duplicated/rotated/clipped content. User BOOT+RESET confirmed; required58/82 and three views are absent; complete frame receipt unconfirmed.',
    'rm_items': {key: value['status'] for key, value in report['items'].items()},
    'reference_status': 'fail', 'policy_status': 'eligible', 'series_policy_status': 'invalid_for_comparison',
    'product_pass': False, 'followups_run': 3, 'remaining_followup_seconds': remaining,
    'remaining_followup_rounds': 0, 'additional_candidate_call_started': False,
    'lcd_output_present': True, 'normal_readable_screen_observed': False,
}
save(OUT / 'observation-finalization.json', finalization)
save(OUT / 'operator-series-completion.json', {
    'comparison_id': ledger_after['comparison_id'], 'recorded_at': now,
    'derived_state': 'remediation_round_limit_reached', 'ledger_state': ledger_after['state'],
    'reason': 'Initial plus three followups reviewed. Visible glyph output occurred, but normal readable screen/reference was not reached. The two additionally authorized calls have ended; unused time does not grant another round.',
    'initial_attempts': 1, 'followup_rounds': 3, 'candidate_invocations': 4,
    'final_run_id': RUN.name, 'final_implementation_commit': freeze['commit'],
    'reference_status': 'fail', 'rm_items': finalization['rm_items'], 'product_pass': False,
    'final_run_policy_status': 'eligible', 'effective_policy_status': 'invalid_for_comparison',
    'quality_reference_cost_eligible': False,
    'series_measured_seconds': sum(x['elapsed_seconds'] for x in ledger_after['runs']),
    'followup_measured_seconds': sum(x['elapsed_seconds'] for x in ledger_after['runs'][1:]),
    'series_normalized_tokens': None, 'known_series_normalized_tokens': 34918496, 'token_measurement_coverage': '3/4',
    'remaining_unused_followup_seconds': remaining, 'remaining_followup_rounds': 0, 'additional_followup_allowed': False,
    'ledger_sha256': digest(ledger_path.read_bytes()), 'video_sha256': metadata['source_sha256'],
    'user_initiated_reset_confirmed': True, 'normal_readable_screen_observed': False,
    'continuous_30s_readable_valid_data_certified': False,
    'original_source_execution_cost_and_prior_results_preserved': True,
})
after['operator']['evidence']['operator-reference-review-input.json'] = digest((RUN / 'operator-reference-review-input.json').read_bytes())
for path in OUT.rglob('*'):
    extended = Path('\\\\?\\' + str(path.resolve()))
    if extended.is_file():
        after['operator']['evidence'][path.relative_to(RUN).as_posix()] = digest(extended.read_bytes())
assert after['measurement'] == original['measurement'] and after['execution'] == original['execution']
assert after['outputs']['implementation_commit'] == freeze['commit']
save(RUN / 'run-manifest.json', after)
verify_evidence(after, RUN)
benchmark.verify_agent_inputs(RUN, after)
assert validate_review(after, RUN / 'run-manifest.json')['decision']['status'] == 'eligible'
assert digest((RUN / 'comparison-source.bundle').read_bytes()) == digest((RUN / 'operator-terminal-source.bundle').read_bytes())
print(json.dumps({'rm_items': finalization['rm_items'], 'remaining_seconds': remaining, 'remaining_rounds': 0, 'policy': 'eligible', 'readable_lcd': False, 'series_closed_by_round_limit': True}))
