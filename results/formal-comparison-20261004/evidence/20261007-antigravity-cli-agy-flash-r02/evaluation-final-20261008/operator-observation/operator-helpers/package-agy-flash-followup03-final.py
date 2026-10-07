"""Archive final optical review without changing earlier immutable packages."""
from pathlib import Path
import json, shutil, sys
RUN=Path('C:/meter-followups-20261007/20261007-antigravity-cli-agy-flash-r02');OUT=RUN/'operator-observation'
PACK=Path('C:/meter-run-packages-20261007/agy-flash-followup03-final');REST=Path('C:/meter-run-restores-20261007/agy-flash-followup03-final')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save,digest,verify_evidence
from evidence_package import create_package,restore_package
from policy_review import validate_review
m=read(RUN/'run-manifest.json')
assert m['operator']['comparison']['reference_status']=='pass'
for helper in [Path(__file__),PACK.parent/'verify-agy-flash-followup03-final.py']:
    shutil.copy2(helper,OUT/'operator-helpers'/helper.name)
for source in OUT.rglob('*'):
    if source.is_file():m['operator']['evidence'][source.relative_to(RUN).as_posix()]=digest(source.read_bytes())
save(RUN/'run-manifest.json',m);verify_evidence(m,RUN)
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='eligible'
created=create_package(RUN,PACK);save(PACK.parent/'agy-flash-followup03-final-create.json',created)
restored=restore_package(PACK,REST,created['package_manifest_sha256'])
print(json.dumps({'package':created,'restore':restored}))
