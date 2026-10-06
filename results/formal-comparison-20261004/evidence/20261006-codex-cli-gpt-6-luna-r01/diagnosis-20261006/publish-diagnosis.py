"""Publish a separate raw snapshot and append operator state; retain original RM/cost fields."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json

root = Path('C:/Users/이광진/orca/codex-desk-meter')
out = Path(__file__).resolve().parent
formal = root / 'results/formal-comparison-20261004'
public = formal / 'evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006'
assert not public.exists(), 'Refuse to replace a diagnostic snapshot'
inventory = {}
for source in sorted(out.rglob('*')):
    if not source.is_file():
        continue
    rel = source.relative_to(out).as_posix()
    target = public / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = Path('\\\\?\\' + str(source.resolve())).read_bytes()
    Path('\\\\?\\' + str(target.resolve())).write_bytes(raw)
    inventory[rel] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
now = datetime.now(timezone.utc).isoformat()
(public / 'snapshot-inventory.json').write_text(json.dumps({
    'run_id': '20261006-codex-cli-gpt-6-luna-r01', 'created_at': now,
    'scope': 'Post-evaluation operator diagnosis; original frozen review/package unaffected.',
    'files': inventory}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = formal / 'progress.json'
state = json.loads(state_path.read_bytes())
before = json.loads((out / 'comparison-state-before-diagnosis.json').read_bytes())
assert state == before, 'Operator state changed while diagnosing'
state['checked_at'] = now
state['operator_diagnosis'] = {
    'date': '2026-10-06', 'status': 'review_complete_with_causal_validation_remaining',
    'report': 'luna-black-screen-diagnosis-20261006.md',
    'evidence': str(public.relative_to(formal)).replace('\\', '/'),
    'boot_observed': True, 'psram_memory_test_ok_observed': True,
    'usb_receiver_ready_observed': True,
    'accepted_sequences_in_first_diagnostic_capture': [0],
    'frame1_acceptance': 'unconfirmed', 'user_after_first_reset': 'continued_black_screen',
    'confirmed_code_defects': ['LCD-INIT-RESET', 'LCD-NATIVE-TIMING'],
    'causal_corrected_firmware_test': 'not_run',
    'source_modifications': 0, 'firmware_rebuilds': 0, 'flash_writes': 0,
    'candidate_invocations': 0, 'operator_native_hard_resets': 2,
    'latest_reset_at': '2026-10-06T12:25:36.590375+00:00',
    'latest_capture': 'Both host writes complete; no accepted/rejected frame logs. Serial closed.',
    'original_rm_and_cost_preserved': True
}
state['board_state'] = 'Same frozen Luna initial app; last diagnostic native reset at2026-10-06 21:25:36KST. Both common host writes complete, latest actual receipt unconfirmed; serial closed. User continued-black report applies to first diagnostic reset. Original upload/evaluation preserved.'
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'files_published': len(inventory), 'state': state['state'], 'diagnostic_status': state['operator_diagnosis']['status']}))
