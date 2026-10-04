"""Publish dated post-terminal evidence and observation-wait state; no candidate/ledger edits."""
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import sys

ROOT=Path.cwd();BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02')
CO=RUN/'checkout';OUT=RUN/'operator-observation';PUBLIC=ROOT/'results/formal-comparison-20261004/evidence'/RUN.name/'evaluation-stage-20261005'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from policy_review import validate_review
from operator_baseline import verify

def windows_path(p):
    p=Path(p).resolve()
    return Path('\\\\?\\'+str(p)) if sys.platform=='win32' else p
def copy_bytes(source,dest):
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(windows_path(source),windows_path(dest))

m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');slot=read(OUT/'hardware-slot.json')
original=read(OUT/'terminal-status.json');checks=read(OUT/'host-checks.json');common=read(OUT/'common-stimulus-check.json')
policy=validate_review(m,RUN/'run-manifest.json')['decision']['status'];capture=read(OUT/'reference-capture-r1/capture.json');panic=read(OUT/'panic-source-review.json')
assert policy=='invalid_for_comparison' and slot['upload_completed'] and capture['status']=='captured'
assert [x['bytes_written'] for x in capture['frames']]==[1543,1543]
assert not slot['receiver_acceptance_observed'] and panic['load_prohibited_panic_count']==2
assert all(c['exit_code']==0 for c in checks['checks'])
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit'] and not benchmark.git('status','--porcelain',cwd=CO)
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
ledger=Path(m['operator']['comparison']['ledger'])
assert digest(ledger.read_bytes())==original['original_ledger_sha256']
assert not read(ledger)['runs'][-1]['reviewed']

reference=BASE/'experiments/reference/codex-7923f96/expected-frames.jsonl';expected=json.loads(reference.read_text(encoding='utf-8').splitlines()[0])
actual=read(OUT/'candidate-collector-legacy-frame.json');diffs=[]
def compare(a,b,path='$'):
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool) and a==b:return
    if type(a)!=type(b):diffs.append({'path':path,'actual':a,'expected':b});return
    if isinstance(a,dict):
        for k in sorted(a.keys()|b.keys()):
            if k not in a or k not in b:diffs.append({'path':path+'.'+k,'actual':a.get(k),'expected':b.get(k)})
            else:compare(a[k],b[k],path+'.'+k)
    elif isinstance(a,list):
        if len(a)!=len(b):diffs.append({'path':path+'.length','actual':len(a),'expected':len(b)})
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'['+str(i)+']')
    elif a!=b:diffs.append({'path':path,'actual':a,'expected':b})
compare(actual['payload'],expected['payload'])
save(OUT/'legacy-common-payload-differences.json',{'run_id':RUN.name,'reference_frames_sha256':digest(reference.read_bytes()),
    'legacy_collector_frame_sha256':digest((OUT/'candidate-collector-legacy-frame.jsonl').read_bytes()),'differences':diffs,
    'numeric_equal_values_treated_equivalent_for_semantic_comparison':True,'wire_canonical_match':False})
HOST=Path(checks['fresh_host_build_directory'])
host_names=['test_meter_parser.exe','test_meter_state.exe','test_feature_imu.exe','test_gui_regression.exe','meter_legacy_adapter.exe',
            'libmeter_core.a','CMakeCache.txt','CTestTestfile.cmake','Testing/Temporary/LastTest.log']
host_inventory={name:{'path':str(HOST/name),'bytes':(HOST/name).stat().st_size,'sha256':digest((HOST/name).read_bytes())} for name in host_names}
save(OUT/'fresh-host-artifact-inventory.json',{'run_id':RUN.name,'implementation_commit':f['commit'],'files':host_inventory,
    'scope':'Separate operator host build, never uploaded. Submitted candidate binaries retained unchanged.'})

if PUBLIC.exists():
    assert not (PUBLIC/'snapshot-inventory.json').exists()
    save(OUT/'publication-attempt1-error.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),
        'operation':'First public evidence copy','error':'Windows 260-character file path limit; target hardware-feature-selection.md path length 265.',
        'recovery':'Resume same incomplete evidence snapshot with extended Windows paths; verify already copied bytes before continuing. No candidate, hardware, terminal manifest or ledger mutation.',
        'model_calls':0})
else:
    PUBLIC.mkdir(parents=True,exist_ok=False)
files=[RUN/name for name in ['run-manifest.json','stdout.jsonl','stderr.txt','command-audit.json','prompt.txt','profile.json','candidate-inputs.json',
    'agent-context.json','policy-review.json','operator-policy-decision.json','operator-source-freeze.json']]
files.extend(p for p in OUT.rglob('*') if p.is_file() and p.suffix.lower() not in {'.elf','.map'})
files.extend([RUN/'operator-launch-preflight/scope-exit.json',RUN/'operator-launch-preflight/current-checks.json'])
for p in files:
    dest=PUBLIC/p.relative_to(RUN)
    if windows_path(dest).is_file():
        assert digest(windows_path(dest).read_bytes())==digest(p.read_bytes()),str(dest)
    else:
        copy_bytes(p,dest)
copy_bytes(ledger,PUBLIC/'ledger-original.json')
for name in ['freeze-agy-flash-r02.py','check-agy-flash-r02.py','observe-agy-flash-r02.py',Path(__file__).name]:
    dest=PUBLIC/'operator-helpers'/name;copy_bytes(RUN.parent/name,dest)
now=datetime.now(timezone.utc).isoformat()
inventory={'run_id':RUN.name,'captured_at':now,'scope':'Post-terminal freeze, policy, independent host and first hardware capture; user optical/RM evaluation and final package pending. Original launch and terminal-status snapshots preserved.',
    'files':{p.relative_to(PUBLIC).as_posix():{'sha256':digest(windows_path(p).read_bytes()),'bytes':windows_path(p).stat().st_size} for p in PUBLIC.rglob('*') if windows_path(p).is_file()},
    'external_source_bundle':{'path':str(RUN/'operator-terminal-source.bundle'),'sha256':f['source_bundle_sha256']},
    'large_elf_map_files':'Outside repository; paths/hash/size preserved in operator-source-freeze.json.'}
save(PUBLIC/'snapshot-inventory.json',inventory)
p=ROOT/'results/formal-comparison-20261004/progress.json';progress=read(p)
progress.update(checked_at=now,state='agy_flash_followup_1_awaiting_optical_observation',policy_status=policy,
    policy_review_required=True,rm_review='awaiting_user_optical_observation',launcher_pid=None,
    implementation_commit=f['commit'],source_git_freeze_status='complete',hardware_artifact_sha256=slot['artifact_sha256'],
    hardware_upload='pass',hardware_upload_completed_at=slot['upload_completed_at'],hardware_reference_capture='captured',
    receiver_acceptance_observed=False,receiver_acceptance_sequences=[],hardware_common_frames_bytes_written=[1543,1543],
    hardware_load_prohibited_panics_observed=2,hardware_rebooting_markers_observed=2,
    candidate_host_tests={'python_passed':6,'fresh_host_c_tests_passed':4,'submitted_executables_passed':4},
    candidate_result_independent_schema_validation='pass',candidate_collector_common_payload_match=False,
    candidate_collector_default_common_payload_match=False,candidate_collector_legacy_common_payload_match=False,
    candidate_encoder_common_wire_match=True,operator_audited_user_interventions=0,
    candidate_current_phase='Frozen and independently checked; submitted original firmware uploaded and common seq 0/1 writes completed. Two LoadProhibited panics/reboots, no acceptance logs. Await user optical/BOOT video and one-time final RM review.',
    board_state=slot['board_state'],terminal_snapshot=PUBLIC.relative_to(ROOT).as_posix(),
    restart_instruction='Do not rerun r02 or replace firmware before video evaluation. Current r02 original app uploaded 2026-10-05 05:38:52 KST. Match user recording to this slot/artifact, record optical/BOOT findings, apply one RM review, archive/restore, then decide allowed followup with 5710.781 seconds and 2 rounds remaining. Policy invalidity and crash/collector mismatch stay preserved.')
save(p,progress)
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
assert digest(ledger.read_bytes())==original['original_ledger_sha256']
print(json.dumps({'public_files':len(inventory['files']),'inventory_sha256':digest((PUBLIC/'snapshot-inventory.json').read_bytes()),
    'source_commit':f['commit'],'policy_status':policy,'upload':'pass','common_write_bytes':[1543,1543],
    'frame_acceptance_observed':False,'load_prohibited_panics':2,'optical_rm_review':'pending_user','manifest_and_ledger_unchanged':True}))
