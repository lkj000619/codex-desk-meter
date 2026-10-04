"""Publish byte-exact recovery metadata and the separately requested hardware recapture."""
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT=Path.cwd()
assert (ROOT/'docs/DOCUMENTATION_MAP.md').is_file()
sys.path.insert(0,str(ROOT/'scripts'))
from benchmark_support import digest,read,save
import benchmark
from policy_review import validate_review

PUB=ROOT/'results/formal-comparison-20261004/timeout-preservation-20261005'
PACK=Path('C:/meter-run-packages-20261005/opencode-muse-r02-provisional')
RESTORE=Path('C:/meter-run-restores-20261005/opencode-muse-r02-provisional')
RUN=Path('C:/meter-followups-20261004/20261004-opencode-cli-opencode-muse-r02')
CO=RUN/'checkout'
original=read(RUN/'run-manifest.json')
ledger_path=Path(original['operator']['comparison']['ledger'])
ledger=read(ledger_path)
freeze=read(RUN/'operator-source-freeze.json')
assert digest((RUN/'run-manifest.json').read_bytes())==freeze['terminal_manifest_sha256']==ledger['runs'][-1]['terminal_manifest_sha256']
assert original['outputs']['implementation_commit'] is None and ledger['runs'][-1]['reviewed'] is False
benchmark.verify_agent_inputs(RUN,original)
validate_review(original,RUN/'run-manifest.json')
assert subprocess.check_output(['git','status','--porcelain'],cwd=CO,text=True).strip()==''
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CO,text=True).strip()==freeze['commit']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd='C:/meter-operator-20261004',text=True).strip()==original['execution']['base_commit']
assert subprocess.check_output(['git','status','--porcelain'],cwd='C:/meter-operator-20261004',text=True).strip()==''

copies={
    'create-report.json':PACK.parent/'opencode-muse-r02-provisional-create.json',
    'package-manifest.json':PACK/'package-manifest.json',
    'manifest-derivation.json':PACK/'operator/manifest-derivation.json',
    'source-snapshot.json':PACK/'operator/operator-source-snapshot.json',
    'restore-report.json':RESTORE/'restore-report.json',
    'restore-audit.json':RESTORE/'frozen-validator-audit.json',
    'prepare-provisional.py':PACK.parent/'prepare-opencode-r02-provisional.py',
    'audit-provisional.py':PACK.parent/'audit-opencode-r02-provisional.py',
    'publish-recovery.py':Path(__file__)}
PUB.mkdir(exist_ok=False)
for name,source in copies.items():shutil.copyfile(source,PUB/name)

REC=RUN/'operator-observation/recapture-r2-20261005'
REC_PUB=ROOT/'results/formal-comparison-20261004/evidence'/original['run_id']/'operator-observation/recapture-r2-20261005'
slot=read(REC/'hardware-slot.json')
capture=read(REC/'reference-capture-r1/capture.json')
assert slot['status']=='awaiting_user_optical_observation'
assert slot['original_terminal_unchanged'] and slot['original_ledger_unchanged']
assert slot['artifact_sha256']==freeze['artifacts']['firmware/build/cdm_meter.bin']['sha256']
assert all(item['literal_acceptance_observed'] for item in slot['receiver_acceptance_review'])
assert capture['sender_kind']=='operator_replay' and capture['optical_status']=='not_run'
assert slot['sent_frames_sha256']=='811c399098ff8ffefc587469d49e61d30ea7c7ffa440c477d47dbe0cffabb2cd'
assert digest((REC/'reference-capture-r1/sent-frames.jsonl').read_bytes())==slot['sent_frames_sha256']
REC_PUB.mkdir(parents=True,exist_ok=False)
for source in REC.rglob('*'):
    if source.is_file():
        target=REC_PUB/source.relative_to(REC);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
shutil.copyfile(Path('C:/meter-followups-20261004/reobserve-opencode-r02-20261005.py'),REC_PUB/'reobserve.py')
rec_inventory={p.relative_to(REC_PUB).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size}
               for p in REC_PUB.rglob('*') if p.is_file()}
save(REC_PUB/'inventory.json',{'scope':'Second operator hardware observation attempt; original attempt preserved.',
                             'run_id':original['run_id'],'files':rec_inventory})

processes=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',
    "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^opencode' -or $_.ProcessId -in @(1900,15812,15184,26704) } | Select-Object ProcessId,Name) | ConvertTo-Json -Compress"],text=True) or '[]')
assert not processes
checked=datetime.now(timezone.utc).isoformat()
validation={'checked_at':checked,'run_id':original['run_id'],'terminal_manifest_sha256':digest((RUN/'run-manifest.json').read_bytes()),
            'original_terminal_and_ledger_unchanged':True,'candidate_source_clean_and_unchanged':True,
            'fixed_operator_baseline_unchanged':True,'immutable_input_files_verified':57,
            'policy_status':'invalid_for_comparison','candidate_processes_alive':False,
            'candidate_executions_added':0,'remaining_followup_seconds':0,
            'provisional_package_manifest_sha256':digest((PACK/'package-manifest.json').read_bytes()),
            'package_files_verified':read(RESTORE/'frozen-validator-audit.json')['files_verified'],
            'frozen_validators_audit':'restore-audit.json','latest_hardware_attempt':str(REC),
            'latest_hardware_artifact_sha256':slot['artifact_sha256'],'latest_receiver_sequences':[0,1],
            'latest_hardware_slot_state':slot['status'],'latest_hardware_ended_at':slot['upload_and_capture_ended_at'],
            'rm_review':'pending_user_optical_observation','candidate_result_submission':'missing',
            'candidate_selection_document_submission':'missing','provisional_package_is_final_rm_record':False}
save(PUB/'validation.json',validation)
files={p.relative_to(PUB).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size}
       for p in PUB.rglob('*') if p.is_file()}
save(PUB/'inventory.json',{'run_id':original['run_id'],'files':files})

progress_path=ROOT/'results/formal-comparison-20261004/progress.json'
progress=read(progress_path)
progress.update(checked_at=checked,started_at=original['execution']['started_at'],candidate_processes_alive=False,
                current_hardware_slot=str(REC/'hardware-slot.json'),hardware_observation_attempt=2,
                hardware_slot_state='Same frozen r02 artifact reuploaded at user request; common frames accepted; manual LCD/BOOT observation pending; serial closed.',
                last_hardware_capture_ended_at=slot['upload_and_capture_ended_at'],
                provisional_preservation='timeout-preservation-20261005/validation.json',
                provisional_preservation_verified=True,
                provisional_package_manifest_sha256=validation['provisional_package_manifest_sha256'])
save(progress_path,progress)
print(json.dumps(validation,ensure_ascii=False,indent=2))
