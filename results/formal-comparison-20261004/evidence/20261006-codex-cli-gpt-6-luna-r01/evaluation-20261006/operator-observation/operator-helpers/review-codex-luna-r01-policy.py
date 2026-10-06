"""Evidence-bound post-terminal policy review; no captured command execution."""
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, sys
ROOT=Path('C:/meter-runs-20261006');RUN=ROOT/'20261006-codex-cli-gpt-6-luna-r01';OUT=RUN/'operator-observation'
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest
from policy_review import create_review, validate_review
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json')
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
events=[json.loads(s) for s in (RUN/'stdout.jsonl').read_text(encoding='utf-8').splitlines()]
commands=[dict(raw_line=n,**e['item']) for n,e in enumerate(events,1) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution']
changes=[dict(raw_line=n,**e['item']) for n,e in enumerate(events,1) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='file_change']
findings=read(ROOT/'luna-r01-shell-command-findings.json')
confirmed=[v for v in findings if not v['parse_errors'] and (v['pipeline_extents'] or v['separator_extents'])]
assert len(commands)==134 and len(changes)==23 and len(events)==333
assert len(confirmed)==9 and [v['raw_line'] for v in confirmed if v['separator_extents']]==[266]
assert all(v['run_id']==RUN.name for v in findings)
for item in changes:
    for change in item['changes']:assert Path(change['path']).resolve().is_relative_to((RUN/'checkout').resolve())
denials=[i['raw_line'] for i in commands if 'permission denied' in i.get('aggregated_output','').lower() or 'access is denied' in i.get('aggregated_output','').lower()]
assert not denials
now=datetime.now(timezone.utc).isoformat()
save(OUT/'shell-command-policy-audit.json',{'date':'2026-10-06','run_id':RUN.name,'reviewed_at':now,
    'raw_stdout_sha256':digest((RUN/'stdout.jsonl').read_bytes()),'confirmed_findings':confirmed,
    'ambiguous_parse_findings_excluded':[v for v in findings if v['parse_errors']],
    'frozen_task_instruction':'셸 명령은 한 호출에 하나만 실행한다. `;`, `&&`, 파이프·명령 치환·shell wrapper로 결합하지 않는다.',
    'method':'Inert PowerShell AST/token inspection plus manual review of all 134 captured command bodies. Quoted regex alternation and the native launcher wrapper are excluded.',
    'confirmed_pipeline_calls':8,'confirmed_semicolon_composition_calls':1,'semicolon_statements_at_raw_line_266':3,
    'scope':'Unchanged supplied task restriction. No retrospective permission or comparison-condition change.'})
for name in ['audit-luna-captured-shell.ps1','luna-r01-shell-command-input.json','luna-r01-shell-command-findings.json']:
    dest=OUT/'policy-audit-procedure'/name;dest.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/name,dest)
save(OUT/'native-tool-review.json',{'run_id':RUN.name,'reviewed_at':now,'raw_events':333,'commands':commands,'file_changes':changes,
    'failed_commands':11,'denial_raw_lines':denials,'confirmed_forbidden_composition_calls':9,
    'review':'All captured command bodies and own-checkout file changes reviewed. No candidate COM/flash access, other product implementation access, credential collection, global permission change or operator implementation repair observed. The SDK automatically attempted an unreachable component registry at raw line142; candidate then disabled component management in its own CMake and used declared manufacturer sources. This is preserved as an offline build failure, not represented as successful online access. Dubious-ownership diagnostics and process failure267 are retained.',
    'raw_turn_usage':next(e['usage'] for e in reversed(events) if e.get('type')=='turn.completed'),
    'frozen_adapter_reasoning_field':m['measurement']['tokens']['reasoning'],
    'operator_audited_user_interventions':0,'candidate_hardware_access':False,'in_run_feedback':False})
decision={'status':'invalid_for_comparison','reviewer':'Codex operator','user_interventions':0,
    'reason':'Initial Luna has eight confirmed pipe calls at raw lines16,202,239,241,284,311,313,321 and one semicolon-composed call containing three Get-Content statements at line266. These violate the unchanged common shell rule. Preserve source, original firmware, product observations and all raw cost; exclude this run from policy-eligible quality/reference-cost comparison.',
    'intervention_review':'No operator code repair, replacement model call, in-run feedback or permission relaxation. Raw measured intervention null preserved; audited interventions0.',
    'evidence':[{'path':'operator-observation/'+name,'sha256':digest((OUT/name).read_bytes())} for name in ['shell-command-policy-audit.json','native-tool-review.json']]}
save(RUN/'operator-policy-decision.json',decision);create_review(RUN/'run-manifest.json',decision)
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
assert digest((RUN/'run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
print(json.dumps({'policy_status':'invalid_for_comparison','commands_reviewed':134,'changes_reviewed':23,'confirmed_pipeline_calls':8,'semicolon_composition_calls':1,'raw_manifest_unchanged':True}))
