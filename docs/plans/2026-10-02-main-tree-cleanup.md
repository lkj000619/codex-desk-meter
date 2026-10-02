# main 파일 트리·문서 정리 계획

작성일: 2026-10-02. 상태: **정리·검증 완료 / 커밋 전**. 기준: 로컬 `main`, HEAD `eb69163`.

## 목표와 선택한 방식

[파일 트리 평가](../../results/main-tree-review-20261002/report.md)의 T01~T04를 정리한다.
문서 역할은 [문서 지도](../DOCUMENTATION_MAP.md)를 따르며, 현재 준비 상태는
[다음 비교 준비 상태](../experiments/next-comparison-readiness.md)에서 관리한다.

사용자는 다음 두 방식을 선택했다.

- 과거 계획 2개를 작성일이 있는 이름으로 `docs/archive/plans/`에 이동하고 참조를 갱신한다.
- 보고서가 참조하는 검증 로그 3개를 검토한 뒤 해당 파일만 Git에 선별 등록한다.

## 작업 상태

- [x] T01: `results/README.md`의 한·영 중복을 줄이고 결과 종류·보고서 링크를 정리했다. 고유한 집계·archive 설명은 운영 관리로 모았다.
- [x] T02: 기존 단회 프로토콜과 gate의 새 비교 안내를 현재 준비 상태에 연결했다.
- [x] T03: 로그 3개의 내용·encoding·SHA-256을 확인하고 좁은 ignore 예외와 byte 보존 속성을 적용했다. 세 로그만 Git index에 등록했다.
- [x] T04: 2026-09-13의 E2E·host pipeline 계획을 보관하고 역사적 적용 범위와 이동 경로를 안내했다.
- [x] 문서 링크·Git 등록 byte·원본 보존·diff 형식을 검증하고 후속 보고서를 연결했다.

## 완료 조건과 보존 범위

- 과거 계획의 원문은 보존하고, 현재 상태를 안내하는 날짜가 있는 주석만 추가한다.
- 과거 평가의 판정·원본 evidence·동결 commit/tag와 당시 파일 목록을 변경하지 않는다.
  과거 경로는 역사적 목록에 남기고 날짜가 있는 이동 안내를 덧붙인다.
- 보고서의 현재 링크는 이동한 경로로 연결한다. 평가 당시 snapshot은 그대로 보존한다.
- 검증 로그는 세 파일만 등록하고 원래 encoding·줄바꿈을 포함한 byte와 SHA-256을 유지한다.
- 코드·schema·fixture·reference·보드 관측 원본을 변경하지 않는다.
- 로컬 Markdown 파일 링크 누락 0건, `git diff --check` 통과와 선택한 파일의 Git blob 검증을 기록한다.
- commit·push와 실제 후보·보드 실행은 이번 정리 작업에 포함하지 않는다.

검증과 후속 적용 범위는 [정리 보고서](../../results/main-tree-cleanup-20261002/report.md)와
[검증 데이터](../../results/main-tree-cleanup-20261002/evidence.json)에 기록했다.

## 후속 커밋 요청 (2026-10-02)

사용자가 정리 이후 커밋을 요청했다. 앞선 도구 구현·문서 정비와 검증 기록을 함께 등록한다.
이 지시는 위 정리 당시의 커밋 제외 범위 이후에 적용한다.
과거 영상 검토의 원본 링크는 [artifact 목록](../../results/codex-reference-upload-20261001/artifact-inventory.json)으로
연결하고, 영상·이미지·flash log·binary·runtime lock은 원래 로컬 경로에 보존한다.
저장소에는 검토·전송 기록과 원본 위치·byte 수·SHA-256을 포함한다.
등록 범위와 링크·원본 byte·회귀시험을 확인한 뒤 로컬 main에 커밋한다.
