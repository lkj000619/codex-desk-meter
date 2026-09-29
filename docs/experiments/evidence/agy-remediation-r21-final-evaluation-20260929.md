# AGY r21 보완 실험 최종 평가

**평가 작성 완료. 제품 전체 판정은 `product_pass: false`이며, 이 문서는 정식 결과 스키마나 순위 결과가 아니다.** 기존 시험 기록, 검증 자료와 보존된 실물 영상만 평가했다. 구현 commit은 `8eb40c0ceb47d1f6585307575a09c7dc74f89d51`이다. 보완 실험은 원래 단회 비교와 별도이며 순위 대상이 아니다.

## 결과 요약

AGY는 r21 작업을 871.828초에 정상 종료했다. 독립 검토에서 CTest 4개, Python 시험 25개, 기존 평가 29개와 ESP-IDF ESP32-S3 빌드가 성공했고, 결과 검증도 통과했다. 독립 빌드 바이너리를 수정 없이 COM3 보드에 올렸으며 ELF 해시가 부팅 로그와 일치했다. 20초 부팅 관측에는 panic/stack overflow 징후가 없었다. 기존 sequence store를 유지한 송신에서 순번 91·92의 프레임 수신 로그를 확인했다. 이는 빌드·업로드·해당 수신 사례의 증거이며 제품 전체 합격을 뜻하지 않는다. [독립 검토](agy-remediation-r21-independent-review-20260928.json), [실물 업로드·수신 검토](agy-remediation-r21-hardware-review-20260929.json), [실물 증거 보존 receipt](agy-remediation-r21-hardware-artifacts-20260929.json)

| 영역 | 최종 상태 | 판정과 근거 |
|---|---|---|
| C1 | `pass` | 독립 fresh build의 ESP-IDF v5.3.2 ESP32-S3 설정·빌드 성공. [독립 검토](agy-remediation-r21-independent-review-20260928.json) |
| C2 | `pass` | 54.33초 video01 중 화면 전체를 확인할 수 있는 연속 약 34초 구간에서 LCD와 세 화면 레이아웃 확인. [video01 검토](agy-remediation-r21-video01-review-20260929.json), [원본 receipt](agy-remediation-r21-video01-artifacts-20260929.json) |
| C3 | `partial` | 고정 fixture 수치가 화면에 표시되고 진단 순번 148·340·344·351 및 host frame 자료와 연결됨. 모든 provider/window matrix와 조건별 완전성은 이 영상만으로 확정하지 않음. [video01 검토](agy-remediation-r21-video01-review-20260929.json), [video02 검토](agy-remediation-r21-video02-review-20260929.json) |
| C4 | `partial` | 글로벌 리셋 화면 전환과 내용 표시 관측. 모든 fixture 경계·값 정확도에 대한 독립적인 화면별 매핑은 완료되지 않음. [video01 검토](agy-remediation-r21-video01-review-20260929.json), [video02 검토](agy-remediation-r21-video02-review-20260929.json) |
| C5 | `not_run` | 리셋 기록 없음/경과시간 미상 fixture를 대상으로 default 화면을 확정하는 실물 화면 시험 근거가 없음. 독립 parser/host 시험은 이 C5 실물 판정을 대신하지 않음. [독립 검토](agy-remediation-r21-independent-review-20260928.json), [평가 기준](../evaluation-contract.md) |
| C6 | `partial` | 화면의 값·상태·진단 정보 표시를 관측했으나 모든 출처·조회 시각 표현을 각 고정 조건과 대조한 판정은 미완료. [video01 검토](agy-remediation-r21-video01-review-20260929.json), [video02 검토](agy-remediation-r21-video02-review-20260929.json) |
| C7 | `partial` | host 회귀 시험과 복구 표시 증거가 있음. 영상의 RST/USB 전원 재인가 복구는 boot+송신 주기 대기를 포함하며, 오류 주입·USB 통신 단절·복구 전체 gate를 충족했다고 보지 않음. [독립 검토](agy-remediation-r21-independent-review-20260928.json), [video02 검토](agy-remediation-r21-video02-review-20260929.json) |
| C8 | `partial` | 관측한 세 짧은 BOOT 동작의 반응 추정치는 300ms 이내. PC 재수집·수신→LCD 2초와 실물 긴 hold 단일 event는 입증되지 않음. [손가락 timing 검토](agy-remediation-r21-finger-timing-review-20260929.json), [독립 검토](agy-remediation-r21-independent-review-20260928.json) |

위 C 판정은 제품 계약의 C1~C8 각각에 대한 증거 상태다. C1/C2 및 일부 화면 기능의 확인으로 나머지 필수 조건을 대체하지 않는다. 자세한 기능 범위와 별도 interface 상태는 아래 표에 기록한다. [제품 계약](../../PRODUCT_CONTRACT.md), [평가 계약](../evaluation-contract.md)

## 입력·복구 시간 관측

| 관측 | 정량 결과 | 해석과 제한 |
|---|---|---|
| 짧은 BOOT 화면 반응 | video02의 세 사용자 식별 손가락 동작 기준 첫 변화 약 **33–167ms**, **33–200ms**, **100–200ms**. 새 내용 완료는 약 **100–200ms**, **100–233ms**, **167–233ms**. | 원속 PTS 약 33.33ms 간격, 126 frame 검토(중복 1, 고유 125). 시작점은 수동으로 추정한 구간이므로 세 사례에 대한 영상 proxy다. 세 사례 모두 300ms 이내지만 전기 접점/debounce 완료 시각이나 전체 입력 성공률은 아니다. 사용자 식별 근거 및 상세 범위: [손가락 timing 검토](agy-remediation-r21-finger-timing-review-20260929.json), 원본 video02 SHA-256 `301a041a35cab7f256b1fc0725929b6c1f9dcff271ee4012ca9face06749203c`. |
| host 입력 probe | 10개 sample phase 각각에서 50ms·100ms press, release 50ms를 둔 연속 두 입력, 3초 hold 한 event 및 16-entry FIFO 동작을 확인. 30ms pulse는 10 phase 모두 event 0개. | ideal host sample 조건으로 실물 접점, 스케줄 지연, LCD latency를 입증하지 않음. 30ms 보장이나 AGY 운영 문서의 무계측 100%/sub-ms 주장을 채택하지 않음. [독립 검토](agy-remediation-r21-independent-review-20260928.json) |
| RST 이후 표시 복구 | video02에서 blank 전환→값 **약 6.7–7.0초**. | 부팅 및 주기 송신 대기 포함. packet receive→LCD 시간 아님. [video02 검토](agy-remediation-r21-video02-review-20260929.json), [verification](agy-remediation-r21-video02-verification-20260929.json) |
| USB 전원 재인가 후 표시 복구 | video02에서 재연결 후 LED/LCD 전원 복귀→값 **약 2.3–2.6초**. | boot 및 다음 송신 대기 포함. LCD 대기 UI와 실제 값 출현은 별도로 판독됨. packet receive→LCD 시간 아님. [video02 검토](agy-remediation-r21-video02-review-20260929.json) |
| packet receive→LCD | 정밀 시간 `null`, `not_verified`. | 실제 값과 진단 순번은 관측했으나 동일 기준 시계의 packet arrival 시작 사건이 영상에 없음. reset/재전원 구간으로 대체할 수 없음. [video02 검토](agy-remediation-r21-video02-review-20260929.json), [coverage correction](agy-remediation-r21-evidence-coverage-correction-20260929.json) |
| 전원 유지 물리 USB cable 제거·재열거 | `not_run`; 현재 구성에서는 `not_feasible_in_current_configuration`. | 보드에 배터리가 없어 cable 제거 중 전원을 유지할 수 없다고 사용자가 확인. 면제·pass·제품 결함으로 계산하지 않으며 활성 사용자 과제에서 제외됨. 재전원 복구 관측은 별도. [USB feasibility 기록](agy-remediation-r21-usb-test-feasibility-20260929.json) |

video01의 세 화면 변화 PTS는 원속 30fps 자료에서 확인됐지만 그 장면의 버튼 시작점은 특정하지 못했다. 오디오 파형의 6.296초 peak는 눌림/놓음/취급 소음으로 분류되지 않아 latency로 채택하지 않았다. 사용자가 식별한 video02 손가락 장면으로 관측된 세 사례에 한해 이전의 시작점 불확실성을 갱신한다. audio input 미지원으로 소리를 직접 들었다고 주장하지 않는다. [PTS 재검토](agy-remediation-r21-video-timing-recheck-20260929.json), [audio 검토](agy-remediation-r21-audio-click-review-20260929.json), [손가락 timing 검토](agy-remediation-r21-finger-timing-review-20260929.json)

## 기능 및 interface 평가

| ID | 상태 | 현재 자료에서 확인한 내용과 남은 한계 |
|---|---|---|
| F1 PC 사용량 collector | `pass` (고정 fixture 범위) | AGY 작성 credential-free fixture collector와 host 회귀시험 범위는 확인됐다. 실제 사용자의 Codex 계정 잔여량/usage collector는 구현되지 않았다. [독립 검토](agy-remediation-r21-independent-review-20260928.json) |
| F2 정규화·출처 분리 | `pass` (검증된 fixture 범위) | parser·fixture 관련 host 회귀시험이 통과했다. 전체 provider matrix에 대한 완결 주장으로 확대하지 않는다. [독립 검토](agy-remediation-r21-independent-review-20260928.json) |
| F3 PC→ESP32 transport | `partial` | 기존 sequence store를 사용한 실제 USB serial 송신과 seq 91·92 수락 로그 확인. 오류 응답·재열거·전송 무결성 전체 contract gate까지 확인한 것은 아님. [독립 검토](agy-remediation-r21-independent-review-20260928.json), [실물 검토](agy-remediation-r21-hardware-review-20260929.json) |
| F4 receiver/state | `partial` | host 회귀 시험, 실제 수신 순번과 영상의 진단 화면이 있음. packet-to-render 시간과 전체 오류/복구 state matrix는 미확정. [독립 검토](agy-remediation-r21-independent-review-20260928.json), [video02 검토](agy-remediation-r21-video02-review-20260929.json) |
| F5 LCD GUI | `partial` | 세 화면, 값 표시, 정상 전환, 회전 후 표시 유지 관측. 정식 G1–G6 조건·점수는 별도 아래 참조. [video01 검토](agy-remediation-r21-video01-review-20260929.json), [video02 검토](agy-remediation-r21-video02-review-20260929.json) |
| F6 입력·갱신 | `partial` | 사용자 확인 짧은 입력 반응과 세 영상 timing 사례 있음. 실물 긴 hold event 수, PC 수동 재수집 동작 및 전체 attempt 성공률은 입증되지 않음. [사용자 확인](agy-remediation-r21-owner-confirmation-20260929.json), [손가락 timing 검토](agy-remediation-r21-finger-timing-review-20260929.json) |
| F7 글로벌 리셋 표시 | `partial` | 글로벌 리셋 화면 전환과 값을 관측. 리셋 기록 없음 등 요구 조건 전체를 다룬 시나리오 점수는 미확정. [독립 검토](agy-remediation-r21-independent-review-20260928.json), [video01 검토](agy-remediation-r21-video01-review-20260929.json) |
| F8 빌드·배포·관측 | `pass` | 독립 ESP-IDF build, artifact hash, 성공한 result validator와 manifest/evidence join, build logs, 동일 binary의 실물 업로드 및 boot ELF identity를 확인했다. [독립 검토](agy-remediation-r21-independent-review-20260928.json), [실물 검토](agy-remediation-r21-hardware-review-20260929.json), [실물 artifact receipt](agy-remediation-r21-hardware-artifacts-20260929.json) |
| F9 자율 하드웨어 기능 | `partial` | IMU 회전 구현, host 시험 및 영상의 회전 표시가 있고 세 후보 선택 문서가 존재한다. AGY의 자체 점수는 잠정 22/30이며 정식 독립 점수는 `null`. [독립 검토](agy-remediation-r21-independent-review-20260928.json), [video02 검토](agy-remediation-r21-video02-review-20260929.json), [AGY F9 후보·자체 평가 원문](C:/Espressif/benchmark-remediation/evaluation-r21-20260928/checkout/docs/agent-runs/20260928-agy-remediation-r21/hardware-feature-selection.md) |
| I1 collector | `pass` (credential-free fixture) | 고정 fixture collector 범위. 실제 Codex usage source collector 없음. 실 계정 연동은 별도 범위. [독립 검토](agy-remediation-r21-independent-review-20260928.json) |
| I2 normalization | `pass` (검증된 fixture 범위) | parser/host fixture 시험 통과. 전체 provider matrix 통과 주장은 하지 않음. [독립 검토](agy-remediation-r21-independent-review-20260928.json) |
| I3 transport | `partial` | 실제 USB frame 수락 사례는 있으나 reconnect/process-restart 수용 계약의 전체 실물 시험은 없음. [실물 검토](agy-remediation-r21-hardware-review-20260929.json) |
| I4 receiver/state | `partial` | 수신·복구 화면 사례 및 host 시험 일부 확인. 동기화 timing, 전 상태 조합 및 영속성 계약은 완결되지 않음. [독립 검토](agy-remediation-r21-independent-review-20260928.json), [video02 검토](agy-remediation-r21-video02-review-20260929.json) |

F/I 기능 구분은 [제품 계약](../../PRODUCT_CONTRACT.md), [기능 비교 기준](../feature-comparison.md), [pipeline 계약](../host-device-pipeline-contract.md)에 따른다. AGY 제출 결과의 schema/evidence join은 통과했고 이 평가에서도 F8 고유 요구인 build·hash·log·manifest/schema 재현성과 배포 identity를 확인해 `pass`로 판정했다. 다른 부분 gate의 상태를 F8에 전가하지 않는다. C7, F3/F4/F7, I3/I4는 각각의 실제 검증 범위에 따라 `partial`이다. 전체 제품 합격은 이 개별 항목의 판정과 별개다. 현 결과에는 실 계정 credential/source 접근이 없었다. 실제 Codex usage integration은 소유자 관리의 별도 live-integration 작업으로 분리된다.

## GUI 및 F9 점수

video01은 LCD 기본 출력 gate인 C2에 대해 30초 이상 보이는 구간과 세 레이아웃을 제공한다. video02 및 video01에서 provider/글로벌 리셋/진단 화면, 실제 값, BOOT 탐색과 회전 후 표시 유지를 관찰했다. 비스듬한 회전으로 투영 면적이 줄어든 일부 frame은 소등으로 판정되지 않았다. 미세 flicker/tearing 무결함까지 입증하지 않는다. [video01 검토](agy-remediation-r21-video01-review-20260929.json), [video02 검토](agy-remediation-r21-video02-review-20260929.json)

정식 G1–G6 점수는 각각 `null`, 총점 `null`이다. 50cm 정면 관찰, 조명·밝기·카메라 노출 고정, 같은 fixture의 오류/stale/unknown 과제 및 모델을 가린 판정이 증거에 없다. 따라서 자료만으로 가능한 서술 관찰은 남기되 0–3 rubric 점수로 바꾸지 않는다. AGY가 이미 알려진 자료라 blind 평가라고도 주장하지 않는다. [AGY의 F9 후보 3개·선택 근거·잠정 점수 원문](C:/Espressif/benchmark-remediation/evaluation-r21-20260928/checkout/docs/agent-runs/20260928-agy-remediation-r21/hardware-feature-selection.md)은 IMU 회전 선택, RTC 및 배터리 ADC 탈락, host 검증 계획과 자체 점수 4+4+4+6+4=22/30을 기록한다. 이 22점은 AGY의 잠정 자체평가이며 독립 정식 F9 점수는 `null`이다. 물리 IMU 잡음과 rubric 판정 조건이 입증되지 않았다. 기준: [GUI 및 F9 rubric](../feature-comparison.md), [독립 검토](agy-remediation-r21-independent-review-20260928.json).

## 공정성, 원래 순위, 전체 판정

r21은 고정 remediation prompt의 단회 보완이고 `ranking_eligible: false`다. 원래 r01 실패·정량 순위는 이 결과로 덮어쓰거나 재산정하지 않는다. 독립 검증자 probe는 후보 제품 코드와 분리한 평가 코드였으며, root는 평가/보존/검증 문서를 정리했고 제품 코드나 제품 시험 작성자가 아니다. AGY 운영 문서의 무계측 latency·성공률 주장은 채택하지 않는다. [독립 검토](agy-remediation-r21-independent-review-20260928.json), [결과 receipt](agy-remediation-r21-result-20260928.json), [coverage correction](agy-remediation-r21-evidence-coverage-correction-20260929.json)

정식 제품 전체 합격에는 C1–C8, I1–I4, F1–F9의 범위와 증거, C2 및 실물 gate가 필요하다. 현 자료에는 `not_run`·`partial`이 남아 있으므로 `product_pass: false`를 유지한다. 이 문서의 평가 작성 완료는 해당 합격 조건 충족 선언이 아니다. 판정 요약 및 항목별 구조화 자료는 이 문서와 같은 basename의 JSON addendum에 기록했다.
