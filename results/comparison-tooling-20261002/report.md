# 남은 비교 도구 구현·검증 결과

2026-10-02, 로컬 main 작업 파일 기준. [설계](../../docs/design/2026-10-02-comparison-tooling.md)와
[계획](../../docs/plans/2026-10-02-comparison-tooling.md)에 따라 운영 도구를 구현했다.
기존 문서 정비와 원본 실험 자료를 보존했으며 commit·push·후보 모델 실행·보드 접근은 수행하지 않았다.

## 구현한 동작

| 대상 | 구현·검증한 내용 |
|---|---|
| 예산·후속 회차 | 최초 7,200초, 후속 최대 3회/누적 7,200초, 실패 시간 차감, 동시 실행 차단, 자기 직전 frozen source/profile/input에서 시작, 고정 feedback, RM 전체 pass 시 종료 |
| 실행 진입·기록 | comparison run의 infrastructure/capability receipt와 input/profile/reference hash 연결. 실제 사용 receipt와 근거 사본 보존. 기존 comparison 없는 pilot gate 유지 |
| 실패 비용 집계 | completed 조건부 표와 별도 전체 시도/timeout/abort/환경 실패/미측정 coverage. 최초·후속·누적·근거가 검증된 RM 도달 비용. 후속은 독립 반복 수에서 제외 |
| production 의미 | source/수신 300초 경계, stale/future/손상·sequence·clock 재설정 oracle, 실제 코드 adapter subprocess·production/linkage hash·로그·값 비교 |
| 실물 관측 도구 | 단일 serial 소유 write/read capture, 기존 queue 분리, 실제 송신 byte/hash·수락/표시 marker 구분. frame에 묶인 수동 광학 annotation·media hash·clock alignment·지연 결합 |
| 독립 복원 | clean source bundle·operator/하위 evidence·ignored 파일·artifact 목록/hash. 새 root에서 기존 checkout 없이 E2E 검증. 원본 manifest와 복원용 경로 사본 보존 |
| 기준 입력 복구 | 원본 sender raw bytes와 `7923f96` source 대조. fixture/frame/hash·UTC·5초 간격·collector 호출 복구. Git 줄바꿈 변환 방지. 선택한 reference를 준비된 baseline에 연결 |

기준 영상의 58%·82%는 5h/weekly **남은 비율**이며 사용 비율은 42%·18%다.
원본은 오래된 source를 담은 synthetic stale frame이다. 과거 영상 판정이나 원본 파일을 바꾸지 않고
[RM 목록](../../docs/experiments/reference-match-matrix.md)에 날짜·범위가 있는 후속 정정을 기록했다.

## 검증 근거

- 전체 unittest **176개: 175 통과, 1 skip**, 43.165초. skip은 Windows의 symlink 생성 권한 부재로 기존 시험 한 건이다.
- 정상 E2E 예제·provider matrix·새 CLI help 통과. C1~C8이 partial인데 product_pass를 선언한 자료는 `PRODUCT_PASS_REQUIRES_CORE_RESULTS`로 거부했다.
- 복구 seq 0/1을 원래 0/5초 간격으로 replay해 두 frame 모두 수락하며 source stale을 유지했다. 이는 offline oracle 결과다.
- package create/restore CLI를 임시 예제에서 실행했다. 원래 checkout을 다른 경로로 옮긴 뒤 독립 root에서 result 검증과 ignored frame 복원을 통과했다. 틀린 trusted manifest hash는 거부했다.
- 새 input hash의 operator 도구/reference 변조 감지, 네 번째 후속·예산 소진·동시 실행·다른 profile 거부, 실제 dummy subprocess 종료 비용·receipt 보존을 확인했다.
- candidate 목록은 필수 MD 3개를 유지한다. 새 operator 코드·reference 원본을 candidate 입력에 추가하지 않았다.
- 전체 로컬 문서 링크와 `git diff --check` 통과. 최종 검사 수·명령·종료 코드·SHA-256은 [evidence](evidence.json), 전체 출력은 [unittest](unittest-final.log)에 저장했다.

첫 전체 검증에서 임시 Git snapshot의 줄바꿈 변환으로 reference hash 불일치가 발견됐다.
원본 reference를 binary로 보존하는 Git attributes를 추가하고 해당 snapshot 시험과 전체 suite를 통과했다.

## 새 검토자의 발견과 수정

`executing-plans`·`requesting-code-review` 절차의 새 검토자는 Critical 0건, Important 3건을 재현했다.
세 항목 모두 재현 시험이 실패하는 것을 확인한 뒤 수정하고 최종 전체 suite를 통과했다.

| 발견 | 수정·회귀시험 |
|---|---|
| 이전 candidate inventory를 변경하면 후속이 새 목록으로 승인 | 복사 전 이전 evidence hash 검증. `test_followup_rejects_replaced_candidate_inventory` |
| RM report만 패키지에 담고 실제 관측 근거 누락 | 하위 evidence를 manifest inventory에 등록하고 복원 시 의존성 확인. feedback·preflight 근거와 frozen reference도 보존. `test_package_restores_reference_review_dependencies_and_frozen_stimulus` |
| optical expected/observed를 둘 다 42로 쓰면 실제 전송 80과 무관하게 pass | hashed 실제 전송 frame에서 expected 값 확인. `test_optical_requires_acceptance_correct_values_and_bound_media` |

Minor·유보한 코드 결함은 보고되지 않았다. 검토자가 판단을 보류한 실제 보드·계정 권한·
adapter production 연결의 수동 검토는 이번 도구 검증의 합격 주장에 포함하지 않는다.

## 실제 실행 전에 남은 확인

도구 구현 완료와 실제 비교 준비 완료는 별개다. [현재 준비 상태](../../docs/experiments/next-comparison-readiness.md)에 남긴 항목은 다음과 같다.

- 실제 CLI/model/profile에서 capability·권한·계측을 새로 관측하고 receipt를 작성한다.
- 후보 생산 코드에 adapter를 연결하고 같은 artifact를 보드에서 평가한다. 실제 LCD·BOOT·단절/재시작·시각 anchor·정밀 timing을 측정한다.
- 광학 값 판독과 media clock alignment는 운영자 확인이다. 영상 내용을 자동 인식하거나 전 요구의 제품 합격을 자동 판정하지 않는다.
- 실제 후보의 build artifact/실물 evidence package를 제작·복원한다. 현재 복원 검증은 controlled incomplete E2E 예제다.
- 새 공통 입력·순서·profile·한도를 동결해 비교를 시작한다. 기존 baseline tag와 과거 판정은 유지한다.

명령과 파일 형식은 [운영자 도구 안내](../../docs/experiments/comparison-tooling.md)를 따른다.
