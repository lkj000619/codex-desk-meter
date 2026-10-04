"""Operator upload of terminal, frozen AGY artifact and common stimulus."""
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import sys
import time

BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-flash-r01')
CO=RUN/'checkout';OUT=RUN/'operator-observation'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save
from policy_review import validate_review
import serial.tools.list_ports

m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
assert m['operator']['status']=='environment_failed' and m['execution']['ended_at']
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='eligible'
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit']
assert not benchmark.git('status','--porcelain',cwd=CO)
benchmark.verify_agent_inputs(RUN,m)
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
for name,v in f['artifacts'].items():assert digest((CO/name).read_bytes())==v['sha256']
ports=[{'port':p.device,'vid':p.vid,'pid':p.pid,'hwid':p.hwid} for p in serial.tools.list_ports.comports()]
assert any(p['port']=='COM3' and p['vid']==0x303a and p['pid']==0x1001 for p in ports)
partition=CO/'build/partition_table/partition-table.bin'
raw=partition.read_bytes();nvs=[]
for start in range(0,len(raw),32):
    entry=raw[start:start+32]
    if entry[:2]!=b'\xaa\x50':continue
    label=entry[12:28].split(b'\x00')[0].decode('ascii')
    if label=='nvs':nvs.append({'label':label,'offset':int.from_bytes(entry[4:8],'little'),'bytes':int.from_bytes(entry[8:12],'little')})
assert nvs==[{'label':'nvs','offset':0x9000,'bytes':0x6000}],nvs
slot={'run_id':RUN.name,'implementation_commit':f['commit'],'artifact_sha256':f['artifacts']['build/meter_esp32s3.bin']['sha256'],
    'owner':'Codex operator','port':'COM3','ports':ports,'started_at':datetime.now(timezone.utc).isoformat(),
    'status':'allocated_after_terminal_and_source_freeze','candidate_execution_status':'environment_failed',
    'candidate_result_submission_missing':True,'operator_source_modification':False,'operator_firmware_rebuild':False,
    'nvs_reset_scope':nvs[0],'partition_sha256':digest(raw),'full_flash_erase':False,'common_fixture_reference':'codex-7923f96','commands':[]}
assert not (OUT/'hardware-slot.json').exists()
save(OUT/'hardware-slot.json',slot)
def execute(name,args,timeout=120):
    start=time.monotonic();p=subprocess.run(args,cwd=BASE,capture_output=True,timeout=timeout)
    (OUT/(name+'-stdout.txt')).write_bytes(p.stdout);(OUT/(name+'-stderr.txt')).write_bytes(p.stderr)
    slot['commands'].append({'name':name,'argv':[str(a) for a in args],'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start})
    save(OUT/'hardware-slot.json',slot)
    if p.returncode:raise RuntimeError(name+' failed: inspect raw logs')
execute('nvs-erase',[sys.executable,'-m','esptool','--chip','esp32s3','--port','COM3','--before','default_reset','--after','hard_reset','erase_region','0x9000','0x6000'])
flash_args=read(CO/'build/flasher_args.json')
flash=[sys.executable,'-m','esptool','--chip','esp32s3','--port','COM3','--baud','460800','--before','default_reset','--after','hard_reset','write_flash',*flash_args['write_flash_args']]
for offset,name in sorted(flash_args['flash_files'].items(),key=lambda item:int(item[0],0)):
    flash.extend([offset,str(CO/'build'/name)])
execute('frozen-artifact-upload',flash)
time.sleep(2)
reference=BASE/'experiments/reference/codex-7923f96'
execute('reference-capture',[sys.executable,'-B','-X','utf8',str(BASE/'scripts/observe-product.py'),
    '--frames',str(reference/'expected-frames.jsonl'),'--reference-time','2026-09-30T18:40:49Z',
    '--send','--port','COM3','--output',str(OUT/'reference-capture-r1'),'--wait-seconds','5'])
capture=OUT/'reference-capture-r1/device-serial.bin';device_raw=capture.read_bytes()
frames=[json.loads(line) for line in (reference/'expected-frames.jsonl').read_text(encoding='utf-8').splitlines()]
accepted=[{'sequence':frame['sequence'],'literal_acceptance_observed':('Frame accepted: seq='+str(frame['sequence'])+',').encode() in device_raw} for frame in frames]
save(OUT/'receiver-source-review.json',{'run_id':RUN.name,'reviewer':'Codex operator','reviewed_at':datetime.now(timezone.utc).isoformat(),
    'source_commit':f['commit'],'source':'main/main.c','source_sha256':digest((CO/'main/main.c').read_bytes()),
    'serial_source':'components/bsp/src/bsp_serial.c','serial_source_sha256':digest((CO/'components/bsp/src/bsp_serial.c').read_bytes()),
    'sdkconfig_sha256':digest((CO/'sdkconfig').read_bytes()),'artifact_sha256':slot['artifact_sha256'],
    'raw_log':capture.relative_to(RUN).as_posix(),'raw_log_sha256':digest(device_raw),'raw_bytes':len(device_raw),'checks':accepted,
    'meaning':'Literal Frame accepted seq is emitted after parse and meter_state_process_frame return success. Absence is absence of logged receipt, not a proven optical failure. No precise latency inferred.',
    'source_transport_observation':'Candidate bsp_serial polls UART_NUM_0. COM3 identity is USB VID303A/PID1001; source transport and captured receipt are recorded without operator repair.'})
slot.update(status='awaiting_user_optical_observation',upload_completed=True,receiver_acceptance_review=accepted,
    serial_closed_after_capture=True,upload_and_capture_ended_at=datetime.now(timezone.utc).isoformat(),
    board_state='Frozen AGY Flash r01 artifact installed; common frames sent; manual LCD/BOOT observation pending.')
save(OUT/'hardware-slot.json',slot)
assert not benchmark.git('status','--porcelain',cwd=CO)
benchmark.verify_agent_inputs(RUN,m)
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
print(json.dumps({'run_id':RUN.name,'hardware_slot':slot['status'],'app_sha256':slot['artifact_sha256'],
    'receiver_checks':accepted,'raw_log_bytes':len(device_raw),'original_manifest_unchanged':True}))
