# 현재 main 파일 트리·중복 평가

평가일: 2026-10-02. 대상은 로컬 `main` 작업 폴더다. commit은
`eb69163ed33ebf1afff4ba3d85d97677dc88b395`이며 구현·문서 정비는 아직 커밋 전이다.
이 평가의 산출물은 집계에서 제외했다. 기존 파일의 이동·삭제·수정은 하지 않았다.

> 후속 안내 (2026-10-02): 아래는 정리 전 평가다. 이후 사용자가 선택한 archive 이동·로그 선별 등록과
> T01~T04 수정은 [정리 결과](../main-tree-cleanup-20261002/report.md)에 기록했다.
> 이 문서에서는 이동한 계획의 현재 링크만 갱신했다. 아래 판정·수치와 `evidence.json`은 평가 당시를 보존한다.

**판정: 상위 구조와 후보 입력 분리는 적절하다. 불필요한 설명 중복 1건, 오래된 현재 상태 안내 2곳,
로그 게시 방식과 과거 계획 위치의 정리가 필요하다. 동일 파일 전체를 일괄 삭제할 근거는 없다.**

## 검사 범위와 결과

| 항목 | 결과·범위 |
|---|---|
| main의 committed HEAD | 378개 파일. 아직 이전 `docs/superpowers/plans/` 경로를 포함 |
| 현재 작업 폴더 | 추적·비무시 미추적 파일 446개, 미추적 69개, 기존 추적 경로 변경 26개 |
| 삭제 표시 | 이전 계획 경로 1개. 실제 계획은 `docs/plans/`에 있어 유실이 아닌 커밋 전 이동 상태 |
| 문서 링크 | MD 100개에서 로컬 링크 679개 검사, 현재 작업 폴더 기준 끊긴 링크 0개 |
| 파일 내용의 동일성 | SHA-256이 같은 파일 9개 묶음. 8 MiB 이하의 파일을 검사 |
| JSON 내용의 동일성 | key 순서·공백을 제외한 동일 JSON 3개 묶음. 위 9개 중 fixture 복사본에 해당하며 추가 3건이 아님 |
| 주요 문서의 완전 반복 | 안내·계약·설계 등 37개 MD에서 100자 이상 동일 본문 문단 0건. 긴 동일 행 8개 묶음은 명령·hash·기준 식별자 등의 반복 |
| 문서 내부의 완전 반복 | 현재 안내 문서에서 100자 이상 같은 문단 반복 0건. 한·영 의미 중복은 별도 수동 검토로 확인 |
| 코드 복제 | scripts의 최상위 함수 중 9행 이상 AST 본문이 완전히 같은 함수 0건. 짧은 wrapper나 의미상 유사 구현의 부재를 보증하는 수치는 아님 |
| 이름·병합 흔적 | Windows 대소문자 충돌 0건, 검사한 text 파일의 merge conflict marker 0건 |
| 형식 | `git diff --check` 통과 |

첫 검사와 재검사에서 파일 수·동일 파일 묶음·링크 결과가 일치했다.
실행 시험은 이번 파일 트리 검사의 범위가 아니다. 이전 구현 시험 176개 중 175 통과·1 skip은
[별도 구현 보고서](../comparison-tooling-20261002/report.md)의 결과로 구분한다.

## 파일 트리의 역할 평가

```text
main 작업 폴더
├─ AGENTS.md, README.md, .gitignore, .gitattributes
├─ docs/                 271개: 역할 지도·계약·운영·과거 기록
│  ├─ decisions/           6개: ADR
│  ├─ design/              1개: 비교 도구 설계
│  ├─ plans/               2개: 정비·구현 계획
│  ├─ experiments/       233개: 운영 문서와 원본 evidence
│  ├─ hardware/            4개: 보드 사실·제조사 source 목록
│  ├─ overview/            4개: 시점별 HTML 자료
│  └─ archive/            17개: 과거 검토·계획 기록
├─ experiments/           85개: config·schema·fixture·prompt·reference
├─ scripts/               41개: 운영 도구·validator·시험
└─ results/               45개: 비교·구현 검토와 로컬 원본 관측
```

`docs/experiments/`는 사람이 읽는 규칙·기록, root `experiments/`는 기계 입력이다.
같은 이름 때문에 두 디렉터리의 역할이 중복된 것은 아니다. CLI와 재사용 Python module,
historical validator와 E2E validator도 역할이 다르므로 파일 이름 유사성만으로 합치지 않는다.

`docs/superpowers/`는 현재 폴더에서 제거되고 `docs/plans/`·`docs/design/`으로 역할을 구분했다.
다만 이 이동과 새 도구는 아직 HEAD에 반영되지 않았다. 지금 폴더의 개선 상태와
새 clone에서 얻는 committed main 상태를 동일하게 해석하면 안 된다.

로컬 `.agents/`·`.claude/`·`artifacts/`·cache는 Git 무시 대상이며 main 추적 구조에 포함하지 않았다.
`runs/`는 현재 빈 디렉터리로 확인했다. 설치된 skill bundle의 파일 수를 프로젝트 중복으로 집계하지 않았다.

## 동일 파일 9개 묶음의 판정

| 종류 | 묶음 수 | 판정 |
|---|---:|---|
| 과거와 현재 검토의 같은 deterministic host frame | 1 | 시점별 시험 증거이므로 각각 보존 |
| 원본 stdout/stderr/report의 같은 내용 또는 빈 출력 | 3 | 서로 다른 명령의 원본 채널 기록. 빈 stderr도 해당 실행의 증거이며 보존 |
| 일반 fixture와 frozen reference fixture | 3 | 같은 byte지만 변경 수명이 다름. 기준 입력은 독립적으로 보존 |
| 기준 upload/retest/lcd-retest의 같은 sender harness | 1 | 각 실행의 source provenance. 원본 경로/hash를 보존 |
| 세 실행 디렉터리의 같은 sender lock 파일 | 1 | 런타임 부산물. 게시·패키지 대상인지 확인할 항목이며 중복만으로 삭제하지 않음 |

reference 아래의 `experiments/fixtures/`가 일반 fixture 경로와 같아 보이는 것은 원본 commit의
상대 경로를 보존하기 때문이다. 이를 일반 fixture에 대한 링크로 바꾸면 향후 fixture 변경이
기준 입력에도 영향을 줄 수 있어 현재의 독립 복사 방식이 목적에 맞는다.

정확한 경로와 SHA-256은 [검사 근거](evidence.json)의 `byte_duplicate_groups`에 기록했다.

## 정리 대상

### T01 — 결과 안내의 한·영 의미 중복과 집계 설명 누락

위치: [results/README.md](../README.md)의 11~16행과 29~40행.
동일한 valid completed grouping·중앙값/범위·중복 제외 설명이 한국어와 영어로 반복된다.
새로 구현한 전체 시도·실패 비용·최초/후속/기준 도달 비용 표 설명도 빠져 있어,
summary 전체가 여전히 completed만 집계한다고 읽힐 수 있다.

조치: 결과 인덱스에는 결과 종류·현재 보고서 링크·짧은 해석만 두고, 상세 명령과 집계 규칙은
[도구 안내](../../docs/experiments/comparison-tooling.md)와
[운영 관리](../../docs/experiments/benchmark-management.md)를 참조한다.
과거 raw run과 새 도구 검증 보고서를 서로 다른 결과 종류로 연결한다.

### T02 — 구현 전 상태가 남은 두 안내 문서

위치: [agent-experiment-protocol.md](../../docs/experiments/agent-experiment-protocol.md) 8행,
[benchmark-readiness.md](../../docs/experiments/benchmark-readiness.md) 18행.

첫 문서는 현재 적용 범위를 정리한 주석에서 “후속 feedback·runner의 누적 예산·reference 판정 연결은
미완료”라고 쓰고, 두 번째는 새 비교의 pilot_pass receipt 연결을 미완료로 적는다.
[현재 readiness](../../docs/experiments/next-comparison-readiness.md)의 5·6번 구현 완료와 충돌한다.
이는 이전 구현 반영에서 갱신이 빠진 부분이다.

조치: 과거 단회 규칙·원본 판정은 그대로 보존한다. 새 비교를 안내하는 문장에 날짜·적용 범위를
추가해 현재 readiness와 도구 안내로 연결한다. 현재 상태를 여러 문서가 각자 정의하지 않도록 한다.

### T03 — 보고서의 세 로그 링크는 Git 무시 대상

현재 파일은 존재하지만 `.gitignore`의 `*.log` 때문에 정상적인 파일 추가에서 제외된다.

- [구현 보고서](../comparison-tooling-20261002/report.md) → `unittest-final.log`
- [문서 정비 보고서](../main-purpose-review-20261002/document-fixes.md) → `document-fixes-unittest.log`
- [첫 main 평가](../main-purpose-review-20261002/review.md) → `unittest.log`

따라서 로컬 링크 0건이라는 결과가 새 clone의 증거 재현성을 보증하지 않는다.
현재는 관련 보고서 자체도 미추적이다.
조치: 게시할 검증 로그를 선별해서 등록하거나 독립 evidence package의 위치/hash로 링크한다.
모든 raw log에 대해 무시 규칙을 해제할 필요는 없다.
보드 원본에는 외부 절대 경로 링크도 있으므로 증거 package와 함께 관리한다.

### T04 — 과거 계획 두 개가 운영 문서 폴더에 남아 있음

위치: 정리 전 `docs/experiments/`에 있던
[E2E 계약 구현 계획](../../docs/archive/plans/2026-09-13-e2e-contract-implementation-plan.md),
[host pipeline 계획](../../docs/archive/plans/2026-09-13-host-device-pipeline-implementation-plan.md).

새 계획은 `docs/plans/`에 있지만 이 두 파일은 `docs/experiments/`에 있고,
생성 시점·완료 상태가 상단에서 선명하지 않다. 큰 본문 복제는 아니지만 현재의 계획 위치 규칙과
역할이 일관되지 않으며 이미 존재하는 schema/host 도구를 다시 만드는 계획으로 오독할 수 있다.

조치: 당시 계획과 완료 기록을 보존한 채 역사적 계획으로 명시한다.
정리할 때 dated `docs/plans/` 또는 archive로 옮기고 저장소 참조를 함께 갱신한다.
지침 적용 이전 문서가 존재한다는 사실 자체를 현재 구현 결함으로 판정하지는 않는다.

## 현재 main의 반영 상태

26개 추적 경로가 변경됐고, 69개 프로젝트 파일은 아직 미추적이다.
새 AGENTS, 이동한 계획, 비교 도구·시험, 복구 reference와 보고서가 포함된다.
원본 upload 자료와 함께 모두 자동 등록하지 말고, 운영 source·현재 문서·보존 자료의 게시 대상을
구분해 검토한 변경을 완결된 단위로 반영해야 한다.

이것은 이번 작업 중인 상태의 설명이며 그 자체를 중복 결함으로 세지 않는다.
파일 이동이나 동일 파일 삭제를 먼저 수행할 이유는 없고, 우선 T01/T02의 현재 안내를 정리하고
T03의 증거 보존 방식을 연결하는 것이 결과 이해와 재현성에 직접 도움이 된다.

기계 검사: [audit_tree.py](audit_tree.py), [evidence.json](evidence.json).
검사는 문서 원문을 읽고 hash·링크·AST를 비교했으며 모델 호출·보드 접근은 수행하지 않았다.
