"""Upload submitted frozen firmware and replay fixed frames; preserve failures without repairs."""
from datetime import datetime,timezone
from pathlib import Path
import json
import subprocess
import sys
import time

BASE=Path('C:/meter-operator-20261004'); RUN=Path('C:/meter-followups-20261007/20261007-antigravity-cli-agy-flash-r02')
CO=RUN/'checkout'; OUT=RUN/'operator-observation'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save
from policy_review import validate_review
import serial.tools.list_ports

m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');policy=validate_review(m,RUN/'run-manifest.json')['decision']['status']
assert m['operator']['status']=='completed' and m['execution']['ended_at']
assert policy=='eligible'
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit'] and not benchmark.git('status','--porcelain',cwd=CO)
benchmark.verify_agent_inputs(RUN,m)
manifest_before_sha256=digest((RUN/'run-manifest.json').read_bytes())
audit=read(Path('C:/meter-run-restores-20261007/agy-flash-followup03-pre-observation/frozen-validator-audit.json'))
assert audit['inventory_bytes_verified'] and audit['candidate_artifact_source_binding_verified'] and audit['files_verified']==485
for name,meta in f['artifacts'].items():assert digest((CO/name).read_bytes())==meta['sha256'],name
ports=[{'port':p.device,'vid':p.vid,'pid':p.pid,'hwid':p.hwid} for p in serial.tools.list_ports.comports()]
assert any(p['port']=='COM3' and p['vid']==0x303a and p['pid']==0x1001 and '28:84:85:B0:85:18' in p['hwid'] for p in ports)
partition=(CO/'build/partition_table/partition-table.bin').read_bytes();nvs=[]
for pos in range(0,len(partition),32):
    entry=partition[pos:pos+32]
    if entry[:2]==b'\xaa\x50' and entry[12:28].split(b'\x00')[0]==b'nvs':
        nvs.append({'label':'nvs','offset':int.from_bytes(entry[4:8],'little'),'bytes':int.from_bytes(entry[8:12],'little')})
assert nvs==[{'label':'nvs','offset':0x9000,'bytes':0x6000}]
assert not (OUT/'hardware-slot.json').exists()
slot={'run_id':RUN.name,'implementation_commit':f['commit'],'artifact_sha256':f['artifacts']['build/meter_esp32s3.bin']['sha256'],
    'owner':'Codex operator','port':'COM3','ports':ports,'started_at':datetime.now(timezone.utc).isoformat(),
    'status':'allocated_after_terminal_and_source_freeze','candidate_execution_status':'completed','policy_status':policy,'series_policy_status':'invalid_for_comparison','pre_observation_audit_sha256':digest(Path('C:/meter-run-restores-20261007/agy-flash-followup03-pre-observation/frozen-validator-audit.json').read_bytes()),
    'evaluation_scope':'Product observations for preserved attempt; policy invalidity excludes quality ranking but does not erase failures/cost or prohibit operator product evidence.',
    'operator_source_modification':False,'operator_firmware_rebuild':False,'nvs_reset_scope':nvs[0],
    'partition_sha256':digest(partition),'full_flash_erase':False,'common_fixture_reference':'codex-7923f96','commands':[]}
save(OUT/'hardware-slot.json',slot)
def execute(name,args,timeout=120):
    start=time.monotonic();p=subprocess.run([str(a) for a in args],cwd=BASE,capture_output=True,timeout=timeout)
    (OUT/(name+'-stdout.txt')).write_bytes(p.stdout);(OUT/(name+'-stderr.txt')).write_bytes(p.stderr)
    slot['commands'].append({'name':name,'argv':[str(a) for a in args],'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start})
    save(OUT/'hardware-slot.json',slot)
    print(json.dumps({'operation':name,'exit_code':p.returncode}),flush=True)
    return p
try:
    erased=execute('nvs-erase',[sys.executable,'-m','esptool','--chip','esp32s3','--port','COM3','--before','default_reset','--after','hard_reset','erase_region','0x9000','0x6000'])
    if erased.returncode:
        slot.update(status='nvs_erase_failed',upload_completed=False)
        raise RuntimeError('NVS erase failed; no upload or retry performed.')
    flash_args=read(CO/'build/flasher_args.json')
    args=[sys.executable,'-m','esptool','--chip','esp32s3','--port','COM3','--baud','460800','--before','default_reset','--after','hard_reset','write_flash',*flash_args['write_flash_args']]
    for offset,name in sorted(flash_args['flash_files'].items(),key=lambda x:int(x[0],0)):
        args.extend([offset,CO/'build'/name])
    uploaded=execute('frozen-artifact-upload',args)
    if uploaded.returncode:
        slot.update(status='upload_failed',upload_completed=False)
        raise RuntimeError('Frozen artifact upload failed; no rebuild or retry performed.')
    slot.update(upload_completed=True,upload_completed_at=datetime.now(timezone.utc).isoformat())
    save(OUT/'hardware-slot.json',slot)
    time.sleep(2)
    reference=BASE/'experiments/reference/codex-7923f96'
    captured=execute('reference-capture',[sys.executable,'-B','-X','utf8',BASE/'scripts/observe-product.py',
        '--frames',reference/'expected-frames.jsonl','--reference-time','2026-09-30T18:40:49Z',
        '--send','--port','COM3','--output',OUT/'reference-capture-r1','--wait-seconds','5'])
    capture_path=OUT/'reference-capture-r1/capture.json'
    capture=read(capture_path) if capture_path.is_file() else None
    serial_path=OUT/'reference-capture-r1/device-serial.bin'; raw=serial_path.read_bytes() if serial_path.is_file() else b''
    frames=[json.loads(line) for line in (reference/'expected-frames.jsonl').read_text(encoding='utf-8').splitlines()]
    accepted=[{'sequence':frame['sequence'],'literal_acceptance_observed':('Frame accepted: seq='+str(frame['sequence'])+',').encode() in raw} for frame in frames]
    save(OUT/'receiver-source-review.json',{'run_id':RUN.name,'reviewer':'Codex operator','reviewed_at':datetime.now(timezone.utc).isoformat(),
        'source_commit':f['commit'],'source':'main/main.c','source_sha256':digest((CO/'main/main.c').read_bytes()),
        'serial_source':'components/bsp/src/bsp_serial.c','serial_source_sha256':digest((CO/'components/bsp/src/bsp_serial.c').read_bytes()),
        'sdkconfig_sha256':digest((CO/'sdkconfig').read_bytes()),'artifact_sha256':slot['artifact_sha256'],
        'raw_log':serial_path.relative_to(RUN).as_posix(),'raw_log_sha256':digest(raw),'raw_bytes':len(raw),'checks':accepted,
        'meaning':'Frame accepted seq is emitted only after parsing and successful meter_state_process_frame. Optical display and timing remain separate.',
        'source_transport_observation':'Candidate polls native USB Serial/JTAG RX after install; console USB Serial/JTAG and UART fallback retained.',
        'transmitted_file_limit':'sent-frames records attempted bytes; use frame bytes_written and actual acceptance log separately to assess delivery.'})
    slot.update(status='awaiting_user_optical_observation' if captured.returncode==0 else 'awaiting_user_optical_observation_after_capture_failure',
        reference_capture_status=capture.get('status') if capture else 'missing',reference_capture_error=capture.get('error') if capture else None,
        receiver_acceptance_review=accepted,receiver_acceptance_observed=all(x['literal_acceptance_observed'] for x in accepted),
        complete_common_stimulus_transmission_confirmed=captured.returncode==0,
        serial_closed_after_capture=True,upload_and_capture_ended_at=datetime.now(timezone.utc).isoformat(),
        board_state='Frozen AGY Flash final followup3 artifact installed; common capture recorded; user LCD/BOOT observation pending.')
finally:
    slot['recorded_at']=datetime.now(timezone.utc).isoformat()
    save(OUT/'hardware-slot.json',slot)
assert not benchmark.git('status','--porcelain',cwd=CO)
benchmark.verify_agent_inputs(RUN,m)
assert digest((RUN/'run-manifest.json').read_bytes())==manifest_before_sha256
print(json.dumps({'hardware_slot':slot['status'],'upload_completed':slot['upload_completed'],'app_sha256':slot['artifact_sha256'],
    'reference_capture':slot.get('reference_capture_status'),'accepted':slot.get('receiver_acceptance_review'),'original_manifest_unchanged':True}))
