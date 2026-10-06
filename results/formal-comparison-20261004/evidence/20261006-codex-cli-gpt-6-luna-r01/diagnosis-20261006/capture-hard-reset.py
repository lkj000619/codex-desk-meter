"""Post-evaluation boot capture; native reset only, no flash write or build."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, time
import serial
import serial.tools.list_ports
from esptool.reset import HardReset

out = Path(__file__).resolve().parent
assert not (out / 'hard-reset-capture.json').exists()
ports = [{'port': p.device, 'vid': p.vid, 'pid': p.pid, 'hwid': p.hwid}
         for p in serial.tools.list_ports.comports()]
assert any(p['port'] == 'COM3' and p['vid'] == 0x303a and p['pid'] == 0x1001 for p in ports)
port = serial.Serial(port=None, baudrate=115200, timeout=.2, write_timeout=2)
port.dtr = False
port.rts = False
port.port = 'COM3'
record = {'run_id': '20261006-codex-cli-gpt-6-luna-r01', 'port': 'COM3', 'ports': ports,
          'started_at': datetime.now(timezone.utc).isoformat(), 'baud': 115200,
          'reset_strategy': 'esptool.reset.HardReset(uses_usb=True)',
          'flash_write': False, 'serial_payload_sent': 0,
          'scope': 'Operator post-evaluation diagnosis; original evaluation unchanged.'}
chunks, events = [], []
tick = time.monotonic()
try:
    port.open()
    record['reset_requested_at'] = datetime.now(timezone.utc).isoformat()
    HardReset(port, uses_usb=True)()
    record['reset_sequence_completed_at'] = datetime.now(timezone.utc).isoformat()
    while time.monotonic() - tick < 20:
        data = port.read(max(1, port.in_waiting))
        if data:
            chunks.append(data)
            events.append({'seconds': time.monotonic() - tick, 'bytes': len(data)})
except Exception as exc:
    record['error'] = repr(exc)
finally:
    port.close()
raw = b''.join(chunks)
(out / 'hard-reset-serial.bin').write_bytes(raw)
record.update(ended_at=datetime.now(timezone.utc).isoformat(), serial_closed=True,
              captured_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), events=events)
(out / 'hard-reset-capture.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
print(raw.decode('utf-8', errors='replace')[:14000])
