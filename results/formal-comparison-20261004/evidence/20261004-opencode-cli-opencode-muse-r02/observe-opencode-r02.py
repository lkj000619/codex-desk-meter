"""Observe the frozen timeout artifact; no candidate repair or rebuild."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

BASE=Path('C:/meter-operator-20261004')
RUN=Path('C:/meter-followups-20261004/20261004-opencode-cli-opencode-muse-r02')
CO=RUN/'checkout'
OUT=RUN/'operator-observation'
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import digest,read,save
import benchmark
import serial.tools.list_ports

m=read(RUN/'run-manifest.json');freeze=read(RUN/'operator-source-freeze.json')
assert m['operator']['status']=='timeout' and m['execution']['ended_at'] is not None
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CO,text=True).strip()==freeze['commit']
assert subprocess.check_output(['git','status','--porcelain'],cwd=CO,text=True).strip()==''
benchmark.verify_agent_inputs(RUN,m)
ports=[{'port':p.device,'vid':p.vid,'pid':p.pid,'hwid':p.hwid} for p in serial.tools.list_ports.comports()]
assert any(p['port']=='COM3' and p['vid']==0x303a and p['pid']==0x1001 for p in ports)
for name,metadata in freeze['artifacts'].items():
    assert digest((CO/name).read_bytes())==metadata['sha256']
slot={'run_id':m['run_id'],'implementation_commit':freeze['commit'],'artifact_sha256':freeze['artifacts']['firmware/build/cdm_meter.bin']['sha256'],
      'owner':'Codex operator','port':'COM3','ports':ports,'started_at':datetime.now(timezone.utc).isoformat(),
      'status':'allocated_after_timeout_and_freeze','candidate_result_submission_missing':True,'operator_source_modification':False,
      'nvs_reset_scope':{'offset':'0x9000','bytes':24576,'partition_source':'firmware/build/partition_table/partition-table.bin'},
      'full_flash_erase':False,'common_fixture_reference':'codex-7923f96','commands':[]}
save(OUT/'hardware-slot.json',slot)
python=sys.executable
def execute(name,args,cwd=BASE):
    started=time.monotonic()
    p=subprocess.run(args,cwd=cwd,capture_output=True,timeout=120)
    (OUT/(name+'-stdout.txt')).write_bytes(p.stdout)
    (OUT/(name+'-stderr.txt')).write_bytes(p.stderr)
    slot['commands'].append({'name':name,'argv':[str(x) for x in args],'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-started})
    save(OUT/'hardware-slot.json',slot)
    if p.returncode: raise RuntimeError(name+' failed: inspect raw logs')
    return p
execute('nvs-erase',[python,'-m','esptool','--chip','esp32s3','--port','COM3','--before','default_reset','--after','hard_reset','erase_region','0x9000','0x6000'])
args=read(CO/'firmware/build/flasher_args.json')
flash=[python,'-m','esptool','--chip','esp32s3','--port','COM3','--baud','460800','--before','default_reset','--after','hard_reset','write_flash',*args['write_flash_args']]
for offset,name in sorted(args['flash_files'].items(),key=lambda item:int(item[0],0)):
    flash += [offset,str(CO/'firmware/build'/name)]
execute('frozen-artifact-upload',flash)
time.sleep(2)
reference=BASE/'experiments/reference/codex-7923f96'
execute('reference-capture',[python,'-B','-X','utf8',str(BASE/'scripts/observe-product.py'),
        '--frames',str(reference/'expected-frames.jsonl'),'--reference-time','2026-09-30T18:40:49Z',
        '--send','--port','COM3','--output',str(OUT/'reference-capture-r1'),'--wait-seconds','5'])
raw_path=OUT/'reference-capture-r1/device-serial.bin'
raw=raw_path.read_bytes()
frames=[json.loads(x) for x in (reference/'expected-frames.jsonl').read_text(encoding='utf-8').splitlines()]
acceptance=[{'sequence':f['sequence'],'crc':f['integrity']['value'],
             'literal_acceptance_observed':('accepted seq '+str(f['sequence'])+' crc '+f['integrity']['value']).encode() in raw}
            for f in frames]
source=CO/'firmware/main/main.c'
save(OUT/'receiver-source-review.json',{'run_id':m['run_id'],'reviewer':'Codex operator','reviewed_at':datetime.now(timezone.utc).isoformat(),
     'source':'firmware/main/main.c','source_sha256':digest(source.read_bytes()),'source_commit':freeze['commit'],
     'artifact_sha256':slot['artifact_sha256'],'raw_log':'reference-capture-r1/device-serial.bin','raw_log_sha256':digest(raw),
     'checks':acceptance,'meaning':'Source review confirms accepted seq/CRC is emitted only after meter_receiver_accept returns METER_FRAME_OK, last-good copy and sequence persistence. Generic acceptance timing fields remain null. This is receiver evidence, not an optical or precise-latency claim.'})
slot.update(status='awaiting_user_optical_observation',upload_completed=True,
            receiver_acceptance_review=acceptance,serial_closed_after_capture=True,
            board_state='Frozen r02 artifact installed; unchanged common frames sent; manual LCD/BOOT observation pending.',
            upload_and_capture_ended_at=datetime.now(timezone.utc).isoformat())
save(OUT/'hardware-slot.json',slot)
print(json.dumps({'run_id':m['run_id'],'hardware_slot':slot['status'],'app_sha256':slot['artifact_sha256'],
                  'receiver_checks':acceptance,'source_unchanged':True},indent=2))
