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

## Runtime 보완 제출 후 실제 재검증 (2026-10-08 23:50 KST)

`task_2b005e480abd` / `ctx_4308689007a9`의 제출은 `7264e76`에 보존했다.
수동 입력 scheduler, bounded RPC, source cache와 OS lock이 추가됐지만, coordinator가
ESP-IDF Python venv에서 실제 32개 시험을 재실행한 결과 Windows lock-owner crash 후
재취득 시험 1개가 실패했다. venv launcher와 실제 잠금 소유 프로세스를 구분해 원인과
정리 방식을 검증해야 한다. 제출자의 32개 PASS는 coordinator 검증 결과와 구분한다.

`SharedCollectionState.collect_all`을 직접 호출한 synthetic 재현에서, 정상 session
관측 후 파일을 지우고 source age가 정확히 300초인 reference로 다시 호출하면 기존 값과
관측 시각은 보존되지만 `stale=false`로 남고 `error_reason`에 전체 로컬 경로가 포함됐다.
동결 multi-provider/personal/global fixture를 실제 collect→build_frame으로 전달한 경로는
유효했으나, 실패 경로의 source identity·미존재 파일·여러 entry 캐시·cold error는 추가 수정 대상이다.

`task_c6f6d8f00810` / `ctx_b3dca8602ce8`에서 같은 PC 담당 역할이 아래를 보완한다.

- 오류에도 원본 관측 시각을 기준으로 300초 stale 처리하고 wire 오류에 개인 경로를 넣지 않음.
- 선택한 session이 바뀌면 이전 session 캐시를 잘못 귀속시키지 않고, provider별 캐시를 보존함.
- 선택한 personal/global 파일이 없어져도 조용히 생략하지 않고 기존값·정확한 오류를 유지함.
- cold error의 metric/provenance와 global capture unknown을 보존함.
- receiver-empty 확인·활성 sender 충돌·load 실패 후 잠금 해제·안전한 alias·영속 필드 검증.
- 실제 Windows 잠금 소유 프로세스를 종료하는 시험과 필요한 production 경로 회귀 검사.

PC 최신 수정 검증과 firmware build가 끝나기 전 통합 검증 Task는 native blocked로 유지한다.
COM·실계정·LCD·24시간 안정성은 아직 시험하지 않았다.

## 2026-10-09 재개 후 실제 wire 확인

`task_c6f6d8f00810` 제출 `msg_9dc702168da7`를 수락하고 `14cc264`에 보존했다.
coordinator가 ESP-IDF Python 3.11로 기존 PC 시험 39개를 실행해 통과했다.
실제 C host build와 8개 시험도 통과했다. 이 결과는 아래 추가 결함을 검사하지 않았다.

[재현 결과](../../experiments/orca-harness-20261008/operator/pc-post-resume-probe.json):

- 실제 watch는 수집 전에 `sent_at`을 기록한다. 30ms 뒤 수집된 관측으로 만든 실제
  PC frame을 production C receiver에 전달하니 `SNAPSHOT_INVALID`로 거절됐다.
- cold global 파일 오류는 `captured_at=null`을 만들고 `build_frame`에서
  `FRAME_SCHEMA_INVALID`가 된다. 동결 schema는 non-null capture를 요구한다.
  관측하지 않은 global record는 wire에서 생략하고 로컬 실패를 명확히 기록해야 한다.
- 세 provider를 담은 동결 fixture를 읽은 뒤 파일이 사라지면 세 캐시 중 google 하나만
  남는다. 파일 캐시 하나 대신 각 원본 source record를 보존해야 한다.

추가 synthetic native token event에 timestamp가 없는데 input=10/output=2를 전달하면
`reference_time=2026-10-09T09:00:00Z`가 원본 `observed_at`·`last_good_at`으로
복사되고 available이 됐다. nullable source 시각은 unknown/null 또는 명확한 오류로
보존해야 한다. cold source 오류에도 관측하지 않은 시각을 성공적 관측으로 만들지 않는다.
이 재현과 지시는 `msg_49d4ac2f5863` / `msg_edcd93ae1205`로 같은 담당에게 전달했다.

이 결함들과 source 선택 identity·갱신 deadline 회귀 검사는 같은 PC 담당의 새 보완
`task_a6eebb977125` / `ctx_04111d8d4601`에 맡겼다. 이전 제출은 성공적인 제출이고
완성된 제품 합격은 아니다. frozen schema·과거 비교 판정은 변경하지 않는다.
