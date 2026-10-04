# 문서 검토 보완 계획

목표: DOC-01~04의 계약 누락·상태 불일치·판정 모호성을 해소한다.
근거: [검토 보고서](../../results/documentation-assessment-20261002/review.md).
실행 방법: 현재 세션에서 순차 수정·검증. 사용자 보완 진행 요청에 따라 수행한다.
상태: 진행 중.

## 설계와 보존 범위

후보 입력 57개와 기존 baseline·profile·receipt·package를 유지한다.
운영자 관측 도구에 선택적 receiver log 설정을 추가한다. 설정은 한 줄짜리 성공 로그의
literal template(`{sequence}` 한 개), 검토자, source 검토 근거를 포함한다.
설정과 근거를 capture에 복사·hash하고 해당 순번의 완전한 성공 로그만 수신 증거로 읽는다.
기존 CDM_RX 기본 경로는 유지한다. 로그 미지원·증거 없음은 제품 실패와 구분한다.
변경된 운영 도구는 기존 준비 package의 검증 범위에 포함됐다고 주장하지 않는다.

## 작업과 완료 조건

- [x] DOC-01: 다른 성공 로그·거부/다른 순번/잘린 로그를 시험하고 CLI 설정과 증거 보존 구현.
  `scripts/product_observation.py`, `scripts/observe-product.py`, 관련 unittest와 도구 안내를 수정한다.
- [x] DOC-02: README·운영 계약을 실제 상태 및 별도 RM 기록에 연결한다.
- [x] DOC-03: RM5 동등 탐색의 사전 판정 절차·상태별 기준과 실행 후 기록을 분리한다.
- [x] DOC-04: 목적 문서에 fixture/live/Version 1 단계별 완료 기준을 추가한다.
- [x] 새 도구의 실행 적용 범위를 readiness에 기록하고 전체 회귀·예제·링크·동결 입력 불변 검사를 수행한다.

완료 조건: 네 항목의 보완 근거가 연결되고 회귀시험 통과, 후보 allowlist bytes 불변,
이전 평가 원본 보존, 실험·flash·계정 통합 미실행을 확인한다.
