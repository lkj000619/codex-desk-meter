# Gemini 4 Argon 별도 최초 테스트

목표: 사용자의 새 모델 테스트 요청에 따라 `gemini-4-argon-high`를 기존 공통 입력과 평가 기준으로 실행한다.
상태: 2026-10-16 18:04:36.026 KST 최초 실행 시작 확인 완료. PID 8696·native session `7d7658d2-7be8-4d99-a92d-00ff7a7c2898`, timeout 7,200초. 결과·정책·실물/RM 평가는 실행 종료 후 필요하다.

원본: [문서 지도](../DOCUMENTATION_MAP.md), [운영 계약](../experiments/comparison-operating-contract.md), [도구 안내](../experiments/comparison-tooling.md), [현재 상태](../experiments/next-comparison-readiness.md).

- [x] 기존 운영 기록 `b933eacc91589c3350556399cc250cd3e2651e6e`에서 branch `lkj000619/test-gemini-4-argon-20261016`을 분리한다.
- [x] 로컬 모델 목록에서 `gemini-4-argon-high`를 확인한다. 기존 Pro의 high 조건을 따른다. 설치 CLI 1.3.2와 동결 CLI 1.2.14 모두 모델 ID를 제공한다.
- [x] 동결 AGY CLI 1.2.14·ESP-IDF 5.3.2·기존 scoped wrapper에서 새 모델의 infrastructure capability와 계측·설정을 실제 검증한다. [원본/검토](../../results/gemini-4-argon-20261016/capabilities.json), probe 221.656초·46,989 정규화 token이다. 후보 제품 시간/비용과 구분한다.
- [x] 기존 baseline `272875140d1998d458e26fdb2f6deab5e5d8f7b5`의 도구로 57개 입력·새 ID·독립 ledger·새 receipt를 준비한다. [예약](../../results/gemini-4-argon-20261016/preparation.json) · [receipt](../../results/gemini-4-argon-20261016/receipt.json).
- [x] 실제 실행할 동결 baseline 회귀는 220개 중 219개 통과·1개 symlink skip·실패 0개다. 현재 운영 branch의 과거 evidence 압축 해제에서 발생한 경로 길이 오류 2건과 불완전한 PowerShell 계측 시도는 별도 원본/메모에 보존한다.
- [x] 최초 1회(상한 7,200초)를 시작하고 native model·permission mode·cwd·실제 시작을 보존한다. [실제 시작](../../results/gemini-4-argon-20261016/launch/native-start-observation.json).
- [x] 현재 준비 상태·결과 기록·재개 경로를 갱신한다. 최종 hash·링크·Git 변경 범위를 검증한다.

완료 조건: 별도 최초 테스트의 실제 시작 또는 구체적인 실행 차단 사유를 원본 evidence와 함께 기록한다. 실행 종료 시 source/artifact·원시 비용·실패를 동결한 뒤 정책·host·실물/RM 평가가 필요하다. 시작은 합격이 아니다.

기존 5개 모델의 17회 실행·5/15 series·판정·비용·동결 commit/tag는 유지한다. Argon은 이 표에 소급 삽입하지 않는 별도 series다. 후보는 기존 제품 구현·운영 문서·과거 결과를 받지 않으며 serial/flash를 사용하지 않는다. 최초 실행 중 구현 피드백은 없고, 후속은 자신의 동결 결과와 평가 후에만 준비한다. 예산은 최초 7,200초, 후속 최대 3회/누적 7,200초다.

2026-10-16 18:51:48 KST 후속 상태: 사용자 연결 후 COM3·기존 USB/MAC 보드를 재확인했다. 후보는 아직 실행 중이며 제출물 동결 전 serial open/reset/flash·후보 피드백을 수행하지 않았다. [연결 증거](../../results/gemini-4-argon-20261016/hardware-reconnected-20261016.json)에 따라 종료 후 원본 펌웨어 실물 평가를 준비한다. 시작 당시 보드 미연결 snapshot은 그대로 보존한다.
