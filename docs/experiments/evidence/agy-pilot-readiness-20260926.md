# AGY 첫 pilot 준비 정비 및 검증 — 2026-09-26 KST

> 실행 전 준비 시점 기록이다. 이후 첫 run은 CLI 인자 오류로 종료됐다.
> 현재 상태는 [실행·사후 검증 기록](agy-pilot-result-20260926.md)을 따른다.

## 판정과 적용 범위

**PILOT_PREPARED / LAUNCH_RECHECK_REQUIRED**. 문서 검토에서 확인한 날짜 충돌과
ADR 상태 불일치를 정리하고, 실행일이 유효한 새 run의 준비 검증을 통과했다.
대상은 `antigravity-cli / gemini-3.8-flash-medium`, AGY 1.2.11, 첫 pilot 1회다.
정식 반복 benchmark와 제품 합격은 이번 준비 판정에 포함하지 않는다.

- 사용자 요청: 문제를 수정해 실험 준비 상태로 만들고 검증(2026-09-26).
- 기존 실행 근거: [2026-09-18 조건부 승인](../preflight-evidence-20260918.md#r10-조건부-승인-기록-2026-09-18-사용자-승인)과
  [Q3의 첫 AGY pilot·COM3 옵션 A 선택](../agy-launch-review-20260925.md).
- 현재 R10: `not_authorized`. 실제 prompt 전달 직전에 아래 재확인과 발효 기록을 남긴다.
  대상·조건이 일치하는 기존 승인을 다시 요청하지 않는다. 이번 작업은 준비 요청이며 모델을 실행하지 않았다.

## 수정한 문제

1. 날짜: 9월 25일 run을 9월 26일에 사용할 수 있다는 안내를 정정했다.
   runner의 날짜 검사는 유지한다. 이전 예약은 보존하고 아래 새 run을 만들었다.
   날짜가 다시 바뀌면 이전 run을 수정하지 말고 새 ID로 준비한다.
2. ADR: 이미 선택되고 동결된 USB serial, 단일 리셋 출처, 가로 화면 기준을
   ADR-0005/0006에 선택된 AGY pilot 범위의 채택 결정으로 정리했다.
   사용자 요청에 따른 현재 정정이며 과거에 승인이 기록돼 있었다고 소급 주장하지 않는다.
3. 문서 상태: README, 문서 지도, readiness, 실행 가이드와 이전 준비 기록을 연결했다.
   과거 R5 차단 문구는 시점별 기록으로 표시하고 현재 pilot-entry 판정과 구분했다.

동결 baseline tag/commit과 prompt/config/fixture/profile은 변경하지 않았다.
이번 변경은 maintainer의 운영 상태·ADR 적용 기록이며, 새 run checkout 밖의 본 기록을
운영자가 사용한다. 동결 checkout의 옛 `planning`·ADR 제안·gate 상태는 동결 당시 기록이고,
현재 운영 판정은 이 기록과 현재 readiness 표를 따른다. agent 입력을 사후 수정하지 않는다.

## 준비된 실행

| 항목 | 값 |
|---|---|
| Run | `20260926-antigravity-cli-agy-flash-medium-r01` |
| 경로 | `C:\Espressif\benchmark-runs\20260926-antigravity-cli-agy-flash-medium-r01` |
| 상태 | `prepared`, `started_at=null` |
| Baseline | `benchmark-v2-baseline-20260925` |
| Commit | `eef278013428a79c29d6b9456018049af149ca61` |
| Profile SHA-256 | `843a2cce0310b710e166de60cd3a4b5b651d88e06550f88f2f4552c6f6474f5e` |
| Bundle SHA-256 | `f7cfc546acac458c7691c10ccb776c20f5078ca141d353f1086fb808fe810948` |
| Port / phase | `COM3` / `pilot` |

생성 명령은 깨끗한 `C:\Espressif\benchmark-baseline-20260925`에서 실행했고 exit 0이었다.

```powershell
.\scripts\new-experiment-run.ps1 -Baseline benchmark-v2-baseline-20260925 `
  -Profile experiments/config/verified-profiles-candidate/agy-gemini-3.8-flash.candidate.json `
  -RunRoot C:\Espressif\benchmark-runs -Seed 20260926 -Phase pilot -Port COM3
```

## 검증 결과

검토자: Codex maintainer, 2026-09-26 KST. 새 run의 기계 검사 시각과 manifest hash는
[검사 결과 JSON](agy-pilot-readiness-20260926.json)에 보존했다.

| 검사 | 결과 |
|---|---|
| 동결 checkout preflight | IDF 5.3.2 활성화 후 `check-experiment-preflight.ps1 -RequireHardware -Port COM3`: exit 0, 실패 0, 경고 0 |
| 오프라인 시험 | preflight 내부 92개 시험 통과 |
| 결과 계약 | historical example, E2E example, provider matrix validator 통과 |
| Receipt | 실제 새 manifest/profile로 `validate_preflight_receipt` 통과, 연결된 증거 hash 일치 |
| Run 무결성 | schema/operator/resolved profile 검증, KST 날짜 일치, checkout clean, HEAD·profile bytes·전달 prompt hash 일치 |
| 입력 무결성 | 새 checkout에서 `input_bundle_hashes` 재계산, manifest의 모든 입력 hash와 일치 |
| CLI/설정 | `agy --version` = 1.2.11, global skill/MCP 검사 통과, 원래 settings/instructions/hooks hash 3개 일치 |
| 보드 접근 | 활성화한 IDF 환경의 `python -m esptool --chip esp32s3 --port COM3 chip_id`: exit 0, ESP32-S3 rev v0.2 / 8 MiB PSRAM |
| 복구 이미지 | 현재 이미지 `ba234a…532b`, factory 이미지 `aa51ba…e6`의 전체 SHA-256이 R9 기록과 일치 |

`chip_id`는 COM3를 열고 RAM stub 및 RTS reset을 사용했다. flash 쓰기나 erase는 수행하지 않았다.
이는 점검 시점의 포트 접근 증거이며 장시간의 포트 예약을 보장하지 않는다.
보드 모델의 사용자 육안 확인은 기존 R9 기록을 사용했다.
검사 스크립트의 최초 시도는 포트 필드를 `operator.port`에서 읽어 KeyError로 중단됐고,
실제 schema의 `hardware.port`로 고친 재검사가 통과했다. 제품 코드는 변경하지 않았다.

## 실제 시작 직전 절차

1. 실행일(KST)과 run ID 날짜, `prepared` 상태를 확인한다. 날짜가 바뀌었다면
   실행 가이드 §5에 따라 새 run을 만들고 receipt·입력 hash를 다시 검증한다.
2. COM3 단독 접근을 다시 확인한다. 다른 board/환경/profile/CLI 변경이 있으면
   영향을 받는 gate를 다시 검토한다. flash 전에는 candidate hash와 복구 이미지를 별도로 대조한다.
3. checkout 밖에 실행일시, 실제 run ID, baseline/profile/bundle hash, COM3 확인 결과와
   기존 조건부 승인 근거를 적은 R10 발효 기록을 남기고 상태를 `AUTHORIZED`로 갱신한다.
4. 실행 가이드 §6의 `agy_pilot_environment.py` wrapper를 통해서만 runner를 실행한다.
   wrapper가 실제 scoped settings와 extension 상태를 다시 확인한다.

R4/R6/R7의 실제 모델 entitlement·권한 동작·stream/usage·개입 여부, 생산 firmware와
LCD 결과는 첫 pilot 이후 검증한다. receipt의 `pilot_pass=false`를 유지하며,
모델·제품 결과가 검증되기 전에는 정식 반복 benchmark를 시작하지 않는다.
