# 검증 결과 인덱스

확인일: 2026-10-04. 새 동일 조건 비교의 정식 집계 결과는 아직 게시하지 않았다. 활성 5개 시작 준비는 완료했고 제품 실험은 0회다.
아래에는 과거 관측 검토와 운영 도구의 검증 기록이 있다. 각 보고서의 날짜·대상·시험 범위를 확인한다.

## 과거 관측·비교 검토

- [AGY·Codex 진행 상태 비교](agy-codex-progress-comparison-20261001.md)
- [Codex 기준 검토 데이터](codex-reference-review-20261001.json)
- [OpenCode 첫 결과 검토](opencode-first-output-review-20261001.md)

이 기록의 실행 조건은 서로 다르다. 새 동일 조건 비교의 순위나 비용 집계로 해석하지 않는다.

## main·운영 도구 검증

| 기록 | 검증 범위 |
|---|---|
| [프로젝트 목적·문서 품질 재검토](documentation-assessment-20261002/review.md) | 현재 계약·후보 입력·평가 도구 대조, 링크·회귀 검증, 보완 권고 |
| [문서 품질 보완 결과](documentation-assessment-20261002/remediation.md) | 2026-10-03 DOC-01~04 반영, 수신 로그 연결·RM5 기준·단계별 완료 조건·검증 |
| [GPT-6 모델 설정 갱신](gpt6-profile-update-20261003/report.md) | Sol/Luna GPT-6 변경, 모델 목록·profile 검사, 본 실험 전 남은 조건 |
| [목적·목표 대비 문서 재검증](documentation-review-20261003/report.md) | 현재 문서·도구 대조, 평가 버전/baseline 연결 공백·gate 링크·F9 피드백 |
| [문서 재검증 피드백 보완](documentation-review-20261003/remediation.md) | R1~R3 및 전체 일정 반영, baseline 보존·독립 복원·회귀 검증과 남은 실행 준비 조건 |
| [실험 실행 경계·hook·제한 정책 검토](experiment-execution-review-20261003/report.md) | 후속 지침·native 권한·준수 판정/집계·CLI 문법 재현, 시작 조건과 hook 적용 범위 |
| [정식 비교 시작 선행 작업 실행](experiment-launch-preparation-20261004/report.md) | E1~E5 수정·활성 5개 실제 capability·baseline 동결·당일 receipt·독립 복원 완료 |
| [프로젝트 목적·실험 개선 검토](main-purpose-review-20261002/review.md) | 정비 전 발견 사항과 당시 시험 |
| [문서 수정 기록](main-purpose-review-20261002/document-fixes.md) | 문서·prompt 정비와 당시 남은 구현 |
| [비교 도구 구현·검증](comparison-tooling-20261002/report.md) | 예산·실패 비용·관측·독립 복원 도구 |
| [파일 트리·중복 평가](main-tree-review-20261002/report.md) | 정리 전 구조·중복·링크 검사 |
| [파일 트리 정리 결과](main-tree-cleanup-20261002/report.md) | 후속 문서 정리·계획 이동·로그 보존 |
| [본 실험 실행 준비](experiment-preparation-20261002/report.md) | 실제 CLI 6개 capability·설정·공통 입력·예약·독립 복원. 제품 실험은 미실행 |

## 새 결과의 작성·해석

집계 명령은 [비교 도구 안내](../docs/experiments/comparison-tooling.md),
비교 적격성·결과 보존·main 게시 기준은 [운영 관리](../docs/experiments/benchmark-management.md)를 따른다.
집계에는 유효 completed의 조건부 표와 별도 전체 시도·실패 비용·최초/후속/기준 도달 비용 표가 있다.
미측정 비용과 실물 미검증을 통과나 0으로 해석하지 않는다.

현재 준비 상태는 [다음 비교 준비 상태](../docs/experiments/next-comparison-readiness.md)에서 확인한다.
과거 보고서의 미완료 표현은 당시의 상태이며 후속 구현·정비 보고서와 함께 읽는다.
