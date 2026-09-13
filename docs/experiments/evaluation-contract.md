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
null, dns, tls, http_500 중 하나다. 출력 필드는 PRODUCT_CONTRACT.md의
UsageSnapshot/GlobalResetSnapshot을 따른다. 로그는 stderr로 출력한다.

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
| C3~C6 | fixture 수치·미확인·출처·확률 표시 |
| C7 | 정상→오류→복구, Wi-Fi 단절, watchdog reset 없음 |
| C8 | BOOT 전환·수동 갱신·자동 주기, RST 재부팅 |
| 자율 기능 | 기능 선정 문서의 5/5/5/10/5 점수와 각각의 증거 |

BOOT를 누른 채 reset하는 동작은 ROM 다운로드 모드 진입 조건이다. 애플리케이션
실행 이전 동작을 펌웨어가 방지한다고 요구하지 않는다. 정상 부팅 후 BOOT 입력을 시험한다.
