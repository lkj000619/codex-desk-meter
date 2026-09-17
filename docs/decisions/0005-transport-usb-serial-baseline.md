# ADR-0005: E2E baseline transport를 USB serial `cdm/1`로 고정

- 상태: 제안 (검토 중, R1 동결 대기)
- 결정일: 2026-09-17

## 배경

`version-2-end-to-end-v1` cohort의 transport 후보는 USB serial(COM3)과 local
Wi-Fi였다. 두 후보를 병기한 문서가 에이전트에게 선택지가 열려 있는 것으로
오독될 소지가 있었고, 재현성·원시 송수신 log 측정·자격증명 불필요 측면에서
하나로 고정해야 한다는 2차 검증 지적이 있었다.

## 결정

E2E baseline transport는 USB serial(COM3) `cdm/1`로 고정한다. 기준은
`experiments/config/version-2-baseline.yaml`의 `transport_choice:
usb-serial-cdm-1`이며, 이 ADR은 그 근거를 기록한다. local Wi-Fi 운용은 별도
비교 cohort에서 다룬다.

## 이유

- 지연·재현성·원시 송수신 log 측정이 쉽다.
- Wi-Fi 자격증명(AP/주소)이 필요 없어 fixture-only 원칙과 충돌하지 않는다.
- COM3 단일 점유 정책과 운영자 실물 평가 절차가 이미 문서화되어 있다.

## 제약과 영향

- E2E 실물 단절 시험의 기준은 USB 케이블 단절·COM 재열거다. Wi-Fi 단절 시험은
  Wi-Fi cohort의 조건이다.
- frame envelope(`cdm/1`, CRC32, sequence 규칙)는 baseline commit 동결 시 최종
  확정된다.
- 본 ADR의 승인과 baseline commit·hash 동결은 R1 종료 조건이며, 승인 전에는
  어떤 agent 실행도 `AUTHORIZED`가 되지 않는다. R10은 `not_authorized`로 유지한다.
