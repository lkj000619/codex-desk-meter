"""Operator diagnosis: capture COM3 without reset, send, build or flash write."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, time
import serial
import serial.tools.list_ports
OUT=Path(__file__).resolve().parent
ports=[{'port':p.device,'vid':p.vid,'pid':p.pid,'hwid':p.hwid} for p in serial.tools.list_ports.comports()]
assert any(p['port']=='COM3' and p['vid']==0x303a and p['pid']==0x1001 for p in ports)
assert not (OUT/'passive-serial.bin').exists()
tick=time.monotonic();chunks=[];events=[]
port=serial.Serial(port=None,baudrate=115200,timeout=.2,write_timeout=2)
port.dtr=False;port.rts=False;port.port='COM3'
started=datetime.now(timezone.utc).isoformat()
try:
    port.open()
    while time.monotonic()-tick<15:
        b=port.read(max(1,port.in_waiting))
        if b:chunks.append(b);events.append({'seconds':time.monotonic()-tick,'bytes':len(b)})
finally:port.close()
raw=b''.join(chunks);(OUT/'passive-serial.bin').write_bytes(raw)
record={'run_id':'20261006-codex-cli-gpt-6-luna-r01','started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),
    'ports':ports,'port':'COM3','baud':115200,'dtr':False,'rts':False,'reset_requested':False,'stimulus_bytes_sent':0,
    'serial_closed':True,'captured_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'events':events,
    'scope':'Post-evaluation operator diagnostic, separate from original common capture and candidate invocation.'}
(OUT/'passive-capture.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))
print(raw.decode('utf-8',errors='replace')[:10000])
