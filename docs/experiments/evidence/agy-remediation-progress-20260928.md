# AGY 별도 보완 실행 — 2026-09-28

사용자가 BOOT 버튼 무반응과 계속되는 화면 깜빡임을 확인하고 남은 작업 진행을 요청했다.
기존 원본 pilot은 보존하며, 평가 결과와 사용자 관찰을 제공하는 별도 remediation으로 진행한다.
기존 단일 prompt 정량 비교 cohort·agent 순위와 합산하지 않는다.

## 작성 책임과 실행 조건

- 제품 구현 수정은 AGY가 수행한다. 운영자는 원본 source 복사, 고정 보완 지시,
  권한 사전 검증, 실행·보존·독립 평가·사용자가 승인한 flash를 수행한다.
- 입력 제품 source는 기존 AGY implementation `9d52fa50529ae8020c6d1f54f193c7f74f875181`.
  canonical Git archive의 제품 파일 111개를 그대로 복사하고 hash로 확인했다.
  Git이 정규화한 dependencies.lock의 line ending을 사용하며 의미 변경은 없다.
- AGY 1.2.11 / gemini-3.8-flash-medium / 제한 120분 / 고정 prompt 1회.
- 실행 중 추가 지시나 구현 수정 없음. agent의 실제 보드 접근·flash는 금지한다.
  실물 시험은 실행 종료 후 운영자가 수행한다.
- source lineage·prompt·model·policy·preflight·usage·도구 로그는 각각 별도 보존한다.

## 이력

| 실행 | 상태 | 근거 |
|---|---|---|
| remediation r01 | 58.359초 후 환경 실패; 제품 변경 없음 | `.gitignore`를 포함한 checkout Git index 조회 거부. 전역 설정 복구·source clean·bundle 보존 확인 |
| dotfile 진단 1 | 첫 조회 성공, 두 번째 조회 거부 | 두 번째 명령의 현재 디렉터리 `.` 선택자가 규칙에 없었음. 원본 진단·usage 보존 |
| dotfile 진단 2 | 통과 | `.gitignore`/`.gitattributes` 및 현재 checkout 조회 모두 실제 AGY에서 실행. 전역 설정 복구 |
| remediation r02 | 실행 시작 | 최종 제한 규칙·고정 입력·원본 source 확인; preflight 112개와 COM3·host runtime·clean checkout 통과 |

정책 보완은 `git ls-files`의 checkout-root `.gitignore`, `.gitattributes`, 현재 디렉터리
선택자뿐이다. parent/absolute 경로·history·compound shell·임의 Python·설치·flash는
기존대로 제외한다. 실패를 재현한 회귀 시험을 먼저 추가한 뒤 규칙을 수정했고,
negative boundary 시험과 실제 AGY 진단을 통과했다.
기존 동결 정량 비교 baseline과 receipt는 변경하지 않는다. 새 정책을 정식 비교에
사용하려면 모든 후보의 공통 조건을 다시 동결·검증해야 한다.

## 보완 범위

GPIO0/BOOT, LCD 렌더링 안정성, 데이터 부재·null·stale 표시, 실제 USB Serial/JTAG
수신, PC fixture collector·정규화·frame·재연결, 시간 경과/300초 stale 처리,
provider 전체·오류·복구 시험, 선택 IMU 기능과 최종 구조화 결과 제출을 포함한다.
독립 평가와 실물 시험 없이 제품 합격을 선언하지 않는다.

## 기록 위치

- [첫 보완 시작·사용자 관찰](agy-remediation-launch-20260928.json)
- [r01 실패 원본·측정·hash](agy-remediation-r01-result-20260928.json)
- [r02 제한 정책·진단·사전 검증](agy-remediation-policy-preflight-20260928.json)
- [기존 남은 작업 점검](agy-remaining-work-review-20260928.md)
- raw root: `C:/Espressif/benchmark-remediation/20260928-agy-remediation-r02`.

이 문서는 시작 시점의 진행 기록이다. 실행 종료 판정은 별도 결과 보고서로 추가한다.
