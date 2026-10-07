"""Preserve same-artifact hardware observations in a new package; old package immutable."""
from pathlib import Path
import json,shutil,sys
BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-followups-20261007/20261007-antigravity-cli-agy-flash-r02');OUT=RUN/'operator-observation'
PACK=Path('C:/meter-run-packages-20261007/agy-flash-followup03-awaiting');REST=Path('C:/meter-run-restores-20261007/agy-flash-followup03-awaiting')
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import read,save,digest,verify_evidence
from evidence_package import create_package,restore_package
from policy_review import validate_review
m=read(RUN/'run-manifest.json');slot=read(OUT/'hardware-slot.json');f=read(RUN/'operator-source-freeze.json')
assert m['operator']['status']=='completed' and slot['upload_completed'] and slot['receiver_acceptance_observed'] and slot['serial_closed_after_capture']
assert slot['artifact_sha256']==f['artifacts']['build/meter_esp32s3.bin']['sha256']
shutil.copy2(RUN.parent/'observe-agy-flash-followup-03.py',OUT/'operator-helpers/observe-agy-flash-followup-03.py')
shutil.copy2(Path(__file__),OUT/'operator-helpers'/Path(__file__).name)
for source in OUT.rglob('*'):
 if source.is_file():m['operator']['evidence'][source.relative_to(RUN).as_posix()]=digest(source.read_bytes())
save(RUN/'run-manifest.json',m);verify_evidence(m,RUN);validate_review(m,RUN/'run-manifest.json')
created=create_package(RUN,PACK);save(PACK.parent/'agy-flash-followup03-awaiting-create.json',created)
restored=restore_package(PACK,REST,created['package_manifest_sha256'])
print(json.dumps({'package':created,'restore':restored}))
