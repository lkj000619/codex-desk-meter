# 세 에이전트 실험 결과에 따른 기준 문서 아키텍처 평가

평가일: 2026-10-02. 원래 검토 HEAD: `ab8cc581fca87dcca7a105aa977e3747b2001b04`.
상태: 평가 기록·수정 계획 작성 완료. 2026-10-02 사용자 결정은
[운영 계약](comparison-operating-contract.md)에 반영했다. 실행 입력 동기화·동결은 후속 작업이다.

**제품 계층 분리와 fixture 비교 방향은 타당하다. 다음 동등 조건 비교의 운영·평가
문서는 주요 수정이 필요하다.** 중요한 문제는 Critical 2건·Major 6건이며 부수 정리
항목은 Minor 2건이다. Critical은 새 실험의 해석을 막는 문제를 뜻한다.

후속 작업은 [수정 계획](../plans/2026-10-02-experiment-contract-remediation.md)을
따른다. 이 문서는 과거 실행의 점수를 바꾸거나 새 제품 실험을 시작하는 지시가 아니다.

## 평가 범위와 근거

Lab-Notes의 프로젝트 Overview, 10월 1일 AGY/Codex·OpenCode Session,
Problem·Decision과 연결된 원본 receipt, 현재 저장소의 제품·평가·통합·실험 계약,
schema와 validator를 대조했다. COM3 접근·flash·추가 후보 실행은 하지 않았다.
영상은 기존 검토 기록을 사용했으며 원본 전체를 이번에 재판독한 것은 아니다.

실험 입력 commit은 `aab0d493888f4fc0bb6eff726bfe7d93b167543c`다. 제품 계약,
평가 계약, E2E result schema, 공통 prompt, host-device 계약의 내용은 원래 검토
HEAD에서 이 입력본과 같았다(줄바꿈 정규화). 따라서 A02는 실험 후 새 문서에서만
생긴 불일치가 아니다. 이번 docs 브랜치에서는 설명 오류를 정정하되 frozen commit을
변경하지 않는다.

원본의 로컬 자료:

- [Lab-Notes 상세 평가](<C:/Users/이광진/Documents/Lab-Notes/20-Projects/Codex Desk Meter/Sessions/2026-10-02 세 에이전트 실험 근거의 기준 문서 아키텍처 평가.md>)
- [AGY·Codex 진행 비교](<C:/Users/이광진/orca/codex-desk-meter/results/agy-codex-progress-comparison-20261001.md>)
- [OpenCode 첫 결과와 r01~r06](<C:/Users/이광진/orca/codex-desk-meter/results/opencode-first-output-review-20261001.md>)
- [OpenCode r06 원본 board 판정](<C:/Espressif/benchmark-runs/20261001-opencode-remediation-r06/hardware-upload-01/board-verification.json>)
- [OpenCode 누적 계측](<C:/Espressif/benchmark-runs/20261001-opencode-remediation-r06/cumulative-measurement.json>)

위 절대 경로 자료는 로컬 evidence이며 새 clone에서 자동 복원되지 않는다. 이번
docs 변경은 기존 미추적 결과·대용량 artifact를 자동으로 Git에 포함하지 않는다.
복구 가능한 source/evidence package는 A10의 별도 작업이다.

## 세 결과가 입증하는 범위

| 대상 | 확인한 결과 | 해석 제한 |
|---|---|---|
| AGY | r21의 build·host 시험, fixture 송수신·LCD·BOOT·IMU·재전원 복구 일부. C2 pass, 여러 C/F/I partial/not_run, product_pass false | 정책·피드백이 바뀐 역사적 개발 이력. r01~r21은 21회 성공 수정 수가 아님 |
| Codex | `7923f96`의 fixture seq 0·1 수락, 값·세 화면 전환. Python 15개·CTest 4개 통과 기록 | 운영자 코드 `04dd1a0` 포함. 26.87초 영상 표본으로 30초 LCD 유지·전체 제품 합격을 확정하지 않음 |
| OpenCode | 독립 첫 결과는 LCD 초기화 실패. r06은 host 8/8·schema 및 upload 통과 후에도 소유자가 검은 화면 확인 | 후보 sender의 device acceptance 미확인, product_pass false. 첫 실행+수정 6회: 5,891.561초, 정규화 input+output 2,235,144; 운영·검증 비용 제외 |

동일 시작 commit만으로 지시·권한·수정 기회·작성 책임까지 같아지지 않는다.
AGY 개별 회차 provider total, Codex 세션 누적 total, OpenCode input+output은
다른 집계 범위·정의이므로 현재 자료로 성능·비용 순위를 확정할 수 없다.
[AGY r21 최종 평가](evidence/agy-remediation-r21-final-evaluation-20260929.md)도
기존 순위 적격성과 전체 제품 합격을 주장하지 않는다.

## 발견 사항

### A01 — Critical: 새 비교와 기존 규칙의 적용 관계

[새 비교 방향](reference-comparison-20260929.md)은 첫 결과와 후속 수정 비용을
함께 평가하고 전체 제품 합격을 후보 시작 전제로 두지 않는다.
[기존 protocol](agent-experiment-protocol.md),
[baseline](../../experiments/config/version-2-baseline.yaml),
[공통 prompt](../../experiments/prompts/version-2-agent-task.md)는 단회·후속 질문 0회와
기존 gate를 정의한다. 첫 실행과 종료 후 remediation은 양립할 수 있지만, 새
비교에서 적용할 cohort·운영 입력·대체 조항이 한곳에 고정되어 있지 않다.

수정: 공통 운영 계약에 최초/후속 실행 규칙과 문서 우선순위를 명시하고 원래 cohort를
historical로 연결한다. 이미 주어진 사용자 지시를 오래된 미승인 문구로 되돌리지 않는다.
운영 계약에는 Q1~Q3의 사용자 선택을 반영했다. 다음 실행 입력과 도구의 동기화는 남아 있다.

### A02 — Major: 설명과 실제 기계 계약 불일치

제품·평가 계약의 중간 문단은 C1~C8 구조화 필드가 없다고 설명했지만
[schema](../../experiments/schema/end-to-end-result.schema.json)의 required와
[validator](../../scripts/validate-end-to-end-result.py)의 `_check_core_results`는 이미
모든 C 항목을 요구한다. D09도 미해결 설명과 원본/정규화 token 연결 완료 설명이
함께 남아 있었다.

수정: 현재 설명을 실제 필드와 맞추고 옛 D09/D10 상태는 날짜·commit이 있는 역사
기록으로 유지한다. validator는 제출된 판정의 계약을 검사하며 실제 LCD 동작을
측정하지 않는다는 경계는 유지한다. 이 불일치가 후보 JSON 오류의 직접 원인이었다는
증거는 없다. 이번 docs 변경에서 설명을 정정한다.

### A03 — Critical: 기준 도달과 공통 수정 예산

새 방향은 기준 도달 또는 공통 한도에서 종료한다고 정하지만 실제 판정 목록·수정
회차·누적 예산을 제공하지 않는다. 기존 120분은 개별 run 한도다. 기준 제품도 전체
계약 합격은 입증되지 않았으므로 reference-match와 production-conformance를 같게
취급할 수 없다. OpenCode 수정마다 사용자 요청이 있었으며 이를 무단 반복으로 해석하지 않는다.

수정: 사용자 선택은 확인된 Codex 기능 도달과 별도 전체 합격, 최초 120분,
후속 최대 3회·누적 120분이다. 피드백은 관측·기대 동작·증거로
구성하고 구현 방법 제공은 개입으로 기록한다. 한도 종료는 미도달로 보존한다.

### A04 — Major: runtime 시계와 freshness 의미

[제품 계약](../PRODUCT_CONTRACT.md)은 RFC3339·reference_time·300초 stale을 정하지만
firmware의 epoch 확보, 시각 미확정, fixture anchor, monotonic 경과 시간의 관계는
충분히 지정하지 않는다. 보존 C 진단을 재실행했을 때 같은 frame은 uptime 10에서
FUTURE_TIMESTAMP로 거부되고 epoch 1788998699에서 수락됐다.

수정: epoch 유효 여부·monotonic 시계·fixture reference anchor를 정의하고 source-age와
receive-age를 분리한다. 부팅/재부팅/299·300초/만료 reset을 runtime 경로로 확인한다.
새 송신으로 원본 observed_at을 바꿔 오래된 source를 신선하게 만드는 것은 금지한다.

### A05 — Major: 보드 전제와 BSP의 비교 범위

[카탈로그](../hardware/version-2-capabilities.md)와
[제조사 source index](../hardware/vendor-source-index.json)는 이미 존재한다.
그러나 핀 역할·백라이트 극성·PSRAM/framebuffer 설정·LCD API 경로·native USB와
UART 관계가 짧은 최소 보드 계약으로 모이지 않았다. Codex는 백라이트 active-low
수정 후 가시 출력이 확인됐고 OpenCode 원본/r02는 다른 LCD 초기화 오류를 보였다.
OpenCode 최종 검은 화면 원인이 Codex와 같다고 확정하지 않는다.

수정: 사용자는 보드 사실·제조사 소스만 제공하고 BSP 구현도 평가하는 비교를 선택했다.
고정 제조사 source를 근거로 설정·메모리 배치를 설명하되 설정 통과와 광학 출력을
별도로 확인한다.

### A06 — Major: 요구사항에서 실제 표시까지의 시험 추적성

OpenCode 첫 결과는 legacy parser 29/29와 result validator를 통과했지만 실제 serial
backend가 없었고 payload 대신 상수 42, reset 대신 sent_at을 표시했다.
[평가 계약](evaluation-contract.md)은 legacy seam의 제한을 정직하게 설명한다.
문제는 전체 요구 ID→stimulus→runtime→관찰 값→판정의 고정 매핑이 부족한 점이다.

수정: 서로 다른 fixture 값을 연속 전달해 production receiver/state/view-model의
window·reset·출처·수치 변화를 검사한다. host의 표시 의미 검사와 실제 glyph·가독성
광학 검사를 구분한다. 상수·잘못된 시각 대체·uptime/epoch 혼동을 잡는 평가 사례를
추가하되 과거 결과에는 평가 버전을 표시한다.

### A07 — Major: 실물 관측과 단절 시험의 실행 절차

일반 실물 증거의 사진·영상 또는 serial 문구는 요구별 증거 종류를 덜 분명하게 한다.
GUI/bring-up 문서는 광학 출력의 별도 확인을 정확히 요구한다.
[cdm/1](host-device-pipeline-contract.md)에는 ACK가 없고 COM3는 단일 점유다.
r06의 write/GUI marker 성공은 장치 수락·가시 출력 성공이 아니었고 별도 진단의
수락도 후보 sender 성공을 대신하지 못했다. 배터리 없는 USB 제거는 전원 유지
데이터 단절 시험이 아니다.

수정: 송신과 capture를 한 port 소유 경로에서 연결하는 관측 절차와 sequence/화면
증거 대응을 정의한다. C2 가시 출력·30초 유지와 G 점수 조건을 구분한다. powered
collector 정지/재시작, 실제 링크 단절, 전원 재인가를 구분한다. ACK 추가는 새 protocol로 한다.

### A08 — Major: 정책 준수·환경·제품 능력 분리

공통 prompt가 AGY pilot 권한 파일을 요구한다. AGY는 미등록 pytest 호출 뒤
environment_failed로 기록됐지만 독립 빌드는 성공했다. OpenCode는 거부된
`build-host/test_meter.exe` 대신 `.\build-host\test_meter.exe`로 계속했고 명시된 종료
지시를 위반했다. Codex reference에는 해당 정책이 적용되지 않았다.

수정: 필요한 작업군을 각 표면의 capability에 매핑하고 실제 읽기·빌드·시험 호출을
사전 검증한다. 실행 상태·정책 준수·제품 기능·비교 적격성을 별도 축으로 기록한다.
지시 위반을 지우지 않고 환경 정책 차이도 모델 능력으로 합치지 않는다. 과거
environment_failed 원본은 덮어쓰지 않는다.

### A09/A10 — Minor: 탐색 문서 상태와 evidence 복원

- A09: Lab-Notes Overview·Home에 이전 Version 1/세로/이중 전망·승인 대기 설명이
  남아 있다. 현재·historical·후속 범위를 구분해 canonical 링크를 갱신한다.
- A10: OpenCode 원본 validator는 통과했지만 source bundle 복제본은 ignore된
  c-frame-1.bin이 없어 실패했다. 별도 artifact 보존은 적절하다. 다음 비교에는 source와
  evidence package의 복구 목록·상대 경로·hash를 묶고 임시 경로 복원을 확인한다.

## 문서 결함과 구분할 구현 미충족

실제 전송 backend 부재, 상수 42·sent_at 대체 표시, 읽을 수 없는 glyph,
1초 BOOT polling, ADC 오류를 75% OK로 표현한 것은 기존 요구 미충족이다.
모든 실패의 원인을 문서로 돌리지 않는다. 실제 계정 수집은 별도 live cohort이므로
fixture 비교 자체의 실패로 세지 않으며, 실 계정 제품 완성으로도 주장하지 않는다.

## 품질 체크리스트와 현재 처리 상태

원래 검토의 24조건 중 확인 15개(62.5%)로 Major Revision 판정이었다. 이는 전수
요구사항 충족률·실험 성공률·산업 표준 인증 점수가 아닌 리뷰어 checklist 판단이다.
완전성 2/4, 명확성 3/4, 일관성 1/4, 검증 가능성 3/4, 추적성 3/4, 실행 가능성 3/4다.
전체 체크 정의는 연결된 Lab-Notes 평가에 보존한다. A02 정정 뒤 이 점수를 새
측정치처럼 재사용하지 않는다.

이번 반영: A02의 제품·평가 설명 정정, 과거 검토의 역사 상태 표시, 문서 지도 연결,
평가/수정 계획과 사용자 결정·운영 계약·기준 목록 초안의 Git 기록.
실행 입력과 도구 동기화, clock/board 및 검증 개선은 후속 작업이며 실행 완료가 아니다.
OpenCode는 2026-10-02 사용자 지시로 중지된 상태를 유지한다.
