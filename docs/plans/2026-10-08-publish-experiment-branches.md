# 실험 구현 브랜치 원격 보존

목표: 첫 비교 블록의 실제 최초·후속 17회 동결 구현을 GitHub에서 회차별로 확인할 수 있게 보존한다. 기존 파일럿·준비·reference 브랜치 4개도 현재 커밋 그대로 게시한다.

상태: 2026-10-08 원본 17회·기존 4개 branch 원격 게시·SHA 21개 확인 완료. 검증 기록과 소스 목록 작성 완료.

범위와 방법:

- 실행·평가가 종료된 5개 series의 17개 `comparison-source.bundle`을 ledger SHA-256 및 동결 commit과 대조한다. 준비만 했던 미실행 run은 포함하지 않는다.
- 기존 bare archive 방식처럼 후보 checkout 밖의 전용 bare 저장소에 원본 bundle을 가져온다. 원본 구현을 `experiment/formal-comparison-20261004/<run-id>` 브랜치로 참조한다.
- 기존 `experiment/` 3개와 `lkj000619/codex-reference-20260929`는 현재 commit과 이름을 유지한다. 정식 17회와 과거 파일럿·준비·기준 ref를 구분한다.
- 기존 원격 ref와 충돌 여부, 파일 크기를 확인한 뒤 21개 ref를 원격에 게시한다. 후보 재실행·source 수정·기존 commit 변경·main 병합은 이 작업의 범위에 없다.
- 원격 branch SHA와 동결 SHA의 일치를 검증하고 결과 목록을 `results/formal-comparison-20261004/`에 기록한다. 실행 결과 문서·문서 지도·현재 준비 상태에서 목록으로 연결한다.

완료 조건:

- [x] 실제 17회 원본 bundle hash와 commit 확인.
- [x] 회차별 17개 및 기존 4개 branch 게시, 21개 원격 SHA 검증.
- [x] 원본 ledger·bundle·평가·동결 commit 보존 확인.
- [x] 브랜치 목록·검증 기록 문서화 및 운영 문서 branch 게시 내용 검증. 게시 commit은 운영 branch의 원격 SHA로 확인한다.

원본 판정은 [실행 기록](../../results/formal-comparison-20261004/report.md)을 따른다. 원격 보존은 제품 합격·비교 적격성·새 실험 실행 승인을 변경하지 않는다.

[게시 결과·회차별 소스](../../results/formal-comparison-20261004/branch-publication-20261008.md) · [원격 검증 기록](../../results/formal-comparison-20261004/branch-publication-20261008.json).
