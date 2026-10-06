"""Repeat the frozen stimulus in one connection after reset; original evaluation unchanged."""
from datetime import datetime, timezone
from pathlib import Path
import json, sys, time
from esptool.reset import HardReset

base = Path('C:/meter-operator-20261004')
sys.path.insert(0, str(base / 'scripts'))
from product_observation import capture_frames, open_observer_serial

out = Path(__file__).resolve().parent
record = {'run_id': '20261006-codex-cli-gpt-6-luna-r01', 'port': 'COM3',
          'started_at': datetime.now(timezone.utc).isoformat(), 'flash_write': False,
          'candidate_invocation': False, 'reset_strategy': 'esptool HardReset uses_usb=True',
          'scope': 'Second post-evaluation diagnostic capture; single connection, reset before sending.'}
assert not (out / 'reset-and-frames-session.json').exists()

def factory(port_name):
    connection = open_observer_serial(port_name)
    try:
        record['reset_requested_at'] = datetime.now(timezone.utc).isoformat()
        HardReset(connection, uses_usb=True)()
        record['reset_sequence_completed_at'] = datetime.now(timezone.utc).isoformat()
        time.sleep(2)
        return connection
    except Exception:
        connection.close()
        raise

frames = Path('C:/meter-run-restores-20261006/codex-luna-r01-evaluation/operator/reference/expected-frames.jsonl')
record['frames_path'] = str(frames)
report = capture_frames(frames.read_bytes().splitlines(keepends=True), 'COM3', factory,
                        out / 'reset-and-frames-capture', wait_seconds=1)
record.update(ended_at=datetime.now(timezone.utc).isoformat(), capture_status=report['status'],
              serial_closed=True, wait_seconds_per_frame=1)
(out / 'reset-and-frames-session.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
print((out / 'reset-and-frames-capture/device-serial.bin').read_bytes().decode('utf-8', errors='replace')[-1500:])
