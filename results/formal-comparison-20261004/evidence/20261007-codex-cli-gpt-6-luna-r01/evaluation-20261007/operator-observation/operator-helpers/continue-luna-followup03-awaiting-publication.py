from datetime import datetime,timezone
from pathlib import Path
import ast,json,shutil,sys
ROOT=Path.cwd();FORMAL=ROOT/'results/formal-comparison-20261004';RUN=Path('C:/meter-followups-20261007/20261007-codex-cli-gpt-6-luna-r01')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save,digest
p=read(FORMAL/'progress.json');assert p['state']=='codex_luna_followup_03_uploaded_awaiting_optical_observation'
remaining=p['remaining_current_series_followup_seconds'];assert p['round']==3 and p['remaining_current_series_followup_rounds']==0
public=FORMAL/'evidence'/RUN.name/'observation-awaiting-20261007'
link=public.relative_to(ROOT).as_posix()
original=RUN.parent/'publish-luna-followup03-optical-awaiting.py';source=original.read_text(encoding='utf-8')
summary=next(ast.literal_eval(node.value) for node in ast.parse(source).body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='summary' for target in node.targets))
protected_keys=['previous_series','closed_agy_pro_series','deferred_agy_flash_series','closed_codex_sol_series','codex_sol_result_at_transition','current_series_first_result','current_series_previous_result'];protected={key:p[key] for key in protected_keys}
assert '## 2026-10-07 Luna 마지막 후속3 종료·원본 업로드' in (FORMAL/'report.md').read_text(encoding='utf-8')
assert '## 2026-10-07 마지막 후속3 검증·관측 대기' in (ROOT/'docs/plans/2026-10-06-codex-luna-remaining-followups.md').read_text(encoding='utf-8')
tail=source[source.index('docmap = ROOT'):]
tail=tail.replace("lines[3].startswith('후보 실행 시작')", "lines[3].startswith('독립 series 종료')")
tail=tail.replace('/operator-observation/native-terminal-failure-review.json','/operator-observation/terminal-verification.json')
exec(compile(tail,str(Path(__file__))+':continuation','exec'))
correction={'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'scope':'Operator observation-checkpoint publication metadata only. Candidate source/artifact, execution, cost and policy unchanged.',
    'original_publisher_sha256':digest(original.read_bytes()),'original_inventory':public.relative_to(ROOT).as_posix()+'/snapshot-inventory.json',
    'original_inventory_sha256':digest((public/'snapshot-inventory.json').read_bytes()),
    'original_inventory_round':read(public/'snapshot-inventory.json')['round'],'corrected_ledger_round':3,
    'publication_error':'Adapted report header assertion expected an older candidate-count paragraph; current paragraph correctly states independent series completion.',
    'first_continuation_error':'Missing local link variable stopped document-map tail after report and plan were written. Continue only the remaining document-map tail; no duplicate historical append.',
    'first_continuation_sha256':digest((RUN.parent/'continue-luna-followup03-awaiting-publication-v1.py').read_bytes()),
    'correction':'Continue only the unfinished report/plan/document-map tail with the current header; preserve original checkpoint bytes and interpret its stale round2 metadata as ledger round3.',
    'native_completion_or_upload_repeated':False,'original_procedure_and_inventory_preserved':True}
assert correction['original_inventory_round']==2
out=RUN/'operator-observation';save(out/'operator-publication-correction.json',correction)
shutil.copy2(Path(__file__),out/'operator-helpers'/Path(__file__).name)
shutil.copy2(RUN.parent/'continue-luna-followup03-awaiting-publication-v1.py',out/'operator-helpers/continue-luna-followup03-awaiting-publication-v1.py')
dated=FORMAL/'evidence'/RUN.name/'publication-correction-20261007';dated.mkdir(exist_ok=False)
shutil.copy2(out/'operator-publication-correction.json',dated/'correction-note.json');shutil.copy2(Path(__file__),dated/Path(__file__).name)
shutil.copy2(RUN.parent/'continue-luna-followup03-awaiting-publication-v1.py',dated/'continue-luna-followup03-awaiting-publication-v1.py')
save(dated/'snapshot-inventory.json',{'run_id':RUN.name,'round':3,'files':{path.name:{'bytes':path.stat().st_size,'sha256':digest(path.read_bytes())} for path in dated.iterdir() if path.is_file()}})
p['observation_snapshot_metadata_correction']=dated.relative_to(ROOT).as_posix()+'/correction-note.json';save(FORMAL/'progress.json',p)
for path,link in [(ROOT/'docs/experiments/next-comparison-readiness.md','../../'+p['observation_snapshot_metadata_correction']),(FORMAL/'report.md','evidence/'+RUN.name+'/publication-correction-20261007/correction-note.json')]:
    with path.open('a',encoding='utf-8') as stream:stream.write('\n2026-10-07 [관측 대기 snapshot의 회차 메타데이터 정정]('+link+'): 원본 inventory의 템플릿 잔존 round2는 실제 ledger round3으로 읽는다. 원본 bytes와 실패한 문서 검사 절차를 보존하고 미완료 문서 반영만 이어서 마쳤다. 후보 호출·펌웨어·계측·판정 변화는 없다.\n')
print(json.dumps({'publication_completed':True,'original_checkpoint_preserved':True,'correct_ledger_round':3}))
