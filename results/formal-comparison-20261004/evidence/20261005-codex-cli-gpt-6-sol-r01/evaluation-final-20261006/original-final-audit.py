"""Fresh independent final audit using only the package/restoration's validators."""
from pathlib import Path
import json,sys,zipfile
PACK=Path('C:/meter-run-packages-20261006/codex-sol-r01-final')
REST=Path('C:/meter-run-restores-20261006/codex-sol-r01-final')
OP=REST/'operator';CO=REST/'checkout';FROZEN=REST/'frozen-operator-audit'
trusted=json.loads((PACK.parent/'codex-sol-r01-final-create.json').read_text(encoding='utf-8'))['package_manifest_sha256']
FROZEN.mkdir(exist_ok=False)
with zipfile.ZipFile(OP/'operator-baseline.zip') as z:z.extractall(FROZEN)
sys.path.insert(0,str(FROZEN/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from operator_baseline import verify
from policy_review import validate_review
from evidence_package import verify_report_dependencies

assert digest((PACK/'package-manifest.json').read_bytes())==trusted
package=read(PACK/'package-manifest.json');m=read(OP/'run-manifest.json');f=read(OP/'operator-source-freeze.json')
for name,item in package['files'].items():
    p=PACK/name;raw=Path('\\\\?\\'+str(p.resolve())).read_bytes()
    assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
verify(m,OP);verify_evidence(m,OP);benchmark.verify_agent_inputs(OP,m);verify_report_dependencies(m,OP)
assert validate_review(m,OP/'run-manifest.json')['decision']['status']=='eligible'
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit']
original=read(OP/'operator-observation/terminal-originals/run-manifest.json')
assert digest((OP/'operator-observation/terminal-originals/run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
assert original['measurement']==m['measurement']
for key,value in original['execution'].items():
    if key!='worktree':assert value==m['execution'][key],key
for name,item in f['sources'].items():
    raw=(OP/item['operator_raw_copy']).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
    if name!=m['outputs']['structured_result']:assert (CO/name).read_bytes().replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'),name
for name,item in f['artifacts'].items():
    raw=(OP/item['operator_raw_copy']).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
    if name.endswith(('.bin','.elf','.exe','.dll.a')):assert (CO/name).read_bytes()==raw,name
assert not f['firmware_source_mutations_after_last_build']
report=read(OP/'reference-review.json');ledger=read(OP/'comparison-ledger.json')
assert {k:v['status'] for k,v in report['items'].items()}=={'RM1':'pass','RM2':'fail','RM3':'fail','RM4':'fail','RM5':'fail'}
assert ledger['runs'][0]['reviewed'] and ledger['runs'][0]['reference_status']=='fail' and len(ledger['runs'])==1
assert ledger['runs'][0]['implementation_commit']==f['commit'] and ledger['runs'][0]['tokens']==m['measurement']['tokens']
assert ledger['runs'][0]['terminal_manifest_sha256']==f['original_terminal_manifest_sha256']
assert report['product_pass'] is False and report['policy_status']=='eligible'
slot=read(OP/'operator-observation/hardware-slot.json');rx=read(OP/'operator-observation/receiver-source-review.json')
assert slot['upload_completed'] and slot['artifact_sha256']==digest((CO/'build/codex_desk_meter.bin').read_bytes())
assert not rx['accepted'] and [v['error'] for v in rx['rejected']]==['SCHEMA_INVALID','SCHEMA_INVALID']
video=OP/'operator-observation/user-video-01';meta=read(video/'video-metadata.json');vr=read(video/'video-review.json')
assert digest((video/'source.mp4').read_bytes())==meta['source_sha256']==vr['video_sha256']
assert vr['navigation']['short_boot_presses_user_confirmed']==3 and vr['navigation']['user_reported_response']=='none'
assert (OP/'operator-observation/reference-capture-r1/sent-frames.jsonl').read_bytes()==(OP/'reference/expected-frames.jsonl').read_bytes()
audit=dict(read(REST/'restore-report.json'),frozen_operator_validators_used=True,inventory_bytes_verified=True,
    immutable_input_files_verified=57,original_terminal_and_cost_preserved=True,
    raw_candidate_source_files_verified=len(f['sources']),raw_candidate_artifacts_verified=len(f['artifacts']),
    candidate_artifact_source_binding_verified=True,rm_review_completed=True,
    rm_items={k:v['status'] for k,v in report['items'].items()},reference_status='fail',policy_status='eligible',product_pass=False,
    physical_upload_verified=True,common_frames_rejected_verified=True,user_video_and_boot_observation_verified=True,
    video_sha256=meta['source_sha256'],video_duration_seconds=meta['duration_seconds'],
    original_run_or_checkout_path_used=False,candidate_rebuild_or_model_replay=False,
    continuous_30s_certified=False,followups_run=0,remaining_followup_seconds=7200,remaining_followup_rounds=3,
    scope='Source/artifact/evidence/measurement/policy/RM independent audit. Existing host checks preserved; no tests rerun, no source mutation.')
save(REST/'frozen-validator-audit.json',audit)
print(json.dumps(audit))
