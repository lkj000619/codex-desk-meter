# Codex 기준 제품 기능 도달 목록

상태: **2026-10-02 원본 stimulus 복구 반영. 실제 후보 RM 평가는 별도 실행.**

사용자 결정은 [운영 계약](comparison-operating-contract.md)을 따른다. 기준 firmware는
`7923f96`이며 fixture 기반 제품이다. 기준을 만족해도 전체 `product_pass` 합격은 별도다.
기존 source 코드를 후보에게 제공하거나 픽셀 단위 복제를 요구하지 않는다.

## 기준 증거

검토·전송 기록은 저장소 상대 경로로 연결한다. 원본 영상·flash log·binary는 별도 로컬
증거 보관 대상이며 [artifact 목록](../../results/codex-reference-upload-20261001/artifact-inventory.json)에
위치·byte 수·SHA-256을 기록했다. 실제 후보의 독립 복원 package와 구분한다.

- [최종 업로드 이력](../../results/codex-reference-upload-20261001/upload-receipt.json): 최종 firmware, 독립 flash 확인, seq 0·1 수락.
- [영상 검토](../../results/codex-reference-upload-20261001/user-video-01/video-review.md): 26.87초 영상 표본, 표시 58%·82%, 세 화면 순환, 진단 seq 1/result 0. 원본 표현은 보존하며 아래 후속 정정으로 값의 의미를 구분한다.
- [진행 비교](../../results/agy-codex-progress-comparison-20261001.md): 최종 Python 15개·CTest 4개, 역할·수정·실물 범위 제한.

## 확인된 reference 도달 대상

| ID | 관련 요구 | 고정할 stimulus | 기대 관찰 | 기준의 확인 범위 |
|---|---|---|---|---|
| RM1 | C1/F8 | ESP-IDF v5.3.2·esp32s3, 기준 artifact의 build/upload 절차 | 후보 firmware가 빌드되며 동일 artifact가 보드에서 실행됨 | 기준 제품 build와 최종 업로드 확인. 후보의 시험 개수를 15/4로 맞추라는 뜻이 아님 |
| RM2 | F1/F2/F3/I1/I2/I3 | 같은 fixture 파일과 collector 전송 명령. raw frame·sequence 기록 | PC fixture에서 정상 frame을 만들고 실제 장치가 해당 frame을 수락 | 기준 seq 0·1 수락. 모든 reconnect/오류 matrix가 확인됐다는 뜻이 아님 |
| RM3 | C2/C3/F4/F5/I4 | RM2의 유효 stale fixture·기준 시각 | LCD의 5h/weekly 남은 비율 58%·82%가 payload의 percent_remaining과 연결됨 | 영상 표본의 값 표시 확인. 사용 비율은 각각 42%·18%이며 합성 값임을 유지 |
| RM4 | C4/C6/F5/F7 | 글로벌 리셋·진단 페이지를 포함한 같은 fixture | 사용량·글로벌 리셋·진단의 세 정보 화면이 가시 출력됨 | 화면 종류·전환 확인. 모든 reset 경계와 출처/조회 시각의 완전성은 미확인 |
| RM5 | C8/F6 | 정상 부팅 후 BOOT 조작 | 사용량→글로벌 리셋→진단→사용량 또는 동일 정보를 제공하는 동등한 화면 탐색 | BOOT 장면과 페이지 순환 확인. 정밀 300ms 성공 판정은 별도 |

RM 항목의 `pass/partial/fail/not_run`과 증거를 기록한다. 모든 필수 RM 항목을
재현했을 때 reference 도달로 판정한다. 2026-10-02 후속 정정의 적용 범위는
원본 전송 fixture·frame과 표시 값의 의미다. 과거 영상 판정·firmware commit·원본 evidence는 변경하지 않는다.
[기계 목록](../../experiments/reference/codex-7923f96/reference-inputs.json)에 실제 raw fixture와 source commit 대조,
collector 호출·기준 UTC·seq 0/1 expected frame/hash·5초 간격을 연결했다.
원본의 오래된 source는 stale이며 새로운 전송 시각이 source freshness를 갱신하지 않는다.
같은 입력을 사용하는 후보 capture·광학 판정 형식은 [도구 안내](comparison-tooling.md)를 따른다.

## RM5 동등한 탐색의 공통 판정 절차

2026-10-02 후속 보완. 다음 후보 평가에 적용하며 과거 reference 영상 판정은 변경하지 않는다.
화면 개수·페이지 이름·배치의 일치를 요구하지 않는다. 다음 절차를 결과 확인 전에 고정한다.

1. RM2의 동일 fixture를 수신한 정상 부팅 상태를 시작점으로 삼고 시작 화면을 기록한다.
2. 후보가 제출한 정상 BOOT 조작 절차에 따라 사용량·글로벌 리셋·진단 정보를 찾는다.
   관측자는 조작 순서와 횟수, 각 정보가 보이는 장면, 시작 정보로 돌아오는 경로를 기록한다.
3. 세 정보에 모두 도달하고 BOOT가 실제 탐색에 사용되며 반복 탐색이 가능하면 pass다.
   세 페이지 순환, BOOT로 선택하는 탭, BOOT로 이동하는 스크롤/초점 방식 모두 인정한다.
   한 화면에 모든 정보를 배치한 경우에도 BOOT를 통한 영역 선택·탐색이 관측되어야 한다.
   고정 화면에 모두 표시되지만 BOOT가 동작하지 않으면 RM4와 구분해 RM5는 partial로 기록한다.
4. 일부 정보에만 도달하면 partial, 시험했으나 탐색이 전혀 작동하지 않으면 fail,
   조작 또는 영상 근거가 없어 확인하지 못했으면 not_run이다. 관측 도구 미지원은 제품 fail로 바꾸지 않는다.

공통 기록은 run/artifact hash, fixture/hash, 정상 부팅 여부, 시작 상태, 제출 조작 절차,
실제 조작 순서·정보별 영상 시점, 복귀 경로, 판정자와 evidence hash다.
동작 확인을 위한 조작 횟수·소요 시간은 기록하되 RM5에 새로운 최대 횟수나 300ms 합격선을
추가하지 않는다. BOOT debounce 후 300ms와 정식 GUI 품질은 C8/G에서 별도로 평가한다.
보드 RST·ROM 다운로드 모드·PC 수동 갱신은 BOOT 탐색의 대체 증거가 아니다.

## 기준에서 미입증이며 별도 평가할 항목

| 항목 | 기준의 상태 | 후보 평가 방식 |
|---|---|---|
| 30초 이상 연속 LCD 유지 | 26.87초 영상 표본으로 입증 불가 | C2의 전체 합격 조건으로 별도 판정; reference evidence와 혼동하지 않음 |
| BOOT 300ms·PC refresh 5초·수신→LCD 2초 | 정밀 측정 미완료 | C8/I3/I4 timing 증거가 있을 때 해당 범위만 판정 |
| null/오류/stale 전체 matrix와 full provider/window 정확성 | 일부 표시·host 시험이 있어도 전체 실물 매핑 미완료 | 고정 평가 시나리오를 추가하고 production-conformance에 기록 |
| powered USB 링크 단절·PC 프로세스 재시작·sequence store 유실 | 전체 수용 시험 미입증 | 별도 복구 시험; write receipt를 device ACK로 해석하지 않음 |
| RTC 전원 차단 holdover | 구현·자동 시험/준비 표시만 존재 | F9 후보 기능의 별도 검증; RM 필수 기능에 포함하지 않음 |
| IMU 회전 | 기준의 물리 회전만으로 자동 회전을 확정하지 않음 | 후보가 선택한 자율 기능을 자신의 근거로 평가 |
| G1~G6 정식 GUI 점수 | 동일 관찰 조건의 정식 점수 없음 | 기존 rubric의 광학 조건이 충족된 경우 별도 채점 |
| 실제 계정 자동 수집 | 미구현 | fixture cohort의 도달 필수 조건이 아닌 owner-only 후속 범위 |

## 입력 동결 전 보완

- [x] 기준의 실제 fixture 경로·hash·reference_time·명령·expected frame을 원본에서 복구.
- [x] RM2의 후보 sender frame과 수락·화면 관측을 연결하는 공통 capture 절차 지정. 실제 후보 관측은 대기.
- [x] 후보별 RM 판정 기록을 전체 C/F/I·product_pass와 구분해 보존하는 형식 지정.
- [x] 동등한 화면 탐색의 공통 판정 절차 확정(위 RM5 절차).
- [ ] 후보 실행 후 동일 절차를 각 후보에 적용하고 조작·영상·판정 근거를 기록. 실행 전 미완료가 정상이다.

이 목록은 추가 촬영이나 실험 재개를 요구하지 않는다. 기준에서 이미 확인한
자료를 복구·연결하는 작업과 다음 후보를 평가하는 작업을 구분한다.
