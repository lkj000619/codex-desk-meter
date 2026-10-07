"""Document verified source branches without altering experiment results."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,shutil
ROOT=Path.cwd();FORMAL=ROOT/'results/formal-comparison-20261004';HELPERS=Path('C:/meter-followups-20261007')
source=HELPERS/'source-branches-publication-20261008.json';p=json.loads(source.read_text(encoding='utf-8'))
assert p['status']=='pushed_and_remote_verified' and len(p['verified_remote_heads'])==21
PUBLIC=FORMAL/'source-branch-publication-20261008';PUBLIC.mkdir(exist_ok=False)
for name in ['prepare-source-branches-20261008.py','push-source-branches-20261008.py','source-branches-push-stdout-20261008.txt','source-branches-push-stderr-20261008.txt',Path(__file__).name]:
    shutil.copy2(HELPERS/name,PUBLIC/name)
shutil.copy2(source,FORMAL/'branch-publication-20261008.json')
repo=p['repository'].removesuffix('.git');rows=[]
def label(row):
    cid=row['comparison_id']
    if 'opencode' in cid:return 'OpenCode Muse'
    if 'agy-flash' in cid:return 'AGY Flash'
    if 'agy-pro' in cid:return 'AGY Pro'
    if 'gpt-6-sol' in cid:return 'Codex Sol'
    if 'gpt-6-luna' in cid:return 'Codex Luna'
    raise ValueError(cid)
for row in p['formal_branches']:
    round_label='최초' if row['round']==0 else '후속 '+str(row['round'])
    rows.append('| '+label(row)+' | '+round_label+' | `'+row['run_id']+'` | '+row['execution_status']+' | [`'+row['commit'][:10]+'`]('+repo+'/commit/'+row['commit']+') | [소스]('+repo+'/tree/'+row['branch']+') |')
text='# 실험 구현 브랜치 원격 보존\n\n확인일: 2026-10-08. 첫 블록의 실제 최초5회·후속12회, 총17개 원본 구현과 기존 파일럿·준비·reference ref4개를 push하고 원격 SHA21개가 원본과 일치함을 확인했다.\n\n'
text+='정식 회차 브랜치는 `experiment/formal-comparison-20261004/<run-id>`다. 아래 각 branch는 평가에 사용한 동결 commit을 그대로 가리킨다. 실행별 별도 checkout/bundle에 있던 source를 전용 bare 저장소에서 게시했으며 원본 구현·Git 이력·ledger·bundle·판정을 변경하지 않았다. 미실행 준비 run은17회에 포함하지 않는다.\n\n'
text+='브랜치 이름의 `rNN`은 해당 날짜의 run 번호이고, 실제 최초/후속 구분은 표의 회차를 따른다. timeout·환경 실패도 소비 비용과 부분 구현 원본을 보존한다. 게시 여부를 제품 합격·비교 적격성으로 해석하지 않는다. source branch의 제출 결과와 운영자 최종 실물 판정은 구분하며, 최종 평가는 [실행 기록](report.md)과 그 evidence를 따른다.\n\n'
text+='## 정식 첫 블록의 17회\n\n| 모델 | 회차 | Run ID | 실행 상태 | 동결 commit | 원격 branch |\n|---|---|---|---|---|---|\n'+'\n'.join(rows)+'\n\n'
text+='## 기존 파일럿·준비·reference 4개\n\n현재 로컬 이름과 commit을 유지했다. 이4개 ref는 정식17회 또는 새로운 독립 실험으로 집계하지 않는다.\n\n| 기존 branch | 동결 commit | 원격 |\n|---|---|---|\n'
for row in p['existing_branches']:
    text+='| `'+row['branch']+'` | [`'+row['commit'][:10]+'`]('+repo+'/commit/'+row['commit']+') | [소스]('+repo+'/tree/'+row['branch']+') |\n'
text+='\n## 검증 기록과 범위\n\n- [기계 목록·원격 SHA·bundle SHA-256](branch-publication-20261008.json): 원본5개 ledger,17개 bundle,21개 branch 조회 결과.\n- [push 원본 로그](source-branch-publication-20261008/source-branches-push-stderr-20261008.txt): 21개 ref의 atomic push 결과.\n- [원격 게시 검증 절차](source-branch-publication-20261008/push-source-branches-20261008.py): branch SHA·원본ledger/bundle·기존원격ref 보존 확인.\n- [작업 계획](../../docs/plans/2026-10-08-publish-experiment-branches.md).\n\n후보 실행·펌웨어 재빌드·보드 업로드는 추가하지 않았다. 첫 블록5/15 종료,전체17회·비용coverage16/17·알려진62,535,521 token·전체 합계미상과 과거부적격/미검증 범위는 유지한다. 실험 source branch를 main에 병합하지 않았다. 이후 독립 반복은 기존 동결baseline에서 새 checkout으로 시작한다.\n'
(FORMAL/'branch-publication-20261008.md').write_text(text,encoding='utf-8')
now=datetime.now(timezone.utc).isoformat();progress_path=FORMAL/'progress.json';progress=json.loads(progress_path.read_text(encoding='utf-8'))
progress['checked_at']=now;progress['source_branch_publication']={'verified_at':p['verified_at'],'formal_source_branches':17,'existing_pilot_preparation_reference_branches':4,
    'remote_sha_verified':21,'status':'pushed_and_remote_verified','inventory':'results/formal-comparison-20261004/branch-publication-20261008.json',
    'index':'results/formal-comparison-20261004/branch-publication-20261008.md','original_frozen_commits_preserved':True,'new_product_experiments_started':False}
progress_path.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readiness=ROOT/'docs/experiments/next-comparison-readiness.md'
readiness.write_text(readiness.read_text(encoding='utf-8')+'\n## 2026-10-08 실험 source branch 원격 보존\n\n실제17회 동결 source와 기존 파일럿·준비·reference4개,총21개 branch를 원격에 게시하고SHA 일치를 확인했다. [회차별 브랜치 목록](../../results/formal-comparison-20261004/branch-publication-20261008.md)과 [기계 검증 기록](../../results/formal-comparison-20261004/branch-publication-20261008.json)을 따른다. 첫 블록5/15 종료와 기존비용·부적격·전체제품미합격 판정은 유지한다. 추가후보 실행이나보드업로드는 없다.\n',encoding='utf-8')
report=FORMAL/'report.md';report.write_text(report.read_text(encoding='utf-8')+'\n## 2026-10-08 원본 구현 브랜치 게시\n\n최초5회·후속12회의 원본동결commit을 회차별브랜치로 게시했다. 기존파일럿·준비·reference4개도 보존해21개 원격SHA를 검증했다. [모델·회차별 소스 링크](branch-publication-20261008.md) · [검증 원본](branch-publication-20261008.json). 기존실행·평가·비용은 변경하지 않았으며main에 실험source를 병합하지 않았다.\n',encoding='utf-8')
docmap=ROOT/'docs/DOCUMENTATION_MAP.md';s=docmap.read_text(encoding='utf-8');needle='| 정식 비교 실제 실행·재개 |';lines=s.splitlines(keepends=True);i=next(i for i,x in enumerate(lines) if x.startswith(needle))
lines.insert(i+1,'| 실험 구현17회·기존reference/파일럿4개 원격branch | [회차별 소스 목록](../results/formal-comparison-20261004/branch-publication-20261008.md) · [원격SHA 검증](../results/formal-comparison-20261004/branch-publication-20261008.json) · [게시 계획](plans/2026-10-08-publish-experiment-branches.md) |\n');docmap.write_text(''.join(lines),encoding='utf-8')
plan=ROOT/'docs/plans/2026-10-08-publish-experiment-branches.md';s=plan.read_text(encoding='utf-8');s=s.replace('원본 ledger·Git bundle·기존 branch 확인 완료, 게시 준비 중.','원본17회·기존4개 branch 원격게시·SHA21개 확인 완료. 검증 기록과 소스 목록 작성 완료, 운영 문서 branch 최종 동기화 진행.')
s=s.replace('- [ ] 실제17회','- [x] 실제17회').replace('- [ ] 실제 17회','- [x] 실제 17회').replace('- [ ] 회차별17개','- [x] 회차별17개').replace('- [ ] 회차별 17개','- [x] 회차별 17개').replace('- [ ] 원본 ledger','- [x] 원본 ledger')
s=s.replace('- [ ] 브랜치 목록·검증 기록 문서화 및 운영 문서 branch push.','- [x] 브랜치 목록·검증 기록 문서화 및 운영 문서 branch 게시 내용 검증. 최종 원격 동기화는 commit 후 SHA 조회로 확인한다.')
s+='\n[게시 결과·회차별 소스](../../results/formal-comparison-20261004/branch-publication-20261008.md) · [원격 검증 기록](../../results/formal-comparison-20261004/branch-publication-20261008.json).\n';plan.write_text(s,encoding='utf-8')
print(json.dumps({'formal_source_branches':17,'existing_source_branches':4,'remote_sha_verified':21,'document_written':str(FORMAL/'branch-publication-20261008.md')}))
