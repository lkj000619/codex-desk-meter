"""Audit timeout preservation using only its package, restored tree and frozen validators."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import zipfile

PACKAGE=Path('C:/meter-run-packages-20261005/opencode-muse-r02-provisional')
RESTORED=Path('C:/meter-run-restores-20261005/opencode-muse-r02-provisional')
FROZEN=Path('C:/meter-run-restores-20261005/opencode-muse-r02-provisional-frozen-operator')
EXPECTED='9a7c506fe8cd3e861184232134dd2127b847d523997b44a51941ad7a9c045fc3'
FROZEN.mkdir(exist_ok=False)
with zipfile.ZipFile(RESTORED/'operator/operator-baseline.zip') as archive:
    for item in archive.infolist():
        relative=Path(item.filename)
        target=FROZEN/relative
        assert not relative.is_absolute() and '..' not in relative.parts
        assert target.resolve().is_relative_to(FROZEN.resolve()) and not item.is_dir()
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(archive.read(item))
sys.path.insert(0,str(FROZEN/'scripts'))
from benchmark_support import digest,read,save,validate_operator,validate_schema,verify_evidence
from benchmark import verify_agent_inputs,validate_preflight_receipt
from evidence_package import verify_report_dependencies
from policy_review import review_eligibility
from reference_inputs import validate_reference

inventory=read(PACKAGE/'package-manifest.json')
assert digest((PACKAGE/'package-manifest.json').read_bytes())==EXPECTED
assert {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*') if p.is_file()}==set(inventory['files'])|{'package-manifest.json'}
for name,metadata in inventory['files'].items():
    data=(PACKAGE/name).read_bytes()
    assert len(data)==metadata['bytes'] and digest(data)==metadata['sha256']
    if name.startswith(('operator/','checkout/')):
        target='operator/raw-run-manifest.json' if name=='operator/run-manifest.json' else name
        assert (RESTORED/target).read_bytes()==data

OP=RESTORED/'operator'
CO=RESTORED/'checkout'
manifest=read(OP/'run-manifest.json')
raw=read(OP/'raw-run-manifest.json')
original=read(OP/'operator-terminal-manifest-original.json')
derivation=read(OP/'manifest-derivation.json')
ledger=read(OP/'comparison-ledger.json')
freeze=read(OP/'operator-source-freeze.json')
original_sha=digest((OP/'operator-terminal-manifest-original.json').read_bytes())
assert original_sha==derivation['original_terminal_manifest_sha256']==freeze['terminal_manifest_sha256']==ledger['runs'][-1]['terminal_manifest_sha256']
assert digest((OP/'comparison-ledger.json').read_bytes())==derivation['original_ledger_sha256']
assert original['operator']['status']=='timeout' and original['outputs']['implementation_commit'] is None
assert ledger['runs'][-1]['reviewed'] is False and ledger['runs'][-1]['implementation_commit'] is None
assert derivation['changed_fields']==['outputs.implementation_commit','operator.evidence']
assert raw['outputs']['implementation_commit']==freeze['commit']==inventory['implementation_commit']
expected=copy.deepcopy(original)
expected['outputs']['implementation_commit']=freeze['commit']
for name,value in derivation['added_evidence'].items():
    assert name not in original['operator']['evidence']
    assert digest((OP/name).read_bytes())==value
    expected['operator']['evidence'][name]=value
expected['operator']['evidence']['manifest-derivation.json']=digest((OP/'manifest-derivation.json').read_bytes())
assert raw==expected
remapped=copy.deepcopy(raw);remapped['execution']['worktree']=str(CO)
assert manifest==remapped
validate_schema(original,'run-manifest.schema.json')
validate_operator(original)
validate_schema(manifest,'run-manifest.schema.json')
validate_operator(manifest)
verify_evidence(manifest,OP)
verify_report_dependencies(manifest,OP)
verify_agent_inputs(OP,manifest)
validate_preflight_receipt(read(OP/'execution-preflight.json'),manifest,read(OP/'profile.json'),OP/'preflight-evidence')
validate_reference(OP/'reference/reference-inputs.json')
eligible,status,reason=review_eligibility(manifest,OP/'run-manifest.json')
assert eligible is False and status=='invalid_for_comparison'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CO,text=True).strip()==freeze['commit']
assert subprocess.check_output(['git','remote'],cwd=CO,text=True).strip()==''
assert inventory['result'] is None and inventory['evaluation_manifest'] is None
for name in ('structured_result','selection_document'):
    assert not (CO/original['outputs'][name]).exists()
assert not (OP/'reference-review.json').exists()

snapshots=read(OP/'operator-source-snapshot.json')
assert snapshots['implementation_commit']==freeze['commit']
source_byte_differences=[]
for name,metadata in snapshots['files'].items():
    data=(OP/metadata['operator_copy']).read_bytes()
    assert digest(data)==metadata['sha256'] and len(data)==metadata['bytes']
    tree_blob=subprocess.check_output(['git','rev-parse','HEAD:'+name],cwd=CO,text=True).strip()
    normalized_blob=subprocess.check_output(['git','hash-object','--path='+name,'--stdin'],cwd=CO,input=data).decode().strip()
    assert tree_blob==normalized_blob
    if (CO/name).read_bytes()!=data:source_byte_differences.append(name)
build=read(OP/'operator-observation/build-source-review.json')
for name,value in build['source_sha256'].items():
    assert snapshots['files'][name]['sha256']==value
artifact_hashes={}
artifact_git_byte_differences=[]
for name,metadata in freeze['artifacts'].items():
    data=(OP/metadata['operator_copy']).read_bytes()
    assert digest(data)==metadata['sha256'] and len(data)==metadata['bytes']
    artifact_hashes[name]=digest(data)
    if (CO/name).read_bytes()!=data:artifact_git_byte_differences.append(name)
assert artifact_hashes['firmware/build/cdm_meter.bin']=='8e4eaaab7dd6c66abdc069043583c3805cd942d2afca496e48073bcc0255c75b'
slot=read(OP/'operator-observation/hardware-slot.json')
assert slot['implementation_commit']==freeze['commit'] and slot['artifact_sha256']==artifact_hashes['firmware/build/cdm_meter.bin']
assert slot['status']=='awaiting_user_optical_observation'
assert slot['receiver_acceptance_review']==[
    {'sequence':0,'crc':'203D8DF3','literal_acceptance_observed':True},
    {'sequence':1,'crc':'C4CAA941','literal_acceptance_observed':True}]
restore=read(RESTORED/'restore-report.json')
assert restore['result_valid'] is False and restore['policy_eligible'] is False
report={**restore,'scope':derivation['scope'],'frozen_operator_validators_used':True,
        'frozen_operator_scripts_root':str(FROZEN/'scripts'),'inventory_bytes_verified':True,
        'immutable_input_files_verified':len(read(OP/'candidate-inputs.json')['files']),
        'original_terminal_manifest_sha256':original_sha,'original_terminal_ledger_binding_verified':True,
        'manifest_derivation_fields_verified':derivation['changed_fields'],
        'source_snapshot_files_verified':len(snapshots['files']),
        'source_snapshot_git_blobs_verified':True,'source_git_checkout_byte_differences':source_byte_differences,
        'raw_artifact_sha256':artifact_hashes,'raw_artifact_copies_verified':len(artifact_hashes),
        'artifact_git_checkout_byte_differences':artifact_git_byte_differences,
        'artifact_storage':'Byte-exact operator copies; missing result cannot declare checkout artifact_paths.',
        'original_run_path_used':False,'candidate_result_submission':'missing',
        'candidate_selection_document_submission':'missing','candidate_execution_repeated':False,
        'candidate_result_fabricated':False,'remaining_followup_seconds':0,
        'rm_review':'pending_user_optical_observation','rm_review_completed':False}
save(RESTORED/'frozen-validator-audit.json',report)
print(json.dumps(report,ensure_ascii=False,indent=2))
