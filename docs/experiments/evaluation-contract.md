# 공통 평가 인터페이스

에이전트는 실제 펌웨어에서 사용하는 파서·상태 전이 모듈에 연결된 host 실행 어댑터를
제공한다. 별도 구현한 모방 파서는 인정하지 않는다. 운영자가 소스 목록, 빌드/링크
로그와 SHA-256을 검토한다. 이 연결 검토는 자동 시험 통과로 대신할 수 없다.

어댑터는 stdin의 UTF-8 JSON 한 개를 읽고 stdout에 snapshot 배열만 출력한다.
각 호출은 새 상태에서 시작하고 events 순서대로 같은 상태를 갱신한다.

이 어댑터 계약은 firmware의 파서·상태 전이를 평가하기 위한 host seam이다. 이를
통과해도 PC에서 실제 Codex 사용량을 수집하거나 ESP32로 전송했다는 뜻은 아니다.
제품 전체 데이터 경로는 `PC collector → normalized snapshot → versioned transport
→ ESP32 receiver/cache/stale → LCD GUI`다. historical hardware-autonomy cohort에서
collector와 transport를 생략한 결과는 `not_run; out of cohort`로만 보존하고,
정식 E2E cohort에서는 I1~I4와 함께 검증한다. 실제 source 전환은 owner-only
live integration에서 송수신 frame, 재연결, 무결성, 승인 절차를 별도로 검증한다.

```json
{"source":"fixture","events":[{"now":"2026-09-11T00:00:00Z","body":{},"error":null}]}
```

`body`는 fixtures의 원본 객체, 잘못된 JSON 문자열 또는 null이다. `error`는
null, dns, tls, http_500 중 하나다. 로그는 stderr로 출력한다.

### 현재 evaluator의 legacy 회귀 출력

`scripts/evaluate-product.py`는 최상위 legacy fixture 3종을 사용하는 회귀
interface다. 현재 `check()`가 요구하는 출력은 최신 UsageSnapshot 전체와 다르다.

| 입력 source | event별 출력의 필수 검사 필드 |
|---|---|
| `fixture` (`personal-usage.json`) | `source: fixture`, 원본 `windows` 배열 그대로(`id` 키 포함), `observed_at: captured_at`, `stale`, `error_code` |
| `codex-reset.com` / `codex-resets.com` | `provider`, `fetched_at`, 정규화한 `latest_reset_at`, nullable `forecast_24h_percent`·`forecast_48h_percent`, `forecast_is_schedule: false`, `stale`, `error_code` |

각 호출에서 세 event에 대응하는 snapshot 세 개를 배열로 반환한다. 오류 event는
마지막 정상 값·조회 시각을 유지하고 `error_code`를 채우며, 정상 복구 후 해제한다.
forecast 필드는 파서 호환 검사이며 현재 C5 화면 표시 판정이 아니다.

이 legacy interface의 `source`/window `id`를 E2E wire 필드로 그대로 보내지 않는다.
E2E의 UsageSnapshot은 `usage-snapshot.schema.json`의 identity, `source_kind`,
window `window_id` 등을 사용하며, global wire 매핑은
[통합 계약](integration-contract.md)을 따른다. host 어댑터가 legacy 출력으로
변환하더라도 실제 제품 파서·상태 모듈 호출 증거가 필요하다. 최신 E2E provider
계약 전체를 이 evaluator 하나로 검사할 수 있다는 의미는 아니다.

운영자는 다음 adapter config를 실제 경로/해시로 채운다. 명령은 argv 배열이며
셸 문자열을 사용하지 않는다. 실행 파일은 절대 경로로 지정한다.

```json
{
  "checkout": "C:/Espressif/benchmark-runs/<run-id>/checkout",
  "argv": ["C:/Espressif/benchmark-runs/<run-id>/checkout/build-host/meter-test.exe"],
  "production_files": {"components/meter/parser.c": "<SHA256>"},
  "reviewer": "<operator>",
  "link_evidence": "C:/Espressif/benchmark-runs/<run-id>/link-evidence.txt",
  "link_evidence_sha256": "<SHA256>"
}
```

`python scripts/evaluate-product.py --adapter-config <config> --output <report>`는
정상값·null 보존, 0/299/300초 stale, 시간/필드/범위 오류, DNS/TLS/HTTP 실패,
마지막 정상값 보존 및 복구를 검사한다. 이는 C3~C7 자동 검사 범위의 회귀 시험이다.
C1 빌드와 C2/C8 실물 동작은 별도로 확인하며 이 도구가 제품 합격을 선언하지 않는다.

E2E result validator 또한 C1~C8 개별 판정을 직접 검사하지 않는다. C별 판정은
아래 평가 기록과 증거로 남기고, 구조화 연결은 [문서 검토 D10](../DOCUMENTATION_REVIEW.md)의
후속 구현 항목으로 관리한다.

## 기능·GUI 결과 분리

공통 evaluator는 C1~C8과 별도로 다음 기능 상태를 기록한다.

| 기능 | historical hardware-autonomy cohort | 정식 E2E/live integration |
|---|---|---|
| F1 PC agent/provider collector | `not_run; out of cohort` | 다중-provider fixture collector, 이후 owner-approved live source |
| F2 정규화·출처 분리 | fixture/parser 범위 | live 승인 source와 fixture 회귀 |
| F3 PC→ESP32 transport | `not_run; out of cohort` | frame·무결성·재연결 raw log |
| F4 ESP32 receiver/state/cache | firmware 직접 입력 범위 | 실제 수신·오류·stale 전이 |
| F5 LCD GUI | 실물 화면 증거 필요 | 동일 |
| F6~F9 | 입력·갱신·리셋·빌드/관측·자율 기능별 증거 | 동일 |

F5 GUI는 `feature-comparison.md`의 G1~G6(각 0~3점)를 사용한다. 화면 사진·영상,
촬영 UTC 시각, fixture 상태, 판정자와 SHA-256이 없으면 점수를 확정하지 않는다.
fixture parser 통과나 GUI 점수는 PC collector·transport의 구현 증거가 아니며,
F1/F3 `not_run` 상태를 제품 전체 합격으로 바꾸지 않는다. 정식 E2E에서는 I1
(collector), I2 (normalization), I3 (transport), I4 (receiver/state)도 각각
pass/partial/fail/not_run과 증거를 남긴다.

## 실물 채점 기록

운영자가 각 항목에 pass/partial/fail/not_run, 판정자, UTC 시각, 증거 경로와
SHA-256을 기록한다. 미검증은 합격으로 간주하지 않는다.

| 항목 | 검증 |
|---|---|
| C1 | ESP-IDF v5.3.2 esp32s3 빌드와 종료 코드 |
| C2 | 부팅 후 30초 LCD 유지, 세 화면의 잘림 없음 |
| C3~C6 | fixture 수치·경과·미확인·출처 표시 |
| C7 | 정상→오류→복구, USB 통신 단절(Wi-Fi cohort는 Wi-Fi 단절), watchdog reset 없음 |
| C8 | BOOT 화면 전환(debounce 후 300ms 이내), PC 수동 재수집(5초 이내 전송·수신 후 2초 이내 LCD 반영), 60초 이하 자동 주기, RST 재부팅 |
| 자율 기능 | 기능 선정 문서의 5/5/5/10/5 점수와 각각의 증거 |

BOOT를 누른 채 reset하는 동작은 ROM 다운로드 모드 진입 조건이다. 애플리케이션
실행 이전 동작을 펌웨어가 방지한다고 요구하지 않는다. 정상 부팅 후 BOOT 입력을 시험한다.

I3/I4 복구 시험은 USB 재연결과 PC collector 프로세스 재시작을 별도로 수행한다.
후자는 보드를 켜 둔 상태에서 수행하고, 영속 순번의 연속성·정상 화면 복구를
확인한다. 순번 저장소 유실은 자동 복구 성공으로 채점하지 않고, 전송 차단과
운영자 복구 절차를 검증한다. 상세 기준은 host-device-pipeline-contract.md를 따른다.
### Machine-enforced E2E scoring and joins

The E2E contract requires top-level `core_results.C1` through `C8` in every
result. F9 details are scoped to `feature_results.F9`; F1-F8 reject that field.
When F9 is assessed, its three candidates record user value,
resource/implementation cost, risk, verification method, selection state, and
selection/rejection rationale or a selection-document evidence reference.
The canonical F9 rubric is a 30-point sum:
`hardware_understanding=5`, `user_value=5`, `selection_logic=5`,
`implementation_completeness=10`, `separation_portability=5`. `total` must
equal the sum.

The normalized token total is always `input + output`; nullable
`provider_total` preserves the provider-reported raw value under its required
definition field. Archive accepts a normalized E2E result only after schema,
semantic, evaluation-manifest, and evidence-join validation, including a
second validation after path normalization. Failed validation retains the raw
snapshot only.
