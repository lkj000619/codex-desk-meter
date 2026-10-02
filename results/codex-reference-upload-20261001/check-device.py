"""Operator hardware check; imports product collector without changing its code."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import re
import time
import types
import serial

parser = argparse.ArgumentParser()
parser.add_argument('workspace', type=pathlib.Path)
args = parser.parse_args()
out = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('cdm_collector', args.workspace / 'scripts/cdm_collector.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
state_path = out / 'sender-state.json'
if not state_path.exists():
    collector.initialize_sender_state(state_path, receiver_known_empty=True)
state = collector.SenderSequence(state_path)
fixture_args = types.SimpleNamespace(all_provider_fixtures=False, fixture=None, omit_global_reset=False)
port = serial.Serial(port=None, baudrate=115200, timeout=0.05, write_timeout=3)
port.dtr = False
port.rts = False
port.port = 'COM3'
port.open()
records = []
raw = bytearray()
try:
    # Wait for device LCD initialization. DTR/RTS remain inactive throughout.
    start = time.monotonic()
    while time.monotonic() - start < 4:
        raw.extend(port.read(4096))
    for attempt in range(2):
        usage, resets = collector.collect_cli_fixtures(fixture_args)
        sequence = state.reserve()
        frame = collector.make_frame(usage, resets, sequence=sequence)
        wire = collector.encode_frame(frame)
        begin = time.monotonic()
        written = collector.write_frame(port, frame)
        port.flush()
        collector.append_serial_log(out / 'sent-frames.jsonl', port='COM3',
            fixture_paths=collector.selected_fixture_paths(fixture_args),
            frame=frame, bytes_written=written)
        response = bytearray()
        while time.monotonic() - begin < 5:
            data = port.read(4096)
            response.extend(data)
            raw.extend(data)
        text = response.decode('utf-8', errors='replace')
        record = {
            'sequence': sequence, 'bytes_written': written,
            'frame_sha256': hashlib.sha256(wire).hexdigest(),
            'receiver_accepted': bool(re.search(rf'CDM_RX sequence={sequence} result=0\b', text)),
            'display_call_completed': bool(re.search(rf'CDM_DISPLAY sequence={sequence} result=0\b', text)),
            'device_response': text,
        }
        records.append(record)
        print(json.dumps(record), flush=True)
finally:
    port.close()
    (out / 'device-serial.log').write_bytes(raw)
    (out / 'device-check.json').write_text(json.dumps({
        'timestamp_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'transport': 'operator pyserial harness with original collector normalization, sequence and writer functions',
        'firmware_source_changed': False,
        'port': 'COM3', 'frames': records,
        'optical_lcd_behavior': 'requires owner observation; serial display marker is not optical evidence',
        'source_data': 'repository synthetic fixtures, not live account usage',
    }, indent=2), encoding='utf-8')
if len(records) != 2 or not all(r['receiver_accepted'] and r['display_call_completed'] for r in records):
    raise SystemExit(2)
