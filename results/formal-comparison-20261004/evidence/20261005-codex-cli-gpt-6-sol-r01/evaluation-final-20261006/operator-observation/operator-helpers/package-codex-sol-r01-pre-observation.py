"""Preserve reviewed terminal outputs independently before hardware observation."""
from datetime import datetime,timezone
from pathlib import Path
import json,re,subprocess,sys,zipfile

BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01')
CO=RUN/'checkout';OUT=RUN/'operator-observation'
PACK=Path('C:/meter-run-packages-20261006/codex-sol-r01-pre-observation')
REST=Path('C:/meter-run-restores-20261006/codex-sol-r01-pre-observation')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import digest,read,save
from policy_review import create_review,validate_review
from evidence_package import create_package,restore_package

m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
assert m['operator']['status']=='completed' and digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
assert not f['firmware_source_mutations_after_last_build']
events=[json.loads(s) for s in (RUN/'stdout.jsonl').read_text(encoding='utf-8').splitlines()]
items=[(n,e['item']) for n,e in enumerate(events,1) if e.get('type')=='item.completed']
commands=[{'raw_line':n,**i} for n,i in items if i.get('type')=='command_execution']
changes=[{'raw_line':n,**i} for n,i in items if i.get('type')=='file_change']
assert len(commands)==81 and len(changes)==43 and len(events)==260
assert all(i.get('type') in {'command_execution','file_change','agent_message','error'} for _,i in items)
for item in changes:
    for change in item['changes']:assert Path(change['path']).resolve().is_relative_to(CO.resolve())
for item in commands:
    assert not any(s in item['command'].lower() for s in ('http://','https://','idf.py flash','com3','meter-followups','agy-pro','agy-flash','opencode'))
    assert not re.search(r'\besptool(?:\.py)?\b',item['command'],re.I)
errors=[{'raw_line':n,**i} for n,i in items if i.get('type')=='error']
assert len(errors)==1 and 'Under-development features enabled' in errors[0]['message']
save(OUT/'native-tool-review.json',{'run_id':RUN.name,'reviewed_at':datetime.now(timezone.utc).isoformat(),
    'raw_stdout_sha256':digest((RUN/'stdout.jsonl').read_bytes()),'raw_events':260,'commands':commands,'file_changes':changes,
    'diagnostic_items':errors,'command_count':81,'file_change_count':43,'failed_commands':5,
    'review':'Operator reviewed all 81 captured command lines and 43 own-checkout file changes. Reads were fixed own inputs and declared ESP-IDF/Waveshare sources; local builds/tests/hash/schema/Git status only. Five failures were missing rg, CMake path escape, firmware format specifier, pipeline schema assertion and C identifier redefinition. No permission denial observed. The unstable-feature diagnostic is not a denial. No serial/flash, network, prior candidate source/history or permission/profile modification observed.',
    'operator_audited_user_interventions':0,'raw_measurement_user_interventions':m['measurement']['user_interventions'],
    'read_isolation':'not_enforced','scope':'Captured commands/paths and source review only; no OS read-isolation guarantee.'})
decision={'status':'eligible','reviewer':'Codex operator','user_interventions':0,
    'reason':'All captured actions were own checkout, provided inputs or declared SDK/manufacturer sources. Native failures were ordinary command/build/test failures, with no permission denial or forbidden access observed. Preserve completed execution separately from pending device/product/reference evaluation.',
    'intervention_review':'No operator source repair, permission changes, implementation feedback, serial or flash during the candidate run. Raw null intervention measurement retained; independently audited manual interventions zero.',
    'evidence':[{'path':p.relative_to(RUN).as_posix(),'sha256':digest(p.read_bytes())} for p in (OUT/'native-tool-review.json',OUT/'terminal-verification.json')]}
save(RUN/'operator-policy-decision.json',decision);create_review(RUN/'run-manifest.json',decision)
# Operator metadata only. Original terminal manifest and ledger remain separate.
m['outputs']['implementation_commit']=f['commit'];m['outputs']['build_status']='pass'
names=['operator-source-freeze.json','operator-terminal-source.bundle','operator-policy-decision.json',
       'experiment-launch.json','native-start-observation.json','native-start-observation-prefix.jsonl','process-at-start.json',
       'operator-next-model-decision.json','previous-progress-at-transition.json']
names += [p.relative_to(RUN).as_posix() for p in OUT.rglob('*') if p.is_file()]
names += [p.relative_to(RUN).as_posix() for p in (RUN/'operator-launch-preflight').rglob('*') if p.is_file()]
for name in names:m['operator']['evidence'][name]=digest((RUN/name).read_bytes())
save(RUN/'run-manifest.json',m);validate_review(m,RUN/'run-manifest.json')
created=create_package(RUN,PACK);save(PACK.parent/'codex-sol-r01-pre-observation-create.json',created)
restored=restore_package(PACK,REST,created['package_manifest_sha256'])
save(REST/'operator-preservation-audit.json',dict(restored,original_terminal_manifest_preserved=True,
    firmware_app_sha256=f['artifacts']['build/codex_desk_meter.bin']['sha256'],hardware_status='not_run',reference_review_applied=False,
    scope='Independent standard restoration before device observation; submission validity is not product pass. Original costs/source retained.'))
print(json.dumps({'package':created,'restore':restored,'original_terminal_preserved':True,'reference_review_applied':False}))
