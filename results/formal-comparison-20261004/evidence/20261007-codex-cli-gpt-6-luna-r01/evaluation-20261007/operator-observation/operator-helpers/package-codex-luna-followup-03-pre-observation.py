"""Preserve build-idf artifacts with the already-generalized operator collector."""
from datetime import datetime, timezone
from pathlib import Path
import importlib.util, json, shutil, sys
BASE=Path('C:/meter-operator-20261004');ROOT=Path('C:/Users/이광진/orca/codex-desk-meter')
RUN=Path('C:/meter-followups-20261007/20261007-codex-cli-gpt-6-luna-r01');OUT=RUN/'operator-observation'
PACK=Path('C:/meter-run-packages-20261007/codex-luna-followup03-pre-observation');REST=Path('C:/meter-run-restores-20261007/codex-luna-followup03-pre-observation')
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import read, save, digest, verify_evidence
from policy_review import validate_review
spec=importlib.util.spec_from_file_location('operator_artifact_collector',ROOT/'scripts/evidence_package.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
assert m['operator']['status'] in {'completed','timeout','aborted','environment_failed'} and digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
assert validate_review(m,RUN/'run-manifest.json')['decision']['status'] in {'eligible','invalid_for_comparison'}
assert not f['firmware_source_mutations_after_last_build']
helpers=OUT/'operator-helpers';helpers.mkdir(exist_ok=False)
for name in ['preserve-codex-luna-followup-03.py','prepare-luna-followup03-shell-audit.py','review-codex-luna-followup-03-policy.py',Path(__file__).name]:shutil.copy2(RUN.parent/name,helpers/name)
shutil.copy2(ROOT/'scripts/evidence_package.py',helpers/'artifact-collector-evidence_package.py')
save(OUT/'artifact-collection-procedure.json',{'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'tool':'operator-helpers/artifact-collector-evidence_package.py','tool_sha256':digest((ROOT/'scripts/evidence_package.py').read_bytes()),
    'existing_remediation':'docs/plans/2026-10-04-evidence-artifact-layout-remediation.md','root_git_head':__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'actual_build_root':'build','method':'Existing result.build.evidence artifact-directory collector; all five firmware artifact kinds required in one directory.',
    'frozen_dependencies_root':str(BASE),'frozen_validators_unchanged':True,'candidate_inputs_source_artifacts_unchanged':True,
    'operator_preparation_error':None})
names=['operator-source-preparation.json','operator-source-freeze.json','operator-terminal-source.bundle','operator-policy-decision.json','policy-review.json']
names += [p.name for p in RUN.iterdir() if p.is_file() and p.name in {'experiment-launch.json','native-start-observation.json','native-start-observation-prefix.jsonl','process-at-start.json','operator-next-model-decision.json','previous-progress-at-transition.json'}]
names += [p.relative_to(RUN).as_posix() for d in ('operator-observation','operator-launch-preflight') for p in (RUN/d).rglob('*') if p.is_file()]
for name in names:m['operator']['evidence'][name]=digest((RUN/name).read_bytes())
m['outputs']['implementation_commit']=f['commit'];m['outputs']['build_status']='pass'
save(RUN/'run-manifest.json',m);verify_evidence(m,RUN);validate_review(m,RUN/'run-manifest.json')
created=collector.create_package(RUN,PACK);save(PACK.parent/'codex-luna-followup03-pre-observation-create.json',created)
restored=collector.restore_package(PACK,REST,created['package_manifest_sha256'])
print(json.dumps({'package':created,'restore':restored}))
