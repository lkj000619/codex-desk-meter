"""Test whether COM3 currently responds as ROM, without resetting or flashing."""
from datetime import datetime, timezone
from pathlib import Path
import json, subprocess, sys, time
OUT=Path(__file__).resolve().parent
assert not (OUT/'rom-no-reset-probe.json').exists()
argv=[sys.executable,'-B','-X','utf8','-m','esptool','--chip','esp32s3','--port','COM3',
    '--before','no_reset','--after','no_reset','--no-stub','--connect-attempts','1','read_mac']
tick=time.monotonic();started=datetime.now(timezone.utc).isoformat()
p=subprocess.run(argv,capture_output=True,timeout=30)
(OUT/'rom-no-reset-stdout.txt').write_bytes(p.stdout);(OUT/'rom-no-reset-stderr.txt').write_bytes(p.stderr)
record={'run_id':'20261006-codex-cli-gpt-6-luna-r01','started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),
    'argv':argv,'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-tick,'reset_requested':False,
    'stub_uploaded':False,'flash_write':False,'sync_probe_bytes_sent':True,'serial_closed':True,
    'scope':'ROM synchronization is a diagnostic stimulus, not common cdm/1 input or a candidate run. Windows esptool4.12 opens with RTS/DTR false; no_reset skips reset strategies. A failed probe alone does not prove application health.'}
(OUT/'rom-no-reset-probe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record));print(p.stdout.decode('utf-8',errors='replace'));print(p.stderr.decode('utf-8',errors='replace'))
