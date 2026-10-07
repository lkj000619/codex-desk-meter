# 실험 구현 브랜치 원격 보존

확인일: 2026-10-08. 첫 블록의 실제 최초5회·후속12회, 총17개 원본 구현과 기존 파일럿·준비·reference ref4개를 push하고 원격 SHA21개가 원본과 일치함을 확인했다.

정식 회차 브랜치는 `experiment/formal-comparison-20261004/<run-id>`다. 아래 각 branch는 평가에 사용한 동결 commit을 그대로 가리킨다. 실행별 별도 checkout/bundle에 있던 source를 전용 bare 저장소에서 게시했으며 원본 구현·Git 이력·ledger·bundle·판정을 변경하지 않았다. 미실행 준비 run은17회에 포함하지 않는다.

브랜치 이름의 `rNN`은 해당 날짜의 run 번호이고, 실제 최초/후속 구분은 표의 회차를 따른다. timeout·환경 실패도 소비 비용과 부분 구현 원본을 보존한다. 게시 여부를 제품 합격·비교 적격성으로 해석하지 않는다. source branch의 제출 결과와 운영자 최종 실물 판정은 구분하며, 최종 평가는 [실행 기록](report.md)과 그 evidence를 따른다.

## 정식 첫 블록의 17회

| 모델 | 회차 | Run ID | 실행 상태 | 동결 commit | 원격 branch |
|---|---|---|---|---|---|
| OpenCode Muse | 최초 | `20261004-opencode-cli-opencode-muse-r01` | completed | [`e14689fea0`](https://github.com/lkj000619/codex-desk-meter/commit/e14689fea0cee5c0bd1e3812f7bd5dfbd122d5db) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261004-opencode-cli-opencode-muse-r01) |
| OpenCode Muse | 후속 1 | `20261004-opencode-cli-opencode-muse-r02` | timeout | [`354c647534`](https://github.com/lkj000619/codex-desk-meter/commit/354c6475345cb521c92f92e3dce448b0dc5ef58b) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261004-opencode-cli-opencode-muse-r02) |
| AGY Flash | 최초 | `20261005-antigravity-cli-agy-flash-r01` | environment_failed | [`29e1d7af54`](https://github.com/lkj000619/codex-desk-meter/commit/29e1d7af54a8c9c879e36192ec4ed689e5bbf82d) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261005-antigravity-cli-agy-flash-r01) |
| AGY Flash | 후속 1 | `20261005-antigravity-cli-agy-flash-r02` | completed | [`94018f1785`](https://github.com/lkj000619/codex-desk-meter/commit/94018f1785a590e1514ef1b5145c40f0c03ffca3) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261005-antigravity-cli-agy-flash-r02) |
| AGY Flash | 후속 2 | `20261007-antigravity-cli-agy-flash-r01` | environment_failed | [`b57439702d`](https://github.com/lkj000619/codex-desk-meter/commit/b57439702d2d3776b67b2e1baab106807aa33621) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261007-antigravity-cli-agy-flash-r01) |
| AGY Flash | 후속 3 | `20261007-antigravity-cli-agy-flash-r02` | completed | [`9e5a01b51c`](https://github.com/lkj000619/codex-desk-meter/commit/9e5a01b51cce581acda2495df402e6aa3d3f63be) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261007-antigravity-cli-agy-flash-r02) |
| AGY Pro | 최초 | `20261005-antigravity-cli-agy-pro-r01` | environment_failed | [`ba5609db6f`](https://github.com/lkj000619/codex-desk-meter/commit/ba5609db6fbf6392166586e50341c6e14a26112f) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261005-antigravity-cli-agy-pro-r01) |
| AGY Pro | 후속 1 | `20261005-antigravity-cli-agy-pro-r02` | environment_failed | [`5e1b658783`](https://github.com/lkj000619/codex-desk-meter/commit/5e1b658783da67995f4330ed1fafa98b842270cc) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261005-antigravity-cli-agy-pro-r02) |
| AGY Pro | 후속 2 | `20261005-antigravity-cli-agy-pro-r03` | environment_failed | [`8059dbf481`](https://github.com/lkj000619/codex-desk-meter/commit/8059dbf481d7a394a985d8757b0b331fc625b40a) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261005-antigravity-cli-agy-pro-r03) |
| AGY Pro | 후속 3 | `20261005-antigravity-cli-agy-pro-r04` | environment_failed | [`ef6aa727fa`](https://github.com/lkj000619/codex-desk-meter/commit/ef6aa727fa3539454708f223d965a1cb40197a56) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261005-antigravity-cli-agy-pro-r04) |
| Codex Sol | 최초 | `20261005-codex-cli-gpt-6-sol-r01` | completed | [`2257fffaa5`](https://github.com/lkj000619/codex-desk-meter/commit/2257fffaa5316773d08fe3353356112c7002159d) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261005-codex-cli-gpt-6-sol-r01) |
| Codex Sol | 후속 1 | `20261006-codex-cli-gpt-6-sol-r01` | completed | [`3a09f26f2f`](https://github.com/lkj000619/codex-desk-meter/commit/3a09f26f2f375f4f45bebb79eb5902667a3ccb1a) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261006-codex-cli-gpt-6-sol-r01) |
| Codex Sol | 후속 2 | `20261006-codex-cli-gpt-6-sol-r02` | completed | [`09ecdaf164`](https://github.com/lkj000619/codex-desk-meter/commit/09ecdaf1645511033b4efda40bb2a9e3b96ae8f7) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261006-codex-cli-gpt-6-sol-r02) |
| Codex Luna | 최초 | `20261006-codex-cli-gpt-6-luna-r01` | completed | [`c0d5d61160`](https://github.com/lkj000619/codex-desk-meter/commit/c0d5d61160664923e0494302fae180089d02d247) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261006-codex-cli-gpt-6-luna-r01) |
| Codex Luna | 후속 1 | `20261006-codex-cli-gpt-6-luna-r02` | completed | [`e683568297`](https://github.com/lkj000619/codex-desk-meter/commit/e68356829715793dc31dd188bc2a9f528f6fcbd2) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261006-codex-cli-gpt-6-luna-r02) |
| Codex Luna | 후속 2 | `20261006-codex-cli-gpt-6-luna-r03` | environment_failed | [`91f7de6032`](https://github.com/lkj000619/codex-desk-meter/commit/91f7de60328b7db9a9d04acef60ac45eafb3685a) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261006-codex-cli-gpt-6-luna-r03) |
| Codex Luna | 후속 3 | `20261007-codex-cli-gpt-6-luna-r01` | completed | [`88b2bbc610`](https://github.com/lkj000619/codex-desk-meter/commit/88b2bbc61047242afb22f272c419b3a57d30bb49) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/formal-comparison-20261004/20261007-codex-cli-gpt-6-luna-r01) |

## 기존 파일럿·준비·reference 4개

현재 로컬 이름과 commit을 유지했다. 이4개 ref는 정식17회 또는 새로운 독립 실험으로 집계하지 않는다.

| 기존 branch | 동결 commit | 원격 |
|---|---|---|
| `experiment/20260911T030200Z-codex-pilot` | [`abed99c4bd`](https://github.com/lkj000619/codex-desk-meter/commit/abed99c4bdded2366a719fdc7f7e8a49e60570ac) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/20260911T030200Z-codex-pilot) |
| `experiment/antigravity/cli/gemini-3-8-flash-high` | [`499e39b1f9`](https://github.com/lkj000619/codex-desk-meter/commit/499e39b1f93b4c862dc3a5fe93c12bca63e287e2) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/antigravity/cli/gemini-3-8-flash-high) |
| `experiment/opencode/cli/muse-spark-1-3-contributor-free` | [`c1be786781`](https://github.com/lkj000619/codex-desk-meter/commit/c1be78678148834844b990f3a2f57c568d40987d) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/experiment/opencode/cli/muse-spark-1-3-contributor-free) |
| `lkj000619/codex-reference-20260929` | [`7923f960fc`](https://github.com/lkj000619/codex-desk-meter/commit/7923f960fc9cc96fd576ab71f36f3d6500cc8190) | [소스](https://github.com/lkj000619/codex-desk-meter/tree/lkj000619/codex-reference-20260929) |

## 검증 기록과 범위

- [기계 목록·원격 SHA·bundle SHA-256](branch-publication-20261008.json): 원본5개 ledger,17개 bundle,21개 branch 조회 결과.
- [push 원본 로그](source-branch-publication-20261008/source-branches-push-stderr-20261008.txt): 21개 ref의 atomic push 결과.
- [원격 게시 검증 절차](source-branch-publication-20261008/push-source-branches-20261008.py): branch SHA·원본ledger/bundle·기존원격ref 보존 확인.
- [작업 계획](../../docs/plans/2026-10-08-publish-experiment-branches.md).

후보 실행·펌웨어 재빌드·보드 업로드는 추가하지 않았다. 첫 블록5/15 종료,전체17회·비용coverage16/17·알려진62,535,521 token·전체 합계미상과 과거부적격/미검증 범위는 유지한다. 실험 source branch를 main에 병합하지 않았다. 이후 독립 반복은 기존 동결baseline에서 새 checkout으로 시작한다.
