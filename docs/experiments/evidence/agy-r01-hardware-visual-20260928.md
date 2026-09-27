# AGY r01 실물 사진·영상 검증 — 2026-09-28

## 판정

**업로드한 AGY 구현의 LCD 출력 확인 / 표시 결함 관측 / 제품 전체 합격 미확인.**

사용자가 업로드를 요청한 뒤 검증된 binary를 COM3에 올렸다. firmware 식별과 flash
검증은 [업로드 기록](agy-r01-hardware-upload-20260928.json)에 있다. 이후 사용자가 제공한
사진과 19.52초 영상을 평가했다. 원본 구현을 수정하거나 AGY에 결과를 되먹임하지 않았다.
실패한 pilot의 시간·usage·완주 판정을 변경하지 않는다.

## 확인된 출력

사진의 `GLOBAL RESET MONITOR`, `SCREEN 2/3`, `DEFAULT SCREEN: No Global Reset Record`,
source·footer 문구가 업로드한 GUI 소스와 일치한다. LCD 전원과 기본 화면의 문자·카드 출력은
확인됐다. 모든 화면·방향에서 잘리지 않는다는 합격 판정은 아직 아니다.

## 결함과 한계

1. 영상을 1fps로 추출한 20개 frame에서 내용이 거의 없거나 일부만 그려진 모습이 보인다.
   약 16~18초에는 header/card 일부만 표시되고 이후 기본 화면이 다시 보인다.
   초기 약 0~7초에도 유사한 모습이 있으나 시야각·반사의 영향을 배제할 수 없다.
   표시 불안정의 원인은 확정하지 않았으며 영상만으로 reset·회전 성공을 주장하지 않는다.
2. 사진의 `Fetched: 2026-09-10 16:54:07Z`는 실제 조회 증거가 아니다. GUI는
   `fetched_at`이 없을 때 이 문자열을 고정 출력한다. 날짜는 촬영 시각·수신 시각으로 쓰지 않는다.
3. 추가 정적 확인: usage window가 없을 때 dashboard는 remaining 58%를 기본값으로,
   유효한 현재 시각이 없을 때 reset 화면은 경과 시간 `2 days 14 hours 58 mins ago`를
   고정 출력하도록 작성됐다. 이 두 값의 실제 화면 표시는 이번 사진에서 확인하지 않았다.
   source 데이터의 부재를 임의 숫자로 채우므로 데이터 의미 검증에서 해결해야 할 결함이다.

BOOT 반응·화면 전환의 원인, IMU 회전, 실제 host frame 수신과 PC 통합은 미검증이다.
화면의 `Monitoring`, `verified source`, `Fetched` 문구만으로 통신·조회 성공을 판정하지 않는다.

## 증거 보존

[사진·영상·frame hash 및 판정](agy-r01-hardware-visual-20260928.json).
원본 사본과 추출 frame은
`C:/Espressif/benchmark-runs/hardware-agy-r01-20260928/user-media`에 보존했다.
시각 검증은 원본 run 종료 후의 운영자 평가이며 비교 측정에 합산하지 않는다.
이 기록은 실물 관측 범위를 추가하며 원본 run의 `environment_failed`·제품 미합격 판정을 유지한다.
