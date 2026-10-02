# main 파일 트리·문서 정리 결과

적용일: 2026-10-02. 대상: 로컬 `main` 작업 파일, 기준 HEAD `eb69163`.
사용자는 과거 계획을 archive로 이동하고 검증 로그 3개를 선별 등록하는 방식을 선택했다.
원본 [평가](../main-tree-review-20261002/report.md)의 판정과 snapshot은 보존한다.

## 반영한 정리

| 항목 | 반영 내용 |
|---|---|
| T01 결과 안내 중복 | `results/README.md`를 결과 인덱스로 정리. 과거 관측·도구 검증을 구분하고 집계·게시 규칙의 상세는 운영 관리로 연결 |
| T02 오래된 상태 안내 | 단회 프로토콜과 pilot gate의 새 비교 안내를 날짜가 있는 정정으로 갱신. 현재 상태의 원본은 새 비교 준비 상태로 통일 |
| T03 로그 보존 | 보고서가 참조하는 세 로그만 ignore 예외·binary attribute 적용. 다른 로그의 무시 정책 유지 |
| T04 과거 계획 위치 | 최초 Git 등록일인 2026-09-13을 이름에 넣어 `docs/archive/plans/`에 이동. 원문과 역사적 적용 범위 보존 |

## 계획 이동과 참조

| 원래 경로 | 보관 경로 |
|---|---|
| `docs/experiments/e2e-contract-implementation-plan.md` | [2026-09-13 E2E 계약 계획](../../docs/archive/plans/2026-09-13-e2e-contract-implementation-plan.md) |
| `docs/experiments/host-device-pipeline-implementation-plan.md` | [2026-09-13 host pipeline 계획](../../docs/archive/plans/2026-09-13-host-device-pipeline-implementation-plan.md) |

두 계획은 Git `d2f2e22`에서 처음 등록됐다. 이동 후 날짜가 있는 보관 안내를 추가했다.
[문서 지도](../../docs/DOCUMENTATION_MAP.md)와 직전 평가의 현재 링크를 갱신했다.
[당시 readiness 검토](../../docs/archive/experiments/readiness-review-20260913.md)의 원문 파일 목록은
역사적 증거이므로 원래 경로를 유지하고 상단에 이동 안내를 추가했다.
직전 평가의 `evidence.json`에 있는 원래 경로도 정리 전 snapshot으로 보존했다.

## 선별 로그

| 파일 | 원래 encoding | byte 수 | SHA-256 |
|---|---|---:|---|
| [최종 구현 시험](../comparison-tooling-20261002/unittest-final.log) | UTF-8 | 60,994 | `226055d6ff7a05fbe6244a87f1d1f753eab164a9daaf15c2088d5adabe310ba2` |
| [문서 수정 시험](../main-purpose-review-20261002/document-fixes-unittest.log) | UTF-8 | 22,389 | `a459db0ea9ce43904890172c0f1c2ea0a1a2b4b5e2e11f7868dce5c5a3298a7d` |
| [첫 목적 평가 시험](../main-purpose-review-20261002/unittest.log) | UTF-16 | 45,892 | `094a70e24e1ad7c72dc25c13b0b3b75dd872fb48f4dbe34733fd5773d0c8b86f` |

검토 범위는 세 로그의 decoded 내용과 credential 후보 검색이다. 비밀키·인증정보 후보는 0건이었다.
원본 시험 출력·Git 경고·임시 시험 경로·PowerShell 출력 포맷을 재작성하지 않았다.
로그의 과거 시험 결과를 이번 문서 정리에서 새로 실행한 시험으로 집계하지 않는다.

## 검증 상태

`python -X utf8 results/main-tree-cleanup-20261002/verify_cleanup.py` 실행: exit 0.

- Markdown 103개에서 로컬 파일 링크 737개 확인: 끊긴 링크 0건, Git 무시 파일을 가리키는 링크 0건.
- 코드·schema·fixture·reference·원본 관측·이전 평가 데이터·archive 등 보존 대상 363개 일치.
  readiness 검토는 추가한 이동 안내를 제외한 원문 byte로 확인했다.
- 이동한 계획 2개는 보관 안내를 제거하면 정리 전 원문 SHA-256과 일치한다. 원래 파일 경로에는 남기지 않았다.
- 로그 3개의 worktree byte와 Git index blob SHA-256이 위 원본 값과 일치한다.
  세 파일의 text/diff/merge 속성은 unset이며 다른 일반 로그는 계속 무시된다.
- `git diff --check`와 `git diff --cached --check` 통과.
  비무시 Markdown·Python·JSON 파일의 trailing whitespace도 0건.
- HEAD `eb69163ed33ebf1afff4ba3d85d97677dc88b395` 유지. Git index에는 선택한 로그 3개만 추가했다.

링크 검증은 로컬 파일 존재를 확인했으며 외부 URL·heading anchor는 대상이 아니다.
코드 실행·schema·보드 동작이 바뀌지 않아 이번에는 문서·파일 보존 검증을 수행했다.
이번 정리로 실제 후보·보드 검증이나 새 baseline 동결이 완료된 것은 아니다.
현재 잔여 실행 조건은 [새 비교 준비 상태](../../docs/experiments/next-comparison-readiness.md)를 따른다.

문서 이동·수정과 ignore/attributes 규칙은 작업 폴더에 반영된 상태이며 아직 커밋하지 않았다.
새 clone에 반영하려면 선별 로그와 함께 해당 변경을 완결된 단위로 커밋해야 한다.

## 후속 게시 정비 (2026-10-02, 커밋 요청 적용)

사용자의 후속 커밋 요청에 따라 구현·문서·보고서를 함께 등록한다.
위 링크 수·index 목록과 `evidence.json`은 정리 완료 당시 snapshot으로 보존한다.
기준 기능 목록의 로컬 절대 링크는 저장소 상대 경로로 연결했다.
과거 영상 검토의 원본 사본 링크는 [artifact 목록](../codex-reference-upload-20261001/artifact-inventory.json)으로
연결했다. 영상·이미지·flash log·binary와 lock 등 31개 로컬 파일은 원래 경로에 보존하며,
이 목록에는 위치·byte 수·SHA-256을 기록했다. 독립 복원 package나 외부 배포 완료를 뜻하지 않는다.
기존 영상의 관측·판정과 동결 source/evidence는 변경하지 않았다.

[정비 계획](../../docs/plans/2026-10-02-main-tree-cleanup.md),
[정리 전 보존 기준](preservation-baseline.json), [검증 스크립트](verify_cleanup.py),
[후속 검증 데이터](evidence.json)를 함께 관리한다.
