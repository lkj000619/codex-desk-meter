"""Preserve completed host checks and post-upload observations without product changes."""
from datetime import datetime, timezone
from pathlib import Path
import json, re, shutil, sys

BASE = Path('C:/meter-operator-20261004')
RUN = Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r03')
REST = Path('C:/meter-run-restores-20261007/codex-luna-followup02-pre-observation')
OUT = RUN / 'operator-observation'
sys.path.insert(0, str(BASE / 'scripts'))
from benchmark_support import read, save, digest, verify_evidence
from policy_review import validate_review

now = datetime.now(timezone.utc).isoformat()
f = read(RUN / 'operator-source-freeze.json')
original = read(OUT / 'terminal-originals/run-manifest.json')
assert digest((OUT / 'terminal-originals/run-manifest.json').read_bytes()) == f['original_terminal_manifest_sha256']
assert original['operator']['status'] == 'environment_failed'
assert original['measurement']['tokens']['total'] is None
for name, target in [
    ('post-restore-host-checks', 'operator-first-audit-host-logs'),
    ('post-restore-host-checks-v2', 'independent-host-checks'),
]:
    shutil.copytree(REST / name, OUT / target)
for name, target in [
    ('operator-audit-procedure-v1.py', 'pre-observation-operator-audit-procedure-v1.py'),
    ('operator-audit-artifact-placement-correction.json', 'pre-observation-operator-audit-artifact-placement-correction.json'),
    ('frozen-validator-audit.json', 'pre-observation-frozen-validator-audit.json'),
    ('restore-report.json', 'pre-observation-restore-report.json'),
]:
    shutil.copy2(REST / name, OUT / target)
for helper in [
    Path(__file__),
    Path('C:/meter-run-packages-20261007/verify-codex-luna-followup02-pre-observation.py'),
    Path('C:/meter-run-packages-20261007/verify-codex-luna-followup02-pre-observation-v2.py'),
    Path('C:/meter-followups-20261006/repair-luna-followup02-restored-test-placement.py'),
    Path('C:/meter-followups-20261006/observe-codex-luna-followup-02.py'),
    Path('C:/meter-followups-20261006/prepare-luna-followup02-reset-capture.py'),
]:
    shutil.copy2(helper, OUT / 'operator-helpers' / helper.name)

procedure = OUT / 'operator-helpers/review-codex-luna-followup-02-policy.py'
assert procedure.exists() and "'commands_reviewed':229" in procedure.read_text(encoding='utf-8')
save(OUT / 'operator-policy-procedure-output-correction.json', {
    'run_id': RUN.name, 'recorded_at': now,
    'scope': 'Printed helper summary only; authoritative policy decision and review were already eligible.',
    'procedure_sha256': digest(procedure.read_bytes()),
    'original_printed_summary': {'policy_status': 'invalid_for_comparison', 'commands_reviewed': 229, 'changes_reviewed': 35, 'confirmed_pipeline_calls': 0, 'raw_manifest_unchanged': True},
    'corrected_summary': {'policy_status': 'eligible', 'commands_reviewed': 129, 'changes_reviewed': 7, 'raw_events': 284, 'confirmed_pipeline_calls': 0},
    'cause': 'Adapted helper retained prior-round literals in its final print statement.',
    'actual_decision_sha256': digest((RUN / 'operator-policy-decision.json').read_bytes()),
    'policy_review_sha256': digest((RUN / 'policy-review.json').read_bytes()),
    'original_procedure_preserved': True, 'candidate_source_or_raw_cost_changed': False,
})

host = read(OUT / 'independent-host-checks/host-checks.json')
common = read(OUT / 'independent-host-checks/common-stimulus-check.json')
assert host['python_tests_passed'] == 22 and all(x['exit_code'] == 0 for x in host['checks'])
assert common['encoder_matches_exact_common_frames'] and common['legacy_collector']['matches_common_reference_payload']
save(OUT / 'host-semantic-review.json', {
    'run_id': RUN.name, 'reviewed_at': now, 'source_commit': f['commit'],
    'python_tests_passed': 22, 'python_skipped_subcases_after_materialization': 0,
    'host_c_executables_passed': 3, 'provider_validity_cases_passed': 17,
    'collector_matches_common_reference_payload': True, 'encoder_matches_common_frames': True,
    'production_c_accepts_common_sequences': [0, 1],
    'candidate_wire_schema_cases': common['candidate_wire_schema_cases'],
    'frozen_operator29_pipeline_completed': False,
    'original_partial_audit_preserved': True, 'materialized_archived_cli_without_rebuild': True,
    'three_original_passing_c_checks_reused': True, 'operator_product_source_modified': False,
    'scope': 'Independent host verification only; device receipt, LCD, BOOT and stability remain separate observations.',
})

reset = OUT / 'hardware-post-upload-reset'
raw = (reset / 'reset-and-frames-capture/device-serial.bin').read_bytes()
boot = re.search(rb'ELF file SHA256:\s*([a-f0-9]+)', raw)
elf_hash = f['artifacts']['build/codex_desk_meter.elf']['sha256']
assert boot and elf_hash.startswith(boot.group(1).decode())
assert b'esp_psram: SPI SRAM memory test OK' in raw
accepted = [int(x) for x in re.findall(rb'accepted cdm/1 frame sequence=(\d+)', raw)]
assert accepted == []
session = read(reset / 'reset-and-frames-session.json')
capture = read(reset / 'reset-and-frames-capture/capture.json')
save(reset / 'runtime-source-binding.json', {
    'run_id': RUN.name, 'source_commit': f['commit'],
    'app_sha256': f['artifacts']['build/codex_desk_meter.bin']['sha256'], 'elf_sha256': elf_hash,
    'boot_elf_sha_prefix_matches': True, 'boot_observed': True, 'psram_memory_test_ok': True,
    'boot_screen_submitted_log_observed': b'boot screen submitted before USB receiver setup' in raw,
    'usb_receiver_ready_observed': b'USB Serial/JTAG receiver ready' in raw,
    'usb_data_chunk_observed': b'USB Serial/JTAG receive path observed data (64 bytes)' in raw,
    'raw_log_sha256': digest(raw), 'serial_capture_bytes': len(raw),
    'reset_requested_at': session['reset_requested_at'], 'receiver_accepted_sequences': accepted,
    'receiver_rejected_errors': [],
    'host_writes_completed_sequences': [x['sequence'] for x in capture['frames'] if x['bytes_written'] == x['bytes_requested']],
    'serial_closed': True, 'wait_seconds_per_frame': 5,
    'scope': 'Same archived ELF boot and first USB chunk observed. Full frame acceptance and readable LCD are unconfirmed; first 86-byte capture preserved.',
})
events = [json.loads(x) for x in (OUT / 'terminal-originals/stdout.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
errors = [x for x in events if x.get('type') in {'error', 'turn.failed'}]
assert errors and any('usage limit' in json.dumps(x).lower() for x in errors)
save(OUT / 'native-terminal-failure-review.json', {
    'run_id': RUN.name, 'reviewed_at': now, 'status': 'environment_failed', 'exit_code': 1,
    'started_at': original['execution']['started_at'], 'ended_at': original['execution']['ended_at'],
    'elapsed_seconds': original['measurement']['wall_clock_seconds'],
    'terminal_manifest_sha256': f['original_terminal_manifest_sha256'],
    'stdout_sha256': digest((OUT / 'terminal-originals/stdout.jsonl').read_bytes()),
    'native_errors': errors, 'tokens': original['measurement']['tokens'],
    'candidate_result_present': True, 'candidate_firmware_build_present': True,
    'normal_assistant_completion_observed': False, 'quota_recovery_assumed': False,
})
m = read(RUN / 'run-manifest.json')
assert m['execution'] == original['execution'] and m['measurement'] == original['measurement']
for path in OUT.rglob('*'):
    if path.is_file(): m['operator']['evidence'][path.relative_to(RUN).as_posix()] = digest(path.read_bytes())
save(RUN / 'run-manifest.json', m)
verify_evidence(m, RUN)
assert validate_review(m, RUN / 'run-manifest.json')['decision']['status'] == 'eligible'
print(json.dumps({'preserved_host_checks': 22, 'c_checks': 3, 'runtime_log_bytes': len(raw), 'frame_acceptance': 'unconfirmed', 'policy': 'eligible', 'optical': 'awaiting_user'}))
