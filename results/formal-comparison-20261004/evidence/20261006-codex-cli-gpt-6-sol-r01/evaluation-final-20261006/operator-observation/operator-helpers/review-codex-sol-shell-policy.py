"""Dated correction for overlooked first-run shell composition; fresh followup review."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,sys
BASE=Path('C:/meter-operator-20261004');FIRST=Path('C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01')
RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r01')
CORRECTION=Path('C:/meter-policy-corrections-20261006/codex-sol-initial')
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import read,save,digest
from policy_review import create_review,validate_review
findings=read(RUN.parent/'shell-command-pipeline-findings.json');now=datetime.now(timezone.utc).isoformat()
confirmed=[v for v in findings if not v['parse_errors']]
assert len([v for v in confirmed if v['run_id']==FIRST.name])==7
assert len([v for v in confirmed if v['run_id']==RUN.name])==4
CORRECTION.mkdir(parents=True,exist_ok=False)
for name in ('stdout.jsonl','stderr.txt','profile.json','prompt.txt','run-manifest.json','common-task.txt'):
    shutil.copy2(FIRST/name,CORRECTION/name)
shutil.copy2(FIRST/'policy-review.json',CORRECTION/'original-policy-review.json')
original=read(FIRST/'policy-review.json');assert original['decision']['status']=='eligible'
for target,identity in ((CORRECTION,FIRST.name),(RUN/'operator-observation',RUN.name)):
    save(target/'shell-command-policy-audit.json',{'date':'2026-10-06','run_id':identity,'reviewed_at':now,
        'raw_stdout_sha256':digest((FIRST/'stdout.jsonl' if identity==FIRST.name else RUN/'stdout.jsonl').read_bytes()),
        'confirmed_findings':[v for v in confirmed if v['run_id']==identity],
        'ambiguous_parse_findings_excluded':[v for v in findings if v['run_id']==identity and v['parse_errors']],
        'frozen_task_instruction':'셸 명령은 한 호출에 하나만 실행한다. `;`, `&&`, 파이프·명령 치환·shell wrapper로 결합하지 않는다.',
        'method':'PowerShell AST inspection of displayed command bodies plus manual review. Candidate commands were not executed by this audit. Regex alternation within quoted patterns is not treated as a pipeline. Ambiguous quoted command extraction is not used for the verdict.',
        'scope':'Explicitly supplied common shell composition restriction; no restriction added after the outcome. Read-only pipeline commands are still prohibited. No online/other-candidate/serial/flash access observed.',
        'reason_for_date_correction':'Initial scope review checked paths/denials/interventions but missed the shell composition prohibition. Original eligible review/package/commit/cost preserved; corrected effective quality status invalid_for_comparison.' if identity==FIRST.name else None})
decision=lambda target,reason:{'status':'invalid_for_comparison','reviewer':'Codex operator','user_interventions':0,
    'reason':reason,'intervention_review':'No operator product repair, permission change or in-run feedback. Raw measured interventions null preserved; audited interventions zero.',
    'evidence':[{'path':('shell-command-policy-audit.json' if target==CORRECTION else 'operator-observation/shell-command-policy-audit.json'),
                 'sha256':digest((target/'shell-command-policy-audit.json').read_bytes())}]}
create_review(CORRECTION/'run-manifest.json',decision(CORRECTION,'2026-10-06 dated reassessment: at least seven explicit read-only shell pipelines violate frozen common task one-command/no-pipeline rule. Original eligible verdict and first-result package retained. Exclude first run and series from identical-condition quality/reference-cost comparisons; preserve all execution/product/cost observations.'))
validate_review(read(CORRECTION/'run-manifest.json'),CORRECTION/'run-manifest.json')
save(CORRECTION/'correction-note.json',{'date':'2026-10-06','run_id':FIRST.name,'recorded_at':now,
    'original_policy_review_sha256':digest((FIRST/'policy-review.json').read_bytes()),'original_status':'eligible',
    'corrected_policy_review_sha256':digest((CORRECTION/'policy-review.json').read_bytes()),'effective_status':'invalid_for_comparison',
    'applies_to':'Identical-condition quality eligibility/reference-cost aggregation of this first run and its Sol series. Product RM verdict, original source/terminal/cost/package not changed.',
    'original_package_manifest_sha256':'93a87074e0f324da7c95e237244870d0a8deebc6be4f3e89b52fb95095acb60e',
    'first_original_evidence_overwritten':False,'reason':'Seven unambiguous shell pipelines; prior operator review omission corrected.'})

events=[json.loads(s) for s in (RUN/'stdout.jsonl').read_text(encoding='utf-8').splitlines()]
items=[(n,e['item']) for n,e in enumerate(events,1) if e.get('type')=='item.completed']
commands=[{'raw_line':n,**i} for n,i in items if i.get('type')=='command_execution'];changes=[{'raw_line':n,**i} for n,i in items if i.get('type')=='file_change']
assert len(events)==165 and len(commands)==62 and len(changes)==16
assert [i['raw_line'] for i in commands if 'Permission denied' in i.get('aggregated_output','')]==[163]
assert not any(n>163 and i.get('type') in {'command_execution','file_change'} for n,i in items)
for i in changes:
    for change in i['changes']:assert Path(change['path']).resolve().is_relative_to((RUN/'checkout').resolve())
save(RUN/'operator-observation/native-tool-review.json',{'run_id':RUN.name,'reviewed_at':now,'commands':commands,'file_changes':changes,
    'raw_events':165,'failed_commands':4,'denial_raw_line':163,'actions_after_denial':0,
    'review':'All 62 commands and16 file changes manually reviewed. Own inputs/feedback/source and declared SDK/manufacturer sources only. Four command failures: rg absent, old unit assertion, provider result identity, final Git index.lock permission denial. Candidate records denial and terminates; no new tool/file action afterwards. Four read-only shell pipelines separately violate fixed composition rule.',
    'raw_turn_usage':events[-1]['usage'],'frozen_adapter_reasoning_field':None,
    'usage_note':'Raw JSONL additionally emits reasoning_output_tokens2880; frozen adapter does not map it and keeps reasoning null. Preserve both without editing measured token total.',
    'operator_audited_user_interventions':0,'candidate_hardware_access':False,'in_run_feedback':False})
d=decision(RUN/'operator-observation','Followup has four explicit shell pipelines at raw lines26/137/147/155, prohibited by unchanged common task. Final Git denial is respected with no subsequent tool action; it does not cure the independent composition violations. Preserve completed/submitted product, full cost and later hardware outcome separately.')
save(RUN/'operator-policy-decision.json',d);create_review(RUN/'run-manifest.json',d)
assert validate_review(read(RUN/'run-manifest.json'),RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
print(json.dumps({'first_original_status':'eligible','first_effective_status':'invalid_for_comparison','followup_policy_status':'invalid_for_comparison','first_confirmed_pipeline_commands':7,'followup_confirmed_pipeline_commands':4,'after_denial_tool_actions':0,'originals_preserved':True}))
