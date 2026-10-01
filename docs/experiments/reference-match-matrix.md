# Codex 기준 제품 기능 도달 목록

상태: **2026-10-02 기준 목록 초안. 확인된 증거와 미확인 항목을 분리.**

사용자 결정은 [운영 계약](comparison-operating-contract.md)을 따른다. 기준 firmware는
`7923f96`이며 fixture 기반 제품이다. 기준을 만족해도 전체 `product_pass` 합격은 별도다.
기존 source 코드를 후보에게 제공하거나 픽셀 단위 복제를 요구하지 않는다.

## 기준 증거

아래 원본은 로컬 evidence이며 이번 docs 커밋의 artifact package가 아니다.

- [최종 업로드 이력](<C:/Users/이광진/orca/codex-desk-meter/results/codex-reference-upload-20261001/upload-receipt.json>): 최종 firmware, 독립 flash 확인, seq 0·1 수락.
- [영상 검토](<C:/Users/이광진/orca/codex-desk-meter/results/codex-reference-upload-20261001/user-video-01/video-review.md>): 26.87초 영상 표본, 사용량 58%·82%, 세 화면 순환, 진단 seq 1/result 0.
- [진행 비교](<C:/Users/이광진/orca/codex-desk-meter/results/agy-codex-progress-comparison-20261001.md>): 최종 Python 15개·CTest 4개, 역할·수정·실물 범위 제한.

## 확인된 reference 도달 대상

| ID | 관련 요구 | 고정할 stimulus | 기대 관찰 | 기준의 확인 범위 |
|---|---|---|---|---|
| RM1 | C1/F8 | ESP-IDF v5.3.2·esp32s3, 기준 artifact의 build/upload 절차 | 후보 firmware가 빌드되며 동일 artifact가 보드에서 실행됨 | 기준 제품 build와 최종 업로드 확인. 후보의 시험 개수를 15/4로 맞추라는 뜻이 아님 |
| RM2 | F1/F2/F3/I1/I2/I3 | 같은 fixture 파일과 collector 전송 명령. raw frame·sequence 기록 | PC fixture에서 정상 frame을 만들고 실제 장치가 해당 frame을 수락 | 기준 seq 0·1 수락. 모든 reconnect/오류 matrix가 확인됐다는 뜻이 아님 |
| RM3 | C2/C3/F4/F5/I4 | RM2의 정상 fixture·기준 시각 | 값이 실제 LCD에서 읽히며 정상 fixture의 사용량 58%·82%가 payload와 연결됨 | 영상 표본의 값 표시 확인. 표시 수치가 합성임을 유지 |
| RM4 | C4/C6/F5/F7 | 글로벌 리셋·진단 페이지를 포함한 같은 fixture | 사용량·글로벌 리셋·진단의 세 정보 화면이 가시 출력됨 | 화면 종류·전환 확인. 모든 reset 경계와 출처/조회 시각의 완전성은 미확인 |
| RM5 | C8/F6 | 정상 부팅 후 BOOT 조작 | 사용량→글로벌 리셋→진단→사용량 또는 동일 정보를 제공하는 동등한 화면 탐색 | BOOT 장면과 페이지 순환 확인. 정밀 300ms 성공 판정은 별도 |

RM 항목의 `pass/partial/fail/not_run`과 증거를 기록한다. 모든 필수 RM 항목을
재현했을 때 reference 도달로 판정하되, 문서만으로 source/window 매핑이나 fixture
hash를 추정해서 채우지 않는다. 다음 입력 동결 전에 원본 collector에서 사용한
fixture·기준 시각·전송 명령·expected payload/hash를 이 표에 연결해야 한다.
현재 표는 그 고정 입력의 복구 완료를 주장하지 않는다.

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

- [ ] 기준의 실제 fixture 경로·hash·reference_time·명령·expected frame을 원본에서 복구.
- [ ] RM2의 후보 sender frame과 수락·화면 관측을 연결하는 공통 capture 절차 지정.
- [ ] 후보별 RM 판정 기록을 전체 C/F/I·product_pass와 구분해 보존하는 형식 지정.
- [ ] 동등한 화면 탐색의 관찰 조건을 모든 후보에게 동일 적용.

이 목록은 추가 촬영이나 실험 재개를 요구하지 않는다. 기준에서 이미 확인한
자료를 복구·연결하는 작업과 다음 후보를 평가하는 작업을 구분한다.
