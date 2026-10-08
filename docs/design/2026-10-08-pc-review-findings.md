# PC 최초 제출 검토 및 보완

2026-10-08 적용 범위: 별도 Orca cohort의 PC 최초 제출 `task_fa0b12bd6fda` /
`ctx_e7bb307f023b`. 과거 비교 결과나 동결 입력을 정정하는 문서가 아니다.
원본 구현 보고와 테스트 13개 통과는 보존하되, 제품 요구 충족·실계정·COM 성공으로 취급하지 않는다.

coordinator는 테스트 13개를 재실행했고 모두 통과했다. 다음 결함은 실제 코드 읽기와
[synthetic probe](../../experiments/orca-harness-20261008/operator/pc-initial-probe.json)로 확인했다.

| 발견 | 확인 결과 | 보완 담당 |
|---|---|---|
| native token event 구조 | `event_msg.payload.info.total_token_usage`의 input=100이 실제로 0·event_count=0으로 반환됨 | AGY Flash |
| 원본 관측 시각 | 이후 무관한 event가 12:00 토큰 관측을 12:10으로 바꿈 | AGY Flash |
| 복수 quota 결과 | `rateLimitsByLimitId`의 정상 window 1개가 0개로 누락됨 | AGY Flash |
| 실행 중 sender state 유실 | 생성 후 state 파일을 지워도 전송 성공·파일 재생성이 일어남 | AGY Flash |
| 실제 전송·수동 갱신 | send는 COM을 무조건 거부하고 watch는 port와 관계없이 loopback을 사용함; 수동 갱신 경로 없음 | AGY Flash |
| RPC·오류·검증 경계 | blocking readline에 실제 timeout 없음, init 응답/initialized 없이 read 전송, cache·stale·의미 검증 누락; stale 시험은 제품 함수를 호출하지 않음 | AGY Flash |

보완은 `task_3963de21ddd1`에서 실제 토큰 형식·선택·unknown, serial 구현/재연결/수동 갱신,
실행 중 상태 유실과 단일 sender, bounded RPC, provider별 last-good와 의미 검증을 처리한다.
작업자는 COM·실계정·실제 사용자 session을 실행 시험하지 않고 mock/synthetic으로 검증한다.
초기 보고에 적힌 live-quota 실행 명령과 실제 결과는 담당자가 날짜를 붙여 정확히 기록해야 한다.

PC 보완 수락 후 실제 C receiver와의 통합 검증, coordinator의 owner-only live 수집·장치
전송과 사용자 LCD 관측이 남는다. unit test 통과나 제출 메시지는 제품 합격 근거를 대신하지 않는다.

## 첫 보완 제출 후 확인

`task_3963de21ddd1` / `ctx_221ff3735dae`는 `msg_3c2b06ec7025`로 제출됐다.
coordinator의 25개 시험 재실행도 통과했다. native event·관측 시각·quota map·실행 중 state 유실에
대한 수정은 추가 시험으로 연결됐으나, 전체 PC 역할 완료 조건은 아직 충족하지 않았다.

- watch에 수동 입력 처리 경로가 없고, 실패 후 `time.sleep(interval)`로 최대 60초 기다린다.
  5초 이내 수동 전송·연결 복구 조건을 만족하지 않는다.
- RPC helper가 여전히 blocking `stdout.readline()`을 직접 호출해 실제 timeout이 없다.
- gather는 session 오류에서 전체를 중단하며 provider별 last-good cache가 없다.
  `collect`의 출력 의미 검증과 fixture provenance를 선택하는 경로도 빠져 있다.
- state 초기화는 기존 파일을 덮어쓰며, 생성 파일 방식의 lock은 비정상 종료 후 남는다.

이 항목은 작은 단위 시험 개수를 늘리는 것으로 해결되지 않는다. 실제 production watch/RPC/cache
경로를 fake stream·transport로 호출하는 시험을 추가하고, 독립 통합 검증 전에 처리한다.
