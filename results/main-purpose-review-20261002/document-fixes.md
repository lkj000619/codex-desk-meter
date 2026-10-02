# main 검토 후 문서 수정 기록

수정일: 2026-10-02. 대상: 로컬 `main`의 작업 파일, 기준 HEAD `eb69163`.
원본 [검토 보고서](review.md)와 당시 검증 데이터는 보존한다. 아래는 그 이후의 문서 수정이다.

| 발견 사항 | 문서 반영 | 남은 실제 작업 |
|---|---|---|
| R01/R02 운영 연결·reference 입력 | 과거 pilot과 새 비교를 구분하고 준비 상태의 원본을 통일 | 후속 manager·gate·실제 RM stimulus 복구/동결 |
| R03 전체 시도·실패 비용 | 관리 문서에 현재 completed 집계의 범위와 추가 지표를 명시 | 상태별 실패 비용·최초/후속 누적 집계 구현 |
| R04 source 시각 | 제품 계약의 source/수신 시각과 unknown 규칙, host 모델의 검사 한계를 명시 | production 의미 검사·실제 runtime anchor 검증 |
| R05 production·광학 관측 | 평가 계약 E1~E8에 실제 fixture 값·요구 ID와 단일 port·수락/화면·powered 단절 절차를 연결 | 공통 harness·자동화·후보/실물 실행 |
| R06 문서 갱신 누락·중복 | F9.details·3개 MD 입력·ADR 채택·YAML/prompt 반영 상태 정정. F9/archive 규칙은 원본 참조로 통합 | 새 실행에서 상태·입력 동결 확인 |
| R07 capability | 정책 파일 참조와 실제 표면별 권한 강제를 구분하고 확인 목록 정의 | 새 profile별 실효 권한·계측 검증 |
| R08 복구 | source/artifact/시험/telemetry package 목록·상대 경로/hash·새 root 복원 조건 정의 | package 제작·독립 복원 실행 |
| R09 깨진 링크 | AGY/Codex 비교 보고서의 archive 링크 정정 | 없음 |

`docs/superpowers/plans/`의 계획은 [docs/plans/](../../docs/plans/2026-10-02-experiment-contract-remediation.md)로 이동했다.
계획에 남은 도구 실행 강제 문구를 제거하고 완료된 문서 정의와 남은 구현을 구분했다.
[문서 지도](../../docs/DOCUMENTATION_MAP.md)는 디렉터리 역할을 설명하고,
[프로젝트 지침](../../AGENTS.md)은 이후 계획의 저장 위치를 지정한다.
폴더 이름 자체의 실행 오류는 발견하지 않았다. 도구별 기본 경로가 중복 생성되거나
이동 뒤 링크가 깨지는 문제는 저장 규칙과 참조 검증으로 관리한다.

이번 수정은 문서·prompt 설명에 한정한다. 실행 코드·schema·fixture·원본 evidence는 보존했다.
제품 계약과 최초 prompt가 후보 입력에 포함되므로 다음 실행은 새 입력 hash를 동결해야 한다.
과거 receipt·tag의 승인이나 결과를 새 입력의 것으로 재사용하지 않는다.

검증 결과:

- 기존 unittest 144개: 143개 통과, Windows symlink 생성 권한으로 1개 skip, exit 0.
- 정상 E2E 예제와 provider matrix: VALID. 부적절한 product_pass 예제: exit 1로 거부.
- 로컬 Markdown 파일 링크와 이동한 계획의 참조: 누락 없음. 외부 URL·heading anchor는 검사 범위 밖이다.
- 후보 inventory: 57개 파일·필수 MD 3개 유지. 수정된 제품 계약·prompt는 LF 정규화 입력 미리보기에서도 bundle hash를 변경한다. 아직 새 baseline을 동결한 것은 아니다.
- E1의 20/80·35/65·40/60·10/90과 E2의 경과 226,687초를 원본 fixture에서 대조했다.
- `git diff --check` 통과. scripts·schema·fixture·원본 evidence·archive에는 변경 없음.

[검증 스크립트](verify_document_fixes.py), [검증 데이터](document-fixes-evidence.json),
[시험 로그](document-fixes-unittest.log)를 보존했다.
실제 후보 실행·serial 접근·flash·실물 측정은 수행하지 않았다.
