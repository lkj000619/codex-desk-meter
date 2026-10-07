"""Fresh interpreter, packaged frozen validators and byte/source/artifact verification."""
from datetime import datetime,timezone
from pathlib import Path
import json,subprocess,sys,zipfile
PACK=Path('C:/meter-run-packages-20261007/agy-flash-followup03-awaiting');REST=Path('C:/meter-run-restores-20261007/agy-flash-followup03-awaiting')
OP=REST/'operator';CO=REST/'checkout';FROZEN=REST/'frozen-operator-audit'
expected=json.loads((PACK.parent/'agy-flash-followup03-awaiting-create.json').read_text(encoding='utf-8'))['package_manifest_sha256']
def extended(p):return Path('\\\\?\\'+str(p.resolve()))
FROZEN.mkdir(exist_ok=False)
with zipfile.ZipFile(OP/'operator-baseline.zip') as z:
 for item in z.infolist():
  target=(FROZEN/item.filename).resolve();assert target.is_relative_to(FROZEN.resolve())
  if item.is_dir():target.mkdir(parents=True,exist_ok=True)
  else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(item))
sys.path.insert(0,str(FROZEN/'scripts'))
import benchmark
from benchmark_support import read,save,digest,verify_evidence,validate_schema,validate_operator
from operator_baseline import verify
from policy_review import validate_review
from evidence_package import verify_report_dependencies
assert digest((PACK/'package-manifest.json').read_bytes())==expected
inventory=read(PACK/'package-manifest.json');m=read(OP/'run-manifest.json');f=read(OP/'operator-source-freeze.json')
for name,item in inventory['files'].items():
 raw=extended(PACK/name).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
validate_schema(m,'run-manifest.schema.json');validate_operator(m);verify(m,OP);verify_evidence(m,OP);benchmark.verify_agent_inputs(OP,m);verify_report_dependencies(m,OP)
benchmark.validate_preflight_receipt(read(OP/'execution-preflight.json'),m,read(OP/'profile.json'),OP/'preflight-evidence')
assert validate_review(m,OP/'run-manifest.json')['decision']['status']=='eligible'
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit']==m['outputs']['implementation_commit']
original=read(OP/'operator-observation/terminal-originals/run-manifest.json')
assert digest((OP/'operator-observation/terminal-originals/run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
assert original['measurement']==m['measurement']
assert {k:v for k,v in original['execution'].items() if k!='worktree'}=={k:v for k,v in m['execution'].items() if k!='worktree'}
generated=[]
for name,item in f['sources'].items():
 raw=extended(OP/item['operator_raw_copy']).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
 if name!=m['outputs']['structured_result']:assert extended(CO/name).read_bytes().replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'),name
 probe=subprocess.run(['git','-c','core.longpaths=true','rev-parse','HEAD:'+name],cwd=CO,capture_output=True,text=True)
 if probe.returncode:assert name=='sdkconfig' and name in f['artifacts'];generated.append(name)
 else:
  blob=subprocess.check_output(['git','-c','core.longpaths=true','hash-object','--path='+name,'--stdin'],cwd=CO,input=raw).decode().strip();assert blob==probe.stdout.strip(),name
for name,item in f['artifacts'].items():
 raw=extended(OP/item['operator_raw_copy']).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
 if name.endswith(('.bin','.elf')):assert extended(CO/name).read_bytes()==raw,name
assert (CO/'build/meter_esp32s3.elf').read_bytes()[:4]==b'\x7fELF' and not f['firmware_source_mutations_after_last_build']
checks=read(OP/'operator-observation/host-checks.json');common=read(OP/'operator-observation/common-stimulus-check.json')
assert all(c['exit_code']==0 for c in checks['checks']) and all(x['matches_common_wire'] for x in common['candidate_encoder_checks'])
assert all(x['matches_common_payload'] and x['matches_common_wire'] for x in common['actual_collector_api_modes'].values())
assert read(REST/'restore-report.json')['result_valid']
slot=read(OP/'operator-observation/hardware-slot.json')
assert slot['upload_completed'] and slot['receiver_acceptance_observed'] and slot['serial_closed_after_capture']
assert slot['artifact_sha256']==f['artifacts']['build/meter_esp32s3.bin']['sha256']
audit=dict(read(REST/'restore-report.json'),checked_at=datetime.now(timezone.utc).isoformat(),frozen_operator_validators_used=True,
 original_run_or_checkout_path_used=False,inventory_bytes_verified=True,immutable_input_files_verified=57,original_terminal_and_cost_preserved=True,
 raw_candidate_source_files_verified=len(f['sources']),raw_candidate_artifacts_verified=len(f['artifacts']),source_git_blobs_verified=True,
 generated_config_raw_verified=generated,candidate_artifact_source_binding_verified=True,archived_host_check_results_verified=True,
 collector_matches_common_reference_payload=True,common_wire_encoder_exact_match=True,reference_review_applied=False,
 hardware_status='uploaded_awaiting_optical_observation',device_common_frames_accepted=True,product_pass=False,series_policy_status='invalid_for_comparison')
save(REST/'frozen-validator-audit.json',audit)
print(json.dumps(audit))
