"""Final independent frozen-validator/source/cost/video/RM audit."""
from pathlib import Path
import json,sys,zipfile
PACK=Path('C:/meter-run-packages-20261006/codex-sol-followup02-final');REST=Path('C:/meter-run-restores-20261006/codex-sol-followup02-final')
OP=REST/'operator';CO=REST/'checkout';FROZEN=REST/'frozen-operator-audit'
trusted=json.loads((PACK.parent/'codex-sol-followup02-final-create.json').read_text(encoding='utf-8'))['package_manifest_sha256']
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
    raw=Path('\\\\?\\'+str((PACK/name).resolve())).read_bytes()
    assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
verify(m,OP);verify_evidence(m,OP);benchmark.verify_agent_inputs(OP,m);verify_report_dependencies(m,OP)
assert validate_review(m,OP/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
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
    if name.endswith(('.bin','.elf')):assert (CO/name).read_bytes()==raw,name
assert not f['firmware_source_mutations_after_last_build']
report=read(OP/'reference-review.json');ledger=read(OP/'comparison-ledger.json');expected={f'RM{i}':'pass' for i in range(1,6)}
assert {k:v['status'] for k,v in report['items'].items()}==expected
assert len(ledger['runs'])==3 and ledger['state']=='reached' and ledger['runs'][-1]['reviewed'] and ledger['runs'][-1]['reference_status']=='pass'
assert ledger['runs'][-1]['implementation_commit']==f['commit'] and ledger['runs'][-1]['tokens']==m['measurement']['tokens']
assert ledger['runs'][-1]['terminal_manifest_sha256']==f['original_terminal_manifest_sha256']
assert report['product_pass'] is False and report['policy_status']=='invalid_for_comparison'
slot=read(OP/'operator-observation/hardware-slot.json');rx=read(OP/'operator-observation/receiver-source-review.json')
assert slot['upload_completed'] and slot['artifact_sha256']==digest((CO/'build/codex_desk_meter.bin').read_bytes())
assert [v['sequence'] for v in rx['accepted']]==[0,1] and not rx['rejected']
video=OP/'operator-observation/user-video-01';meta=read(video/'video-metadata.json');vr=read(video/'video-review.json');identity=read(video/'capture-identity-confirmation.json')
assert digest((video/'source.mp4').read_bytes())==meta['source_sha256']==vr['video_sha256']==identity['video_sha256']
assert meta['duration_seconds']==63.3 and identity['user_initiated_reset_confirmed'] and vr['navigation']['returned_to_starting_information']
assert vr['reference_reached'] and vr['quality_reference_cost_eligible'] is False and not vr['continuity']['continuous_30s_readable_valid_data_certified']
for n in vr['individual_readable_frames_reviewed']:
    expected_frame=meta['sample_frames'][n-1]['sha256']
    assert digest((video/f'readable-frame-{n:03d}.png').read_bytes())==expected_frame
assert (OP/'operator-observation/reference-capture-r1/sent-frames.jsonl').read_bytes()==(OP/'reference/expected-frames.jsonl').read_bytes()
host=read(OP/'operator-observation/independent-host-checks/host-checks.json');common=read(OP/'operator-observation/independent-host-checks/common-stimulus-check.json')
assert all(v['exit_code']==0 for v in host['checks']) and common['legacy_collector']['matches_common_reference_payload']
assert common['encoder_matches_exact_common_frames']
remaining=7200-sum(v['elapsed_seconds'] for v in ledger['runs'] if v['round'])
audit=dict(read(REST/'restore-report.json'),frozen_operator_validators_used=True,inventory_bytes_verified=True,immutable_input_files_verified=57,
    original_terminal_and_cost_preserved=True,raw_candidate_source_files_verified=len(f['sources']),raw_candidate_artifacts_verified=len(f['artifacts']),
    candidate_artifact_source_binding_verified=True,rm_review_completed=True,rm_items=expected,reference_status='pass',
    policy_status='invalid_for_comparison',quality_reference_cost_eligible=False,product_pass=False,
    physical_upload_verified=True,common_frames_accepted_verified=[0,1],own_collector_and_common_payload_equality_verified=True,
    user_video_and_navigation_verified=True,user_initiated_reset_confirmed=True,video_sha256=meta['source_sha256'],video_duration_seconds=63.3,
    original_run_or_checkout_path_used=False,candidate_rebuild_or_model_replay=False,continuous_30s_readable_valid_data_certified=False,
    followups_run=2,remaining_followup_seconds=remaining,remaining_followup_rounds=1,additional_followup_allowed=False,ledger_state='reached',
    scope='Independent full evidence/cost/policy/RM audit with own frozen validators. Existing host checks preserved, no product tests replayed. Observed reference pass is separate from invalid quality/reference cost and incomplete full product.')
save(REST/'frozen-validator-audit.json',audit)
print(json.dumps(audit))
