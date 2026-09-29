# AGY r20 검증 상태와 남은 실물 시험

## 현재 판정

- AGY 실행: **정상 완주 확인**, 596.484초.
- 독립 소프트웨어 검증: **통과**. CTest 4개·Python 20개·기존 29개·host/ESP32 build·현재 결과 검증.
- 업로드: **완료**. 독립 빌드 해시와 실물 boot ELF 일치.
- 실제 데이터 표시·BOOT 화면 전환·180도 IMU 회전: **영상 관측 확인**.
- C2 LCD 유지·세 화면 출력: **영상 기준 통과**. 새 단일 영상 38.96초에서 LCD 유지와 세 화면의 정상 레이아웃을 확인했다.
- 같은 전원의 native serial close/reopen 후 순번 역전 거부: **제한된 실제 시험 통과**.
- 전체 제품 합격: **보류**. 아래 직접 측정 및 정식 채점이 남아 있다.

구현 commit: `6e00bd8ba518f008d50a762f035a5e8c7e8b6e5c`.
제품 구현과 제품 시험 작성은 AGY가 담당했다. 운영자 검증 도구는 제품 외부에 있고,
이 보완 실행은 원래 단회 정량 비교 순위에 포함하지 않는다.

## PC 송신 구현과 실사용 연동 범위

- PC→ESP32 송신 프로그램은 AGY r20 checkout의 `scripts/run-host-device-pipeline.py`에 구현되어 있고,
  동일 프로그램으로 실제 USB 송신·재수집·주기 송신·순번 지속을 검증했다.
- 현재 입력은 `FixtureRegistry`와 `FixtureFileAdapter`가 읽는 저장소의 고정 JSON fixture다.
  화면의 80% remaining·20% used 및 글로벌 reset 시각은 예제 값이며 사용자 실제 계정의 잔여량이 아니다.
- 로컬 Codex 런타임이나 실제 계정 source에서 사용량/쿼터를 자동 수집하는 adapter는 현재 AGY 결과에 없다.
  송신 경로의 완성과 실제 계정 수집기의 완성은 구분한다.
- 아래 네 가지 잔여 검증은 **고정 fixture E2E 실험**의 범위다. 이를 모두 통과해도 실제 계정 연동을
  완료했다고 판정하지 않는다. PRODUCT_CONTRACT의 실제 source 전환은 별도 `version-2-live-integration-v1`이다.
- 실사용 준비에는 허용된 로컬 source의 실제 제공 지표 확인, source adapter 구현, 조회 시각·오류·갱신
  검증, 기존 frame/USB 경로와의 통합 시험이 추가로 필요하다. source가 절대 잔여 token 수를 제공하지
  않으면 제공된 백분율/단위만 표시한다. 고정 fixture와 원래 실험 판정·순위는 유지한다.

## 남은 조건

| 조건 | 현재 증거 | 필요한 다음 증거 |
|---|---|---|
| BOOT 피드백 ≤300ms | 세 화면 전환 관측 | 물리 버튼 접점/눌림과 첫 새 화면을 같은 시간축에서 직접 측정 |
| 수신 후 LCD 표시 ≤2s | 실제 seq20·9건 수신·사용량/reset 화면 표시 | 프레임 수신과 첫 화면 변경을 같은 시간축에서 직접 측정 |
| 전원 유지 USB 분리·재열거 | native backend 재열기 순서 유지·offline 오류 복구 | 별도 보드 전원을 유지한 실제 USB cable 제거/재연결 및 동일 alias 순번 지속 |
| G1–G6·최종 F9 | 실제 화면과 회전 영상, AGY 잠정 F9 22 | 50cm·동일 조명/노출·모델 비공개 평가와 실제 IMU 잡음 안정성 확인 |

저장된 영상을 연결해 연속 30초 조건을 충족했다고 처리하지 않는다.
41.73초 영상의 약 5~7초 black/데이터 대기는 사용자가 확인한 의도적인 RST다.
이후 사용자가 RST를 다시 눌러 값이 사라졌다고 확인했다. 같은 store의 순번 28을 실제 AGY 송신기로
재송신했고, 보드의 기존 로그에서 정상 수신을 확인했다. 새 영상 `KakaoTalk_20260929_150711023.mp4`
38.96초에서 값 표시 복구·순번 28·1건 수신/0건 dropped를 직접 확인했다. 두 번째 RST도 사용자 조작으로 기록한다.
새 영상에는 BOOT 전환·회전과 약 27.53초의 순간적인 손 가림이 있으나 LCD 소등/reset 징후는 관측되지 않았다.
원래 계약은 30초 LCD 유지와 세 화면의 잘림 없음이며, 버튼 없는 고정 촬영은 운영자의 증거 수집 요청이었다.
이를 추가 합격 조건으로 적용하지 않는다. C2를 영상 기준 pass로 기록하되 미세 flicker·정밀 latency는 별도로 둔다.
시리얼 관측 중 발생한 한 번의 ClearCommError는 원본을 보존했으며 원인은 미확정이다.
후속 실제 송신 및 영상은 정상 관측됐지만 전체 USB 무오류 시험으로 확대하지 않는다.

## 현재 보존된 실행 경로

AGY 작성 운영 절차:
`C:/Espressif/benchmark-remediation/evaluation-r20-20260928/checkout/docs/agent-runs/20260928-agy-remediation-r20/hardware-feature-selection.md`

실제 sender:
`C:/Espressif/benchmark-remediation/evaluation-r20-20260928/checkout/scripts/run-host-device-pipeline.py`

현재 실제 시험 store:
`C:/Espressif/benchmark-remediation/hardware-r20-20260929/actual-cli-tests/sequence-store`

식별자 `esp32s3-288485b08518`, 현재 포트 COM3, 다음 영구 순번 **29**.
정상 재실행은 이 store와 alias를 이어서 사용한다. 수신기를 리셋하지 않은 상태에서 재초기화하지 않는다.
데이터는 고정 offline fixture이며 실제 online quota가 아니다.

## 기록

- [독립 소프트웨어 검증](agy-remediation-r20-independent-review-20260928.json)
- [실물 업로드·순번·영상 검증](agy-remediation-r20-hardware-review-20260929.json)
- [RST 확인·같은 store 27 수신 추가 기록](agy-remediation-r20-rst-video-supplement-20260929.json)
- [두 번째 사용자 RST·같은 store 28 재수신 기록](agy-remediation-r20-second-rst-supplement-20260929.json)
- [38.96초 영상·값 복구·C2 LCD 유지 판정](agy-remediation-r20-video04-review-20260929.json)
- [38.96초 원본 영상 archive receipt](agy-remediation-r20-video04-artifacts-20260929.json)
- [두 번째 RST 재수신 원본 archive receipt](agy-remediation-r20-second-rst-artifacts-20260929.json)
- [실물 원본·세 영상 archive receipt](agy-remediation-r20-hardware-artifacts-20260929.json)
- [실물 원본 자료 archive](agy-remediation-r20-hardware-artifacts-20260929.zip)
- [누적 진행 기록](agy-remediation-progress-20260928.md)
