"""Reuse the existing original-artifact upload procedure with Luna's layout/logs."""
from pathlib import Path
src=Path('C:/meter-followups-20261006/observe-codex-sol-followup-02.py').read_text(encoding='utf-8')
src=src.replace('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r02','C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01').replace('codex-sol-followup02','codex-luna-r01')
src=src.replace("'build/","'build-idf/").replace("CO/'build'","CO/'build-idf'")
src=src.replace('artifact-snapshot/build/flasher_args.json','artifact-snapshot/build-idf/flasher_args.json')
src=src.replace('Host accepts both common frames0/1; hardware acceptance and optical outcome require separate capture.','Restored encoder exactly matches common frames0/1; own production C tests pass. Arbitrary common-frame host receiver seam absent; hardware acceptance and optical outcome require this capture.')
start=src.index('accepted=re.findall(')
src=src[:start]+'''accepted=re.findall(rb'accepted cdm/1 frame sequence=(\\d+)',serial_raw)
rejected=re.findall(rb'rejected frame: ([^;\\r\\n]+); last-good sequence=(\\d+)',serial_raw)
save(OUT/'receiver-source-review.json',{'run_id':RUN.name,'reviewed_at':datetime.now(timezone.utc).isoformat(),'source_commit':f['commit'],
    'source':'main/app_main.c','source_sha256':digest((CO/'main/app_main.c').read_bytes()),
    'receiver_source':'components/meter_core/meter_core.c','receiver_source_sha256':digest((CO/'components/meter_core/meter_core.c').read_bytes()),
    'artifact_sha256':slot['artifact_sha256'],'raw_log':serial_path.relative_to(RUN).as_posix(),
    'raw_log_sha256':digest(serial_raw),'raw_bytes':len(serial_raw),
    'accepted':[{'sequence':int(a)} for a in accepted],
    'rejected':[{'error':a.decode(),'retained_last_good_sequence':int(b)} for a,b in rejected],
    'meaning':'finish_line logs accepted only when production meter_receiver_receive returns true. A rejected last-good sequence is retained state, not successful receipt. No LCD readability, precise latency or stability inferred.',
    'transport':'Direct USB Serial/JTAG input. COM3 VID303A/PID1001; same frozen operator wire bytes; no collector or receiver repair.'})
slot.update(status='awaiting_user_optical_observation',receiver_accepted_sequences=[int(a) for a in accepted],
    receiver_rejected_errors=[a.decode() for a,b in rejected],serial_closed_after_capture=True,
    upload_and_capture_ended_at=datetime.now(timezone.utc).isoformat(),
    board_state='Frozen Codex Luna initial artifact installed; common frames sent; LCD/BOOT/stability observation pending.')
save(OUT/'hardware-slot.json',slot)
print(json.dumps({'run_id':RUN.name,'status':slot['status'],'upload_completed_at':slot['upload_completed_at'],
    'artifact_sha256':slot['artifact_sha256'],'receiver_accepted_sequences':slot['receiver_accepted_sequences'],
    'receiver_rejected_errors':slot['receiver_rejected_errors'],'raw_log_bytes':len(serial_raw),'serial_closed':True}))
'''
Path('C:/meter-runs-20261006/observe-codex-luna-r01.py').write_text(src,encoding='utf-8')
print('Prepared original-artifact COM3 upload; no hardware access by this preparation.')
