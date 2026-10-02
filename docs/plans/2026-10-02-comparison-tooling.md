# 남은 실험 도구 구현 계획

목표: [설계](../design/2026-10-02-comparison-tooling.md)에 따라 R01~R08의 도구 공백을 구현한다.
상태: 도구 구현·오프라인 검증 완료. 기존 문서 수정과 미추적 원본을 보존하며 현재 main 작업 파일에서 이어서 작업했다. 실제 후보·보드·표면 관측과 새 조건 동결은 readiness에 남긴다.
작업 방식: 현재 세션에서 직접 구현하고, 각 항목의 실패 재현·회귀시험·전체 시험으로 검증한다.

## 검토 초점

- timeout·실행 중단 뒤 잔여 예산이 되살아나거나 동시 run이 시작되지 않음.
- 후속 실행에 다른 profile·기준 입력·타 후보 source를 섞지 않음.
- 누락/잘못된 제품 결과의 소비 비용과 미측정 token을 숨기지 않음.
- 새 frame의 수신이 오래된 source를 신선한 값으로 바꾸지 않음.
- package 경로 이탈·evidence 누락과 host write를 실물 pass로 해석하는 오류를 차단함.

## 작업과 완료 조건

1. [x] `scripts/summarize-benchmark.py`·`test_summarize_benchmark.py`: 전체 시도와 실패 비용·비용 coverage를 추가. 성공 completed+timeout에서 전체 성공률 0.5, 두 시도의 비용 합계 확인.
2. [x] `scripts/comparison_manager.py`·`scripts/comparison.py`·`test_comparison_manager.py`: 최초/후속 ledger, frozen source 복사·feedback hash, 회차·누적 예산·reference 판정. 4번째 후속·예산 초과·동시 실행·다른 profile을 거부하는 시험 확인.
3. [x] `scripts/benchmark.py`·operator schema·runner 시험: ledger run의 실제 timeout·종료 기록과 인프라 receipt 연결. 과거 pilot gate 회귀 유지.
4. [x] `scripts/product_observation.py`·`scripts/observe-product.py`·`test_product_observation.py`: source/수신 clock oracle와 단일 소유 capture/replay. 오래된/미래 source·손상·재연결·ACK 없는 관측을 검증.
5. [x] `scripts/evidence_package.py`·`scripts/package-evidence.py`·`test_evidence_package.py`: package 목록·source/evidence 복원과 hash·경로 검증. 원래 checkout 없이 유효 result 검증, 누락·변조·경로 이탈 거부.
6. [x] reference 원본 fixture/frame/명령 복구·기계 목록과 capability receipt 검증을 연결. 복구 불가능하거나 실제 측정이 필요한 항목은 근거와 함께 남김.
7. [x] readiness·운영 안내 갱신, 전체 unittest·정상/부정 CLI·링크·`git diff --check` 실행. 제품/실물 pass와 도구 구현 완료를 구분해 보고.

검증 기록은 `results/comparison-tooling-20261002/`에 저장한다. 과거 tag·원본 판정·evidence는 변경하지 않는다.

## 완료 기록

[결과 보고서](../../results/comparison-tooling-20261002/report.md)와
[기계 근거](../../results/comparison-tooling-20261002/evidence.json): 176개 중 175 통과, 기존 Windows symlink 1개 skip.
정상/부정 CLI, 단일 backend·source/수신 시각, 독립 package 복원과 링크를 확인했다.
새 검토자가 재현한 Important 3건은 실패 시험→수정→통과 후 전체 suite로 검증했다.
변경된 inventory의 재승인, RM 근거 누락, stimulus와 무관한 optical 기대값을 수정했다.

실행 방법은 현재 main에서 사용자 요청에 따라 기존 변경을 보존하는 직접 구현으로 선택했다.
스킬의 기본 폴더·commit 작업 단계 대신 프로젝트 계획/결과 경로에 기록하며,
commit·push와 실제 비교/보드 실행은 수행하지 않았다. 제품 합격을 확인한 상태가 아니다.
