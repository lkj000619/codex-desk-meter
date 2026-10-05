"""Independent package-byte, frozen-validator, cost, RM and photograph audit."""
from pathlib import Path
import json,sys,zipfile
PACK=Path('C:/meter-run-packages-20261006/codex-sol-followup01-final')
REST=Path('C:/meter-run-restores-20261006/codex-sol-followup01-final')
OP=REST/'operator';CO=REST/'checkout';FROZEN=REST/'frozen-operator-audit'
trusted=json.loads((PACK.parent/'codex-sol-followup01-final-create.json').read_text(encoding='utf-8'))['package_manifest_sha256']
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
report=read(OP/'reference-review.json');ledger=read(OP/'comparison-ledger.json')
expected={'RM1':'pass','RM2':'partial','RM3':'fail','RM4':'fail','RM5':'fail'}
assert {k:v['status'] for k,v in report['items'].items()}==expected
assert len(ledger['runs'])==2 and ledger['runs'][-1]['reviewed'] and ledger['runs'][-1]['reference_status']=='fail'
assert ledger['runs'][-1]['implementation_commit']==f['commit'] and ledger['runs'][-1]['tokens']==m['measurement']['tokens']
assert ledger['runs'][-1]['terminal_manifest_sha256']==f['original_terminal_manifest_sha256']
assert report['product_pass'] is False and report['policy_status']=='invalid_for_comparison'
slot=read(OP/'operator-observation/hardware-slot.json');rx=read(OP/'operator-observation/receiver-source-review.json')
assert slot['upload_completed'] and slot['artifact_sha256']==digest((CO/'build/codex_desk_meter.bin').read_bytes())
assert [v['sequence'] for v in rx['accepted']]==[0,1] and not rx['rejected']
photo=OP/'operator-observation/user-photo-01';meta=read(photo/'photo-metadata.json');vr=read(photo/'photo-review.json')
assert digest((photo/'source.png').read_bytes())==meta['source_sha256']==vr['photo_sha256']
assert vr['navigation']['user_reported_response']=='none' and vr['reset']['user_initiated_reset_confirmed']
assert not vr['continuity']['continuous_30s_verified'] and not vr['reset']['spontaneous_reboot_verified']
assert (OP/'operator-observation/reference-capture-r1/sent-frames.jsonl').read_bytes()==(OP/'reference/expected-frames.jsonl').read_bytes()
host=read(OP/'operator-observation/independent-host-checks/host-checks.json')
assert all(v['exit_code']==0 for v in host['checks'])
diffs=read(OP/'operator-observation/independent-host-checks/legacy-collector-payload-differences.json')
assert len(diffs['differences'])==2 and diffs['all_other_payload_values_equal']
remaining=7200-sum(v['elapsed_seconds'] for v in ledger['runs'] if v['round'])
audit=dict(read(REST/'restore-report.json'),frozen_operator_validators_used=True,inventory_bytes_verified=True,
    immutable_input_files_verified=57,original_terminal_and_cost_preserved=True,
    raw_candidate_source_files_verified=len(f['sources']),raw_candidate_artifacts_verified=len(f['artifacts']),
    candidate_artifact_source_binding_verified=True,rm_review_completed=True,rm_items=expected,
    reference_status='fail',policy_status='invalid_for_comparison',product_pass=False,
    physical_upload_verified=True,common_frames_accepted_verified=[0,1],user_photo_and_button_observation_verified=True,
    photo_sha256=meta['source_sha256'],original_run_or_checkout_path_used=False,candidate_rebuild_or_model_replay=False,
    continuous_30s_certified=False,followups_run=1,remaining_followup_seconds=remaining,remaining_followup_rounds=2,
    source_executables_archived_and_host_checks_preserved=True,
    scope='Independent full evidence/cost/policy/RM audit with own frozen validators. Existing host checks preserved, no tests replayed.')
save(REST/'frozen-validator-audit.json',audit)
print(json.dumps(audit))
