"""Upload the independently preserved original artifact and send common frames."""
from datetime import datetime,timezone
from pathlib import Path
import json,re,subprocess,sys,time

BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r02')
REST=Path('C:/meter-run-restores-20261006/codex-sol-followup02-pre-observation');CO=REST/'checkout';OUT=RUN/'operator-observation'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save
from policy_review import validate_review
import serial.tools.list_ports

m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');audit=read(REST/'frozen-validator-audit.json')
assert m['operator']['status']=='completed' and m['execution']['ended_at']
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
assert audit['frozen_operator_validators_used'] and audit['inventory_bytes_verified'] and audit['candidate_artifact_source_binding_verified']
assert audit['package_manifest_sha256']==read(Path('C:/meter-run-packages-20261006/codex-sol-followup02-pre-observation-create.json'))['package_manifest_sha256']
for name,item in f['artifacts'].items():
    if name.endswith(('.bin','.elf')):assert digest((CO/name).read_bytes())==item['sha256'],name
assert not f['firmware_source_mutations_after_last_build']
ports=[{'port':p.device,'vid':p.vid,'pid':p.pid,'hwid':p.hwid} for p in serial.tools.list_ports.comports()]
assert any(p['port']=='COM3' and p['vid']==0x303a and p['pid']==0x1001 for p in ports)
partition=CO/'build/partition_table/partition-table.bin';raw=partition.read_bytes();nvs=[]
for start in range(0,len(raw),32):
    entry=raw[start:start+32]
    if entry[:2]!=b'\xaa\x50':continue
    if entry[12:28].split(b'\0')[0]==b'nvs':nvs.append({'offset':int.from_bytes(entry[4:8],'little'),'bytes':int.from_bytes(entry[8:12],'little')})
assert nvs==[{'offset':0x9000,'bytes':0x6000}],nvs
slot={'run_id':RUN.name,'implementation_commit':f['commit'],'artifact_sha256':f['artifacts']['build/codex_desk_meter.bin']['sha256'],
    'owner':'Codex operator','port':'COM3','ports':ports,'started_at':datetime.now(timezone.utc).isoformat(),
    'status':'allocated_after_terminal_freeze_and_independent_restore','candidate_execution_status':'completed',
    'operator_source_modification':False,'operator_firmware_rebuild':False,'source_restore':str(REST),
    'package_manifest_sha256':audit['package_manifest_sha256'],'nvs_reset_scope':nvs[0],'full_flash_erase':False,
    'common_fixture_reference':'codex-7923f96','host_common_frame_result':'Host accepts both common frames0/1; hardware acceptance and optical outcome require separate capture.',
    'commands':[]}
assert not (OUT/'hardware-slot.json').exists();save(OUT/'hardware-slot.json',slot)
def execute(name,args,timeout=120):
    tick=time.monotonic();p=subprocess.run([str(x) for x in args],cwd=BASE,capture_output=True,timeout=timeout)
    (OUT/(name+'-stdout.txt')).write_bytes(p.stdout);(OUT/(name+'-stderr.txt')).write_bytes(p.stderr)
    slot['commands'].append({'name':name,'argv':[str(x) for x in args],'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-tick})
    if p.returncode:slot['status']='operator_command_failed'
    save(OUT/'hardware-slot.json',slot)
    if p.returncode:raise RuntimeError(name+' failed; inspect original logs without repeating candidate execution.')
execute('nvs-erase',[sys.executable,'-m','esptool','--chip','esp32s3','--port','COM3','--before','default_reset','--after','hard_reset','erase_region','0x9000','0x6000'])
flash_args=read(REST/'operator/operator-observation/artifact-snapshot/build/flasher_args.json');assert flash_args['extra_esptool_args']['chip']=='esp32s3'
flash=[sys.executable,'-m','esptool','--chip','esp32s3','--port','COM3','--baud','460800','--before','default_reset','--after','hard_reset','write_flash',*flash_args['write_flash_args']]
for offset,name in sorted(flash_args['flash_files'].items(),key=lambda x:int(x[0],0)):flash.extend([offset,CO/'build'/name])
execute('frozen-artifact-upload',flash)
slot.update(upload_completed=True,upload_completed_at=datetime.now(timezone.utc).isoformat());save(OUT/'hardware-slot.json',slot)
time.sleep(2)
reference=REST/'operator/reference'
execute('reference-capture',[sys.executable,'-B','-X','utf8',BASE/'scripts/observe-product.py','--frames',reference/'expected-frames.jsonl',
    '--reference-time','2026-09-30T18:40:49Z','--send','--port','COM3','--output',OUT/'reference-capture-r1','--wait-seconds','5'])
serial_path=OUT/'reference-capture-r1/device-serial.bin';serial_raw=serial_path.read_bytes()
accepted=re.findall(rb'frame accepted seq=(\d+) error=\s+bytes=(\d+)',serial_raw)
rejected=re.findall(rb'frame rejected seq=(\d+) error=([^\s]+) bytes=(\d+)',serial_raw)
save(OUT/'receiver-source-review.json',{'run_id':RUN.name,'reviewed_at':datetime.now(timezone.utc).isoformat(),'source_commit':f['commit'],
    'source':'main/main.c','source_sha256':digest((CO/'main/main.c').read_bytes()),'receiver_source':'main/receiver.c',
    'receiver_source_sha256':digest((CO/'main/receiver.c').read_bytes()),'artifact_sha256':slot['artifact_sha256'],
    'raw_log':serial_path.relative_to(RUN).as_posix(),'raw_log_sha256':digest(serial_raw),'raw_bytes':len(serial_raw),
    'accepted':[{'sequence':int(a),'bytes':int(b)} for a,b in accepted],
    'rejected':[{'state_sequence':int(a),'error':b.decode(),'bytes':int(c)} for a,b,c in rejected],
    'meaning':'main/main.c logs accepted only after production cdm_accept returns true. A rejected state_sequence is the retained state, not successful receipt. No optical output or precise latency inferred.',
    'transport':'Candidate directly reads USB serial/JTAG; COM3 has VID303A/PID1001. Common operator wires, no candidate collector repair.'})
slot.update(status='awaiting_user_optical_observation',receiver_accepted_sequences=[int(a) for a,b in accepted],
    receiver_rejected_errors=[b.decode() for a,b,c in rejected],serial_closed_after_capture=True,
    upload_and_capture_ended_at=datetime.now(timezone.utc).isoformat(),
    board_state='Frozen Codex Sol followup01 artifact installed; common fixture frames sent; manual LCD/BOOT/stability observation pending.')
save(OUT/'hardware-slot.json',slot)
print(json.dumps({'run_id':RUN.name,'status':slot['status'],'upload_completed_at':slot['upload_completed_at'],
    'artifact_sha256':slot['artifact_sha256'],'receiver_accepted_sequences':slot['receiver_accepted_sequences'],
    'receiver_rejected_errors':slot['receiver_rejected_errors'],'raw_log_bytes':len(serial_raw),'serial_closed':True}))
