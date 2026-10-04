"""Package post-timeout evidence without modifying its authoritative terminal record."""
import copy
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path('C:/Users/\uC774\uAD11\uC9C4/orca/codex-desk-meter')
RUN=Path('C:/meter-followups-20261004/20261004-opencode-cli-opencode-muse-r02')
STAGING=Path('C:/meter-run-packages-20261005/opencode-muse-r02-provisional-staging')
PACKAGE=Path('C:/meter-run-packages-20261005/opencode-muse-r02-provisional')
sys.path.insert(0,str(ROOT/'scripts'))
from benchmark_support import read,save,digest,verify_evidence
import benchmark
from policy_review import validate_review
from evidence_package import create_package,safe_path

raw=(RUN/'run-manifest.json').read_bytes()
original=read(RUN/'run-manifest.json')
ledger_path=Path(original['operator']['comparison']['ledger'])
ledger_bytes=ledger_path.read_bytes()
ledger=read(ledger_path)
assert original['operator']['status']=='timeout'
assert original['outputs']['implementation_commit'] is None
assert ledger['runs'][-1]['reviewed'] is False
assert ledger['runs'][-1]['terminal_manifest_sha256']==digest(raw)
CO=Path(original['execution']['worktree'])
assert not (CO/original['outputs']['structured_result']).exists()
assert not (CO/original['outputs']['selection_document']).exists()
benchmark.verify_agent_inputs(RUN,original)
verify_evidence(original,RUN)
validate_review(original,RUN/'run-manifest.json')
freeze=read(RUN/'operator-source-freeze.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CO,text=True).strip()==freeze['commit']
assert subprocess.check_output(['git','status','--porcelain'],cwd=CO,text=True).strip()==''
STAGING.mkdir(exist_ok=False)
for p in RUN.rglob('*'):
    relative=p.relative_to(RUN)
    if relative.parts[0]=='checkout': continue
    if p.is_file():
        assert not p.is_symlink()
        target=safe_path(STAGING,relative.as_posix())
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,target)
source_snapshot={}
for base in ('firmware','pc_tools','tests'):
    for p in (CO/base).rglob('*'):
        relative=p.relative_to(CO)
        if (p.is_file() and not p.is_symlink() and 'build' not in relative.parts
                and '__pycache__' not in relative.parts
                and (p.suffix in {'.c','.h','.py'} or p.name in {'CMakeLists.txt','sdkconfig','sdkconfig.defaults'})):
            name='operator-observation/source-snapshot/'+relative.as_posix()
            target=safe_path(STAGING,name);target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,target)
            source_snapshot[relative.as_posix()]={'operator_copy':name,'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size}
save(STAGING/'operator-source-snapshot.json',{'implementation_commit':freeze['commit'],'files':source_snapshot})
derived=copy.deepcopy(original)
derived['outputs']['implementation_commit']=freeze['commit']
added={}
for p in STAGING.rglob('*'):
    if p.is_file() and p.name!='run-manifest.json':
        name=p.relative_to(STAGING).as_posix()
        expected=digest(p.read_bytes())
        if name not in derived['operator']['evidence']:
            added[name]=expected
        derived['operator']['evidence'][name]=expected
derivation={'run_id':original['run_id'],'created_at':datetime.now(timezone.utc).isoformat(),
            'scope':'Provisional evidence preservation before optical answer and RM review. Authoritative terminal record is unchanged.',
            'original_terminal_manifest_sha256':digest(raw),'original_ledger_sha256':digest(ledger_bytes),
            'authoritative_terminal_manifest_copy':'operator-terminal-manifest-original.json',
            'changed_fields':['outputs.implementation_commit','operator.evidence'],
            'implementation_commit':freeze['commit'],'added_evidence':added,
            'candidate_result_submission':'missing','candidate_selection_document_submission':'missing',
            'candidate_execution_repeated':False,'remaining_followup_seconds':0,'rm_review':'pending_user_optical_observation'}
save(STAGING/'manifest-derivation.json',derivation)
derived['operator']['evidence']['manifest-derivation.json']=digest((STAGING/'manifest-derivation.json').read_bytes())
save(STAGING/'run-manifest.json',derived)
assert {k:v for k,v in derived['outputs'].items() if k!='implementation_commit'}=={k:v for k,v in original['outputs'].items() if k!='implementation_commit'}
assert derived['measurement']==original['measurement'] and derived['execution']==original['execution']
assert derived['operator']['status']==original['operator']['status']
validate_review(derived,STAGING/'run-manifest.json')
created=create_package(STAGING,PACKAGE)
assert (RUN/'run-manifest.json').read_bytes()==raw and ledger_path.read_bytes()==ledger_bytes
assert subprocess.check_output(['git','status','--porcelain'],cwd=CO,text=True).strip()==''
report={'created_at':datetime.now(timezone.utc).isoformat(),**created,'scope':derivation['scope'],
        'original_terminal_unchanged':True,'original_ledger_unchanged':True,'source_snapshot_files':len(source_snapshot),
        'candidate_source_unchanged':True,'candidate_result_submission':'missing',
        'candidate_selection_document_submission':'missing','packager_sha256':digest((ROOT/'scripts/evidence_package.py').read_bytes())}
save(PACKAGE.parent/'opencode-muse-r02-provisional-create.json',report)
import json
print(json.dumps(report,ensure_ascii=False,indent=2))
