"""Package the bounded followup2 review, preserving the earlier package."""
from pathlib import Path
import importlib.util, json, shutil, sys
RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r03');OUT=RUN/'operator-observation'
PACK=Path('C:/meter-run-packages-20261007/codex-luna-followup02-evaluation');REST=Path('C:/meter-run-restores-20261007/codex-luna-followup02-evaluation')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest, verify_evidence
from policy_review import validate_review
m=read(RUN/'run-manifest.json');assert m['operator']['comparison']['reference_status']=='fail'
shutil.copy2(Path(__file__),OUT/'operator-helpers'/Path(__file__).name)
shutil.copy2(Path('C:/meter-run-packages-20261007/verify-codex-luna-followup02-evaluation.py'),OUT/'operator-helpers/verify-codex-luna-followup02-evaluation.py')
for p in OUT.rglob('*'):
    if p.is_file():m['operator']['evidence'][p.relative_to(RUN).as_posix()]=digest(p.read_bytes())
save(RUN/'run-manifest.json',m);verify_evidence(m,RUN);validate_review(m,RUN/'run-manifest.json')
spec=importlib.util.spec_from_file_location('operator_artifact_collector',OUT/'operator-helpers/artifact-collector-evidence_package.py');collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
created=collector.create_package(RUN,PACK);save(PACK.parent/'codex-luna-followup02-evaluation-create.json',created)
restored=collector.restore_package(PACK,REST,created['package_manifest_sha256'])
print(json.dumps({'package':created,'restore':restored}))
